"""PyQt5 interface for playing Spades against AI opponents.

This module mirrors the features available in :mod:`card_games.spades.gui`
while embracing Qt widgets and layouts.  The UI is organised into three
primary groupings:

* **Bidding controls** – Allows the human player to submit bids and review
  partnership commitments made by AI partners and opponents.
* **Trick tracker** – Displays the current trick in progress so players can
  confirm that suits are being followed and who has priority.
* **Scoreboards and logs** – Surfaces partnership scores, round breakdowns,
  and a scrollable log that documents each bid and play.

Timers are used to emulate the sequencing previously handled by Tkinter's
``after`` method, ensuring AI turns unfold naturally without blocking the
event loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QMainWindow, QPushButton, QSpinBox, QTextEdit, QVBoxLayout, QWidget

from card_games.common.cards import Card
from card_games.common.soundscapes import initialize_game_soundscape
from card_games.spades.game import SpadesGame, SpadesPlayer
from common.gui_base_pyqt import PYQT5_AVAILABLE, BaseGUI, GUIConfig


@dataclass
class _BidDisplay:
    """Container storing widgets that present a player's bid."""

    value_label: QLabel


class SpadesPyQtGUI(QMainWindow, BaseGUI):
    """Main window that coordinates a :class:`SpadesGame` session."""

    def __init__(
        self,
        game: Optional[SpadesGame] = None,
        *,
        player_name: str = "You",
        enable_sounds: bool = True,
    ) -> None:
        """Initialise the PyQt GUI and start the first round.

        Args:
            game: Optional pre-configured :class:`SpadesGame` instance.
            player_name: Display name used when creating a default human player.

        Raises:
            RuntimeError: Raised when PyQt5 is unavailable at runtime.
        """

        if not PYQT5_AVAILABLE:
            raise RuntimeError("PyQt5 is required to launch the Spades PyQt GUI")

        QMainWindow.__init__(self)
        config = GUIConfig(
            window_title="Card Games - Spades",
            window_width=1100,
            window_height=760,
            theme_name="dark",
            accessibility_mode=True,
            enable_sounds=enable_sounds,
            enable_animations=True,
        )
        BaseGUI.__init__(self, self, config)
        self.sound_manager = initialize_game_soundscape(
            "spades",
            module_file=__file__,
            enable_sounds=config.enable_sounds,
            existing_manager=self.sound_manager,
        )

        if game is None:
            players = [
                SpadesPlayer(name=player_name, is_ai=False),
                SpadesPlayer(name="AI North", is_ai=True),
                SpadesPlayer(name="Partner", is_ai=True),
                SpadesPlayer(name="AI East", is_ai=True),
            ]
            self.game = SpadesGame(players)
        else:
            self.game = game

        self.human_index = next((idx for idx, player in enumerate(self.game.players) if not player.is_ai), 0)
        self.human_player = self.game.players[self.human_index]
        self.team_names = [
            " & ".join((self.game.players[0].name, self.game.players[2].name)),
            " & ".join((self.game.players[1].name, self.game.players[3].name)),
        ]

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.phase = "Bidding"
        self.status_text = "Welcome to Spades! Enter your bid to begin."

        self.team_score_labels: List[QLabel] = []
        self.team_bag_labels: List[QLabel] = []
        self.trick_labels: Dict[str, QLabel] = {}
        self.bid_displays: Dict[str, _BidDisplay] = {}

        self.phase_label: Optional[QLabel] = None
        self.status_label: Optional[QLabel] = None
        self.bid_spinbox: Optional[QSpinBox] = None
        self.bid_button: Optional[QPushButton] = None
        self.next_round_button: Optional[QPushButton] = None
        self.log_widget: Optional[QTextEdit] = None
        self.breakdown_widget: Optional[QTextEdit] = None
        self.hand_container: Optional[QWidget] = None
        self.hand_layout: Optional[QGridLayout] = None

        self.awaiting_bid = False
        self.awaiting_play = False
        self.bids_taken = 0
        self.bidding_index: Optional[int] = None
        self.leader_index: Optional[int] = None

        self.build_layout()
        self.apply_theme()

        self.register_shortcut("Ctrl+N", self._shortcut_next_round, "Start the next round after scoring")
        self.register_shortcut("Ctrl+L", self._focus_log, "Focus the round log")
        self.register_shortcut("F1", self.show_shortcuts_help, "Display keyboard shortcut help")

        self.start_new_round()

    def build_layout(self) -> None:
        """Construct the Spades interface using Qt group boxes and layouts."""

        main_layout = QGridLayout()
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)
        main_layout.setRowStretch(3, 1)
        main_layout.setRowStretch(4, 1)
        self.central_widget.setLayout(main_layout)

        header_widget = QWidget(self.central_widget)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_widget.setLayout(header_layout)

        self.status_label = QLabel(self.status_text)
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("statusLabel")
        header_layout.addWidget(self.status_label, 1)

        self.phase_label = QLabel(self.phase)
        self.phase_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.phase_label.setObjectName("phaseLabel")
        header_layout.addWidget(self.phase_label, 0)

        main_layout.addWidget(header_widget, 0, 0, 1, 2)

        score_group = QGroupBox("Partnership scores", self.central_widget)
        score_layout = QGridLayout()
        score_layout.setContentsMargins(12, 12, 12, 12)
        score_group.setLayout(score_layout)

        for index, name in enumerate(self.team_names):
            name_label = QLabel(name)
            name_label.setObjectName(f"teamName{index}")
            name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            name_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
            score_layout.addWidget(name_label, index * 2, 0, 1, 2)

            score_value = QLabel("0")
            score_value.setAlignment(Qt.AlignmentFlag.AlignRight)
            score_value.setStyleSheet("font-size: 14pt; color: #79c0ff;")
            score_layout.addWidget(score_value, index * 2, 2)
            self.team_score_labels.append(score_value)

            bag_label = QLabel("0 bags")
            bag_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            score_layout.addWidget(bag_label, index * 2 + 1, 0, 1, 3)
            self.team_bag_labels.append(bag_label)

        main_layout.addWidget(score_group, 1, 0)

        bidding_group = QGroupBox("Bidding", self.central_widget)
        bidding_layout = QGridLayout()
        bidding_layout.setContentsMargins(12, 12, 12, 12)
        bidding_group.setLayout(bidding_layout)

        self.bid_spinbox = QSpinBox()
        self.bid_spinbox.setRange(0, 13)
        self.bid_spinbox.setToolTip("Select your bid between 0 and 13")
        bidding_layout.addWidget(self.bid_spinbox, 0, 0)

        self.bid_button = QPushButton("Submit bid")
        self.bid_button.setToolTip("Submit the selected bid")
        self.bid_button.clicked.connect(self._handle_human_bid)
        bidding_layout.addWidget(self.bid_button, 0, 1)

        separator = QWidget()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #3c3c3c;")
        bidding_layout.addWidget(separator, 1, 0, 1, 2)

        for row_index, player in enumerate(self.game.players, start=2):
            name_label = QLabel(player.name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            bidding_layout.addWidget(name_label, row_index, 0)

            value_label = QLabel("Pending")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_label.setObjectName(f"bidValue{player.name}")
            bidding_layout.addWidget(value_label, row_index, 1)
            self.bid_displays[player.name] = _BidDisplay(value_label=value_label)

        main_layout.addWidget(bidding_group, 1, 1)

        trick_group = QGroupBox("Current trick", self.central_widget)
        trick_layout = QGridLayout()
        trick_layout.setContentsMargins(12, 12, 12, 12)
        trick_group.setLayout(trick_layout)

        for index, player in enumerate(self.game.players):
            name_label = QLabel(player.name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            trick_layout.addWidget(name_label, index, 0)

            value_label = QLabel("Waiting")
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            value_label.setObjectName(f"trickValue{player.name}")
            trick_layout.addWidget(value_label, index, 1)
            self.trick_labels[player.name] = value_label

        main_layout.addWidget(trick_group, 2, 0)

        hand_group = QGroupBox("Your hand", self.central_widget)
        hand_layout = QVBoxLayout()
        hand_group.setLayout(hand_layout)

        self.hand_container = QWidget()
        self.hand_layout = QGridLayout()
        self.hand_layout.setContentsMargins(6, 6, 6, 6)
        self.hand_layout.setHorizontalSpacing(6)
        self.hand_layout.setVerticalSpacing(6)
        self.hand_container.setLayout(self.hand_layout)
        hand_layout.addWidget(self.hand_container)

        main_layout.addWidget(hand_group, 2, 1)

        log_group = QGroupBox("Round log", self.central_widget)
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)

        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setToolTip("Chronological record of bids and plays")
        log_layout.addWidget(self.log_widget)

        main_layout.addWidget(log_group, 3, 0, 1, 2)

        breakdown_group = QGroupBox("Round breakdown", self.central_widget)
        breakdown_layout = QVBoxLayout()
        breakdown_group.setLayout(breakdown_layout)

        self.breakdown_widget = QTextEdit()
        self.breakdown_widget.setReadOnly(True)
        self.breakdown_widget.setToolTip("Summary of bidding, tricks, and scores for the round")
        breakdown_layout.addWidget(self.breakdown_widget)

        main_layout.addWidget(breakdown_group, 4, 0, 1, 2)

        controls_widget = QWidget(self.central_widget)
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(12, 6, 12, 6)
        controls_widget.setLayout(controls_layout)
        controls_layout.addStretch(1)

        self.next_round_button = QPushButton("Start next round")
        self.next_round_button.setToolTip("Start the next round after reviewing scores")
        self.next_round_button.setEnabled(False)
        self.next_round_button.clicked.connect(self.start_new_round)
        controls_layout.addWidget(self.next_round_button)

        main_layout.addWidget(controls_widget, 5, 0, 1, 2)

    def update_display(self) -> None:
        """Refresh all dynamic widgets to match the latest game state."""

        for index in (0, 1):
            self.team_score_labels[index].setText(str(self.game.team_scores[index]))
            self.team_bag_labels[index].setText(f"{self.game.bags[index]} bags")

        self._update_bids_panel()
        self._update_trick_display()
        self._render_hand()

        if self.phase_label is not None:
            self.phase_label.setText(self.phase)
        if self.status_label is not None:
            self.status_label.setText(self.status_text)

        if self.bid_spinbox is not None:
            self.bid_spinbox.setEnabled(self.awaiting_bid)
        if self.bid_button is not None:
            self.bid_button.setEnabled(self.awaiting_bid)

        if self.next_round_button is not None:
            enable = self.phase == "Round complete" and not self.game.is_game_over()
            self.next_round_button.setEnabled(enable)

    def start_new_round(self) -> None:
        """Start a new round, resetting bidding state and prompting the leader."""

        if self.game.is_game_over():
            self.status_text = "The match is over. Restart the programme for a new game."
            self.phase = "Game complete"
            self.update_display()
            return

        self.game.start_new_round()
        self.phase = "Bidding"
        self.status_text = "Bidding phase: enter your bid when prompted."
        self.bids_taken = 0
        self.awaiting_play = False
        self.leader_index = self.game.current_player_index or 0
        self.bidding_index = self.leader_index

        for display in self.bid_displays.values():
            display.value_label.setText("Pending")
        for value in self.trick_labels.values():
            value.setText("Waiting")

        if self.bid_spinbox is not None:
            self.bid_spinbox.setValue(0)

        if self.breakdown_widget is not None:
            self.breakdown_widget.clear()

        if self.log_widget is not None:
            self._log_message(f"\nRound {self.game.round_number} begins. Leader: {self.game.players[self.leader_index].name}.")

        self.update_display()
        self._prompt_next_bidder()

    def _shortcut_next_round(self) -> None:
        """Keyboard shortcut handler for advancing to the next round."""

        if self.phase == "Round complete" and self.next_round_button and self.next_round_button.isEnabled():
            self.start_new_round()

    def _focus_log(self) -> None:
        """Give keyboard focus to the log widget for accessibility purposes."""

        if self.log_widget is not None:
            self.log_widget.setFocus()

    def _prompt_next_bidder(self) -> None:
        """Advance bidding order, prompting either the human or AI players."""

        if self.bids_taken >= len(self.game.players):
            self._finish_bidding()
            return

        assert self.bidding_index is not None
        player = self.game.players[self.bidding_index]
        if player.is_ai:
            self.awaiting_bid = False
            self.status_text = f"Waiting for {player.name} to bid..."
            self.update_display()

            QTimer.singleShot(400, lambda p=player: self._record_ai_bid(p))
        else:
            self.awaiting_bid = True
            self.status_text = "Enter your bid (0-13) and press Submit bid."
            self.update_display()
            if self.bid_spinbox is not None:
                self.bid_spinbox.setFocus()

    def _handle_human_bid(self) -> None:
        """Validate and register the human player's bid selection."""

        if not self.awaiting_bid or self.bid_spinbox is None:
            return

        bid_value = int(self.bid_spinbox.value())
        self.awaiting_bid = False
        self._register_bid(self.human_player, bid_value)
        self._advance_bid_order()

    def _register_bid(self, player: SpadesPlayer, bid_value: int) -> None:
        """Record a bid with the game engine and update the UI."""

        self.game.register_bid(player, bid_value)
        label = "Blind nil" if player.blind_nil else ("Nil" if bid_value == 0 else str(bid_value))
        self.bid_displays[player.name].value_label.setText(label)
        if self.log_widget is not None:
            self._log_message(f"{player.name} bids {label}.")

    def _record_ai_bid(self, player: SpadesPlayer) -> None:
        """Request an AI bid and proceed to the next player."""

        if self.phase != "Bidding":
            return

        bid_value = self.game.suggest_bid(player)
        self._register_bid(player, bid_value)
        self._advance_bid_order()

    def _advance_bid_order(self) -> None:
        """Move bidding control to the next player in sequence."""

        self.bids_taken += 1
        if self.bids_taken >= len(self.game.players):
            self._finish_bidding()
            return

        assert self.bidding_index is not None
        self.bidding_index = (self.bidding_index + 1) % len(self.game.players)
        self._prompt_next_bidder()

    def _finish_bidding(self) -> None:
        """Transition from bidding into active trick play."""

        self.phase = "Playing"
        self.status_text = "Trick play: follow suit when you can."
        self.awaiting_bid = False
        self.update_display()
        QTimer.singleShot(300, self._advance_ai_turns)

    def _advance_ai_turns(self) -> None:
        """Play out AI turns until the human player must act."""

        if self.phase != "Playing":
            return

        current_index = self.game.current_player_index or 0
        player = self.game.players[current_index]

        if not player.is_ai:
            self.awaiting_play = True
            self.status_text = "Your turn: select an available card to play."
            self.update_display()
            return

        self.awaiting_play = False
        self.status_text = f"{player.name} is selecting a card..."
        self.update_display()

        def complete_ai_turn() -> None:
            if self.phase != "Playing":
                return

            card = self.game.select_card_to_play(player)
            self.game.play_card(player, card)
            if self.log_widget is not None:
                self._log_message(f"{player.name} plays {card}.")
            self.update_display()

            if len(self.game.current_trick) == 4:
                winner = self.game.complete_trick()
                if self.log_widget is not None:
                    self._log_message(f"{winner.name} wins the trick.")
                for value in self.trick_labels.values():
                    value.setText("Waiting")
                self.update_display()

                if self.game.total_tricks_played >= 13:
                    self._finish_round()
                    return

            QTimer.singleShot(450, self._advance_ai_turns)

        QTimer.singleShot(420, complete_ai_turn)

    def _on_card_selected(self, card: Card) -> None:
        """Handle a card button click from the human player."""

        if self.phase != "Playing" or not self.awaiting_play:
            return

        try:
            self.game.play_card(self.human_player, card)
        except ValueError:
            self.status_text = "That card is not a legal play right now."
            self.update_display()
            return

        self.awaiting_play = False
        if self.log_widget is not None:
            self._log_message(f"{self.human_player.name} plays {card}.")
        self.update_display()

        if len(self.game.current_trick) == 4:
            winner = self.game.complete_trick()
            if self.log_widget is not None:
                self._log_message(f"{winner.name} wins the trick.")
            for value in self.trick_labels.values():
                value.setText("Waiting")
            self.update_display()
            if self.game.total_tricks_played >= 13:
                self._finish_round()
                return

        QTimer.singleShot(350, self._advance_ai_turns)

    def _update_bids_panel(self) -> None:
        """Synchronise bid labels with player data when in or after bidding."""

        for player in self.game.players:
            display = self.bid_displays[player.name]
            if player.bid is None:
                display.value_label.setText("Pending")
            elif player.blind_nil:
                display.value_label.setText("Blind nil")
            elif player.bid == 0:
                display.value_label.setText("Nil")
            else:
                display.value_label.setText(str(player.bid))

    def _update_trick_display(self) -> None:
        """Show the current trick composition in the trick panel."""

        active = {player.name: str(card) for player, card in self.game.current_trick}
        for player in self.game.players:
            self.trick_labels[player.name].setText(active.get(player.name, "Waiting"))

    def _render_hand(self) -> None:
        """Render the human player's hand as clickable card buttons."""

        if self.hand_layout is None:
            return

        while self.hand_layout.count():
            item = self.hand_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        cards = list(self.human_player.hand)
        if not cards:
            placeholder = QLabel("(No cards)")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.hand_layout.addWidget(placeholder, 0, 0)
            return

        valid_cards = set(self.game.get_valid_plays(self.human_player)) if self.phase == "Playing" else set(cards)

        for column, card in enumerate(cards):
            button = QPushButton(str(card))
            button.setToolTip(f"Play {card}")
            button.setEnabled(self.awaiting_play and card in valid_cards)
            button.clicked.connect(lambda _=False, c=card: self._on_card_selected(c))
            self.hand_layout.addWidget(button, 0, column)

    def _set_breakdown_text(self, text: str) -> None:
        """Update the breakdown panel with new round information."""

        if self.breakdown_widget is None:
            return
        self.breakdown_widget.setPlainText(text)

    def _finish_round(self) -> None:
        """Calculate scores, update summaries, and await the next round."""

        round_scores = self.game.calculate_round_score()
        lines = [f"Round {self.game.round_number} results:"]
        for player in self.game.players:
            bid_text = "Nil" if (player.bid or 0) == 0 else str(player.bid)
            lines.append(f"  {player.name}: bid {bid_text}, won {player.tricks_won} tricks")
        lines.append("")
        lines.append("Bids:")
        for bidder, bid in self.game.bidding_history:
            lines.append(f"  {bidder.name}: {bid}")
        lines.append("")
        lines.append("Tricks:")
        for index, trick in enumerate(self.game.trick_history, start=1):
            plays = ", ".join(f"{player.name} {card}" for player, card in trick)
            lines.append(f"  Trick {index}: {plays}")
        lines.append("")
        lines.append(f"Partnership 1 ({self.team_names[0]}): {round_scores[0]} this round, {self.game.team_scores[0]} total, {self.game.bags[0]} bags")
        lines.append(f"Partnership 2 ({self.team_names[1]}): {round_scores[1]} this round, {self.game.team_scores[1]} total, {self.game.bags[1]} bags")

        self.phase = "Round complete"
        self.status_text = "Round complete. Review the breakdown or press Ctrl+N for the next round."
        self.awaiting_play = False
        self._set_breakdown_text("\n".join(lines))
        self.update_display()

        if self.game.is_game_over():
            winner_index = self.game.get_winner()
            if winner_index is None:
                self.status_text = "Game complete: the partnerships tied."
            else:
                self.status_text = f"Game complete: {self.team_names[winner_index]} win!"
            if self.next_round_button is not None:
                self.next_round_button.setEnabled(False)
            self.update_display()

    def _log_message(self, message: str) -> None:
        """Append a message to the round log widget."""

        if self.log_widget is not None:
            self.log_widget.append(message)
            scrollbar = self.log_widget.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())


def run_app(player_name: Optional[str] = None) -> None:
    """Launch the Spades PyQt GUI application."""

    if not PYQT5_AVAILABLE:
        raise RuntimeError("PyQt5 is not available; cannot launch the Spades GUI.")

    app = QApplication.instance() or QApplication([])
    window = SpadesPyQtGUI(player_name=player_name or "You")
    window.show()
    app.exec_()


__all__ = ["SpadesPyQtGUI", "run_app"]
