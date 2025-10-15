"""PyQt5 graphical interface for the Crazy Eights card game.

This module recreates the Tkinter-based GUI using PyQt5 widgets while
leveraging :class:`common.gui_base_pyqt.BaseGUI` for consistent theming,
logging, and configuration behavior. The interface focuses on three key
areas:

* **Header** – Displays the active player, top discard card, and draw pile.
* **Scoreboard** – Highlights the active player and celebrates the winner.
* **Hand controls** – Provides playable-card buttons, draw/pass actions, and
  a modal dialog to choose a suit after playing an eight.

The GUI keeps itself synchronized with :class:`card_games.crazy_eights.game.CrazyEightsGame`
through state summaries and mirrors the logging logic from the Tkinter
implementation. All Tk-specific styling calls were replaced by PyQt
stylesheet updates so the look adapts to the active theme.
"""

from __future__ import annotations

from collections import Counter
from functools import partial
from typing import Any, Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from card_games.common.cards import Card, Suit
from card_games.crazy_eights.game import CrazyEightsGame, Player
from common.gui_base_pyqt import BaseGUI, GUIConfig


class CrazyEightsGUI(QMainWindow):
    """PyQt5 GUI that visualises and runs a Crazy Eights match.

    Note: Does not inherit from BaseGUI as it's designed for Tkinter,
    and would cause metaclass conflicts with QMainWindow.
    """

    def __init__(self, game: CrazyEightsGame, config: Optional[GUIConfig] = None) -> None:
        """Initialise the Crazy Eights PyQt GUI.

        Args:
            game: Game engine instance to visualise.
            config: Optional configuration overrides for the GUI window.
        """
        self.game = game
        self._current_turn_name: str = ""
        self._draws_this_turn: int = 0
        self._game_over: bool = False
        self._suit_dialog: Optional[QDialog] = None

        gui_config = config or GUIConfig(
            window_title="Crazy Eights",
            window_width=1080,
            window_height=720,
            log_height=14,
            log_width=70,
        )

        QMainWindow.__init__(self)
        BaseGUI.__init__(self, self, gui_config)

        self._central_widget = QWidget(self)
        self.setCentralWidget(self._central_widget)
        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(16, 16, 16, 16)
        self._main_layout.setSpacing(12)
        self._central_widget.setLayout(self._main_layout)

        self._build_complete_layout()
        self.apply_theme()
        self.update_display()
        self._log("Game ready. You go first!")
        QTimer.singleShot(400, self._advance_ai_turns)

    # ------------------------------------------------------------------
    # BaseGUI contract
    # ------------------------------------------------------------------
    def build_layout(self) -> None:  # pragma: no cover - satisfied by _build_complete_layout
        """BaseGUI hook (layout already constructed in __init__)."""

    def update_display(self) -> None:
        """Refresh labels, scoreboard, and hand to match the engine state."""
        summary = self.game.get_state_summary()
        colors = self.current_theme.colors

        self.turn_label.setText(f"Current player: {summary['current_player']}")
        self.turn_label.setStyleSheet(f"color: {colors.foreground};")

        top_card_text = summary["top_card"] or "—"
        if summary["active_suit"]:
            top_card_text = f"{top_card_text} (Suit in play: {summary['active_suit']})"
        self.active_card_label.setText(f"Top card: {top_card_text}")
        self.active_card_label.setStyleSheet(f"color: {colors.primary};")

        self.deck_label.setText(f"Draw pile: {summary['deck_cards']} cards")
        self.deck_label.setStyleSheet(f"color: {colors.secondary};")

        self.status_label.setStyleSheet(
            " ".join(
                [
                    f"color: {colors.info};",
                    f"font-size: {self.current_theme.font_size + 1}pt;",
                    "padding: 6px 4px;",
                ]
            )
        )

        self.log_widget.setStyleSheet(
            " ".join(
                [
                    f"background-color: {colors.background};",
                    f"color: {colors.foreground};",
                    f"border: 1px solid {colors.border};",
                    "padding: 6px;",
                ]
            )
        )

        if summary["current_player"] != self._current_turn_name:
            self._current_turn_name = summary["current_player"]
            if self._is_human_turn():
                self._draws_this_turn = 0

        self._render_scoreboard(summary, colors)
        self._render_hand(colors)
        self._update_controls(summary)

        if summary["state"] == "GAME_OVER" and not self._game_over:
            self._handle_game_over()

    # ------------------------------------------------------------------
    # Layout construction helpers
    # ------------------------------------------------------------------
    def _build_complete_layout(self) -> None:
        """Create the complete window layout."""
        theme = self.current_theme

        # Header with turn information and pile summaries
        header = QWidget(self._central_widget)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(20)
        header.setLayout(header_layout)

        self.turn_label = QLabel("Preparing table...", header)
        self.turn_label.setFont(QFont(theme.font_family, theme.font_size + 4, QFont.Weight.Bold))
        header_layout.addWidget(self.turn_label, 1, Qt.AlignmentFlag.AlignLeft)

        self.active_card_label = QLabel("Top card: —", header)
        self.active_card_label.setFont(QFont(theme.font_family, theme.font_size + 2))
        header_layout.addWidget(self.active_card_label, 1, Qt.AlignmentFlag.AlignLeft)

        self.deck_label = QLabel("Draw pile: 52", header)
        self.deck_label.setFont(QFont(theme.font_family, theme.font_size + 2))
        header_layout.addWidget(self.deck_label, 0, Qt.AlignmentFlag.AlignRight)

        self._main_layout.addWidget(header)

        # Central board with scoreboard and log
        board = QWidget(self._central_widget)
        board_layout = QHBoxLayout()
        board_layout.setContentsMargins(0, 0, 0, 0)
        board_layout.setSpacing(16)
        board.setLayout(board_layout)

        self.scoreboard_group = self.create_label_frame(board, "Table scoreboard")
        scoreboard_layout = QVBoxLayout()
        scoreboard_layout.setContentsMargins(12, 10, 12, 12)
        scoreboard_layout.setSpacing(8)
        self.scoreboard_group.setLayout(scoreboard_layout)

        header_row = QWidget(self.scoreboard_group)
        header_row_layout = QHBoxLayout()
        header_row_layout.setContentsMargins(0, 0, 0, 0)
        header_row_layout.setSpacing(12)
        header_row.setLayout(header_row_layout)

        name_header = QLabel("Player", header_row)
        name_header.setStyleSheet("font-weight: bold;")
        info_header = QLabel("Cards / Score", header_row)
        info_header.setStyleSheet("font-weight: bold;")
        header_row_layout.addWidget(name_header)
        header_row_layout.addWidget(info_header, 1, Qt.AlignmentFlag.AlignRight)
        scoreboard_layout.addWidget(header_row)

        self.scoreboard_body_widget = QWidget(self.scoreboard_group)
        self.scoreboard_body_layout = QVBoxLayout()
        self.scoreboard_body_layout.setContentsMargins(0, 0, 0, 0)
        self.scoreboard_body_layout.setSpacing(6)
        self.scoreboard_body_widget.setLayout(self.scoreboard_body_layout)
        scoreboard_layout.addWidget(self.scoreboard_body_widget)
        scoreboard_layout.addStretch()

        board_layout.addWidget(self.scoreboard_group, 1)

        self.log_group = self.create_label_frame(board, "Game log")
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(12, 10, 12, 12)
        log_layout.setSpacing(4)
        self.log_group.setLayout(log_layout)

        self.log_widget: QTextEdit = self.create_log_widget(self.log_group)
        log_layout.addWidget(self.log_widget)

        board_layout.addWidget(self.log_group, 2)
        board_layout.setStretchFactor(self.scoreboard_group, 1)
        board_layout.setStretchFactor(self.log_group, 2)

        self._main_layout.addWidget(board, 1)

        # Hand and controls
        self.hand_group = self.create_label_frame(self._central_widget, "Your hand")
        hand_layout = QVBoxLayout()
        hand_layout.setContentsMargins(12, 10, 12, 12)
        hand_layout.setSpacing(10)
        self.hand_group.setLayout(hand_layout)

        self.status_label = QLabel("Welcome to Crazy Eights! Click a card to play.", self.hand_group)
        self.status_label.setWordWrap(True)
        self.status_label.setFont(QFont(theme.font_family, theme.font_size + 1))
        hand_layout.addWidget(self.status_label)

        self.hand_container = QWidget(self.hand_group)
        self.hand_layout = QGridLayout()
        self.hand_layout.setContentsMargins(0, 0, 0, 0)
        self.hand_layout.setSpacing(6)
        self.hand_container.setLayout(self.hand_layout)
        hand_layout.addWidget(self.hand_container)

        controls = QWidget(self.hand_group)
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        controls.setLayout(controls_layout)

        self.draw_button = QPushButton("Draw card", controls)
        self.draw_button.clicked.connect(self._on_draw_card)
        controls_layout.addWidget(self.draw_button)

        self.pass_button = QPushButton("Pass", controls)
        self.pass_button.clicked.connect(self._on_pass_turn)
        controls_layout.addWidget(self.pass_button)

        hand_layout.addWidget(controls)
        self._main_layout.addWidget(self.hand_group)

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def _render_scoreboard(self, summary: dict[str, Any], colors: Any) -> None:
        """Render scoreboard rows for each player."""
        self._clear_layout(self.scoreboard_body_layout)

        current = summary["current_player"]
        max_score = max((player["score"] for player in summary["players"]), default=0)
        state = summary["state"]

        for player in summary["players"]:
            is_current = player["name"] == current and state != "GAME_OVER"
            is_winner = state == "GAME_OVER" and player["score"] == max_score and max_score > 0
            row_bg = colors.highlight if is_current else colors.background
            if is_winner:
                row_bg = colors.success
            text_color = colors.foreground if not is_winner else "#FFFFFF"

            row_widget = QWidget(self.scoreboard_body_widget)
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(8, 6, 8, 6)
            row_layout.setSpacing(12)
            row_widget.setLayout(row_layout)

            row_widget.setStyleSheet(
                " ".join(
                    [
                        f"background-color: {row_bg};",
                        f"color: {text_color};",
                        "border-radius: 6px;",
                    ]
                )
            )

            name_label = QLabel(player["name"], row_widget)
            name_label.setStyleSheet(
                " ".join(
                    [
                        f"color: {text_color};",
                        "font-weight: bold;",
                    ]
                )
            )
            row_layout.addWidget(name_label)

            info_text = f"Cards: {player['hand_size']}"
            if player["score"]:
                info_text += f" | Score: {player['score']}"
            info_label = QLabel(info_text, row_widget)
            info_label.setStyleSheet(f"color: {text_color};")
            row_layout.addWidget(info_label, 1, Qt.AlignmentFlag.AlignRight)

            self.scoreboard_body_layout.addWidget(row_widget)

        self.scoreboard_body_layout.addStretch()

    def _render_hand(self, colors: Any) -> None:
        """Show the human player's hand as clickable card buttons."""
        self._clear_layout(self.hand_layout)

        human = self.game.players[0]
        playable = human.get_playable_cards(self.game.active_suit, self.game.active_rank)
        is_turn = self._is_human_turn()

        if not human.hand:
            empty_label = QLabel("(No cards)", self.hand_container)
            empty_label.setStyleSheet(f"color: {colors.secondary};")
            self.hand_layout.addWidget(empty_label, 0, 0, 1, 1, Qt.AlignmentFlag.AlignLeft)
            return

        sorted_hand = sorted(human.hand, key=lambda c: (c.suit.value, c.value))
        for index, card in enumerate(sorted_hand):
            button = QPushButton(str(card), self.hand_container)
            button.setEnabled(is_turn and card in playable)
            button.setFont(QFont(self.current_theme.font_family, self.current_theme.font_size + 1, QFont.Weight.Bold))

            background = colors.highlight if card in playable else colors.background
            if card.rank == "8" and card not in playable:
                background = "#fde68a"

            border_color = self.current_theme.colors.primary if card in playable else colors.border
            style = " ".join(
                [
                    f"background-color: {background};",
                    f"color: {colors.foreground};",
                    f"border: 2px solid {border_color};",
                    "border-radius: 6px;",
                    "padding: 10px;",
                    "min-width: 80px;",
                ]
            )
            button.setStyleSheet(style)
            button.clicked.connect(partial(self._on_card_clicked, card))

            row = index // 12
            column = index % 12
            self.hand_layout.addWidget(button, row, column)

    def _update_controls(self, summary: dict[str, Any]) -> None:
        """Enable/disable draw and pass controls based on turn context."""
        human_turn = self._is_human_turn() and not self._game_over
        human = self.game.players[0]
        playable = human.get_playable_cards(self.game.active_suit, self.game.active_rank)

        if human_turn:
            self.draw_button.setEnabled(True)
            if playable:
                self.status_label.setText("Choose a card to play or draw from the pile.")
            else:
                self.status_label.setText("No playable cards. Draw from the pile.")

            allow_pass = False
            if not playable:
                if self.game.draw_limit == 0:
                    allow_pass = summary["deck_cards"] == 0
                else:
                    allow_pass = self._draws_this_turn >= self.game.draw_limit
            self.pass_button.setEnabled(allow_pass)
        else:
            self.draw_button.setEnabled(False)
            self.pass_button.setEnabled(False)
            if not self._game_over:
                self.status_label.setText("Waiting for opponents...")

    # ------------------------------------------------------------------
    # Interaction helpers
    # ------------------------------------------------------------------
    def _is_human_turn(self) -> bool:
        """Determine whether the first player (human) has the turn."""
        return self.game.get_current_player() == self.game.players[0]

    def _on_card_clicked(self, card: Card) -> None:
        """Handle a click on a card in the human hand."""
        if not self._is_human_turn() or self._game_over:
            return
        if card.rank == "8":
            self._prompt_suit_selection(card)
            return
        self._play_card(card, None)

    def _play_card(self, card: Card, new_suit: Optional[Suit]) -> None:
        """Play the selected card and handle results."""
        result = self.game.play_card(card, new_suit)
        if not result["success"]:
            self.status_label.setText(result["message"])
            self._log(result["message"])
            return

        self._log(result["message"])
        self._draws_this_turn = 0
        self.update_display()

        if result.get("game_over"):
            self._handle_game_over()
        else:
            QTimer.singleShot(450, self._advance_ai_turns)

    def _prompt_suit_selection(self, card: Card) -> None:
        """Open a modal dialog to choose a suit when an eight is played."""
        if self._suit_dialog is not None:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Choose a suit")
        dialog.setModal(True)
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        dialog.setLayout(layout)

        prompt = QLabel("Select the suit to continue:", dialog)
        prompt.setFont(QFont(self.current_theme.font_family, self.current_theme.font_size + 2, QFont.Weight.Bold))
        layout.addWidget(prompt)

        for suit in Suit:
            button = QPushButton(f"{suit.name.title()} {suit.value}", dialog)
            button.clicked.connect(partial(self._finalise_suit_choice, dialog, card, suit))
            layout.addWidget(button)

        dialog.rejected.connect(partial(self._finalise_suit_choice, dialog, card, None))
        dialog.open()
        self._suit_dialog = dialog

    def _finalise_suit_choice(self, dialog: QDialog, card: Card, suit: Optional[Suit]) -> None:
        """Close the suit dialog and play the eight with the chosen suit."""
        if self._suit_dialog is None:
            return
        self._suit_dialog = None
        dialog.close()
        if suit is None:
            self.status_label.setText("Suit selection cancelled. Choose again.")
            return
        self._play_card(card, suit)

    def _on_draw_card(self) -> None:
        """Draw a card for the human player."""
        if not self._is_human_turn() or self._game_over:
            return
        result = self.game.draw_card()
        if result["success"]:
            self._draws_this_turn += 1
            card = result.get("card")
            card_text = f" ({card})" if isinstance(card, Card) else ""
            message = result["message"] + card_text
            self._log(message)
            self.status_label.setText(message)
        else:
            self._log(result["message"])
            self.status_label.setText(result["message"])
        self.update_display()

    def _on_pass_turn(self) -> None:
        """Pass the turn after drawing the maximum allowed cards."""
        if not self._is_human_turn() or self._game_over:
            return
        result = self.game.pass_turn()
        if result["success"]:
            self._log(result["message"])
            self._draws_this_turn = 0
            self.update_display()
            QTimer.singleShot(450, self._advance_ai_turns)
        else:
            self.status_label.setText(result["message"])
            self._log(result["message"])

    def _advance_ai_turns(self) -> None:
        """Automatically resolve AI turns until the human is active again."""
        if self._game_over:
            return
        if self._is_human_turn():
            self.update_display()
            return

        current_player = self.game.get_current_player()
        self.status_label.setText(f"{current_player.name} is thinking...")
        QTimer.singleShot(350, self._execute_ai_turn)

    def _execute_ai_turn(self) -> None:
        """Execute a single AI turn and schedule subsequent turns."""
        if self._game_over:
            return

        player = self.game.get_current_player()
        if player == self.game.players[0]:
            self.update_display()
            return

        playable = player.get_playable_cards(self.game.active_suit, self.game.active_rank)
        if playable:
            card = self._select_ai_card(playable)
            suit = self._select_ai_suit(player) if card.rank == "8" else None
            result = self.game.play_card(card, suit)
            self._log(result["message"])
            self.update_display()
            if result.get("game_over"):
                self._handle_game_over()
                return
            QTimer.singleShot(450, self._advance_ai_turns)
            return

        draws = 0
        while self.game.draw_limit == 0 or draws < self.game.draw_limit:
            draw_result = self.game.draw_card()
            if not draw_result["success"]:
                self._log(draw_result["message"])
                break
            draws += 1
            card = draw_result.get("card")
            card_desc = f" ({card})" if isinstance(card, Card) else ""
            self._log(draw_result["message"] + card_desc)
            if player.has_playable_card(self.game.active_suit, self.game.active_rank):
                break
            if self.game.draw_limit == 0:
                continue

        if player.has_playable_card(self.game.active_suit, self.game.active_rank):
            QTimer.singleShot(350, self._advance_ai_turns)
            return

        result = self.game.pass_turn()
        if result["success"]:
            self._log(result["message"])

        self.update_display()
        if self._game_over:
            return
        QTimer.singleShot(450, self._advance_ai_turns)

    def _select_ai_card(self, playable: list[Card]) -> Card:
        """Choose which card an AI should play."""
        non_eights = [card for card in playable if card.rank != "8"]
        if non_eights:
            return max(non_eights, key=lambda card: card.value)
        return playable[0]

    def _select_ai_suit(self, player: Player) -> Suit:
        """Select a suit for an AI after playing an eight."""
        suit_counts = Counter(card.suit for card in player.hand if card.rank != "8")
        if not suit_counts:
            return Suit.HEARTS
        return max(suit_counts.items(), key=lambda item: item[1])[0]

    def _handle_game_over(self) -> None:
        """Handle end-of-game UI updates."""
        self._game_over = True
        summary = self.game.get_state_summary()
        winner = max(summary["players"], key=lambda player: player["score"])
        message = f"Game over! {winner['name']} wins with {winner['score']} points."
        self.status_label.setText(message)
        self._log(message)
        self.draw_button.setEnabled(False)
        self.pass_button.setEnabled(False)
        self.update_display()

    def _log(self, message: str) -> None:
        """Append a message to the game log widget."""
        self.log_message(self.log_widget, message)

    @staticmethod
    def _clear_layout(layout: QLayout) -> None:
        """Remove all widgets from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
            elif item.layout() is not None:
                CrazyEightsGUI._clear_layout(item.layout())


__all__ = ["CrazyEightsGUI"]
