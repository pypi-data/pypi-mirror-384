"""Tkinter GUI for double-deck Pinochle."""

from __future__ import annotations

from typing import Optional

from card_games.pinochle.game import PinochleGame, PinochlePlayer
from common.gui_base import (
    TKINTER_AVAILABLE,
    BaseGUI,
    GUIConfig,
    scrolledtext,
    tk,
    ttk,
)


class PinochleGUI(BaseGUI):
    """Interactive Tkinter interface that wraps :class:`PinochleGame`."""

    def __init__(self, root: tk.Tk, game: Optional[PinochleGame] = None) -> None:
        if not TKINTER_AVAILABLE:
            raise RuntimeError("Tkinter is required to launch the Pinochle GUI")

        config = GUIConfig(
            window_title="Card Games - Pinochle",
            window_width=1100,
            window_height=760,
            theme_name="emerald",
            enable_sounds=True,
            enable_animations=True,
        )
        super().__init__(root, config)

        if game is None:
            players = [
                PinochlePlayer(name="South"),
                PinochlePlayer(name="West"),
                PinochlePlayer(name="North"),
                PinochlePlayer(name="East"),
            ]
            self.game = PinochleGame(players)
        else:
            self.game = game

        self.phase = "setup"
        self.status_var = tk.StringVar(value="Click \"New round\" to deal cards.")
        self.phase_var = tk.StringVar(value="Idle")
        self.team_score_vars = [tk.StringVar(value="0"), tk.StringVar(value="0")]
        self.current_player_var = tk.StringVar(value="-")
        self.bid_history_var = tk.StringVar(value="No bids yet")
        self.trump_var = tk.StringVar(value="Undeclared")
        self.trick_history_widget: Optional[scrolledtext.ScrolledText] = None
        self.meld_widget: Optional[scrolledtext.ScrolledText] = None
        self.hand_listbox: Optional[tk.Listbox] = None
        self.bid_entry: Optional[ttk.Spinbox] = None
        self.play_button: Optional[ttk.Button] = None
        self.pass_button: Optional[ttk.Button] = None
        self.bid_button: Optional[ttk.Button] = None
        self.new_round_button: Optional[ttk.Button] = None
        self.trump_selector: Optional[ttk.Combobox] = None

        self.build_layout()
        self.register_shortcut("Control-n", self.start_new_round, "Deal a new round")
        self.register_shortcut("Control-b", self._focus_bid, "Focus the bid input")
        self.register_shortcut("Control-p", self._focus_hand, "Focus current hand list")
        self.start_new_round()

    def build_layout(self) -> None:
        bg = self.current_theme.colors.background
        fg = self.current_theme.colors.foreground
        accent = self.current_theme.colors.primary

        container = tk.Frame(self.root, bg=bg, padx=18, pady=18)
        container.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

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

        scoreboard = self.create_label_frame(container, "Partnership scores")
        scoreboard.configure(bg=bg)
        scoreboard.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(12, 12))
        for team_index, label in enumerate(("South & North", "West & East")):
            tk.Label(
                scoreboard,
                text=label,
                font=(self.current_theme.font_family, self.current_theme.font_size + 2, "bold"),
                bg=bg,
                fg=fg,
            ).grid(row=team_index * 2, column=0, sticky="w", pady=(0, 2))
            tk.Label(
                scoreboard,
                textvariable=self.team_score_vars[team_index],
                font=(self.current_theme.font_family, self.current_theme.font_size + 2),
                bg=bg,
                fg=accent,
            ).grid(row=team_index * 2, column=1, sticky="e")

        controls = self.create_label_frame(container, "Round control")
        controls.configure(bg=bg)
        controls.grid(row=1, column=1, sticky="nsew", pady=(12, 12))
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text="Current player:").grid(row=0, column=0, sticky="w")
        ttk.Label(controls, textvariable=self.current_player_var).grid(row=0, column=1, sticky="w")

        ttk.Label(controls, text="Trump suit:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(controls, textvariable=self.trump_var).grid(row=1, column=1, sticky="w", pady=(4, 0))

        ttk.Label(controls, text="Bid / action:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.bid_entry = ttk.Spinbox(controls, from_=self.game.min_bid, to=1000, increment=10, width=8)
        self.bid_entry.grid(row=2, column=1, sticky="w", pady=(8, 0))
        self.bid_button = ttk.Button(controls, text="Submit bid", command=self._submit_bid)
        self.bid_button.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        self.pass_button = ttk.Button(controls, text="Pass", command=self._pass_bid)
        self.pass_button.grid(row=3, column=1, sticky="ew", pady=(6, 0))

        ttk.Separator(controls, orient=tk.HORIZONTAL).grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(controls, text="Select trump:").grid(row=5, column=0, sticky="w")
        self.trump_selector = ttk.Combobox(controls, values=["Clubs", "Diamonds", "Hearts", "Spades"], state="readonly")
        self.trump_selector.grid(row=5, column=1, sticky="ew")
        ttk.Button(controls, text="Confirm trump", command=self._confirm_trump).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        ttk.Separator(controls, orient=tk.HORIZONTAL).grid(row=7, column=0, columnspan=2, sticky="ew", pady=10)

        self.play_button = ttk.Button(controls, text="Play selected card", command=self._play_card)
        self.play_button.grid(row=8, column=0, columnspan=2, sticky="ew")

        self.new_round_button = ttk.Button(controls, text="New round", command=self.start_new_round)
        self.new_round_button.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        bids_frame = self.create_label_frame(container, "Bidding history")
        bids_frame.configure(bg=bg)
        bids_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 12))
        bids_frame.columnconfigure(0, weight=1)
        ttk.Label(bids_frame, textvariable=self.bid_history_var, justify="left").grid(row=0, column=0, sticky="nw")

        meld_frame = self.create_label_frame(container, "Meld summary")
        meld_frame.configure(bg=bg)
        meld_frame.grid(row=2, column=1, sticky="nsew")
        self.meld_widget = scrolledtext.ScrolledText(meld_frame, height=8, width=40, state="disabled", wrap="word")
        self.meld_widget.grid(row=0, column=0, sticky="nsew")

        trick_frame = self.create_label_frame(container, "Trick history")
        trick_frame.configure(bg=bg)
        trick_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        trick_frame.columnconfigure(0, weight=1)
        trick_frame.rowconfigure(0, weight=1)

        self.trick_history_widget = scrolledtext.ScrolledText(trick_frame, height=10, wrap="word", state="disabled")
        self.trick_history_widget.grid(row=0, column=0, sticky="nsew")

        hand_frame = self.create_label_frame(container, "Current hand")
        hand_frame.configure(bg=bg)
        hand_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        hand_frame.columnconfigure(0, weight=1)

        self.hand_listbox = tk.Listbox(hand_frame, height=8, activestyle="dotbox")
        self.hand_listbox.grid(row=0, column=0, sticky="nsew")

    def _focus_bid(self) -> None:
        if self.bid_entry:
            self.bid_entry.focus_set()

    def _focus_hand(self) -> None:
        if self.hand_listbox:
            self.hand_listbox.focus_set()

    def start_new_round(self) -> None:
        self.play_sound("shuffle")
        self.game.shuffle_and_deal()
        self.game.start_bidding()
        self.phase = "bidding"
        self.status_var.set("Bidding phase: enter bids or pass for each player.")
        self.phase_var.set("Bidding")
        self.trump_var.set("Undeclared")
        self._log_message("New round started. Deck shuffled and cards dealt.")
        self.update_display()

    def _log_message(self, message: str) -> None:
        if not self.trick_history_widget:
            return
        self.trick_history_widget.configure(state="normal")
        self.trick_history_widget.insert(tk.END, message + "\n")
        self.trick_history_widget.configure(state="disabled")
        self.trick_history_widget.see(tk.END)

    def _submit_bid(self) -> None:
        if not self.game.bidding_phase:
            return
        try:
            value = int(self.bid_entry.get()) if self.bid_entry else self.game.min_bid
        except (TypeError, ValueError):
            value = self.game.min_bid
        try:
            self.game.place_bid(value)
            self._log_message(f"{self.game.bidding_history[-1][0]} bids {value}.")
        except ValueError as exc:
            self.status_var.set(str(exc))
            return
        if self.game.bidding_phase.finished:
            self.status_var.set("Bidding complete. Select trump suit.")
            self.phase_var.set("Trump selection")
            winner = self.game.bidding_phase.high_bidder
            if winner:
                self.current_player_var.set(winner.name)
        self.update_display()

    def _pass_bid(self) -> None:
        if not self.game.bidding_phase:
            return
        self.game.place_bid(None)
        self._log_message(f"{self.game.bidding_history[-1][0]} passes.")
        if self.game.bidding_phase.finished:
            self.status_var.set("Bidding complete. Select trump suit.")
            self.phase_var.set("Trump selection")
            winner = self.game.bidding_phase.high_bidder
            if winner:
                self.current_player_var.set(winner.name)
        self.update_display()

    def _confirm_trump(self) -> None:
        if not self.game.bidding_phase or not self.game.bidding_phase.finished:
            self.status_var.set("Finish bidding before choosing trump.")
            return
        selection = (self.trump_selector.get() if self.trump_selector else "").lower()
        suit_map = {
            "clubs": "CLUBS",
            "diamonds": "DIAMONDS",
            "hearts": "HEARTS",
            "spades": "SPADES",
        }
        if selection not in suit_map:
            self.status_var.set("Select a trump suit from the list.")
            return
        from card_games.common.cards import Suit

        suit = Suit[suit_map[selection]]
        self.game.set_trump(suit)
        self.game.score_melds()
        self.trump_var.set(selection.title())
        self.phase = "tricks"
        self.phase_var.set("Meld & play")
        self.status_var.set("Meld scored. Play out tricks by selecting cards in turn.")
        self._log_message(f"Trump suit set to {selection.title()}.")
        self.update_display()

    def _play_card(self) -> None:
        if self.phase != "tricks" or self.game.current_player_index is None:
            return
        if not self.hand_listbox:
            return
        selection = self.hand_listbox.curselection()
        if not selection:
            self.status_var.set("Select a card to play.")
            return
        player = self.game.players[self.game.current_player_index]
        card = player.hand[selection[0]]
        if not self.game.is_valid_play(player, card):
            self.status_var.set("You must follow suit when able.")
            return
        self.game.play_card(card)
        self.play_sound("card")
        self._log_message(f"{player.name} plays {card}.")
        if len(self.game.current_trick) == len(self.game.players):
            winner = self.game.complete_trick()
            self.play_sound("win")
            self._log_message(
                f"Trick won by {winner.name}: {self.game.format_trick(self.game.trick_history[-1])}"
            )
            if not any(p.hand for p in self.game.players):
                totals = self.game.resolve_round()
                scores = ", ".join(
                    f"Team {team + 1}: {values['total']}" for team, values in totals.items()
                )
                self._log_message(f"Round complete. {scores}")
                self.phase = "scoring"
                self.phase_var.set("Scoring")
                self.status_var.set("Round complete. Start a new round when ready.")
        self.update_display()

    def update_display(self) -> None:
        totals = self.game.partnership_scores
        for index, value in enumerate(totals):
            self.team_score_vars[index].set(str(value))
        if self.game.bidding_history:
            history = [f"{name}: {action}" for name, action in self.game.bidding_history]
            self.bid_history_var.set("\n".join(history))
        else:
            self.bid_history_var.set("No bids yet")
        if self.phase == "bidding" and self.game.bidding_phase:
            current = self.game.players[self.game.bidding_phase.current_index]
            self.current_player_var.set(current.name)
        elif self.game.current_player_index is not None:
            self.current_player_var.set(self.game.players[self.game.current_player_index].name)
        if self.meld_widget:
            self.meld_widget.configure(state="normal")
            self.meld_widget.delete("1.0", tk.END)
            if self.game.meld_breakdowns:
                for player in self.game.players:
                    breakdown = self.game.meld_breakdowns.get(player.name, {})
                    parts = ", ".join(
                        f"{key.replace('_', ' ')}: {value}" for key, value in breakdown.items()
                    )
                    if not parts:
                        parts = "no meld"
                    self.meld_widget.insert(
                        tk.END, f"{player.name}: {player.meld_points} ({parts})\n"
                    )
            else:
                self.meld_widget.insert(tk.END, "Meld has not been scored yet.\n")
            self.meld_widget.configure(state="disabled")
        if self.hand_listbox:
            self.hand_listbox.delete(0, tk.END)
            if self.game.current_player_index is not None:
                player = self.game.players[self.game.current_player_index]
            elif self.game.bidding_phase:
                player = self.game.players[self.game.bidding_phase.current_index]
            else:
                player = self.game.players[0]
            for card in player.hand:
                self.hand_listbox.insert(tk.END, str(card))


def run_app(player_names: Optional[list[str]] = None) -> None:
    """Launch the Tkinter application."""

    if not TKINTER_AVAILABLE:
        raise RuntimeError("Tkinter is not available on this system")
    players: Optional[list[PinochlePlayer]] = None
    if player_names:
        names = list(player_names)[:4]
        while len(names) < 4:
            names.append(f"Player {len(names) + 1}")
        players = [PinochlePlayer(name=name) for name in names]
    root = tk.Tk()
    game = PinochleGame(players) if players else None
    gui = PinochleGUI(root, game=game)
    gui.update_display()
    root.mainloop()


__all__ = ["PinochleGUI", "run_app"]
