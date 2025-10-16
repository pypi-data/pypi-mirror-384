"""PyQt5 graphical interface for the Bluff card game.

The widget tree mirrors the structure of the original Tkinter GUI but swaps in
Qt equivalents that better match the repository's migration plan:

* **Log panel** – Implemented with :class:`~PyQt5.QtWidgets.QTextEdit` so the
  scrolling transcript from the CLI is always visible.
* **Scoreboard** – Rendered via :class:`~PyQt5.QtWidgets.QTableWidget` allowing
  both team and individual statistics to be displayed in a tabular format.
* **Card controls** – Built from an exclusive :class:`~PyQt5.QtWidgets.QButtonGroup`
  containing :class:`~PyQt5.QtWidgets.QPushButton` instances for each card in the
  user's hand, providing an intuitive way to pick a card before confirming a
  claim.

The asynchronous flow that relied on ``Tk.after`` has been converted to
``QTimer.singleShot`` calls so the UI remains responsive while bots take their
turns and challenges are resolved.  Dialog prompts for confirming claims and
deciding whether to challenge now use :class:`~PyQt5.QtWidgets.QMessageBox`
which keeps the interaction style consistent with other PyQt5 GUIs in the
project.
"""

from __future__ import annotations

import random
from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .bluff import BluffGame, DeckType, DifficultyLevel, Phase
from card_games.common.soundscapes import initialize_game_soundscape
from common.gui_base_pyqt import BaseGUI, GUIConfig


