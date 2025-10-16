"""PyQt interface mirroring the Tkinter Canasta GUI."""

from __future__ import annotations

from typing import Optional

from card_games.canasta.game import CanastaGame, CanastaPlayer, DrawSource, MeldError, card_point_value
from card_games.common.soundscapes import initialize_game_soundscape
from common.gui_base_pyqt import PYQT5_AVAILABLE, BaseGUI, GUIConfig

if PYQT5_AVAILABLE:  # pragma: no cover - UI specific branch
    from PyQt5.QtWidgets import (
        QAbstractItemView,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
else:  # pragma: no cover - fallback when PyQt is unavailable
    QAbstractItemView = None  # type: ignore
    QLabel = None  # type: ignore
    QListWidget = None  # type: ignore
    QListWidgetItem = None  # type: ignore
    QMainWindow = None  # type: ignore
    QMessageBox = None  # type: ignore
    QPushButton = None  # type: ignore
    QTextEdit = None  # type: ignore
    QVBoxLayout = None  # type: ignore
    QWidget = None  # type: ignore


class CanastaPyQtGUI(QMainWindow, BaseGUI):
    """Lightweight PyQt front-end with the same controls as the Tk GUI."""

    def __init__(
        self,
        *,
        game: Optional[CanastaGame] = None,
        player_name: str = "You",
        enable_sounds: bool = True,
        config: Optional[GUIConfig] = None,
    ) -> None:
        if not PYQT5_AVAILABLE:  # pragma: no cover - defensive guard
            raise RuntimeError("PyQt5 is required to launch the Canasta PyQt GUI")

        QMainWindow.__init__(self)
        config = config or GUIConfig(
            window_title="Card Games - Canasta (PyQt)",
            window_width=1000,
            window_height=720,
            theme_name="forest",
            enable_animations=True,
            enable_sounds=enable_sounds,
        )
        BaseGUI.__init__(self, self, config)
        self.sound_manager = initialize_game_soundscape(
            "canasta",
            module_file=__file__,
            enable_sounds=config.enable_sounds,
            existing_manager=self.sound_manager,
        )

        if game is None:
            players = [
                CanastaPlayer(name=player_name, team_index=0, is_ai=False),
                CanastaPlayer(name="AI East", team_index=1, is_ai=True),
                CanastaPlayer(name="Partner", team_index=0, is_ai=True),
                CanastaPlayer(name="AI West", team_index=1, is_ai=True),
            ]
            self.game = CanastaGame(players)
        else:
            self.game = game

        self.human_index = next((idx for idx, player in enumerate(self.game.players) if not player.is_ai), 0)
        self.phase = "draw"

        self.central = QWidget(self)
        self.setCentralWidget(self.central)
        self.status_label: QLabel
        self.discard_label: QLabel
        self.stock_label: QLabel
        self.hand_list: QListWidget
        self.melds_display: QTextEdit
        self.log_widget: QTextEdit

        self.build_layout()
        self.update_display()

    def build_layout(self) -> None:
        """Construct the PyQt widgets."""

        layout = QVBoxLayout()
        self.central.setLayout(layout)

        self.status_label = QLabel("Click a draw button to begin your turn.")
        layout.addWidget(self.status_label)

        info_bar = QHBoxLayout()
        self.discard_label = QLabel("Discard: —")
        self.stock_label = QLabel("Stock: —")
        info_bar.addWidget(self.discard_label)
        info_bar.addWidget(self.stock_label)
        layout.addLayout(info_bar)

        body = QHBoxLayout()
        layout.addLayout(body)

        self.hand_list = QListWidget()
        self.hand_list.setSelectionMode(QAbstractItemView.MultiSelection)
        body.addWidget(self.hand_list, 2)

        self.melds_display = QTextEdit()
        self.melds_display.setReadOnly(True)
        body.addWidget(self.melds_display, 2)

        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        layout.addWidget(self.log_widget, 1)

        button_bar = QHBoxLayout()
        layout.addLayout(button_bar)

        actions = [
            ("Draw Stock", self.draw_from_stock),
            ("Take Discard", self.draw_from_discard),
            ("Lay Meld", self.lay_selected_meld),
            ("Discard", self.discard_selected_card),
            ("Go Out", self.go_out),
            ("Next Turn", self.end_turn),
        ]
        for label, callback in actions:
            button = QPushButton(label)
            button.clicked.connect(callback)  # type: ignore[arg-type]
            button_bar.addWidget(button)

    def update_display(self) -> None:
        """Refresh labels and list widgets."""

        stock_remaining = self.game.deck.remaining()
        self.stock_label.setText(f"Stock: {stock_remaining} cards")
        if self.game.discard_pile:
            text = f"Discard: {self.game.discard_pile[-1]} ({len(self.game.discard_pile)})"
            if self.game.discard_frozen:
                text += " – frozen"
            self.discard_label.setText(text)
        else:
            self.discard_label.setText("Discard: —")

        self.hand_list.clear()
        for index, card in enumerate(self.game.players[self.human_index].hand, start=1):
            item = QListWidgetItem(f"{index:2}: {card}")
            self.hand_list.addItem(item)

        team = self.game.teams[self.game.players[self.human_index].team_index]
        meld_lines = []
        for meld in team.melds:
            tag = "natural" if meld.is_natural else "mixed"
            bonus = " (canasta)" if meld.is_canasta else ""
            description = ", ".join(str(card) for card in meld.cards)
            meld_lines.append(f"{meld.rank}s: {description} [{tag}{bonus}]")
        self.melds_display.setPlainText("\n".join(meld_lines) if meld_lines else "No melds yet.")
        self.animate_highlight(self.hand_list)
        self.animate_highlight(self.melds_display)

    def _set_status(self, text: str, *, highlight_color: str = "#2f8f9d") -> None:
        """Update and animate the status banner text."""

        self.status_label.setText(text)
        self.animate_highlight(self.status_label, highlight_color=highlight_color)

    def draw_from_stock(self) -> None:
        """Draw from the stock and update the display."""

        if self.phase != "draw":
            self._set_status("Discard before drawing again.")
            return
        card = self.game.draw(self.game.players[self.human_index], DrawSource.STOCK)
        self._log(f"You drew {card} from stock.")
        self.phase = "meld"
        self.update_display()

    def draw_from_discard(self) -> None:
        """Attempt to take the discard pile."""

        if self.phase != "draw":
            self._set_status("Drawing allowed only after discarding.")
            return
        player = self.game.players[self.human_index]
        if not self.game.can_take_discard(player):
            self._set_status("Discard pile unavailable.")
            return
        card = self.game.draw(player, DrawSource.DISCARD)
        self._log(f"You collected the discard pile; top card {card}.")
        self.phase = "meld"
        self.update_display()

    def lay_selected_meld(self) -> None:
        """Lay down a meld from the selected cards."""

        if self.phase not in {"meld", "discard"}:
            self._set_status("Draw a card first.")
            return
        indexes = [item.row() for item in self.hand_list.selectedIndexes()]
        if not indexes:
            self._set_status("Select cards to meld.")
            return
        cards = [self.game.players[self.human_index].hand[index] for index in indexes]
        try:
            meld = self.game.add_meld(self.game.players[self.human_index], cards)
        except MeldError as exc:
            self._set_status(str(exc), highlight_color="#bf3f5f")
            return
        self._log(f"Meld laid for {sum(card_point_value(card) for card in meld.cards)} points.")
        self.phase = "discard"
        self._set_status(f"Meld laid: {', '.join(str(card) for card in meld.cards)}")
        self.update_display()

    def discard_selected_card(self) -> None:
        """Discard the chosen card and move to the next player."""

        if self.phase == "draw":
            self._set_status("Draw before discarding.")
            return
        indexes = [item.row() for item in self.hand_list.selectedIndexes()]
        if not indexes:
            self._set_status("Select a card to discard.")
            return
        card = self.game.players[self.human_index].hand[indexes[0]]
        self.game.discard(self.game.players[self.human_index], card)
        self._log(f"Discarded {card}.")
        self.phase = "draw"
        self._set_status(f"Discarded {card}.")
        self._complete_ai_cycle()
        self.update_display()

    def end_turn(self) -> None:
        """Skip to the next player if the turn is complete."""

        if self.phase != "draw":
            self._set_status("Discard before ending your turn.")
            return
        self._complete_ai_cycle()
        self.update_display()

    def go_out(self) -> None:
        """Attempt to finish the round."""

        player = self.game.players[self.human_index]
        if not self.game.can_go_out(player.team_index):
            self._set_status("Cannot go out yet.")
            return
        breakdown = self.game.go_out(player)
        QMessageBox.information(self, "Round Complete", "Round finished and scores updated.")
        for team_index, delta in breakdown.items():
            team = self.game.teams[team_index]
            self._log(f"{team.name}: delta {delta}, total {team.score}")
        self._set_status("Round complete.")
        self.update_display()

    def _complete_ai_cycle(self) -> None:
        """Allow AI players to take simple turns."""

        while not self.game.round_over:
            self.game.advance_turn()
            if self.game.current_player_index == self.human_index:
                break
            player = self.game.players[self.game.current_player_index]
            drawn = self.game.draw(player, DrawSource.STOCK)
            discard_card = player.hand[0]
            self.game.discard(player, discard_card)
            self._log(f"{player.name} drew {drawn} and discarded {discard_card}.")
        if self.game.round_over:
            self._set_status("Round complete.")

    def _log(self, message: str) -> None:
        """Append ``message`` to the log widget."""

        self.log_widget.append(message)


__all__ = ["CanastaPyQtGUI"]
