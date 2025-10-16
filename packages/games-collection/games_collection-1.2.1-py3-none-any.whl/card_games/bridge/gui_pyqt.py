"""PyQt5 interface for the Bridge card game.

This module ports the Tkinter Bridge GUI to the PyQt5 framework while keeping
the underlying :class:`~card_games.bridge.game.BridgeGame` state machine intact.
It rebuilds the scoreboard, bidding history, trick display, and South player's
hand controls using Qt widgets and layouts. Automated bidding and play retain
their sequencing via :class:`PyQt5.QtCore.QTimer` events so AI timing mirrors
the legacy implementation.
"""

from __future__ import annotations

import random
import sys
from typing import Iterable, Optional

from card_games.bridge.game import (
    BidSuit,
    BridgeGame,
    BridgePlayer,
    Call,
    CallType,
    Contract,
    Vulnerability,
)
from card_games.common.cards import Card, Suit
from card_games.common.soundscapes import initialize_game_soundscape
from common.gui_base_pyqt import PYQT5_AVAILABLE, BaseGUI, GUIConfig

if not PYQT5_AVAILABLE:  # pragma: no cover - module should not import without PyQt5
    raise ImportError("PyQt5 is required for the Bridge PyQt GUI")

from PyQt5.QtCore import QRectF, Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QPainter, QTextCursor
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

SUIT_DISPLAY_ORDER = {
    Suit.SPADES: 0,
    Suit.HEARTS: 1,
    Suit.DIAMONDS: 2,
    Suit.CLUBS: 3,
}

SUIT_SYMBOLS = {
    BidSuit.CLUBS: "♣",
    BidSuit.DIAMONDS: "♦",
    BidSuit.HEARTS: "♥",
    BidSuit.SPADES: "♠",
    BidSuit.NO_TRUMP: "NT",
}


class TrickDisplay(QWidget):
    """Custom widget that renders the current trick and dummy information."""

    def __init__(self, config: GUIConfig, theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.config = config
        self.theme = theme
        self.dummy_text = "Dummy hidden"
        self.plays: list[tuple[str, str]] = []
        self.setMinimumSize(380, 240)
        self.setAutoFillBackground(True)
        self._apply_theme()

    def set_theme(self, theme) -> None:
        """Update the widget palette based on a new theme."""

        self.theme = theme
        self._apply_theme()
        self.update()

    def set_display(self, dummy_text: str, plays: Iterable[tuple[str, str]]) -> None:
        """Update the dummy description and trick card placements."""

        self.dummy_text = dummy_text
        self.plays = list(plays)
        self.update()

    def _apply_theme(self) -> None:
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(self.theme.colors.canvas_bg))
        palette.setColor(self.foregroundRole(), QColor(self.theme.colors.foreground))
        self.setPalette(palette)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor(self.theme.colors.foreground))

        # Dummy information
        header_font = QFont(self.config.font_family, self.config.font_size)
        painter.setFont(header_font)
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            self.dummy_text,
        )

        # Trick positions relative to the widget bounds
        positions = {
            "N": (0.5, 0.30),
            "E": (0.72, 0.55),
            "S": (0.5, 0.80),
            "W": (0.28, 0.55),
        }

        card_font = QFont(self.config.font_family, self.config.font_size + 2, QFont.Weight.Bold)
        painter.setFont(card_font)
        width = float(self.rect().width())
        height = float(self.rect().height())

        for position, card_text in self.plays:
            rel_x, rel_y = positions.get(position, (0.5, 0.55))
            x = rel_x * width
            y = rel_y * height
            text_rect = QRectF(x - 80, y - 24, 160, 48)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, f"{position}: {card_text}")