class BluffPyQtGUI(QWidget, BaseGUI):
    """PyQt5 GUI that orchestrates a BluffGame session.

    The widget is responsible for constructing the interface, synchronising the
    display with the underlying :class:`~card_games.bluff.bluff.BluffGame`
    instance, and handling all user input.  It keeps track of the currently
    selected card index and the most recent claim text so both can be updated in
    response to status changes.
    """

    def __init__(
        self,
        game: BluffGame,
        *,
        enable_sounds: bool = True,
        config: Optional[GUIConfig] = None,
    ) -> None:
        """Initialise the PyQt5 GUI.

        Args:
            game: The active :class:`BluffGame` instance that supplies state and
                resolves actions.
        """

        QWidget.__init__(self)
        gui_config = config or GUIConfig(
            window_title="Card Games - Bluff (PyQt5)",
            window_width=1080,
            window_height=720,
            enable_sounds=enable_sounds,
            enable_animations=True,
            theme_name="dark",
        )
        BaseGUI.__init__(self, root=self, config=gui_config)
        self.sound_manager = initialize_game_soundscape(
            "bluff",
            module_file=__file__,
            enable_sounds=gui_config.enable_sounds,
            existing_manager=self.sound_manager,
        )
        self.game = game

        self._selected_card: Optional[int] = None
        self._last_claim_text = "No claim yet."

        self.setWindowTitle("Card Games - Bluff (PyQt5)")
        self.resize(1080, 720)

        self._build_layout()
        self._populate_rank_choices()
        self._update_header()
        self._update_scoreboard()
        self._update_user_hand()
        self._set_user_controls_enabled(False)

        self._log_message("Welcome to Bluff! Shed every card to win.")
        QTimer.singleShot(300, self.advance_game)

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        """Create all widgets and layouts for the interface."""

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        header_widget = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(12, 12, 12, 12)
        header_widget.setLayout(header_layout)

        self.status_label = QLabel("Welcome to Bluff! Shed every card to win.")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(self.status_label, 3, Qt.AlignmentFlag.AlignLeft)

        self.turn_label = QLabel("Turn 1")
        self.turn_label.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(self.turn_label, 1, Qt.AlignmentFlag.AlignRight)

        self.pile_label = QLabel("Pile: 0 cards")
        self.pile_label.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(self.pile_label, 1, Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(header_widget)

        content_widget = QWidget()
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(12, 0, 12, 0)
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget, 1)

        log_group = QGroupBox("Game Log")
        log_layout = QVBoxLayout()
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setStyleSheet("background-color: #101820; color: #E0E6ED;")
        log_layout.addWidget(self.log_edit)
        log_group.setLayout(log_layout)
        content_layout.addWidget(log_group, 3)

        sidebar_group = QGroupBox("Scoreboard")
        sidebar_layout = QVBoxLayout()
        sidebar_group.setLayout(sidebar_layout)
        content_layout.addWidget(sidebar_group, 2)

        self.scoreboard = QTableWidget(0, 5)
        self.scoreboard.setHorizontalHeaderLabels(["Player/Team", "Cards", "Truths", "Lies", "Calls"])
        self.scoreboard.horizontalHeader().setStretchLastSection(True)
        self.scoreboard.verticalHeader().setVisible(False)
        self.scoreboard.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.scoreboard.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        sidebar_layout.addWidget(self.scoreboard)

        self.last_claim_label = QLabel(self._last_claim_text)
        self.last_claim_label.setWordWrap(True)
        sidebar_layout.addWidget(self.last_claim_label)

        controls_group = QGroupBox("Player Controls")
        controls_layout = QVBoxLayout()
        controls_layout.setContentsMargins(12, 12, 12, 12)
        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group)

        self.hand_group = QGroupBox("Your hand")
        self.hand_layout = QGridLayout()
        self.hand_layout.setHorizontalSpacing(8)
        self.hand_layout.setVerticalSpacing(8)
        self.hand_group.setLayout(self.hand_layout)
        controls_layout.addWidget(self.hand_group)

        claim_row = QWidget()
        claim_row_layout = QHBoxLayout()
        claim_row_layout.setContentsMargins(0, 0, 0, 0)
        claim_row.setLayout(claim_row_layout)
        controls_layout.addWidget(claim_row)

        claim_row_layout.addWidget(QLabel("Declare rank:"))
        self.claim_combo = QComboBox()
        claim_row_layout.addWidget(self.claim_combo, 1)

        self.submit_button = QPushButton("Play selected card")
        self.submit_button.clicked.connect(self.submit_claim)
        claim_row_layout.addWidget(self.submit_button)

        self.card_button_group = QButtonGroup(self)
        self.card_button_group.setExclusive(True)
        self.card_button_group.idClicked.connect(self._select_card)

    def _populate_rank_choices(self) -> None:
        """Populate the rank combo box with valid ranks."""

        self.claim_combo.clear()
        for rank in self.game.deck_type.ranks:
            self.claim_combo.addItem(rank)

    # ------------------------------------------------------------------
    # State synchronisation
    # ------------------------------------------------------------------
    def _update_header(self) -> None:
        """Refresh the header labels using the game's public state."""

        state = self.game.public_state()
        self.turn_label.setText(f"Turn {state['turns_played'] + 1} of {state['max_turns']}")
        card_text = "card" if state["pile_size"] == 1 else "cards"
        self.pile_label.setText(f"Pile: {state['pile_size']} {card_text}")

    def _update_scoreboard(self) -> None:
        """Rebuild the scoreboard table to reflect current statistics."""

        rows: list[tuple[str, str, str, str, str, bool]] = []
        if getattr(self.game, "team_play", False) and getattr(self.game, "teams", None):
            for team in self.game.teams:
                rows.append((f"{team.name} (Total: {team.total_cards()} cards)", "", "", "", "", True))
                for member in team.members:
                    calls = f"{member.challenge_successes}/{member.challenge_attempts}" if member.challenge_attempts else "0/0"
                    rows.append(
                        (
                            member.name,
                            str(len(member.hand)),
                            str(member.truths),
                            str(member.lies),
                            calls,
                            False,
                        )
                    )
        else:
            for player in self.game.players:
                calls = f"{player.challenge_successes}/{player.challenge_attempts}" if player.challenge_attempts else "0/0"
                rows.append(
                    (
                        player.name,
                        str(len(player.hand)),
                        str(player.truths),
                        str(player.lies),
                        calls,
                        False,
                    )
                )

        self.scoreboard.setRowCount(len(rows))
        for row_index, (name, cards, truths, lies, calls, is_header) in enumerate(rows):
            items = [name, cards, truths, lies, calls]
            for col, value in enumerate(items):
                item = QTableWidgetItem(value)
                if is_header:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.scoreboard.setItem(row_index, col, item)

        self.scoreboard.resizeColumnsToContents()
        self.animate_highlight(self.scoreboard)

    def _set_status(self, text: str, *, highlight_color: str = "#1f6aa5") -> None:
        """Update the status label and animate the change when enabled."""

        self.status_label.setText(text)
        self.animate_highlight(self.status_label, highlight_color=highlight_color)

    def _update_user_hand(self) -> None:
        """Rebuild the user's hand buttons to match their cards."""

        # Clear existing buttons
        for button in self.card_button_group.buttons():
            self.card_button_group.removeButton(button)
            button.deleteLater()

        while self.hand_layout.count():
            item = self.hand_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        user = self.game.players[0]
        if self._selected_card is not None and self._selected_card >= len(user.hand):
            self._selected_card = None

        for index, card in enumerate(user.hand):
            button = QPushButton(str(card))
            button.setCheckable(True)
            self.card_button_group.addButton(button, index)
            row = index // 8
            column = index % 8
            self.hand_layout.addWidget(button, row, column)
            if index == self._selected_card:
                button.setChecked(True)

        if self._selected_card is not None and 0 <= self._selected_card < len(user.hand):
            self.claim_combo.setCurrentText(user.hand[self._selected_card].rank)

        if user.hand:
            self.animate_highlight(self.hand_group)

    def _set_user_controls_enabled(self, enabled: bool) -> None:
        """Enable or disable the controls for the user's turn."""

        self.submit_button.setEnabled(enabled)
        self.claim_combo.setEnabled(enabled)
        for button in self.card_button_group.buttons():
            button.setEnabled(enabled)

    def _log_message(self, message: str) -> None:
        """Append a message to the log panel."""

        self.log_edit.append(message)
        self.log_edit.verticalScrollBar().setValue(self.log_edit.verticalScrollBar().maximum())

    # ------------------------------------------------------------------
    # Game progression
    # ------------------------------------------------------------------
    def advance_game(self) -> None:
        """Progress the game state and refresh the UI."""

        self._update_header()
        self._update_scoreboard()
        self._update_user_hand()

        if self.game.finished:
            self._handle_game_end()
            return

        current = self.game.current_player
        state = self.game.public_state()
        self.turn_label.setText(f"Turn {state['turns_played'] + 1} of {state['max_turns']}")

        if current.is_user:
            self._set_status("Your turn: choose a card and declare its rank.")
            self._last_claim_text = "Awaiting your play."
            self.last_claim_label.setText(self._last_claim_text)
            self.animate_highlight(self.last_claim_label)
            self._set_user_controls_enabled(True)
        else:
            self._set_user_controls_enabled(False)
            claim, messages = self.game.play_bot_turn()
            for message in messages:
                self._log_message(message)
            self._log_message(f"{current.name} claims their card is a {claim.claimed_rank}.")
            self._last_claim_text = f"Latest claim: {current.name} says {claim.claimed_rank}."
            self.last_claim_label.setText(self._last_claim_text)
            self.animate_highlight(self.last_claim_label)
            self._update_header()
            self._update_scoreboard()
            QTimer.singleShot(450, self._resolve_challenges)

    def submit_claim(self) -> None:
        """Play the selected card with the chosen rank."""

        if self.game.finished or self.game.current_player is not self.game.players[0]:
            return

        if self._selected_card is None:
            QMessageBox.warning(self, "No card selected", "Choose a card from your hand before declaring a rank.")
            return

        user = self.game.players[0]
        if not (0 <= self._selected_card < len(user.hand)):
            QMessageBox.warning(self, "Invalid selection", "The selected card is no longer available.")
            self._selected_card = None
            self._update_user_hand()
            return

        rank = self.claim_combo.currentText().upper()
        card_preview = str(user.hand[self._selected_card])
        confirmation = QMessageBox.question(
            self,
            "Confirm claim",
            f"Play {card_preview} while claiming it is a {rank}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            claim = self.game.play_user_turn(self._selected_card, rank)
        except (ValueError, RuntimeError) as exc:  # pragma: no cover - defensive programming
            QMessageBox.critical(self, "Cannot play card", str(exc))
            return

        self._log_message(f"You play {claim.card} while stating it's a {claim.claimed_rank}.")
        self._last_claim_text = f"Latest claim: You said {claim.claimed_rank}."
        self.last_claim_label.setText(self._last_claim_text)
        self.animate_highlight(self.last_claim_label)
        self._selected_card = None
        self._set_user_controls_enabled(False)
        self._update_header()
        self._update_scoreboard()
        self._update_user_hand()
        QTimer.singleShot(200, self._resolve_challenges)

    def _select_card(self, index: int) -> None:
        """Mark a card as selected and sync the rank picker."""

        self._selected_card = index
        user = self.game.players[0]
        if 0 <= index < len(user.hand):
            self.claim_combo.setCurrentText(user.hand[index].rank)

    def _resolve_challenges(self) -> None:
        """Handle pending challenges by bots or prompt the user."""

        if self.game.finished:
            self.advance_game()
            return

        while self.game.phase == Phase.CHALLENGE and not self.game.finished:
            challenger = self.game.current_challenger
            if challenger is None:
                break

            if challenger.is_user:
                claim = self.game.claim_in_progress
                if claim is None:
                    break
                prompt = f"{claim.claimant.name} claims the card is a {claim.claimed_rank}.\n" "Do you want to challenge the claim?"
                response = QMessageBox.question(
                    self,
                    "Challenge claim?",
                    prompt,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                decision = response == QMessageBox.StandardButton.Yes
                if decision:
                    self._log_message("You challenge the claim!")
                else:
                    self._log_message("You let the claim stand.")
                self._finish_resolve_challenge(decision)
                return

            decision = self.game.bot_should_challenge(challenger)
            action_text = "challenges the claim!" if decision else "decides to wait."
            self._log_message(f"{challenger.name} {action_text}")
            outcome = self.game.evaluate_challenge(decision)
            for line in outcome.messages:
                self._log_message(line)
            self._update_header()
            self._update_scoreboard()
            self._update_user_hand()

        if self.game.phase != Phase.CHALLENGE:
            QTimer.singleShot(450, self.advance_game)

    def _finish_resolve_challenge(self, decision: bool) -> None:
        """Resolve a challenge decision and schedule the next action."""

        outcome = self.game.evaluate_challenge(decision)
        for line in outcome.messages:
            self._log_message(line)

        self._update_header()
        self._update_scoreboard()
        self._update_user_hand()

        if self.game.phase == Phase.CHALLENGE:
            QTimer.singleShot(350, self._resolve_challenges)
        else:
            QTimer.singleShot(450, self.advance_game)

    def _handle_game_end(self) -> None:
        """Display a dialog summarising the game outcome."""

        self._set_user_controls_enabled(False)

        if self.game.winner is None:
            message = "The match ends in a tie."
        elif self.game.winner.is_user:
            message = "Congratulations, you outmaneuvered the table!"
        else:
            message = f"{self.game.winner.name} claims victory this time."

        self._set_status(message)
        QMessageBox.information(self, "Game complete", message)


def run_gui(
    difficulty: DifficultyLevel,
    *,
    rounds: int,
    seed: int | None = None,
    deck_type: DeckType | None = None,
    record_replay: bool = False,
) -> None:
    """Launch the PyQt5 GUI for the Bluff card game."""

    rng = random.Random(seed) if seed is not None else random.Random()
    game = BluffGame(
        difficulty,
        rounds=rounds,
        rng=rng,
        record_replay=record_replay,
        seed=seed,
        deck_type=deck_type,
    )

    app = QApplication.instance() or QApplication([])
    window = BluffPyQtGUI(game)
    window.show()
    app.exec_()
