"""PyQt5 graphical interface for the Hearts card game.

This module ports the original Tkinter interface to the shared
``common.gui_base_pyqt.BaseGUI`` infrastructure. The layout mirrors the
tabletop experience offered by the legacy implementation while adopting
native Qt widgets for richer accessibility support and better
integration with the rest of the PyQt5 migration work.

Key interface areas:

* **Header & status row** – shows the current round, whether hearts have
  been broken, and keyboard shortcut hints.
* **Passing controls** – multi-select list that lets the human choose
  three cards to pass when required.
* **Trick arena** – four seat widgets around the table representing the
  cards played in the current trick.
* **Scoreboard & log** – live scores, penalty tracking, and the running
  action log powered by :class:`~PyQt5.QtWidgets.QTextEdit`.

The GUI preserves all keyboard shortcuts exposed by the original
Tkinter variant via :meth:`common.gui_base_pyqt.BaseGUI.register_shortcut`.
Timers (:class:`~PyQt5.QtCore.QTimer`) replace ``Tk.after`` calls so that
AI turns continue to feel fluid without blocking the Qt event loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from card_games.common.cards import Card, Suit, format_cards
from common.gui_base_pyqt import BaseGUI, GUIConfig

from .game import QUEEN_OF_SPADES, HeartsGame, HeartsPlayer, PassDirection


@dataclass
class _TrickSeatWidget:
    """Represents the widgets that render a single table seat."""

    frame: QFrame
    name_label: QLabel
    card_label: QLabel

    def set_name(self, text: str) -> None:
        self.name_label.setText(text)

    def show_card(self, card_text: str) -> None:
        self.card_label.setText(card_text)


class HeartsGUI(QMainWindow):
    """PyQt5 GUI for a round of Hearts.

    Note: Does not inherit from BaseGUI as it's designed for Tkinter,
    and would cause metaclass conflicts with QMainWindow.
    """

    def __init__(
        self,
        game: HeartsGame,
        *,
        human_index: int = 0,
        config: Optional[GUIConfig] = None,
    ) -> None:
        self.game = game
        self.human_index = human_index
        self.phase: str = "passing"
        self.pending_passes: Dict[HeartsPlayer, Sequence[Card]] = {}
        self.pass_selection: set[Card] = set()
        self.current_player_index: Optional[int] = None
        self.table_seats: Dict[int, _TrickSeatWidget] = {}

        self.status_label: Optional[QLabel] = None
        self.shortcut_hint_label: Optional[QLabel] = None
        self.round_label: Optional[QLabel] = None
        self.hearts_label: Optional[QLabel] = None
        self.pass_group: Optional[QGroupBox] = None
        self.pass_direction_label: Optional[QLabel] = None
        self.pass_list: Optional[QListWidget] = None
        self.pass_button: Optional[QPushButton] = None
        self.play_group: Optional[QGroupBox] = None
        self.play_hint_label: Optional[QLabel] = None
        self.play_cards_container: Optional[QWidget] = None
        self.play_cards_layout: Optional[QGridLayout] = None
        self.next_round_button: Optional[QPushButton] = None
        self.score_table: Optional[QTableWidget] = None
        self.log_widget: Optional[QTextEdit] = None

        QMainWindow.__init__(self)

        default_config = GUIConfig(
            window_title="Hearts – PyQt5 Table",
            window_width=1100,
            window_height=780,
            background_color="#0B1622",
            font_family="Segoe UI",
            font_size=12,
            log_height=12,
            log_width=70,
            enable_sounds=False,
            enable_animations=True,
            theme_name="midnight",
            language="en",
            accessibility_mode=config.accessibility_mode if config else False,
        )

        BaseGUI.__init__(self, root=self, config=config or default_config)

        self._build_reference_fonts()
        self.build_layout()
        self.update_display()
        self._start_new_round()

    # ------------------------------------------------------------------
    # BaseGUI overrides
    # ------------------------------------------------------------------
    def build_layout(self) -> None:
        """Create the static widget hierarchy for the GUI."""

        central = QWidget(self)
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        central.setLayout(main_layout)

        # Header
        header = QWidget(central)
        header_layout = QGridLayout()
        header_layout.setColumnStretch(0, 2)
        header_layout.setColumnStretch(1, 1)
        header_layout.setColumnStretch(2, 1)
        header.setLayout(header_layout)

        title = self.create_header(header, "Hearts Table")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(title, 0, 0)

        self.round_label = QLabel("Round 1", header)
        self.round_label.setFont(QFont(self.config.font_family, self.config.font_size + 2, QFont.Weight.Bold))
        header_layout.addWidget(self.round_label, 0, 1, Qt.AlignmentFlag.AlignRight)

        self.hearts_label = QLabel("Hearts are unbroken", header)
        header_layout.addWidget(self.hearts_label, 0, 2, Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(header)

        # Status bar with shortcut hints
        status_row = QWidget(central)
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_row.setLayout(status_layout)

        self.status_label = QLabel("Setting up table…", status_row)
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label, 3)

        self.shortcut_hint_label = QLabel("Ctrl+H: accessibility help | Ctrl+L: focus log", status_row)
        self.shortcut_hint_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        status_layout.addWidget(self.shortcut_hint_label, 2)

        main_layout.addWidget(status_row)

        # Main body with table and sidebar
        body = QWidget(central)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(16)
        body.setLayout(body_layout)
        main_layout.addWidget(body, 1)

        # Left column – trick arena and controls
        left_column = QWidget(body)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)
        left_column.setLayout(left_layout)
        body_layout.addWidget(left_column, 3)

        self._build_trick_arena(left_column)
        self._build_passing_controls(left_column)
        self._build_play_controls(left_column)

        # Right column – scoreboard and log
        right_column = QWidget(body)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(12)
        right_column.setLayout(right_layout)
        body_layout.addWidget(right_column, 2)

        self._build_scoreboard(right_column)
        self._build_log(right_column)

    def update_display(self) -> None:
        """Refresh scoreboard, trick view, and header text."""

        self._refresh_scoreboard()
        self._update_trick_cards()
        self._update_status_banner()

    def _setup_shortcuts(self) -> None:
        """Register keyboard shortcuts supported by the GUI."""

        self.register_shortcut(
            "Ctrl+N",
            self._handle_shortcut_new_round,
            "Start the next round once scoring is complete",
        )
        self.register_shortcut(
            "Ctrl+L",
            self._focus_log,
            "Move focus to the action log",
        )
        self.register_shortcut(
            "Ctrl+H",
            self._show_accessibility_tips,
            "Show accessibility options for the Hearts table",
        )

    # ------------------------------------------------------------------
    # Layout construction helpers
    # ------------------------------------------------------------------
    def _build_reference_fonts(self) -> None:
        """Prepare fonts used throughout the interface."""

        self._card_font = QFont("Consolas", self.config.font_size + 6)
        self._name_font = QFont(self.config.font_family, self.config.font_size, QFont.Weight.Bold)

    def _build_trick_arena(self, parent: QWidget) -> None:
        """Construct widgets representing the four seats around the table."""

        arena_group = QGroupBox("Current trick", parent)
        arena_layout = QGridLayout()
        arena_layout.setSpacing(12)
        arena_group.setLayout(arena_layout)
        parent.layout().addWidget(arena_group)

        seat_indices = [
            self.human_index,
            (self.human_index + 1) % 4,
            (self.human_index + 2) % 4,
            (self.human_index + 3) % 4,
        ]
        seat_positions = {
            seat_indices[0]: (2, 1),  # South (human)
            seat_indices[1]: (1, 2),  # West
            seat_indices[2]: (0, 1),  # North
            seat_indices[3]: (1, 0),  # East
        }

        for index, (row, col) in seat_positions.items():
            frame = QFrame(arena_group)
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            frame_layout = QVBoxLayout()
            frame_layout.setContentsMargins(8, 8, 8, 8)
            frame.setLayout(frame_layout)

            name_label = QLabel(self._format_player_name(index), frame)
            name_label.setFont(self._name_font)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            frame_layout.addWidget(name_label)

            card_label = QLabel("–", frame)
            card_label.setFont(self._card_font)
            card_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_label.setMinimumHeight(48)
            frame_layout.addWidget(card_label)

            arena_layout.addWidget(frame, row, col)
            self.table_seats[index] = _TrickSeatWidget(frame=frame, name_label=name_label, card_label=card_label)

    def _build_passing_controls(self, parent: QWidget) -> None:
        """Create controls for the passing phase."""

        self.pass_group = QGroupBox("Passing phase", parent)
        layout = QVBoxLayout()
        layout.setSpacing(8)
        self.pass_group.setLayout(layout)

        top_row = QWidget(self.pass_group)
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_row.setLayout(top_layout)

        self.pass_direction_label = QLabel("", top_row)
        top_layout.addWidget(self.pass_direction_label, 1)

        self.pass_button = QPushButton("Pass selected cards", top_row)
        self.pass_button.setEnabled(False)
        self.pass_button.clicked.connect(self._finalise_pass_selection)
        top_layout.addWidget(self.pass_button, 0, Qt.AlignmentFlag.AlignRight)

        layout.addWidget(top_row)

        self.pass_list = QListWidget(self.pass_group)
        self.pass_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.pass_list.itemSelectionChanged.connect(self._handle_pass_selection_change)
        self.pass_list.setAlternatingRowColors(True)
        self.pass_list.setAccessibleName("Select exactly three cards to pass")
        layout.addWidget(self.pass_list)

        parent.layout().addWidget(self.pass_group)

    def _build_play_controls(self, parent: QWidget) -> None:
        """Create the trick-playing controls that appear after passing."""

        self.play_group = QGroupBox("Play a card", parent)
        play_layout = QVBoxLayout()
        play_layout.setSpacing(8)
        self.play_group.setLayout(play_layout)

        self.play_hint_label = QLabel("Waiting for your turn…", self.play_group)
        self.play_hint_label.setWordWrap(True)
        play_layout.addWidget(self.play_hint_label)

        self.play_cards_container = QWidget(self.play_group)
        self.play_cards_layout = QGridLayout()
        self.play_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.play_cards_layout.setHorizontalSpacing(6)
        self.play_cards_container.setLayout(self.play_cards_layout)
        play_layout.addWidget(self.play_cards_container)

        parent.layout().addWidget(self.play_group)
        self.play_group.hide()

    def _build_scoreboard(self, parent: QWidget) -> None:
        """Create the live scoreboard area."""

        scoreboard_group = QGroupBox("Scoreboard", parent)
        layout = QVBoxLayout()
        layout.setSpacing(6)
        scoreboard_group.setLayout(layout)

        self.score_table = QTableWidget(len(self.game.players), 4, scoreboard_group)
        self.score_table.setHorizontalHeaderLabels(["Player", "Score", "Penalty cards", "Tricks won"])
        self.score_table.verticalHeader().setVisible(False)
        self.score_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.score_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.score_table.setAlternatingRowColors(True)
        self.score_table.setAccessibleName("Scoreboard with totals and penalty counts")
        layout.addWidget(self.score_table)

        parent.layout().addWidget(scoreboard_group, 1)

    def _build_log(self, parent: QWidget) -> None:
        """Create the scrolling action log widget."""

        log_group = QGroupBox("Action log", parent)
        layout = QVBoxLayout()
        log_group.setLayout(layout)

        self.log_widget = self.create_log_widget(log_group)
        layout.addWidget(self.log_widget)

        parent.layout().addWidget(log_group, 1)

    # ------------------------------------------------------------------
    # Round management
    # ------------------------------------------------------------------
    def _start_new_round(self) -> None:
        """Deal cards, determine passing direction, and prepare the UI."""

        self.game.deal_cards()
        if self.round_label:
            self.round_label.setText(f"Round {self.game.round_number + 1}")
        self.pass_selection.clear()
        self.pending_passes = {}
        self.phase = "passing"
        if self.next_round_button:
            self.next_round_button.setEnabled(False)
        if self.pass_button:
            self.pass_button.setEnabled(False)
        if self.pass_list:
            self.pass_list.clearSelection()
        if self.hearts_label:
            self.hearts_label.setText("Hearts are unbroken")
        if self.shortcut_hint_label:
            self.shortcut_hint_label.setText("Ctrl+H: accessibility help | Ctrl+L: focus log")
        self._log(f"--- Starting round {self.game.round_number + 1} ---")

        if self.play_group:
            self.play_group.hide()
        if self.pass_group:
            self.pass_group.show()

        pass_direction = self.game.get_pass_direction()
        if pass_direction is PassDirection.NONE:
            if self.pass_direction_label:
                self.pass_direction_label.setText("No passing this round. Waiting for the 2♣.")
            if self.pass_group:
                self.pass_group.setTitle("Passing skipped")
            if self.pass_group:
                self.pass_group.hide()
            self.phase = "playing"
            self.current_player_index = self.game.players.index(self.game.find_starting_player())
            self._prepare_play_phase()
        else:
            direction_text = {
                PassDirection.LEFT: "left",
                PassDirection.RIGHT: "right",
                PassDirection.ACROSS: "across",
            }[pass_direction]
            if self.pass_direction_label:
                self.pass_direction_label.setText(f"Pass three cards to the {direction_text}.")
            if self.pass_group:
                self.pass_group.setTitle("Passing phase")
            self._render_human_hand_for_passing()
            for idx, player in enumerate(self.game.players):
                if idx == self.human_index:
                    continue
                self.pending_passes[player] = self.game.select_cards_to_pass(player)
            if self.status_label:
                self.status_label.setText("Select exactly three cards to pass.")

        self.update_display()

    def _prepare_play_phase(self) -> None:
        """Switch from passing controls to trick-taking controls."""

        assert self.current_player_index is not None
        self.phase = "playing"
        if self.pass_group:
            self.pass_group.hide()
        if self.play_group:
            self.play_group.show()
        if self.play_hint_label:
            self.play_hint_label.setText("Waiting for your turn…")
        self._render_human_hand_for_play()
        starting_player = self.game.players[self.current_player_index]
        if starting_player.hand and self.status_label:
            self.status_label.setText(f"{starting_player.name} will lead the trick.")
        QTimer.singleShot(300, self._continue_turn_sequence)

    # ------------------------------------------------------------------
    # Passing logic
    # ------------------------------------------------------------------
    def _render_human_hand_for_passing(self) -> None:
        """Populate the list view with the human hand during passing."""

        if not self.pass_list:
            return
        self.pass_list.clear()
        player = self.game.players[self.human_index]
        for card in player.hand:
            item = QListWidgetItem(str(card))
            item.setData(Qt.ItemDataRole.UserRole, card)
            self.pass_list.addItem(item)

    def _handle_pass_selection_change(self) -> None:
        """Enforce selection limits and update UI state."""

        if not self.pass_list:
            return
        items = self.pass_list.selectedItems()
        if len(items) > 3:
            for item in items[3:]:
                item.setSelected(False)
            items = self.pass_list.selectedItems()

        self.pass_selection = {item.data(Qt.ItemDataRole.UserRole) for item in items}
        if self.pass_button:
            self.pass_button.setEnabled(len(self.pass_selection) == 3)

    def _finalise_pass_selection(self) -> None:
        """Apply the selected cards and transition to the play phase."""

        if len(self.pass_selection) != 3:
            return

        human = self.game.players[self.human_index]
        ordered_cards = sorted(self.pass_selection, key=lambda c: (c.suit.value, c.value))
        self.pending_passes[human] = ordered_cards
        self.game.pass_cards(self.pending_passes)
        self._log(f"You passed {format_cards(ordered_cards)}")
        self.pass_selection.clear()
        if self.pass_list:
            self.pass_list.clearSelection()
        self.current_player_index = self.game.players.index(self.game.find_starting_player())
        self._prepare_play_phase()
        self.update_display()

    # ------------------------------------------------------------------
    # Playing logic
    # ------------------------------------------------------------------
    def _render_human_hand_for_play(self) -> None:
        """Render the human hand as buttons for the play phase."""

        if not self.play_cards_layout:
            return

        while self.play_cards_layout.count():
            item = self.play_cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        player = self.game.players[self.human_index]
        valid_cards = set(self.game.get_valid_plays(player))

        for column, card in enumerate(player.hand):
            button = QPushButton(str(card), self.play_cards_container)
            button.setEnabled(card in valid_cards)
            button.clicked.connect(lambda checked=False, c=card: self._handle_human_play(c))
            self.play_cards_layout.addWidget(button, 0, column)
            button.setAccessibleName(f"Play {card}")

    def _handle_human_play(self, card: Card) -> None:
        """Handle the human selecting a card to play."""

        if self.phase != "playing" or self.current_player_index != self.human_index:
            return
        player = self.game.players[self.human_index]
        if card not in self.game.get_valid_plays(player):
            if self.status_label:
                self.status_label.setText("That card is not valid right now.")
            return
        self.game.play_card(player, card)
        self._log(f"You played {card}")
        self._update_trick_card_display(self.human_index, card)
        self._advance_after_play()

    def _continue_turn_sequence(self) -> None:
        """Advance through AI turns until it is the human's move."""

        if self.phase != "playing" or self.current_player_index is None:
            return
        player = self.game.players[self.current_player_index]
        if not player.hand and not self.game.current_trick:
            return
        if player.is_ai:
            if self.play_hint_label:
                self.play_hint_label.setText(f"{player.name} is playing…")
            card = self.game.select_card_to_play(player)
            self.game.play_card(player, card)
            self._log(f"{player.name} played {card}")
            self._update_trick_card_display(self.current_player_index, card)
            self._advance_after_play(delay_ms=500)
        else:
            valid_cards = format_cards(self.game.get_valid_plays(player))
            if self.status_label:
                self.status_label.setText(f"Your turn. Valid cards: {valid_cards}")
            if self.play_hint_label:
                self.play_hint_label.setText("Select one of your valid cards to play.")
            self._render_human_hand_for_play()

    def _advance_after_play(self, delay_ms: int = 0) -> None:
        """Move to the next player or resolve the trick."""

        if len(self.game.current_trick) == 4:
            QTimer.singleShot(max(200, delay_ms), self._resolve_trick)
            return
        assert self.current_player_index is not None
        self.current_player_index = (self.current_player_index + 1) % 4
        QTimer.singleShot(max(200, delay_ms), self._continue_turn_sequence)
        self.update_display()

    def _resolve_trick(self) -> None:
        """Award the trick to the winner and continue play."""

        winner = self.game.complete_trick()
        self._log(f"{winner.name} won the trick")
        for seat in self.table_seats.values():
            seat.show_card("–")
        self.current_player_index = self.game.players.index(winner)
        if self.game.hearts_broken and self.hearts_label:
            self.hearts_label.setText("Hearts have been broken")
        self.update_display()
        if all(not player.hand for player in self.game.players):
            self._complete_round()
        else:
            QTimer.singleShot(600, self._continue_turn_sequence)

    def _complete_round(self) -> None:
        """Handle scoring at the end of a round and present a summary."""

        self.phase = "round_end"
        round_scores = self.game.calculate_scores()
        self._log("Round complete. Scores:")
        for player in self.game.players:
            points = round_scores[player.name]
            self._log(f"  {player.name}: {points} points (total {player.score})")
        self.game.round_number += 1
        if self.next_round_button is None and self.play_group:
            self.next_round_button = QPushButton("Start next round", self.play_group)
            self.next_round_button.clicked.connect(self._handle_next_round)
            self.play_group.layout().addWidget(self.next_round_button)
        if self.next_round_button:
            self.next_round_button.setEnabled(True)
        if self.game.is_game_over():
            winner = self.game.get_winner()
            if self.status_label:
                self.status_label.setText(f"Game over. {winner.name} wins with {winner.score} points!")
            if self.next_round_button:
                self.next_round_button.setEnabled(False)
        else:
            if self.status_label:
                self.status_label.setText("Round finished. Press the button or Ctrl+N to continue.")
        self.update_display()

    def _handle_next_round(self) -> None:
        """Start the next round when requested."""

        if self.phase != "round_end" or self.game.is_game_over():
            return
        if self.next_round_button:
            self.next_round_button.setEnabled(False)
        self._start_new_round()

    # ------------------------------------------------------------------
    # Shortcuts & accessibility helpers
    # ------------------------------------------------------------------
    def _handle_shortcut_new_round(self) -> None:
        if self.phase == "round_end" and not self.game.is_game_over():
            self._handle_next_round()

    def _focus_log(self) -> None:
        if self.log_widget:
            self.log_widget.setFocus()

    def _show_accessibility_tips(self) -> None:
        tips = (
            "Keyboard shortcuts:\n"
            "  Ctrl+L – Focus the action log\n"
            "  Ctrl+N – Start the next round\n"
            "  Ctrl+H – Show this help dialog\n\n"
            "High contrast mode is available via the --high-contrast flag or by enabling accessibility mode."
        )
        QMessageBox.information(self, "Hearts accessibility", tips)

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------
    def _refresh_scoreboard(self) -> None:
        if not self.score_table:
            return
        human_player = self.game.players[self.human_index]
        for row, player in enumerate(self.game.players):
            penalties = sum(1 for card in player.tricks_won if card.suit == Suit.HEARTS or card == QUEEN_OF_SPADES)
            tricks_captured = len(player.tricks_won) // 4 if player.tricks_won else 0
            name = f"{player.name} (You)" if player is human_player else player.name

            self.score_table.setItem(row, 0, QTableWidgetItem(name))
            self.score_table.setItem(row, 1, QTableWidgetItem(str(player.score)))
            self.score_table.setItem(row, 2, QTableWidgetItem(str(penalties)))
            self.score_table.setItem(row, 3, QTableWidgetItem(str(tricks_captured)))
        self.score_table.resizeColumnsToContents()

    def _update_trick_cards(self) -> None:
        for idx, seat in self.table_seats.items():
            seat.set_name(self._format_player_name(idx))
            seat.show_card("–")
        for player, card in self.game.current_trick:
            idx = self.game.players.index(player)
            self._update_trick_card_display(idx, card)

    def _update_trick_card_display(self, player_index: int, card: Card) -> None:
        seat = self.table_seats.get(player_index)
        if seat:
            seat.show_card(str(card))

    def _update_status_banner(self) -> None:
        if self.game.hearts_broken and self.hearts_label:
            self.hearts_label.setText("Hearts have been broken")

    def _format_player_name(self, index: int) -> str:
        player = self.game.players[index]
        suffix = " (You)" if index == self.human_index else ""
        return f"{player.name}{suffix}"

    def _log(self, message: str) -> None:
        if self.log_widget is not None:
            self.log_message(self.log_widget, message)


def run_app(
    *,
    player_name: str = "Player",
    high_contrast: bool = False,
    accessibility_mode: bool = False,
) -> None:
    """Launch the Hearts PyQt5 GUI with optional accessibility settings."""

    app = QApplication.instance() or QApplication([])
    config = GUIConfig(
        window_title="Hearts – PyQt5 Table",
        window_width=1100,
        window_height=780,
        accessibility_mode=accessibility_mode or high_contrast,
        theme_name="high_contrast" if high_contrast else "midnight",
        font_size=14 if accessibility_mode else 12,
    )
    players = [
        HeartsPlayer(name=player_name, is_ai=False),
        HeartsPlayer(name="AI West", is_ai=True),
        HeartsPlayer(name="AI North", is_ai=True),
        HeartsPlayer(name="AI East", is_ai=True),
    ]
    game = HeartsGame(players)
    gui = HeartsGUI(game, human_index=0, config=config)
    gui.show()
    app.exec_()


__all__ = ["HeartsGUI", "run_app"]
