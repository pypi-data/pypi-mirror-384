"""Tkinter GUI for playing rounds of Spades against AI opponents.

The interface combines the :class:`SpadesGame` engine with the shared :mod:`common.gui_base`
infrastructure. It presents dedicated panels for bidding, trick tracking, score summaries,
and a comprehensive log so players can review the flow of each round. Human actions are
limited to legal bids and card plays, while AI partners and opponents resolve their turns
automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from card_games.common.cards import Card
from card_games.spades.game import SpadesGame, SpadesPlayer
from common.gui_base import TKINTER_AVAILABLE, BaseGUI, GUIConfig, scrolledtext, tk, ttk


@dataclass
class _BidDisplay:
    """Simple container for widgets that show a player's bid."""

    value: tk.StringVar
    label: ttk.Label


class SpadesGUI(BaseGUI):
    """Graphical front-end that manages a :class:`SpadesGame` session."""

    def __init__(self, root: tk.Tk, game: Optional[SpadesGame] = None, *, player_name: str = "You") -> None:
        """Initialise the GUI and prepare the first round.

        Args:
            root: Root Tkinter window provided by the caller.
            game: Optional pre-configured :class:`SpadesGame` instance.
            player_name: Human player's display name when ``game`` is ``None``.

        Raises:
            RuntimeError: If Tkinter is not available in the runtime environment.
        """

        if not TKINTER_AVAILABLE:
            raise RuntimeError("Tkinter is required to launch the Spades GUI")

        config = GUIConfig(
            window_title="Card Games - Spades",
            window_width=1100,
            window_height=760,
            theme_name="dark",
            accessibility_mode=True,
        )
        super().__init__(root, config)

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

        self.phase_var = tk.StringVar(value="Bidding")
        self.status_var = tk.StringVar(value="Welcome to Spades! Enter your bid to begin.")
        self.bid_var = tk.StringVar(value="")
        self.team_score_vars = [tk.StringVar(value="0"), tk.StringVar(value="0")]
        self.team_bag_vars = [tk.StringVar(value="0 bags"), tk.StringVar(value="0 bags")]
        self.trick_vars: Dict[str, tk.StringVar] = {}
        self.bid_displays: Dict[str, _BidDisplay] = {}
        self.log_widget: Optional[scrolledtext.ScrolledText] = None
        self.breakdown_widget: Optional[scrolledtext.ScrolledText] = None
        self.hand_frame: Optional[tk.Frame] = None
        self.bid_entry: Optional[ttk.Spinbox] = None
        self.bid_button: Optional[ttk.Button] = None
        self.next_round_button: Optional[ttk.Button] = None

        self.awaiting_bid = False
        self.awaiting_play = False
        self.bids_taken = 0
        self.bidding_index: Optional[int] = None
        self.leader_index: Optional[int] = None

        self.build_layout()
        self.register_shortcut("Control-n", self._shortcut_next_round, "Start the next round after scoring")
        self.register_shortcut("Control-l", self._focus_log, "Focus the round log")
        self.register_shortcut("F1", self.show_shortcuts_help, "Display keyboard shortcut help")
        self.start_new_round()

    def build_layout(self) -> None:
        """Construct all widgets required for the Spades interface."""

        bg = self.current_theme.colors.background
        fg = self.current_theme.colors.foreground
        accent = self.current_theme.colors.primary

        container = tk.Frame(self.root, bg=bg, padx=18, pady=18)
        container.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        for col in range(2):
            container.grid_columnconfigure(col, weight=1)
        for row in range(6):
            container.grid_rowconfigure(row, weight=1 if row in (1, 2, 3) else 0)

        header = tk.Frame(container, bg=bg)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)

        status_label = tk.Label(
            header,
            textvariable=self.status_var,
            font=(self.current_theme.font_family, self.current_theme.font_size + 4, "bold"),
            bg=bg,
            fg=fg,
            anchor="w",
        )
        status_label.grid(row=0, column=0, sticky="w")

        phase_label = tk.Label(
            header,
            textvariable=self.phase_var,
            font=(self.current_theme.font_family, self.current_theme.font_size + 2, "bold"),
            bg=bg,
            fg=accent,
        )
        phase_label.grid(row=0, column=1, sticky="e")

        # Partnership score panel
        score_frame = self.create_label_frame(container, "Partnership scores")
        score_frame.configure(bg=bg)
        score_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(12, 12))
        for index in (0, 1):
            tk.Label(
                score_frame,
                text=self.team_names[index],
                font=(self.current_theme.font_family, self.current_theme.font_size + 2, "bold"),
                bg=bg,
                fg=fg,
            ).grid(row=index * 2, column=0, sticky="w", pady=(0, 2))
            tk.Label(
                score_frame,
                textvariable=self.team_score_vars[index],
                font=(self.current_theme.font_family, self.current_theme.font_size + 2),
                bg=bg,
                fg=accent,
            ).grid(row=index * 2, column=1, sticky="e", padx=(10, 0))
            tk.Label(
                score_frame,
                textvariable=self.team_bag_vars[index],
                font=(self.current_theme.font_family, self.current_theme.font_size - 1),
                bg=bg,
                fg=self.current_theme.colors.info,
            ).grid(row=index * 2 + 1, column=0, columnspan=2, sticky="w")

        # Bidding panel
        bidding_frame = self.create_label_frame(container, "Bidding")
        bidding_frame.configure(bg=bg)
        bidding_frame.grid(row=1, column=1, sticky="nsew", pady=(12, 12))
        bidding_frame.grid_columnconfigure(1, weight=1)

        self.bid_entry = ttk.Spinbox(
            bidding_frame,
            from_=0,
            to=13,
            textvariable=self.bid_var,
            width=5,
            justify="center",
        )
        self.bid_entry.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.accessibility_manager.add_focus_indicator(self.bid_entry)

        self.bid_button = ttk.Button(bidding_frame, text="Submit bid", command=self._handle_human_bid)
        self.bid_button.grid(row=0, column=1, sticky="w")
        self.accessibility_manager.add_focus_indicator(self.bid_button)
        self.accessibility_manager.add_screen_reader_label(self.bid_button, "Submit the selected bid")

        ttk.Separator(bidding_frame, orient=tk.HORIZONTAL).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 8))

        for row_index, player in enumerate(self.game.players, start=2):
            label = ttk.Label(bidding_frame, text=player.name)
            label.grid(row=row_index, column=0, sticky="w", pady=2)
            value = tk.StringVar(value="Pending")
            display_label = ttk.Label(bidding_frame, textvariable=value, width=12)
            display_label.grid(row=row_index, column=1, sticky="e")
            self.bid_displays[player.name] = _BidDisplay(value=value, label=display_label)

        # Trick panel
        trick_frame = self.create_label_frame(container, "Current trick")
        trick_frame.configure(bg=bg)
        trick_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 12))
        for index, player in enumerate(self.game.players):
            row = tk.Frame(trick_frame, bg=bg)
            row.grid(row=index, column=0, sticky="ew", pady=2)
            tk.Label(
                row,
                text=player.name,
                bg=bg,
                fg=fg,
                width=14,
                anchor="w",
            ).pack(side=tk.LEFT)
            value = tk.StringVar(value="Waiting")
            tk.Label(
                row,
                textvariable=value,
                bg=bg,
                fg=self.current_theme.colors.highlight,
                width=18,
                anchor="w",
            ).pack(side=tk.LEFT, padx=(6, 0))
            self.trick_vars[player.name] = value

        # Hand panel
        hand_container = self.create_label_frame(container, "Your hand")
        hand_container.configure(bg=bg)
        hand_container.grid(row=2, column=1, sticky="nsew")
        self.hand_frame = tk.Frame(hand_container, bg=bg)
        self.hand_frame.pack(fill=tk.BOTH, expand=True)

        # Log panel
        log_frame = self.create_label_frame(container, "Round log")
        log_frame.configure(bg=bg)
        log_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        self.log_widget = self.create_log_widget(log_frame)
        self.log_widget.configure(height=12)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

        # Breakdown panel and controls
        breakdown_frame = self.create_label_frame(container, "Round breakdown")
        breakdown_frame.configure(bg=bg)
        breakdown_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        self.breakdown_widget = self.create_log_widget(breakdown_frame)
        self.breakdown_widget.configure(height=8)
        self.breakdown_widget.pack(fill=tk.BOTH, expand=True)

        controls = tk.Frame(container, bg=bg)
        controls.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        controls.columnconfigure(0, weight=1)
        self.next_round_button = ttk.Button(controls, text="Start next round", command=self.start_new_round, state=tk.DISABLED)
        self.next_round_button.grid(row=0, column=0, sticky="e")
        self.accessibility_manager.add_focus_indicator(self.next_round_button)

    def update_display(self) -> None:
        """Refresh all dynamic widgets to match the latest game state."""

        for index in (0, 1):
            self.team_score_vars[index].set(str(self.game.team_scores[index]))
            self.team_bag_vars[index].set(f"{self.game.bags[index]} bags")

        self._update_bids_panel()
        self._update_trick_display()
        self._render_hand()

        if self.bid_entry is not None:
            self.bid_entry.configure(state=tk.NORMAL if self.awaiting_bid else tk.DISABLED)
        if self.bid_button is not None:
            self.bid_button.configure(state=tk.NORMAL if self.awaiting_bid else tk.DISABLED)

        if self.next_round_button is not None:
            self.next_round_button.configure(state=tk.NORMAL if self.phase_var.get() == "Round complete" and not self.game.is_game_over() else tk.DISABLED)

    def start_new_round(self) -> None:
        """Start a new round, resetting bidding state and prompting the leader."""

        if self.game.is_game_over():
            self.status_var.set("The match is over. Restart the programme for a new game.")
            return

        self.game.start_new_round()
        self.phase_var.set("Bidding")
        self.status_var.set("Bidding phase: enter your bid when prompted.")
        self.bids_taken = 0
        self.awaiting_play = False
        self.leader_index = self.game.current_player_index or 0
        self.bidding_index = self.leader_index

        for display in self.bid_displays.values():
            display.value.set("Pending")
        for value in self.trick_vars.values():
            value.set("Waiting")
        self.bid_var.set("")
        self._set_breakdown_text("")

        if self.log_widget is not None:
            self.log_message(self.log_widget, f"\nRound {self.game.round_number} begins. Leader: {self.game.players[self.leader_index].name}.")
        self.update_display()
        self._prompt_next_bidder()

    def _shortcut_next_round(self) -> None:
        """Keyboard shortcut handler for advancing to the next round."""

        if self.phase_var.get() == "Round complete" and self.next_round_button and str(self.next_round_button["state"]) != tk.DISABLED:
            self.start_new_round()

    def _focus_log(self) -> None:
        """Give keyboard focus to the log widget for screen-reader users."""

        if self.log_widget is not None:
            self.log_widget.focus_set()

    def _prompt_next_bidder(self) -> None:
        """Advance bidding order, prompting either the human or AI players."""

        if self.bids_taken >= len(self.game.players):
            self._finish_bidding()
            return

        assert self.bidding_index is not None
        player = self.game.players[self.bidding_index]
        if player.is_ai:
            self.awaiting_bid = False
            self.status_var.set(f"Waiting for {player.name} to bid...")
            self.update_display()
            self.root.after(400, lambda p=player: self._record_ai_bid(p))
        else:
            self.awaiting_bid = True
            self.status_var.set("Enter your bid (0-13) and press Submit bid.")
            self.update_display()
            if self.bid_entry is not None:
                self.bid_entry.focus_set()

    def _handle_human_bid(self) -> None:
        """Validate and register the human player's bid selection."""

        if not self.awaiting_bid:
            return
        try:
            bid_value = int(self.bid_var.get())
        except ValueError:
            self.status_var.set("Please enter a whole number between 0 and 13.")
            return

        if bid_value < 0 or bid_value > 13:
            self.status_var.set("Bids must be between 0 and 13.")
            return

        self.awaiting_bid = False
        self._register_bid(self.human_player, bid_value)
        self._advance_bid_order()

    def _register_bid(self, player: SpadesPlayer, bid_value: int) -> None:
        """Record a bid with the game engine and update the UI."""

        self.game.register_bid(player, bid_value)
        label = "Blind nil" if player.blind_nil else ("Nil" if bid_value == 0 else str(bid_value))
        self.bid_displays[player.name].value.set(label)
        if self.log_widget is not None:
            self.log_message(self.log_widget, f"{player.name} bids {label}.")

    def _record_ai_bid(self, player: SpadesPlayer) -> None:
        """Request an AI bid and proceed to the next player."""

        if self.phase_var.get() != "Bidding":
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

        self.phase_var.set("Playing")
        self.status_var.set("Trick play: follow suit when you can.")
        self.awaiting_bid = False
        self.update_display()
        self._advance_ai_turns()

    def _advance_ai_turns(self) -> None:
        """Play out AI turns until the human player must act."""

        if self.phase_var.get() != "Playing":
            return

        while True:
            current_index = self.game.current_player_index or 0
            player = self.game.players[current_index]
            if not player.is_ai:
                self.awaiting_play = True
                self.status_var.set("Your turn: select a highlighted card to play.")
                self.update_display()
                return

            card = self.game.select_card_to_play(player)
            self.game.play_card(player, card)
            if self.log_widget is not None:
                self.log_message(self.log_widget, f"{player.name} plays {card}.")
            self.update_display()

            if len(self.game.current_trick) == 4:
                winner = self.game.complete_trick()
                if self.log_widget is not None:
                    self.log_message(self.log_widget, f"{winner.name} wins the trick.")
                for value in self.trick_vars.values():
                    value.set("Waiting")
                self.update_display()

                if self.game.total_tricks_played >= 13:
                    self._finish_round()
                    return
                continue

    def _on_card_selected(self, card: Card) -> None:
        """Handle a card button click from the human player."""

        if self.phase_var.get() != "Playing" or not self.awaiting_play:
            return

        try:
            self.game.play_card(self.human_player, card)
        except ValueError:
            self.status_var.set("That card is not a legal play right now.")
            return

        self.awaiting_play = False
        if self.log_widget is not None:
            self.log_message(self.log_widget, f"{self.human_player.name} plays {card}.")
        self.update_display()

        if len(self.game.current_trick) == 4:
            winner = self.game.complete_trick()
            if self.log_widget is not None:
                self.log_message(self.log_widget, f"{winner.name} wins the trick.")
            for value in self.trick_vars.values():
                value.set("Waiting")
            self.update_display()
            if self.game.total_tricks_played >= 13:
                self._finish_round()
                return

        self._advance_ai_turns()

    def _update_bids_panel(self) -> None:
        """Synchronise bid labels with player data when in or after bidding."""

        for player in self.game.players:
            display = self.bid_displays[player.name]
            if player.bid is None:
                display.value.set("Pending")
            elif player.blind_nil:
                display.value.set("Blind nil")
            elif player.bid == 0:
                display.value.set("Nil")
            else:
                display.value.set(str(player.bid))

    def _update_trick_display(self) -> None:
        """Show the current trick composition in the trick panel."""

        active = {player.name: str(card) for player, card in self.game.current_trick}
        for player in self.game.players:
            self.trick_vars[player.name].set(active.get(player.name, "Waiting"))

    def _render_hand(self) -> None:
        """Render the human player's hand as clickable card buttons."""

        if self.hand_frame is None:
            return

        for widget in self.hand_frame.winfo_children():
            widget.destroy()

        cards = list(self.human_player.hand)
        if not cards:
            tk.Label(self.hand_frame, text="(No cards)", bg=self.current_theme.colors.background, fg=self.current_theme.colors.foreground).pack()
            return

        valid_cards = set(self.game.get_valid_plays(self.human_player)) if self.phase_var.get() == "Playing" else set(cards)

        for column, card in enumerate(cards):
            state = tk.NORMAL if self.awaiting_play and card in valid_cards else tk.DISABLED
            button = tk.Button(
                self.hand_frame,
                text=str(card),
                width=5,
                state=state,
                command=lambda c=card: self._on_card_selected(c),
                bg=self.current_theme.colors.button_bg,
                fg=self.current_theme.colors.button_fg,
                relief=self.current_theme.button_relief,
                font=(self.current_theme.font_family, self.current_theme.font_size + 1, "bold"),
            )
            button.grid(row=0, column=column, padx=4, pady=6)
            self.accessibility_manager.add_focus_indicator(button)
            self.accessibility_manager.add_screen_reader_label(button, f"Play {card}")

        for column in range(len(cards)):
            self.hand_frame.grid_columnconfigure(column, weight=1)

    def _set_breakdown_text(self, text: str) -> None:
        """Update the breakdown panel with new round information."""

        if self.breakdown_widget is None:
            return
        self.breakdown_widget.configure(state=tk.NORMAL)
        self.breakdown_widget.delete("1.0", tk.END)
        self.breakdown_widget.insert(tk.END, text)
        self.breakdown_widget.configure(state=tk.DISABLED)

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
        lines.append(
            f"Partnership 1 ({self.team_names[0]}): {round_scores[0]} this round, {self.game.team_scores[0]} total, {self.game.bags[0]} bags",
        )
        lines.append(
            f"Partnership 2 ({self.team_names[1]}): {round_scores[1]} this round, {self.game.team_scores[1]} total, {self.game.bags[1]} bags",
        )

        self.phase_var.set("Round complete")
        self.status_var.set("Round complete. Review the breakdown or press Ctrl+N for the next round.")
        self.awaiting_play = False
        self._set_breakdown_text("\n".join(lines))
        self.update_display()

        if self.game.is_game_over():
            winner_index = self.game.get_winner()
            if winner_index is None:
                self.status_var.set("Game complete: the partnerships tied.")
            else:
                self.status_var.set(f"Game complete: {self.team_names[winner_index]} win!")
            if self.next_round_button is not None:
                self.next_round_button.configure(state=tk.DISABLED)
        else:
            if self.next_round_button is not None:
                self.next_round_button.configure(state=tk.NORMAL)


def run_app(player_name: Optional[str] = None) -> None:
    """Launch the Spades GUI application.

    Args:
        player_name: Optional display name for the human player.

    Raises:
        RuntimeError: If Tkinter is unavailable in the current environment.
    """

    if not TKINTER_AVAILABLE:
        raise RuntimeError("Tkinter is not available; cannot launch the GUI.")

    root = tk.Tk()
    SpadesGUI(root, player_name=player_name or "You")
    root.mainloop()
