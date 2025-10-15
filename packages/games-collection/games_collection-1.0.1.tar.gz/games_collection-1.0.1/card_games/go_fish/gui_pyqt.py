"""PyQt5-powered graphical interface for the Go Fish card game.

This module implements a PyQt5-based interface that visualizes the Go Fish
engine. The GUI focuses on making round progression easy to follow by providing
three dedicated areas:

* **Scoreboard** – Lists each player's remaining cards and completed books.
* **Control cluster** – Lets the active player pick an opponent and a rank via
  comboboxes before requesting cards.
* **Hand view** – Groups the current player's cards by rank and celebrates new
  books with subtle animations so achievements are noticeable without being
  distracting.

The GUI synchronizes itself with GoFishGame.get_state_summary() whenever
an action is taken to ensure the display accurately reflects the underlying
game state.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from card_games.common.cards import RANKS
from card_games.go_fish.game import GoFishGame, Player


@dataclass
class ScoreboardRow:
    """Container tracking widgets related to a player in the scoreboard."""

    frame: QWidget
    name_label: QLabel
    cards_label: QLabel
    books_label: QLabel
    book_icons_label: QLabel
    widgets: List[QWidget]


class GoFishGUI(QWidget):
    """PyQt5 interface that visualizes and drives a GoFishGame.

    The GUI manages layout construction, user interactions, and log updates.
    It keeps the interface synchronized with the game engine by repeatedly
    querying GoFishGame.get_state_summary() and applying the latest data
    to the widgets.
    """

    def __init__(self, game: GoFishGame) -> None:
        """Initialize the Go Fish GUI.

        Args:
            game: The Go Fish engine to display and control.
        """
        super().__init__()
        self.game = game
        self.player_rows: Dict[str, ScoreboardRow] = {}
        self._deck_empty_logged = False
        self._flash_timer: Optional[QTimer] = None
        self._flash_count = 0
        self._flash_target_name = ""

        self.setWindowTitle("Card Games - Go Fish")
        self.resize(1100, 720)

        self.build_layout()
        self.update_display()
        self._log_message("Game initialized. Waiting for the first move...")

    def build_layout(self) -> None:
        """Build the full Go Fish interface layout."""
        main_layout = QGridLayout()
        main_layout.setColumnStretch(0, 3)
        main_layout.setColumnStretch(1, 2)
        main_layout.setRowStretch(3, 1)
        self.setLayout(main_layout)

        # Header row with turn, deck, and state
        header = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)
        header.setLayout(header_layout)

        self.turn_label = QLabel()
        self.turn_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(self.turn_label, 1, Qt.AlignmentFlag.AlignLeft)

        self.deck_label = QLabel()
        self.deck_label.setStyleSheet("font-size: 14pt;")
        header_layout.addWidget(self.deck_label, 1, Qt.AlignmentFlag.AlignCenter)

        self.state_label = QLabel()
        self.state_label.setStyleSheet("font-size: 14pt;")
        header_layout.addWidget(self.state_label, 1, Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(header, 0, 0, 1, 2)

        # Scoreboard
        scoreboard_group = QGroupBox("Scoreboard")
        scoreboard_layout = QVBoxLayout()
        scoreboard_group.setLayout(scoreboard_layout)

        # Scoreboard header
        header_widget = QWidget()
        header_grid = QGridLayout()
        header_widget.setLayout(header_grid)
        for idx, title in enumerate(["Player", "Cards", "Books", "Celebration"]):
            label = QLabel(title)
            label.setStyleSheet("font-weight: bold;")
            header_grid.addWidget(label, 0, idx)
        scoreboard_layout.addWidget(header_widget)

        # Scoreboard rows for each player
        for idx, player in enumerate(self.game.players):
            row_frame = QWidget()
            row_layout = QGridLayout()
            row_layout.setContentsMargins(4, 2, 4, 2)
            row_frame.setLayout(row_layout)

            name_label = QLabel(player.name)
            name_label.setStyleSheet("font-size: 13pt; font-weight: bold;")
            row_layout.addWidget(name_label, 0, 0, Qt.AlignmentFlag.AlignLeft)

            cards_label = QLabel()
            row_layout.addWidget(cards_label, 0, 1, Qt.AlignmentFlag.AlignCenter)

            books_label = QLabel()
            row_layout.addWidget(books_label, 0, 2, Qt.AlignmentFlag.AlignCenter)

            book_icons_label = QLabel()
            book_icons_label.setStyleSheet("color: #F7B500; font-size: 14pt;")
            row_layout.addWidget(book_icons_label, 0, 3, Qt.AlignmentFlag.AlignCenter)

            widgets = [name_label, cards_label, books_label, book_icons_label]
            self.player_rows[player.name] = ScoreboardRow(
                frame=row_frame,
                name_label=name_label,
                cards_label=cards_label,
                books_label=books_label,
                book_icons_label=book_icons_label,
                widgets=widgets,
            )
            scoreboard_layout.addWidget(row_frame)

        main_layout.addWidget(scoreboard_group, 1, 0)

        # Controls for requesting cards
        controls_group = QGroupBox("Ask for Cards")
        controls_layout = QGridLayout()
        controls_group.setLayout(controls_layout)

        controls_layout.addWidget(QLabel("Opponent:"), 0, 0)
        self.opponent_combo = QComboBox()
        controls_layout.addWidget(self.opponent_combo, 0, 1)

        controls_layout.addWidget(QLabel("Rank:"), 1, 0)
        self.rank_combo = QComboBox()
        controls_layout.addWidget(self.rank_combo, 1, 1)

        self.ask_button = QPushButton("Ask")
        self.ask_button.clicked.connect(self.handle_request)
        controls_layout.addWidget(self.ask_button, 2, 0, 1, 2)

        self.status_label = QLabel("Welcome to Go Fish! Select an opponent and rank to begin.")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 10px;")
        controls_layout.addWidget(self.status_label, 3, 0, 1, 2)

        main_layout.addWidget(controls_group, 2, 0)

        # Hand visualization
        hand_group = QGroupBox("Your Hand")
        hand_layout = QVBoxLayout()
        hand_group.setLayout(hand_layout)

        self.hand_scroll = QScrollArea()
        self.hand_scroll.setWidgetResizable(True)
        self.hand_container = QWidget()
        self.hand_container_layout = QHBoxLayout()
        self.hand_container.setLayout(self.hand_container_layout)
        self.hand_scroll.setWidget(self.hand_container)
        hand_layout.addWidget(self.hand_scroll)

        main_layout.addWidget(hand_group, 3, 0)

        # Action log on the right side
        log_group = QGroupBox("Action Log")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)

        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        log_layout.addWidget(self.log_widget)

        main_layout.addWidget(log_group, 1, 1, 3, 1)

    def update_display(self) -> None:
        """Refresh the scoreboard, hand view, and control state."""
        summary = self.game.get_state_summary()
        self.turn_label.setText(f"Turn: {summary['current_player']}")

        deck_count = summary["deck_cards"]
        deck_text = "Deck depleted" if deck_count == 0 else f"Deck: {deck_count} cards remaining"
        self.deck_label.setText(deck_text)

        state_readable = summary["state"].replace("_", " ").title()
        self.state_label.setText(f"State: {state_readable}")

        if deck_count == 0 and not self._deck_empty_logged:
            self._log_message("The draw pile is empty. Every card is now in someone's hand!")
            self._deck_empty_logged = True

        for info in summary["players"]:
            row = self.player_rows[info["name"]]
            row.cards_label.setText(f"Cards: {info['hand_size']}")
            row.books_label.setText(f"Books: {info['books']}")
            row.book_icons_label.setText("⭐" * info["books"])

            font_weight = "bold" if info["name"] == summary["current_player"] else "normal"
            row.name_label.setStyleSheet(f"font-size: 13pt; font-weight: {font_weight};")

        self._render_hand(self.game.get_current_player())
        self._update_controls(summary)

    def handle_request(self) -> None:
        """Execute an ask-for-cards action using the selected controls."""
        actor = self.game.get_current_player()
        target = self.opponent_combo.currentText()
        rank = self.rank_combo.currentText()

        if not target or not rank:
            self.status_label.setText("Select both an opponent and a rank to continue.")
            return

        result = self.game.ask_for_cards(target, rank)
        self._log_message(result["message"])
        self.status_label.setText(result["message"])

        self.update_display()

        if result.get("new_books", 0) > 0:
            self._celebrate_books(actor.name, result["new_books"])

        if result.get("game_over"):
            self._handle_game_over(result)

    def _update_controls(self, summary: Dict[str, Any]) -> None:
        """Synchronize combobox choices with the latest game state."""
        current_player_name = summary["current_player"]
        opponents = [info["name"] for info in summary["players"] if info["name"] != current_player_name]

        self.opponent_combo.clear()
        self.opponent_combo.addItems(opponents)

        current_player = self.game.get_current_player()
        available_ranks = sorted(set(card.rank for card in current_player.hand))

        self.rank_combo.clear()
        self.rank_combo.addItems(available_ranks)

        if summary["state"] == "GAME_OVER":
            self.ask_button.setEnabled(False)
            self.opponent_combo.setEnabled(False)
            self.rank_combo.setEnabled(False)
        else:
            self.ask_button.setEnabled(len(available_ranks) > 0)
            self.opponent_combo.setEnabled(True)
            self.rank_combo.setEnabled(True)

    def _render_hand(self, player: Player) -> None:
        """Display the current player's hand grouped by rank."""
        # Clear existing hand widgets
        while self.hand_container_layout.count():
            item = self.hand_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        rank_groups: Dict[str, List] = defaultdict(list)
        for card in player.hand:
            rank_groups[card.rank].append(card)

        for rank in sorted(rank_groups.keys(), key=lambda r: RANKS.index(r)):
            cards = rank_groups[rank]
            group_widget = QWidget()
            group_layout = QVBoxLayout()
            group_layout.setContentsMargins(5, 5, 5, 5)
            group_widget.setLayout(group_layout)

            rank_label = QLabel(f"{rank}")
            rank_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
            rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            group_layout.addWidget(rank_label)

            count_label = QLabel(f"×{len(cards)}")
            count_label.setStyleSheet("font-size: 12pt;")
            count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            group_layout.addWidget(count_label)

            # Card suits
            suits_text = " ".join(str(card.suit.value) for card in cards)
            suits_label = QLabel(suits_text)
            suits_label.setStyleSheet("font-size: 16pt;")
            suits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            group_layout.addWidget(suits_label)

            # Style the group
            group_widget.setStyleSheet("QWidget { background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 5px; padding: 5px; }")

            self.hand_container_layout.addWidget(group_widget)

        self.hand_container_layout.addStretch()

    def _celebrate_books(self, player_name: str, new_books: int) -> None:
        """Flash the book icons for a player who just completed sets."""
        self._flash_target_name = player_name
        self._flash_count = 0
        self._flash_timer = QTimer()
        self._flash_timer.timeout.connect(self._flash_step)
        self._flash_timer.start(200)

    def _flash_step(self) -> None:
        """Perform one step of the celebration flash animation."""
        if self._flash_count >= 6:
            if self._flash_timer:
                self._flash_timer.stop()
                self._flash_timer = None
            # Restore normal display
            self.update_display()
            return

        row = self.player_rows[self._flash_target_name]
        if self._flash_count % 2 == 0:
            row.book_icons_label.setStyleSheet("color: #FF0000; font-size: 14pt;")
        else:
            row.book_icons_label.setStyleSheet("color: #F7B500; font-size: 14pt;")

        self._flash_count += 1

    def _handle_game_over(self, result: Dict[str, Any]) -> None:
        """Display the game-over message."""
        winner = result.get("winner")
        if winner:
            message = f"Game Over! {winner} wins with the most books!"
        else:
            message = "Game Over! It's a tie!"

        QMessageBox.information(self, "Game Over", message)

    def _log_message(self, message: str) -> None:
        """Add a message to the action log."""
        self.log_widget.append(message)


def run_gui(num_players: int = 2) -> int:
    """Launch the PyQt5 GUI for Go Fish.

    Args:
        num_players: Number of players (2-6)

    Returns:
        Exit code
    """
    import sys

    app = QApplication(sys.argv)
    game = GoFishGame(num_players=num_players)
    window = GoFishGUI(game)
    window.show()
    return app.exec()


if __name__ == "__main__":
    import sys

    sys.exit(run_gui())
