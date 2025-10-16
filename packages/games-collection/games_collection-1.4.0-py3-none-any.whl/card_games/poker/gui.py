"""Tkinter front-end for visualising and playing a :class:`PokerMatch`.

Whereas :mod:`card_games.poker.poker` focuses on the rules engine, this module
documents how those mechanics are exposed to users in a desktop application.
Comments and docstrings emphasise the mapping between UI widgets and poker
concepts (boards, pots, betting actions) so that developers can adapt the
implementation to other toolkits with minimal guesswork.
"""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk
from typing import Optional

from card_games.common.soundscapes import initialize_game_soundscape
from common.gui_base import BaseGUI, GUIConfig

from ..common.cards import format_cards
from .poker import Action, ActionType, PokerMatch


class PokerGUI(BaseGUI):
    """Manages the interactive Tkinter interface for a `PokerMatch`.

    This class builds the UI, renders the game state, and handles the game loop,
    advancing through bot turns and pausing to await user input.
    """

    def __init__(
        self,
        root: tk.Tk,
        match: PokerMatch,
        rng: random.Random | None = None,
        *,
        enable_sounds: bool = True,
        config: Optional[GUIConfig] = None,
    ) -> None:
        """Initialize the Poker GUI.

        Args:
            root: The root Tkinter window.
            match: The `PokerMatch` instance to visualize.
            rng: An optional random number generator.
        """
        gui_config = config or GUIConfig(
            window_title="Poker Table",
            window_width=1280,
            window_height=780,
            enable_sounds=enable_sounds,
            enable_animations=True,
            theme_name="dark",
        )
        super().__init__(root, gui_config)
        self.sound_manager = initialize_game_soundscape(
            "poker",
            module_file=__file__,
            enable_sounds=gui_config.enable_sounds,
            existing_manager=self.sound_manager,
        )
        self.theme_manager.set_current_theme(gui_config.theme_name)
        self.current_theme = self.theme_manager.get_current_theme()
        self.match = match
        # A dedicated RNG powers cosmetic shuffles (e.g., log animations) so the
        # deterministic behaviour of the core engine is unaffected.
        self.rng = rng or random.Random()
        self.awaiting_user = False
        self.completed_hands = 0

        variant_name = "Omaha Hold'em" if match.game_variant.value == "omaha" else "Texas Hold'em"
        self.root.title(f"Card Games - {variant_name}")
        self.root.geometry("980x680")

        # UI state variables
        self.status_var = tk.StringVar(value="Welcome to the poker table!")
        self.pot_var = tk.StringVar(value="Pot: 0")
        self.stage_var = tk.StringVar(value="Stage: pre-flop")
        self.blinds_var = tk.StringVar(value="")

        # Build the layout and start the first hand
        self._build_layout()
        self._update_stacks()
        self._update_board()
        self.start_hand()

    def _build_layout(self) -> None:
        """Construct the main layout of the application window."""
        root = self.root
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        # Header with status, stage, and pot information
        header = ttk.Frame(root, padding=10)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)
        header.columnconfigure(2, weight=1)
        ttk.Label(header, textvariable=self.status_var, font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w")

        info_frame = ttk.Frame(header)
        info_frame.grid(row=0, column=1, sticky="n")
        ttk.Label(info_frame, textvariable=self.stage_var).pack()
        ttk.Label(info_frame, textvariable=self.blinds_var, font=("Segoe UI", 9)).pack()

        ttk.Label(header, textvariable=self.pot_var, anchor="e").grid(row=0, column=2, sticky="e")

        # Community card board
        self.board_frame = ttk.Frame(root, padding=10)
        self.board_frame.grid(row=1, column=0, sticky="nsew")
        self.board_frame.columnconfigure(tuple(range(5)), weight=1)

        # Player information frames
        self.player_frames: dict[str, ttk.Frame] = {}
        self.player_vars: dict[str, dict[str, tk.StringVar]] = {}
        players_container = ttk.Frame(root, padding=10)
        players_container.grid(row=2, column=0, sticky="ew")
        players_container.columnconfigure(tuple(range(len(self.match.players))), weight=1)

        for i, player in enumerate(self.match.players):
            frame = ttk.LabelFrame(players_container, text=player.name, padding=10)
            frame.grid(row=0, column=i, sticky="nsew", padx=5)
            frame.columnconfigure(0, weight=1)
            cards_var = tk.StringVar(value="??")
            chips_var = tk.StringVar(value=f"Chips: {player.chips}")
            action_var = tk.StringVar(value="Waiting")
            ttk.Label(frame, textvariable=cards_var, font=("Consolas", 16)).grid(row=0, column=0, sticky="n")
            ttk.Label(frame, textvariable=chips_var).grid(row=1, column=0, sticky="n")
            ttk.Label(frame, textvariable=action_var, foreground="#555").grid(row=2, column=0, sticky="n")
            self.player_frames[player.name] = frame
            self.player_vars[player.name] = {
                "cards": cards_var,
                "chips": chips_var,
                "action": action_var,
            }

        # Action controls and game log
        actions_frame = ttk.Frame(root, padding=(10, 0, 10, 10))
        actions_frame.grid(row=3, column=0, sticky="ew")
        actions_frame.columnconfigure(1, weight=1)

        self.log = tk.Text(
            actions_frame,
            height=10,
            state="disabled",
            wrap="word",
            background="#101820",
            foreground="#E0E6ED",
        )
        self.log.grid(row=0, column=0, columnspan=4, sticky="nsew", pady=(0, 10))

        ttk.Label(actions_frame, text="Wager amount:").grid(row=1, column=0, sticky="w")
        self.amount_var = tk.StringVar()
        ttk.Entry(actions_frame, textvariable=self.amount_var).grid(row=1, column=1, sticky="ew", padx=5)

        self.btn_fold = ttk.Button(
            actions_frame,
            text="Fold",
            command=lambda: self.handle_user_action(ActionType.FOLD),
        )
        self.btn_call = ttk.Button(actions_frame, text="Call/Check", command=self._handle_call_or_check)
        self.btn_raise = ttk.Button(
            actions_frame,
            text="Bet/Raise",
            command=lambda: self.handle_user_action(ActionType.RAISE),
        )
        self.btn_all_in = ttk.Button(
            actions_frame,
            text="All-in",
            command=lambda: self.handle_user_action(ActionType.ALL_IN),
        )

        self.btn_fold.grid(row=2, column=0, sticky="ew")
        self.btn_call.grid(row=2, column=1, sticky="ew", padx=5)
        self.btn_raise.grid(row=2, column=2, sticky="ew")
        self.btn_all_in.grid(row=2, column=3, sticky="ew", padx=5)

        self._set_action_buttons_state("disabled")

    def start_hand(self) -> None:
        """Starts a new hand, resetting the table and dealing cards."""
        if self._match_complete():
            self.status_var.set("Match complete! Thanks for playing.")
            self._set_action_buttons_state("disabled")
            self._display_final_statistics()
            return

        table = self.match.table
        self.completed_hands += 1

        # Update blinds if tournament mode is enabled.
        if self.match.tournament_mode.enabled:
            sb, bb = self.match.tournament_mode.get_blinds(self.completed_hands - 1)
            table.small_blind = sb
            table.big_blind = bb
            self.blinds_var.set(f"Blinds: {sb}/{bb}")

        self.status_var.set(f"Hand {self.completed_hands} of {self.match.rounds}")
        table.start_hand()
        table.last_actions.clear()
        self.amount_var.set(str(max(table.min_raise_amount, table.big_blind)))
        self._log(f"New hand begins. Your cards: {format_cards(self.match.user.hole_cards)}")
        self._update_board()
        self._update_stacks()
        self._update_player_cards(show_all=False)
        self._set_action_buttons_state("disabled")
        self.root.after(400, self._advance_until_user)

    def _match_complete(self) -> bool:
        """Checks if the match has concluded."""
        if self.completed_hands >= self.match.rounds and self.match.rounds > 0:
            return True
        if self.match.user.chips <= 0:
            return True
        if all(bot.chips <= 0 for bot in self.match.bots):
            return True
        return False

    def _advance_until_user(self) -> None:
        """Automatically plays bot turns until it is the user's turn or the hand ends."""
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
        """Prepares the UI for the user's turn by enabling controls and updating labels."""
        table = self.match.table
        player = self.match.user
        to_call = table.current_bet - player.current_bet
        self.status_var.set(f"Your turn | Pot: {table.pot} | To call: {to_call}")
        self._set_action_buttons_state("normal")
        self._update_board()
        self._update_player_cards(show_all=False)

        options = table.valid_actions(player)
        self.btn_fold.configure(state="normal" if ActionType.FOLD in options else "disabled")
        self.btn_call.configure(text="Check" if to_call <= 0 else f"Call ({min(to_call, player.chips)})")
        self.btn_raise.configure(state=("normal" if ActionType.RAISE in options or ActionType.BET in options else "disabled"))
        self.btn_all_in.configure(state="normal" if ActionType.ALL_IN in options else "disabled")

    def _handle_call_or_check(self) -> None:
        """Handles a click on the 'Call/Check' button, dispatching the correct action."""
        to_call = self.match.table.current_bet - self.match.user.current_bet
        self.handle_user_action(ActionType.CHECK if to_call <= 0 else ActionType.CALL)

    def handle_user_action(self, action_type: ActionType) -> None:
        """Handles an action submitted by the user."""
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
                amount = self._parse_amount(self.amount_var.get(), default=table.min_raise_amount)
                target = (player.current_bet if action_type is ActionType.BET else table.current_bet) + amount
                action = Action(action_type, target_bet=target)
            else:
                return
        except ValueError:
            self.status_var.set("Invalid amount. Please enter a positive integer.")
            return

        table.apply_action(player, action)
        self.awaiting_user = False
        self._set_action_buttons_state("disabled")
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

        self.root.after(200, self._advance_until_user)

    def _finish_hand(self) -> None:
        """Finishes the hand, determines the winner, and distributes the pot."""
        table = self.match.table
        self._flush_action_log()

        # Update player statistics for hands played and folded.
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
            # Animate showdown with hand ranking explanations.
            self._animate_showdown(rankings)
            for player, rank in rankings:
                player.statistics.showdowns_reached += 1
                self._log(f"{player.name}: {format_cards(player.hole_cards)} -> {rank.describe()}")
            payouts = table.distribute_pot()
            for name, amount in payouts.items():
                if amount > 0:
                    self._log(f"{name} collects {amount} chips.")
            self._update_player_cards(show_all=True)

        # Update statistics for winners.
        for player in self.match.players:
            if payouts.get(player.name, 0) > 0:
                player.statistics.hands_won += 1
                player.statistics.total_winnings += payouts[player.name]
                if table._active_player_count() > 1:
                    player.statistics.showdowns_won += 1

        self._update_stacks()
        self._update_board()
        self._set_action_buttons_state("disabled")

        if self._match_complete():
            self.status_var.set("Match complete! Close the window to exit.")
            return

        self.status_var.set("Preparing for the next hand...")
        self.match.table.rotate_dealer()
        self.root.after(2200, self.start_hand)

    def _end_betting_round(self) -> None:
        """Logs all actions from the completed betting round."""
        self._flush_action_log()

    def _flush_action_log(self) -> None:
        """Logs any pending actions from the game table."""
        for line in self.match.table.last_actions:
            self._log(line)
        self.match.table.last_actions.clear()

    def _update_board(self) -> None:
        """Updates the community cards and pot display."""
        table = self.match.table
        self.stage_var.set(f"Stage: {table.stage}")
        self.pot_var.set(f"Pot: {table.pot}")
        for widget in self.board_frame.winfo_children():
            widget.destroy()
        for i in range(5):
            card_text = str(table.community_cards[i]) if i < len(table.community_cards) else "🂠"
            ttk.Label(self.board_frame, text=card_text, font=("Consolas", 24), padding=10).grid(row=0, column=i, padx=6)

    def _update_player_cards(self, *, show_all: bool) -> None:
        """Updates the display of each player's hole cards and last action."""
        for player in self.match.players:
            vars = self.player_vars[player.name]
            if player.is_user or show_all or player.folded:
                vars["cards"].set(format_cards(player.hole_cards) if player.hole_cards else "--")
            else:
                vars["cards"].set("??")
            vars["action"].set(player.last_action.capitalize())

    def _update_stacks(self) -> None:
        """Updates the chip count display for each player."""
        for player in self.match.players:
            self.player_vars[player.name]["chips"].set(f"Chips: {player.chips}")

    def _log(self, message: str) -> None:
        """Appends a message to the game log text widget."""
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_action_buttons_state(self, state: str) -> None:
        """Sets the state of all user action buttons."""
        for button in (self.btn_fold, self.btn_call, self.btn_raise, self.btn_all_in):
            button.configure(state=state)

    def _animate_showdown(self, rankings: list[tuple[object, object]]) -> None:
        """Animates the showdown sequence with hand ranking explanations."""
        # Reveal all player cards with a brief animation.
        for i, (player, rank) in enumerate(rankings):
            self.root.after(i * 300, lambda p=player: self._update_player_cards(show_all=True))
            self.root.after(i * 300 + 150, lambda r=rank: self.status_var.set(f"Evaluating hands... {r.category.name.replace('_', ' ').title()}"))

        # Highlight the winner(s) after a delay.
        if rankings:
            best_rank = rankings[0][1]
            winners = [p for p, r in rankings if r == best_rank]
            self.root.after(len(rankings) * 300 + 500, lambda: self.status_var.set(f"Winner(s): {', '.join(w.name for w in winners)}"))

    def _display_final_statistics(self) -> None:
        """Displays final player statistics in the log."""
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
        """Parses a string into a valid wager amount."""
        raw = raw.strip()
        if not raw:
            return default
        value = int(raw)
        if value <= 0:
            raise ValueError("Amount must be positive")
        return value


def launch_gui(match: PokerMatch, *, rng: Optional[random.Random] = None) -> None:
    """Entry point to launch the Poker GUI.

    Args:
        match: The `PokerMatch` instance to be played.
        rng: An optional random number generator.
    """
    root = tk.Tk()
    PokerGUI(root, match, rng=rng)
    root.mainloop()


__all__ = ["PokerGUI", "launch_gui"]
