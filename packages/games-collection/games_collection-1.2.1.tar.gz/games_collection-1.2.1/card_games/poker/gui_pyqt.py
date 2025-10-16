"""PyQt5 interface for visualising and playing a :class:`PokerMatch`.

This module mirrors the Tkinter implementation found in :mod:`card_games.poker.gui`
using Qt widgets. The goal is feature parity so the migration away from Tkinter can
be completed incrementally. The interface reproduces the same layout and control
flow: a header with match details, a board panel for community cards, labelled
player frames, action buttons, and a scrolling log for narration.
"""

from __future__ import annotations

import random
import sys
from typing import Dict, Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..common.cards import format_cards
from .poker import Action, ActionType, PokerMatch
from card_games.common.soundscapes import initialize_game_soundscape
from common.gui_base_pyqt import BaseGUI, GUIConfig


class PokerPyQtGUI(QWidget, BaseGUI):
    """PyQt5 window that drives and renders a :class:`PokerMatch`.

    The GUI keeps a mirror of the internal match state through a collection of
    labels stored in ``player_vars``. Bot turns are executed immediately while the
    interface pauses when ``awaiting_user`` becomes ``True``. This mirrors the
    control flow of the Tkinter implementation to preserve gameplay semantics.
    """

    def __init__(
        self,
        match: PokerMatch,
        rng: Optional[random.Random] = None,
        *,
        enable_sounds: bool = True,
        config: Optional[GUIConfig] = None,
    ) -> None:
        """Initialise the PyQt poker window."""
        QWidget.__init__(self)
        gui_config = config or GUIConfig(
            window_title="Card Games - Poker",
            window_width=980,
            window_height=680,
            enable_sounds=enable_sounds,
            enable_animations=True,
            theme_name="dark",
        )
        BaseGUI.__init__(self, root=self, config=gui_config)
        self.sound_manager = initialize_game_soundscape(
            "poker",
            module_file=__file__,
            enable_sounds=gui_config.enable_sounds,
            existing_manager=self.sound_manager,
        )
        self.match = match
        self.rng = rng or random.Random()
        self.awaiting_user = False
        self.completed_hands = 0

        variant_name = "Omaha Hold'em" if match.game_variant.value == "omaha" else "Texas Hold'em"
        self.setWindowTitle(f"Card Games - {variant_name}")
        self.resize(gui_config.window_width, gui_config.window_height)

        self.player_frames: Dict[str, QWidget] = {}
        self.player_vars: Dict[str, Dict[str, QLabel]] = {}
        self.board_labels: list[QLabel] = []

        self._build_layout()
        self._update_stacks()
        self._update_board()
        self._update_player_cards(show_all=False)
        self.start_hand()

    def _build_layout(self) -> None:
        """Create the full layout, mirroring the Tkinter grid design."""
        main_layout = QGridLayout()
        main_layout.setRowStretch(1, 1)
        main_layout.setRowStretch(2, 1)
        self.setLayout(main_layout)

        header_widget = QWidget()
        header_layout = QGridLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_widget.setLayout(header_layout)

        self.status_label = QLabel("Welcome to the poker table!")
        self.status_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(self.status_label, 0, 0, Qt.AlignmentFlag.AlignLeft)

        info_frame = QWidget()
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        info_frame.setLayout(info_layout)
        self.stage_label = QLabel("Stage: pre-flop")
        self.blinds_label = QLabel("")
        self.blinds_label.setStyleSheet("font-size: 9pt; color: #666;")
        info_layout.addWidget(self.stage_label, alignment=Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.blinds_label, alignment=Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(info_frame, 0, 1, Qt.AlignmentFlag.AlignCenter)

        self.pot_label = QLabel("Pot: 0")
        self.pot_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.pot_label, 0, 2)

        main_layout.addWidget(header_widget, 0, 0)

        board_frame = QFrame()
        board_frame.setFrameShape(QFrame.Shape.NoFrame)
        board_layout = QGridLayout()
        board_layout.setContentsMargins(10, 10, 10, 10)
        board_layout.setSpacing(12)
        board_frame.setLayout(board_layout)
        self.board_labels = []
        for i in range(5):
            label = QLabel("🂠")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-family: 'Consolas'; font-size: 24pt; padding: 10px;")
            board_layout.addWidget(label, 0, i)
            self.board_labels.append(label)
        self.board_frame = board_frame
        main_layout.addWidget(board_frame, 1, 0)

        players_widget = QWidget()
        players_layout = QGridLayout()
        players_layout.setContentsMargins(10, 10, 10, 10)
        players_layout.setHorizontalSpacing(10)
        players_widget.setLayout(players_layout)

        for column, player in enumerate(self.match.players):
            group = QGroupBox(player.name)
            group_layout = QGridLayout()
            group_layout.setContentsMargins(10, 10, 10, 10)
            group.setLayout(group_layout)

            cards_label = QLabel("??")
            cards_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cards_label.setStyleSheet("font-family: 'Consolas'; font-size: 18pt;")
            chips_label = QLabel(f"Chips: {player.chips}")
            action_label = QLabel("Waiting")
            action_label.setStyleSheet("color: #555;")

            group_layout.addWidget(cards_label, 0, 0)
            group_layout.addWidget(chips_label, 1, 0)
            group_layout.addWidget(action_label, 2, 0)

            players_layout.addWidget(group, 0, column)
            self.player_frames[player.name] = group
            self.player_vars[player.name] = {
                "cards": cards_label,
                "chips": chips_label,
                "action": action_label,
            }

        main_layout.addWidget(players_widget, 2, 0)

        actions_widget = QWidget()
        actions_layout = QGridLayout()
        actions_layout.setContentsMargins(10, 0, 10, 10)
        actions_layout.setHorizontalSpacing(8)
        actions_widget.setLayout(actions_layout)

        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMinimumHeight(160)
        self.log_widget.setStyleSheet("background-color: #101820; color: #E0E6ED;")
        actions_layout.addWidget(self.log_widget, 0, 0, 1, 4)

        wager_label = QLabel("Wager amount:")
        self.amount_input = QLineEdit()
        actions_layout.addWidget(wager_label, 1, 0)
        actions_layout.addWidget(self.amount_input, 1, 1, 1, 3)

        self.btn_fold = QPushButton("Fold")
        self.btn_fold.clicked.connect(lambda: self.handle_user_action(ActionType.FOLD))
        self.btn_call = QPushButton("Call/Check")
        self.btn_call.clicked.connect(self._handle_call_or_check)
        self.btn_raise = QPushButton("Bet/Raise")
        self.btn_raise.clicked.connect(self._handle_bet_or_raise)
        self.btn_all_in = QPushButton("All-in")
        self.btn_all_in.clicked.connect(lambda: self.handle_user_action(ActionType.ALL_IN))

        actions_layout.addWidget(self.btn_fold, 2, 0)
        actions_layout.addWidget(self.btn_call, 2, 1)
        actions_layout.addWidget(self.btn_raise, 2, 2)
        actions_layout.addWidget(self.btn_all_in, 2, 3)

        main_layout.addWidget(actions_widget, 3, 0)
        self._set_action_buttons_enabled(False)
        self._raise_button_action: Optional[ActionType] = None

    def start_hand(self) -> None:
        """Start a new hand and reset UI state."""
        if self._match_complete():
            self.status_label.setText("Match complete! Thanks for playing.")
            self._set_action_buttons_enabled(False)
            self._display_final_statistics()
            return

        table = self.match.table
        self.completed_hands += 1

        if self.match.tournament_mode.enabled:
            sb, bb = self.match.tournament_mode.get_blinds(self.completed_hands - 1)
            table.small_blind = sb
            table.big_blind = bb
            self.blinds_label.setText(f"Blinds: {sb}/{bb}")
        else:
            self.blinds_label.setText("")

        self.status_label.setText(f"Hand {self.completed_hands} of {self.match.rounds}")
        table.start_hand()
        table.last_actions.clear()
        self.amount_input.setText(str(max(table.min_raise_amount, table.big_blind)))
        self._log(f"New hand begins. Your cards: {format_cards(self.match.user.hole_cards)}")
        self._update_board()
        self._update_stacks()
        self._update_player_cards(show_all=False)
        self._set_action_buttons_enabled(False)
        QTimer.singleShot(400, self._advance_until_user)

    def _match_complete(self) -> bool:
        """Return ``True`` if the match has concluded."""
        if self.completed_hands >= self.match.rounds and self.match.rounds > 0:
            return True
        if self.match.user.chips <= 0:
            return True
        if all(bot.chips <= 0 for bot in self.match.bots):
            return True
        return False

    def _advance_until_user(self) -> None:
        """Play bot turns until the user must act or the hand finishes."""
        table = self.match.table
        while True:
            if table._active_player_count() <= 1 or not table.players_can_act() or (table.stage == "river" and table.betting_round_complete()):
                self._finish_hand()
                return

            player = table.players[table.current_player_index]
            if player.is_user and not player.folded and not player.all_in:
                self.awaiting_user = True
                self._prepare_user_turn()
                return

            if player.folded or player.all_in:
                table.current_player_index = table._next_index(table.current_player_index)
                continue

            controller = next(c for c in self.match.bot_controllers if c.player is player)
            action = controller.decide(table)
            table.apply_action(player, action)
            self._flush_action_log()
            self._update_stacks()
            self._update_player_cards(show_all=False)

            if table.betting_round_complete():
                self._end_betting_round()
                if table.stage == "river":
                    self._finish_hand()
                    return
                table.proceed_to_next_stage()
                self._log(f"Stage advances to {table.stage}. Board: {format_cards(table.community_cards)}")
                self._update_board()
                self._update_player_cards(show_all=False)

    def _prepare_user_turn(self) -> None:
        """Enable controls and refresh labels for the player's turn."""
        table = self.match.table
        player = self.match.user
        to_call = table.current_bet - player.current_bet
        self.status_label.setText(f"Your turn | Pot: {table.pot} | To call: {to_call}")
        self._set_action_buttons_enabled(True)
        self._update_board()
        self._update_player_cards(show_all=False)

        options = table.valid_actions(player)
        self.btn_fold.setEnabled(ActionType.FOLD in options)
        self.btn_call.setText("Check" if to_call <= 0 else f"Call ({min(to_call, player.chips)})")
        self.btn_call.setEnabled(ActionType.CHECK in options or ActionType.CALL in options)
        if ActionType.RAISE in options:
            self._raise_button_action = ActionType.RAISE
        elif ActionType.BET in options:
            self._raise_button_action = ActionType.BET
        else:
            self._raise_button_action = None
        self.btn_raise.setEnabled(self._raise_button_action is not None)
        self.btn_all_in.setEnabled(ActionType.ALL_IN in options)

    def _handle_call_or_check(self) -> None:
        """Dispatch the correct action for the call/check button."""
        to_call = self.match.table.current_bet - self.match.user.current_bet
        action = ActionType.CHECK if to_call <= 0 else ActionType.CALL
        self.handle_user_action(action)

    def _handle_bet_or_raise(self) -> None:
        """Dispatch a bet when opening the action, otherwise a raise."""
        if self._raise_button_action is None:
            return
        self.handle_user_action(self._raise_button_action)

    def handle_user_action(self, action_type: ActionType) -> None:
        """Handle an action chosen by the user."""
        if not self.awaiting_user:
            return

        table = self.match.table
        player = self.match.user
        try:
            if action_type is ActionType.FOLD:
                action = Action(ActionType.FOLD)
            elif action_type is ActionType.CHECK:
                action = Action(ActionType.CHECK)
            elif action_type is ActionType.CALL:
                action = Action(ActionType.CALL, target_bet=table.current_bet)
            elif action_type is ActionType.ALL_IN:
                action = Action(ActionType.ALL_IN, target_bet=player.current_bet + player.chips)
            elif action_type in {ActionType.BET, ActionType.RAISE}:
                amount = self._parse_amount(self.amount_input.text(), default=table.min_raise_amount)
                base = player.current_bet if action_type is ActionType.BET else table.current_bet
                action = Action(action_type, target_bet=base + amount)
            else:
                return
        except ValueError:
            self.status_label.setText("Invalid amount. Please enter a positive integer.")
            return

        table.apply_action(player, action)
        self.awaiting_user = False
        self._set_action_buttons_enabled(False)
        self._flush_action_log()
        self._update_stacks()
        self._update_player_cards(show_all=False)

        if table.betting_round_complete():
            self._end_betting_round()
            if table.stage == "river":
                self._finish_hand()
                return
            table.proceed_to_next_stage()
            self._log(f"Stage advances to {table.stage}. Board: {format_cards(table.community_cards)}")
            self._update_board()

        QTimer.singleShot(200, self._advance_until_user)

    def _finish_hand(self) -> None:
        """Resolve the hand and schedule the next one if needed."""
        table = self.match.table
        self._flush_action_log()

        for player in self.match.players:
            player.statistics.hands_played += 1
            if player.folded:
                player.statistics.hands_folded += 1
            player.statistics.total_wagered += player.total_invested

        if table._active_player_count() == 1:
            payouts = table.distribute_pot()
            winner_name = next(name for name, amount in payouts.items() if amount > 0)
            self._log(f"{winner_name} wins the pot uncontested ({payouts[winner_name]} chips).")
        else:
            rankings = table.showdown()
            self._animate_showdown(rankings)
            for player, rank in rankings:
                player.statistics.showdowns_reached += 1
                self._log(f"{player.name}: {format_cards(player.hole_cards)} -> {rank.describe()}")
            payouts = table.distribute_pot()
            for name, amount in payouts.items():
                if amount > 0:
                    self._log(f"{name} collects {amount} chips.")
            self._update_player_cards(show_all=True)

        for player in self.match.players:
            if payouts.get(player.name, 0) > 0:
                player.statistics.hands_won += 1
                player.statistics.total_winnings += payouts[player.name]
                if table._active_player_count() > 1:
                    player.statistics.showdowns_won += 1

        self._update_stacks()
        self._update_board()
        self._set_action_buttons_enabled(False)

        if self._match_complete():
            self.status_label.setText("Match complete! Close the window to exit.")
            return

        self.status_label.setText("Preparing for the next hand...")
        self.match.table.rotate_dealer()
        QTimer.singleShot(2200, self.start_hand)

    def _end_betting_round(self) -> None:
        """Log all actions from the completed betting round."""
        self._flush_action_log()

    def _flush_action_log(self) -> None:
        """Flush the poker table's pending action log into the GUI log."""
        for line in self.match.table.last_actions:
            self._log(line)
        self.match.table.last_actions.clear()

    def _update_board(self) -> None:
        """Refresh community cards, stage, and pot labels."""
        table = self.match.table
        self.stage_label.setText(f"Stage: {table.stage}")
        self.pot_label.setText(f"Pot: {table.pot}")
        for i, label in enumerate(self.board_labels):
            if i < len(table.community_cards):
                label.setText(str(table.community_cards[i]))
            else:
                label.setText("🂠")

    def _update_player_cards(self, *, show_all: bool) -> None:
        """Update hole card and action labels for every player."""
        for player in self.match.players:
            vars = self.player_vars[player.name]
            if player.is_user or show_all or player.folded:
                vars["cards"].setText(format_cards(player.hole_cards) if player.hole_cards else "--")
            else:
                vars["cards"].setText("??")
            vars["action"].setText(player.last_action.capitalize())

    def _update_stacks(self) -> None:
        """Refresh chip counts for each player."""
        for player in self.match.players:
            self.player_vars[player.name]["chips"].setText(f"Chips: {player.chips}")

    def _log(self, message: str) -> None:
        """Append a message to the scrollable log."""
        self.log_widget.append(message)
        self.log_widget.ensureCursorVisible()

    def _set_action_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable all action buttons."""
        for button in (self.btn_fold, self.btn_call, self.btn_raise, self.btn_all_in):
            button.setEnabled(enabled)

    def _animate_showdown(self, rankings: list[tuple[object, object]]) -> None:
        """Animate showdown updates by scheduling label refreshes."""
        for i, (player, rank) in enumerate(rankings):
            QTimer.singleShot(i * 300, lambda: self._update_player_cards(show_all=True))
            description = rank.category.name.replace("_", " ").title()
            QTimer.singleShot(i * 300 + 150, lambda text=description: self.status_label.setText(f"Evaluating hands... {text}"))

        if rankings:
            best_rank = rankings[0][1]
            winners = [p for p, r in rankings if r == best_rank]
            names = ", ".join(player.name for player in winners)
            QTimer.singleShot(len(rankings) * 300 + 500, lambda: self.status_label.setText(f"Winner(s): {names}"))

    def _display_final_statistics(self) -> None:
        """Dump final player statistics into the log."""
        self._log("\n=== Final Statistics ===")
        for player in self.match.players:
            stats = player.statistics
            self._log(f"\n{player.name}:")
            self._log(f"  Hands: {stats.hands_won}/{stats.hands_played} won ({stats.win_rate:.1f}%)")
            self._log(f"  Folds: {stats.hands_folded} ({stats.fold_frequency:.1f}%)")
            self._log(f"  Showdowns: {stats.showdowns_won}/{stats.showdowns_reached}")
            self._log(f"  Net: {stats.net_profit:+d} chips")

    @staticmethod
    def _parse_amount(raw: str, *, default: int) -> int:
        """Parse the wager amount entered by the user."""
        raw = raw.strip()
        if not raw:
            return default
        value = int(raw)
        if value <= 0:
            raise ValueError("Amount must be positive")
        return value


def launch_gui(match: PokerMatch, *, rng: Optional[random.Random] = None) -> int:
    """Launch the PyQt5 poker GUI."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = PokerPyQtGUI(match, rng=rng)
    window.show()
    return app.exec()


__all__ = ["PokerPyQtGUI", "launch_gui"]