class BridgeGUI(BaseGUI):
    """PyQt5 implementation of a Bridge table with automated opponents."""

    def __init__(
        self,
        root: Optional[QMainWindow] = None,
        *,
        enable_sounds: bool = True,
        config: Optional[GUIConfig] = None,
    ) -> None:
        if root is None:
            root = QMainWindow()
        gui_config = config or GUIConfig(
            window_title="Contract Bridge",
            window_width=1100,
            window_height=720,
            font_family="Segoe UI",
            font_size=11,
            theme_name="dark",
            enable_sounds=enable_sounds,
            enable_animations=True,
        )
        super().__init__(root, gui_config)
        self.sound_manager = initialize_game_soundscape(
            "bridge",
            module_file=__file__,
            enable_sounds=gui_config.enable_sounds,
            existing_manager=self.sound_manager,
        )

        self.players = [
            BridgePlayer(name="North AI", is_ai=True),
            BridgePlayer(name="South Player", is_ai=False),
            BridgePlayer(name="East AI", is_ai=True),
            BridgePlayer(name="West AI", is_ai=True),
        ]
        self.game = BridgeGame(
            self.players,
            vulnerability=random.choice(list(Vulnerability)),
        )
        self.contract: Optional[Contract] = None
        self.dummy_index: Optional[int] = None
        self.active_player_index: Optional[int] = None
        self.awaiting_human_play = False
        self.dummy_revealed = False
        self.opening_lead_played = False
        self.hand_complete = False
        self.current_valid_cards: Optional[list[Card]] = None

        # UI state
        self.hand_labels: dict[str, QLabel] = {}
        self.vulnerability_label: Optional[QLabel] = None
        self.contract_label: Optional[QLabel] = None
        self.declarer_label: Optional[QLabel] = None
        self.trick_label: Optional[QLabel] = None
        self.status_label: Optional[QLabel] = None
        self.card_button_layout: Optional[QHBoxLayout] = None
        self.trick_display: Optional[TrickDisplay] = None
        self.bidding_text: Optional[QTextEdit] = None
        self.log_text: Optional[QTextEdit] = None

        self.central_widget = QWidget(self.root)
        self.root.setCentralWidget(self.central_widget)

        self.build_layout()
        self.apply_theme()
        self.update_display()
        QTimer.singleShot(250, self.start_new_hand)

    def build_layout(self) -> None:
        main_layout = QGridLayout()
        main_layout.setColumnStretch(0, 3)
        main_layout.setColumnStretch(1, 2)
        self.central_widget.setLayout(main_layout)

        header = QWidget(self.central_widget)
        header_layout = QVBoxLayout()
        header.setLayout(header_layout)

        title = QLabel("Bridge Scoreboard", header)
        title.setFont(QFont(self.config.font_family, self.config.font_size + 4, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(title)

        detail_widget = QWidget(header)
        detail_layout = QGridLayout()
        detail_widget.setLayout(detail_layout)

        self.vulnerability_label = QLabel("Vulnerability:")
        self.contract_label = QLabel("Contract:")
        self.declarer_label = QLabel("Declarer:")
        self.trick_label = QLabel("Tricks:")
        for label in (
            self.vulnerability_label,
            self.contract_label,
            self.declarer_label,
            self.trick_label,
        ):
            label.setFont(QFont(self.config.font_family, self.config.font_size))

        detail_layout.addWidget(self.vulnerability_label, 0, 0)
        detail_layout.addWidget(self.contract_label, 0, 1)
        detail_layout.addWidget(self.declarer_label, 1, 0)
        detail_layout.addWidget(self.trick_label, 1, 1)

        header_layout.addWidget(detail_widget)
        main_layout.addWidget(header, 0, 0, 1, 2)

        play_area = QWidget(self.central_widget)
        play_layout = QGridLayout()
        play_layout.setRowStretch(0, 1)
        play_layout.setRowStretch(1, 1)
        play_layout.setRowStretch(2, 1)
        play_layout.setColumnStretch(0, 1)
        play_layout.setColumnStretch(1, 1)
        play_layout.setColumnStretch(2, 1)
        play_area.setLayout(play_layout)

        north = self._create_seat_widget(self.players[0])
        play_layout.addWidget(north, 0, 1, Qt.AlignmentFlag.AlignCenter)

        west = self._create_seat_widget(self.players[3])
        play_layout.addWidget(west, 1, 0, Qt.AlignmentFlag.AlignCenter)

        center = QFrame(play_area)
        center.setFrameShape(QFrame.Shape.StyledPanel)
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(8, 8, 8, 8)
        center.setLayout(center_layout)

        self.trick_display = TrickDisplay(self.config, self.current_theme)
        center_layout.addWidget(self.trick_display)

        play_layout.addWidget(center, 1, 1)

        east = self._create_seat_widget(self.players[2])
        play_layout.addWidget(east, 1, 2, Qt.AlignmentFlag.AlignCenter)

        south = self._create_seat_widget(self.players[1])
        play_layout.addWidget(south, 2, 1, Qt.AlignmentFlag.AlignCenter)

        card_container = QWidget(south)
        self.card_button_layout = QHBoxLayout()
        self.card_button_layout.setSpacing(6)
        card_container.setLayout(self.card_button_layout)
        south.layout().addWidget(card_container)  # type: ignore[union-attr]

        main_layout.addWidget(play_area, 1, 0)

        sidebar = QWidget(self.central_widget)
        sidebar_layout = QVBoxLayout()
        sidebar.setLayout(sidebar_layout)

        bidding_label = QLabel("Bidding History", sidebar)
        bidding_label.setFont(QFont(self.config.font_family, self.config.font_size + 2, QFont.Weight.Bold))
        sidebar_layout.addWidget(bidding_label)

        self.bidding_text = QTextEdit(sidebar)
        self.bidding_text.setReadOnly(True)
        self.bidding_text.setFont(QFont(self.config.font_family, self.config.font_size))
        self.bidding_text.setMinimumHeight(200)
        sidebar_layout.addWidget(self.bidding_text)

        log_label = QLabel("Deal Log", sidebar)
        log_label.setFont(QFont(self.config.font_family, self.config.font_size + 2, QFont.Weight.Bold))
        sidebar_layout.addWidget(log_label)

        self.log_text = QTextEdit(sidebar)
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont(self.config.font_family, self.config.font_size))
        sidebar_layout.addWidget(self.log_text)

        main_layout.addWidget(sidebar, 1, 1)

        footer = QWidget(self.central_widget)
        footer_layout = QVBoxLayout()
        footer_layout.setContentsMargins(8, 8, 8, 8)
        footer.setLayout(footer_layout)

        self.status_label = QLabel("Preparing deal...")
        self.status_label.setWordWrap(True)
        self.status_label.setFont(QFont(self.config.font_family, self.config.font_size))
        footer_layout.addWidget(self.status_label)

        main_layout.addWidget(footer, 2, 0, 1, 2)

    def update_display(self) -> None:
        self._update_scoreboard()
        self._refresh_hand_views()
        self._refresh_trick_display()

    def start_new_hand(self) -> None:
        self._clear_log()
        self.game.deal_cards()
        self.contract = self.game.conduct_bidding()
        self.dummy_index = None
        self.active_player_index = None
        self.awaiting_human_play = False
        self.dummy_revealed = False
        self.opening_lead_played = False
        self.hand_complete = False
        self.current_valid_cards = None
        self._append_log(f"Vulnerability: {self.game.vulnerability.value}")

        if self.contract is None:
            self._render_bidding_history()
            self._set_status("All players passed. Deal over.")
            self._append_log("Board passed out - no play.")
            self.update_display()
            self._refresh_card_buttons()
            return

        self.dummy_index = self.contract.declarer.partner_index
        self.active_player_index = self.game.starting_player_index()
        self._render_bidding_history()
        contract_text = self._format_contract(self.contract)
        declarer = self.contract.declarer
        dummy = self.players[self.dummy_index]
        self._append_log(f"Contract: {contract_text} by {declarer.position}")
        self._append_log(f"Dummy: {dummy.position} ({dummy.name})")
        self._set_status("Opening lead in progress...")
        self.update_display()
        QTimer.singleShot(500, self._advance_turn)

    def _create_seat_widget(self, player: BridgePlayer) -> QWidget:
        container = QWidget(self.central_widget)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        container.setLayout(layout)

        title = QLabel(f"{player.name} ({player.position})", container)
        title.setFont(QFont(self.config.font_family, self.config.font_size + 1, QFont.Weight.Bold))
        layout.addWidget(title)

        hand_label = QLabel("", container)
        hand_label.setFont(QFont(self.config.font_family, self.config.font_size))
        hand_label.setWordWrap(True)
        hand_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(hand_label)

        self.hand_labels[player.position] = hand_label
        return container

    def _update_scoreboard(self) -> None:
        if self.vulnerability_label is not None:
            self.vulnerability_label.setText(f"Vulnerability: {self.game.vulnerability.value}")

        if self.contract is None:
            if self.contract_label is not None:
                self.contract_label.setText("Contract: None")
            if self.declarer_label is not None:
                self.declarer_label.setText("Declarer: -")
        else:
            contract_text = self._format_contract(self.contract)
            dummy = self.players[self.contract.declarer.partner_index]
            if self.contract_label is not None:
                self.contract_label.setText(f"Contract: {contract_text}")
            if self.declarer_label is not None:
                self.declarer_label.setText(f"Declarer: {self.contract.declarer.position} | Dummy: {dummy.position}")

        ns_tricks = sum(player.tricks_won for player in self.players if player.position in {"N", "S"})
        ew_tricks = sum(player.tricks_won for player in self.players if player.position in {"E", "W"})
        if self.trick_label is not None:
            self.trick_label.setText(f"Tricks - NS: {ns_tricks} | EW: {ew_tricks}")
            self.animate_highlight(self.trick_label)

    def _refresh_hand_views(self) -> None:
        for player in self.players:
            label = self.hand_labels.get(player.position)
            if label is None:
                continue
            display = self._format_hand_display(player)
            label.setText(display)
        self._refresh_card_buttons()

    def _refresh_trick_display(self) -> None:
        if self.trick_display is None:
            return

        dummy_text = "Dummy hidden"
        if self.dummy_index is not None:
            dummy_player = self.players[self.dummy_index]
            if self.dummy_revealed:
                dummy_cards = self._format_cards_line(dummy_player.hand)
                dummy_text = f"Dummy {dummy_player.position}: {dummy_cards or 'Empty'}"
            else:
                dummy_text = f"Dummy {dummy_player.position}: {len(dummy_player.hand)} cards"

        plays = [(player.position, str(card)) for player, card in self.game.current_trick]
        self.trick_display.set_display(dummy_text, plays)
        self.animate_highlight(self.trick_display)

    def _render_bidding_history(self) -> None:
        if self.bidding_text is None:
            return
        self.bidding_text.clear()
        if not self.game.bidding_history:
            self.bidding_text.append("No calls made.")
        else:
            for call in self.game.bidding_history:
                entry = self._format_call(call)
                self.bidding_text.append(entry)
        self.bidding_text.moveCursor(QTextCursor.End)
        self.bidding_text.ensureCursorVisible()

    def _advance_turn(self) -> None:
        if self.hand_complete or self.contract is None or self.active_player_index is None:
            return

        player = self.players[self.active_player_index]
        if player.is_ai:
            self._set_status(f"{player.name} thinking...")
            QTimer.singleShot(600, lambda: self._play_ai_turn(player))
        else:
            self.awaiting_human_play = True
            valid = self.game.get_valid_plays(player)
            self.current_valid_cards = valid
            self._set_status("Your turn - select a card to play.")
            self.update_display()

    def _play_ai_turn(self, player: BridgePlayer) -> None:
        if self.hand_complete:
            return
        card = self.game.select_card_to_play(player)
        self._finalize_play_for_card(player, card)

    def _handle_human_card(self, card: Card) -> None:
        if not self.awaiting_human_play or self.contract is None:
            return

        player = self.players[self.active_player_index]
        if card not in self.game.get_valid_plays(player):
            return

        self.awaiting_human_play = False
        self.current_valid_cards = None
        self._finalize_play_for_card(player, card)

    def _finalize_play_for_card(self, player: BridgePlayer, card: Card) -> None:
        self.game.play_card(player, card)
        self._append_log(f"{player.position} plays {card}")
        if not self.opening_lead_played:
            self.opening_lead_played = True
            if self.dummy_index is not None:
                self.dummy_revealed = True
                dummy = self.players[self.dummy_index]
                self._append_log(f"Dummy hand revealed: {dummy.position}")
        self.update_display()
        if len(self.game.current_trick) == 4:
            self._set_status("Evaluating trick winner...")
            QTimer.singleShot(700, self._complete_trick)
        else:
            self.active_player_index = (self.active_player_index + 1) % 4
            QTimer.singleShot(200, self._advance_turn)

    def _complete_trick(self) -> None:
        winner = self.game.complete_trick()
        self._append_log(f"{winner.position} wins the trick")
        ns_tricks = sum(player.tricks_won for player in self.players if player.position in {"N", "S"})
        ew_tricks = sum(player.tricks_won for player in self.players if player.position in {"E", "W"})
        self._set_status(f"Trick won by {winner.position}. NS {ns_tricks} - EW {ew_tricks}")
        self.active_player_index = self.players.index(winner)
        self.update_display()
        if all(not player.hand for player in self.players):
            self._finalize_hand()
        else:
            QTimer.singleShot(400, self._advance_turn)

    def _finalize_hand(self) -> None:
        self.hand_complete = True
        self.awaiting_human_play = False
        self.current_valid_cards = None
        scores = self.game.calculate_score()
        if self.contract is None:
            result_text = "Board passed out."
        else:
            declarer = self.contract.declarer
            partner = self.players[self.contract.declarer.partner_index]
            declarer_tricks = declarer.tricks_won + partner.tricks_won
            required = 6 + self.contract.bid.level
            if declarer_tricks >= required:
                result_text = f"Contract made with {declarer_tricks} tricks."
            else:
                result_text = f"Contract down {required - declarer_tricks}."
        self._set_status(result_text)
        self._append_log(result_text)
        self._append_log("Scores - North/South: {north_south} | East/West: {east_west}".format(**scores))
        self.update_display()

    def _refresh_card_buttons(self) -> None:
        if self.card_button_layout is None:
            return
        while self.card_button_layout.count():
            item = self.card_button_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        south = self.players[1]
        sorted_cards = sorted(
            south.hand,
            key=lambda card: (SUIT_DISPLAY_ORDER[card.suit], -card.value),
        )
        valid_cards = set(self.current_valid_cards or [])
        for card in sorted_cards:
            button = QPushButton(str(card))
            button.setFixedWidth(48)
            button.clicked.connect(lambda checked=False, c=card: self._handle_human_card(c))
            button.setEnabled((not valid_cards) or (card in valid_cards))
            self.card_button_layout.addWidget(button)
        self.card_button_layout.addStretch(1)

    def _format_hand_display(self, player: BridgePlayer) -> str:
        if player.position == "S":
            return self._format_cards_line(player.hand)
        if self.dummy_revealed and self.dummy_index is not None and player == self.players[self.dummy_index]:
            return self._format_cards_line(player.hand)
        return f"{len(player.hand)} cards"

    def _format_cards_line(self, cards: Iterable[Card]) -> str:
        cards_list = list(cards)
        if not cards_list:
            return ""
        ordered = sorted(cards_list, key=lambda card: (SUIT_DISPLAY_ORDER[card.suit], -card.value))
        return " ".join(str(card) for card in ordered)

    def _format_call(self, call: Call) -> str:
        if call.call_type == CallType.BID and call.bid is not None:
            symbol = SUIT_SYMBOLS.get(call.bid.suit, "")
            return f"{call.player.position}: {call.bid.level}{symbol}"
        if call.call_type == CallType.DOUBLE:
            return f"{call.player.position}: Double"
        if call.call_type == CallType.REDOUBLE:
            return f"{call.player.position}: Redouble"
        return f"{call.player.position}: Pass"

    def _format_contract(self, contract: Contract) -> str:
        symbol = SUIT_SYMBOLS.get(contract.bid.suit, "")
        suffix = ""
        if contract.redoubled:
            suffix = " XX"
        elif contract.doubled:
            suffix = " X"
        return f"{contract.bid.level}{symbol}{suffix}"

    def _append_log(self, message: str) -> None:
        if self.log_text is None:
            return
        self.log_text.append(message)
        self.log_text.moveCursor(QTextCursor.End)
        self.log_text.ensureCursorVisible()

    def _clear_log(self) -> None:
        if self.log_text is None:
            return
        self.log_text.clear()

    def _set_status(self, message: str) -> None:
        if self.status_label is not None:
            self.status_label.setText(message)
            self.animate_highlight(self.status_label)

    def show(self) -> None:
        """Expose ``show`` to mirror QWidget-like behavior for callers."""

        self.root.show()

    def apply_theme(self) -> None:  # type: ignore[override]
        super().apply_theme()
        if self.trick_display is not None:
            self.trick_display.set_theme(self.current_theme)


def run_gui(config: Optional[GUIConfig] = None) -> bool:
    """Launch the Bridge PyQt GUI.

    Returns ``True`` when the GUI is launched successfully. ``False`` is
    returned if PyQt5 cannot be initialized (for example in headless
    environments).  The caller can then fall back to another interface.
    """

    if not PYQT5_AVAILABLE:
        print("PyQt5 is unavailable. Cannot launch the Bridge PyQt GUI.")
        return False

    if config is None:
        config = GUIConfig(
            window_title="Contract Bridge",
            window_width=1100,
            window_height=720,
            font_family="Segoe UI",
            font_size=11,
            theme_name="dark",
            enable_sounds=True,
            enable_animations=True,
        )

    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
    except Exception as error:  # pragma: no cover - environment dependent
        print(f"Failed to initialize PyQt5 application: {error}")
        return False

    window = BridgeGUI(config=config)
    window.show()

    try:
        app.exec()
    except Exception as error:  # pragma: no cover - environment dependent
        print(f"PyQt5 event loop terminated unexpectedly: {error}")
        return False
    return True


__all__ = ["BridgeGUI", "run_gui"]
