"""Graphical interface for the Bridge card game.

This module builds a complete Tkinter layout for a single deal of Contract
Bridge. The GUI renders the auction history, score information, the current
trick, and interactive card buttons for the South player while sequencing
automated play for the remaining seats.
"""

from __future__ import annotations

import random
from typing import Optional

from card_games.bridge.game import AuctionState, BidSuit, BridgeGame, BridgePlayer, Call, CallType, Contract, Vulnerability
from card_games.common.cards import Card, Suit
from common.gui_base import TKINTER_AVAILABLE, BaseGUI, GUIConfig, scrolledtext, tk, ttk

if TKINTER_AVAILABLE:
    from tkinter import messagebox, simpledialog
else:  # pragma: no cover - GUI fallback when Tk is unavailable
    messagebox = None  # type: ignore
    simpledialog = None  # type: ignore

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


class BridgeGUI(BaseGUI):
    """Tkinter implementation of a Bridge table with automated opponents."""

    def __init__(self, root: tk.Tk, config: Optional[GUIConfig] = None) -> None:
        super().__init__(root, config)
        self.players = [
            BridgePlayer(name="North AI", is_ai=True),
            BridgePlayer(name="East AI", is_ai=True),
            BridgePlayer(name="South Player", is_ai=False),
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
        self.current_selection_player: Optional[BridgePlayer] = self.players[2]
        self.hand_vars = {player.position: tk.StringVar() for player in self.players}
        self.vulnerability_var = tk.StringVar()
        self.contract_var = tk.StringVar()
        self.declarer_var = tk.StringVar()
        self.trick_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Preparing deal...")
        self.seat_labels: dict[str, tk.Label] = {}
        self.card_button_frame: Optional[tk.Frame] = None
        self.trick_canvas: Optional[tk.Canvas] = None
        self.bidding_text: Optional[scrolledtext.ScrolledText] = None
        self.log_text: Optional[scrolledtext.ScrolledText] = None
        self.build_layout()
        self.root.after(250, self.start_new_hand)

    def build_layout(self) -> None:
        """Create Bridge-specific UI widgets."""
        bg = self.current_theme.colors.background
        fg = self.current_theme.colors.foreground
        self.root.configure(bg=bg)
        main = tk.Frame(self.root, bg=bg)
        main.pack(fill="both", expand=True)
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        header = tk.Frame(main, bg=bg, pady=10)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(
            header,
            text="Bridge Scoreboard",
            font=(self.config.font_family, self.config.font_size + 4, "bold"),
        ).pack(anchor="w", padx=16)
        details = tk.Frame(header, bg=bg)
        details.pack(fill="x", padx=16, pady=(6, 0))
        ttk.Label(details, textvariable=self.vulnerability_var).grid(row=0, column=0, sticky="w")
        ttk.Label(details, textvariable=self.contract_var).grid(row=0, column=1, sticky="w", padx=(18, 0))
        ttk.Label(details, textvariable=self.declarer_var).grid(row=1, column=0, sticky="w")
        ttk.Label(details, textvariable=self.trick_var).grid(row=1, column=1, sticky="w", padx=(18, 0))
        play_area = tk.Frame(main, bg=bg)
        play_area.grid(row=1, column=0, sticky="nsew")
        play_area.rowconfigure(0, weight=1)
        play_area.rowconfigure(1, weight=1)
        play_area.rowconfigure(2, weight=1)
        play_area.columnconfigure(0, weight=1)
        play_area.columnconfigure(1, weight=1)
        play_area.columnconfigure(2, weight=1)
        north_frame = tk.Frame(play_area, bg=bg)
        north_frame.grid(row=0, column=1, pady=12)
        self._create_seat_widget(north_frame, self.players[0])
        west_frame = tk.Frame(play_area, bg=bg)
        west_frame.grid(row=1, column=0, pady=12)
        self._create_seat_widget(west_frame, self.players[3])
        center_frame = tk.Frame(play_area, bg=bg, bd=1, relief="ridge")
        center_frame.grid(row=1, column=1, padx=8, pady=8, sticky="nsew")
        center_frame.rowconfigure(0, weight=1)
        center_frame.columnconfigure(0, weight=1)
        self.trick_canvas = tk.Canvas(
            center_frame,
            bg=self.current_theme.colors.canvas_bg,
            highlightthickness=0,
        )
        self.trick_canvas.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        east_frame = tk.Frame(play_area, bg=bg)
        east_frame.grid(row=1, column=2, pady=12)
        self._create_seat_widget(east_frame, self.players[1])
        south_frame = tk.Frame(play_area, bg=bg)
        south_frame.grid(row=2, column=1, pady=12)
        self._create_seat_widget(south_frame, self.players[2])
        self.card_button_frame = tk.Frame(south_frame, bg=bg)
        self.card_button_frame.pack(pady=(8, 0))
        sidebar = tk.Frame(main, bg=bg)
        sidebar.grid(row=1, column=1, sticky="nsew")
        sidebar.rowconfigure(1, weight=1)
        ttk.Label(
            sidebar,
            text="Bidding History",
            font=(self.config.font_family, self.config.font_size + 2, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(0, 6))
        self.bidding_text = scrolledtext.ScrolledText(
            sidebar,
            height=12,
            width=36,
            state="disabled",
            font=(self.config.font_family, self.config.font_size),
        )
        self.bidding_text.grid(row=1, column=0, sticky="nsew", padx=12)
        ttk.Label(
            sidebar,
            text="Deal Log",
            font=(self.config.font_family, self.config.font_size + 2, "bold"),
        ).grid(row=2, column=0, sticky="w", padx=12, pady=(10, 6))
        self.log_text = scrolledtext.ScrolledText(
            sidebar,
            height=10,
            width=36,
            state="disabled",
            font=(self.config.font_family, self.config.font_size),
        )
        self.log_text.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 12))
        footer = tk.Frame(main, bg=bg, pady=10)
        footer.grid(row=2, column=0, columnspan=2, sticky="ew")
        ttk.Label(
            footer,
            textvariable=self.status_var,
            font=(self.config.font_family, self.config.font_size),
            foreground=fg,
        ).pack(anchor="w", padx=16)
        button_frame = tk.Frame(footer, bg=bg)
        button_frame.pack(anchor="e", padx=16)
        ttk.Button(button_frame, text="Review Tricks", command=self._show_trick_history_dialog).pack(side="left", padx=6)
        ttk.Button(button_frame, text="Claim Tricks", command=self._handle_claim_dialog).pack(side="left", padx=6)

    def update_display(self) -> None:
        """Synchronize the UI with the current game state."""
        self._update_scoreboard()
        self._refresh_hand_views()
        self._refresh_trick_canvas()

    def start_new_hand(self) -> None:
        """Deal cards, conduct bidding, and prepare for play."""
        self._clear_log()
        self.game.deal_cards()
        self.contract = self.game.conduct_bidding(call_selector=self._select_call)
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
            self.status_var.set("All players passed. Deal over.")
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
        self.status_var.set("Opening lead in progress...")
        self.update_display()
        self.root.after(500, self._advance_turn)

    def _select_call(
        self,
        player: BridgePlayer,
        legal_calls: list[Call],
        history: list[Call],
        state: AuctionState,
    ) -> Call:
        """Determine a call for ``player`` during the auction."""

        if player.is_ai:
            call = self.game.bidding_helper.choose_call(player, legal_calls, history.copy(), state)
            entry = self._format_call(call)
            if call.explanation:
                entry += f" [{call.explanation}]"
            self._append_log(f"{player.position} calls {entry}")
            return call
        return self._prompt_call_dialog(player, legal_calls, history, state)

    def _prompt_call_dialog(
        self,
        player: BridgePlayer,
        legal_calls: list[Call],
        history: list[Call],
        state: AuctionState,
    ) -> Call:
        """Ask the human player for a call via a dialog box."""

        if simpledialog is None:
            return legal_calls[0]

        while True:
            options = []
            for index, option in enumerate(legal_calls, start=1):
                text = self._format_call(option)
                if option.forced:
                    text += " (forced)"
                options.append(f"{index}. {text}")
            prompt = "\n".join(
                [
                    f"Your turn, {player.name} ({player.position}).",
                    "Select a call by number or enter a bid (e.g. 2H, 3NT, X, XX, PASS).",
                    "Type 'history' to review the auction or 'suggest' for a hint.",
                    "",
                    *options,
                ]
            )
            response = simpledialog.askstring("Bridge Bidding", prompt, parent=self.root)
            if response is None:
                continue
            lowered = response.strip().lower()
            if not lowered:
                continue
            if lowered in {"history", "h"}:
                message = "\n".join(self._format_call(call) for call in history) or "No calls yet."
                if messagebox is not None:
                    messagebox.showinfo("Auction History", message, parent=self.root)
                continue
            if lowered in {"suggest", "s"}:
                suggestion = self.game.bidding_helper.choose_call(player, legal_calls, history.copy(), state)
                suggestion_text = self._format_call(suggestion)
                if suggestion.explanation:
                    suggestion_text += f"\nExplanation: {suggestion.explanation}"
                if messagebox is not None:
                    messagebox.showinfo("Suggested Call", suggestion_text, parent=self.root)
                continue
            matched = self._parse_bidding_input(response, legal_calls)
            if matched is None:
                if messagebox is not None:
                    messagebox.showinfo("Invalid", "Input did not match a legal call.", parent=self.root)
                continue
            return matched

    def _parse_bidding_input(self, text: str, legal_calls: list[Call]) -> Optional[Call]:
        """Return the matching call from ``legal_calls`` for ``text``."""

        cleaned = text.strip().upper()
        if not cleaned:
            return None
        if cleaned.isdigit():
            index = int(cleaned) - 1
            if 0 <= index < len(legal_calls):
                return legal_calls[index]
            return None
        mapping = {
            "P": CallType.PASS,
            "PASS": CallType.PASS,
            "X": CallType.DOUBLE,
            "DOUBLE": CallType.DOUBLE,
            "XX": CallType.REDOUBLE,
            "REDOUBLE": CallType.REDOUBLE,
        }
        if cleaned in mapping:
            desired = mapping[cleaned]
            for option in legal_calls:
                if option.call_type == desired:
                    return option
            return None
        level = ""
        suit = ""
        for char in cleaned:
            if char.isdigit():
                level += char
            else:
                suit += char
        if not level or not suit:
            return None
        try:
            level_value = int(level)
        except ValueError:
            return None
        suit_key = suit.replace("NT", "N")
        suit_map = {
            "C": BidSuit.CLUBS,
            "D": BidSuit.DIAMONDS,
            "H": BidSuit.HEARTS,
            "S": BidSuit.SPADES,
            "N": BidSuit.NO_TRUMP,
        }
        bid_suit = suit_map.get(suit_key)
        if bid_suit is None:
            return None
        for option in legal_calls:
            if option.call_type == CallType.BID and option.bid is not None:
                if option.bid.level == level_value and option.bid.suit == bid_suit:
                    return option
        return None

    def _create_seat_widget(self, container: tk.Frame, player: BridgePlayer) -> None:
        """Create labels representing a player seat."""
        bg = self.current_theme.colors.background
        fg = self.current_theme.colors.foreground
        ttk.Label(
            container,
            text=f"{player.name} ({player.position})",
            font=(self.config.font_family, self.config.font_size + 1, "bold"),
        ).pack()
        hand_label = tk.Label(
            container,
            textvariable=self.hand_vars[player.position],
            font=(self.config.font_family, self.config.font_size),
            wraplength=220,
            justify="center",
            bg=bg,
            fg=fg,
        )
        hand_label.pack(pady=(4, 0))
        self.seat_labels[player.position] = hand_label

    def _update_scoreboard(self) -> None:
        """Update status variables for the scoreboard widgets."""
        self.vulnerability_var.set(f"Vulnerability: {self.game.vulnerability.value}")
        if self.contract is None:
            self.contract_var.set("Contract: None")
            self.declarer_var.set("Declarer: -")
        else:
            contract_text = self._format_contract(self.contract)
            dummy = self.players[self.contract.declarer.partner_index]
            self.contract_var.set(f"Contract: {contract_text}")
            self.declarer_var.set(f"Declarer: {self.contract.declarer.position} | Dummy: {dummy.position}")
        ns_tricks = sum(player.tricks_won for player in self.players if player.position in {"N", "S"})
        ew_tricks = sum(player.tricks_won for player in self.players if player.position in {"E", "W"})
        self.trick_var.set(f"Tricks - NS: {ns_tricks} | EW: {ew_tricks}")

    def _refresh_hand_views(self) -> None:
        """Render text for each seat."""
        for player in self.players:
            display = self._format_hand_display(player)
            self.hand_vars[player.position].set(display)
        self._refresh_card_buttons()

    def _refresh_trick_canvas(self) -> None:
        """Draw the current trick and dummy information."""
        if self.trick_canvas is None:
            return
        self.trick_canvas.delete("all")
        fg = self.current_theme.colors.foreground
        dummy_text = "Dummy hidden"
        if self.dummy_index is not None:
            dummy_player = self.players[self.dummy_index]
            if self.dummy_revealed:
                dummy_cards = self._format_cards_line(dummy_player.hand)
                dummy_text = f"Dummy {dummy_player.position}: {dummy_cards or 'Empty'}"
            else:
                dummy_text = f"Dummy {dummy_player.position}: {len(dummy_player.hand)} cards"
        self.trick_canvas.create_text(
            200,
            28,
            text=dummy_text,
            font=(self.config.font_family, self.config.font_size),
            fill=fg,
        )
        positions = {"N": (200, 90), "E": (340, 150), "S": (200, 210), "W": (60, 150)}
        for player, card in self.game.current_trick:
            pos = player.position
            x, y = positions.get(pos, (200, 150))
            self.trick_canvas.create_text(
                x,
                y,
                text=f"{pos}: {card}",
                font=(self.config.font_family, self.config.font_size + 2, "bold"),
                fill=fg,
            )

    def _render_bidding_history(self) -> None:
        """Populate the bidding history widget."""
        if self.bidding_text is None:
            return
        self.bidding_text.configure(state="normal")
        self.bidding_text.delete("1.0", tk.END)
        if not self.game.bidding_history:
            self.bidding_text.insert(tk.END, "No calls made.\n")
        else:
            for call in self.game.bidding_history:
                entry = self._format_call(call)
                self.bidding_text.insert(tk.END, f"{entry}\n")
        self.bidding_text.configure(state="disabled")

    def _advance_turn(self) -> None:
        """Progress to the next player's action."""
        if self.hand_complete or self.contract is None or self.active_player_index is None:
            return
        player = self.players[self.active_player_index]
        controller = self._controller_for_player(player)
        if controller.is_ai:
            self.status_var.set(f"{player.name} thinking...")
            self.root.after(600, lambda: self._play_ai_turn(player))
        else:
            self.awaiting_human_play = True
            self.current_selection_player = player
            valid = self.game.get_valid_plays(player)
            self.current_valid_cards = valid
            self.status_var.set(f"{player.position} - choose a card to play.")
            self.update_display()

    def _play_ai_turn(self, player: BridgePlayer) -> None:
        """Execute an automated play."""
        if self.hand_complete:
            return
        card = self.game.select_card_to_play(player)
        self._finalize_play_for_card(player, card)

    def _handle_human_card(self, card: Card) -> None:
        """Handle a card chosen by the human player."""
        if not self.awaiting_human_play or self.contract is None:
            return
        player = self.players[self.active_player_index]
        if card not in self.game.get_valid_plays(player):
            return
        self.awaiting_human_play = False
        self.current_valid_cards = None
        self.current_selection_player = self.players[2]
        self._finalize_play_for_card(player, card)

    def _finalize_play_for_card(self, player: BridgePlayer, card: Card) -> None:
        """Apply a played card and update the interface."""
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
            self.status_var.set("Evaluating trick winner...")
            self.root.after(700, self._complete_trick)
        else:
            self.active_player_index = (self.active_player_index + 1) % 4
            self.root.after(200, self._advance_turn)

    def _complete_trick(self) -> None:
        """Resolve the current trick and continue play."""
        winner = self.game.complete_trick()
        self._append_log(f"{winner.position} wins the trick")
        ns_tricks = sum(player.tricks_won for player in self.players if player.position in {"N", "S"})
        ew_tricks = sum(player.tricks_won for player in self.players if player.position in {"E", "W"})
        self.status_var.set(f"Trick won by {winner.position}. NS {ns_tricks} - EW {ew_tricks}")
        self.active_player_index = self.players.index(winner)
        self.update_display()
        if all(not player.hand for player in self.players):
            self._finalize_hand()
        else:
            self.root.after(400, self._advance_turn)

    def _finalize_hand(self) -> None:
        """Compute the final score and present the outcome."""
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
        self.status_var.set(result_text)
        self._append_log(result_text)
        self._append_log("Scores - North/South: {north_south} | East/West: {east_west}".format(**scores))
        self.update_display()

    def _refresh_card_buttons(self) -> None:
        """Render card selection buttons for the South player."""
        if self.card_button_frame is None:
            return
        for widget in self.card_button_frame.winfo_children():
            widget.destroy()
        target = self.current_selection_player or self.players[2]
        sorted_cards = sorted(
            target.hand,
            key=lambda card: (SUIT_DISPLAY_ORDER[card.suit], -card.value),
        )
        valid_cards = set(self.current_valid_cards or [])
        for card in sorted_cards:
            button = ttk.Button(
                self.card_button_frame,
                text=str(card),
                command=lambda c=card: self._handle_human_card(c),
                width=4,
            )
            if valid_cards and card in valid_cards:
                button.state(["!disabled"])
            else:
                button.state(["disabled"])
            button.pack(side="left", padx=2)

    def _format_hand_display(self, player: BridgePlayer) -> str:
        """Return formatted hand text for ``player``."""
        if player.position == "S":
            return self._format_cards_line(player.hand)
        if self.dummy_revealed and self.dummy_index is not None and player == self.players[self.dummy_index]:
            return self._format_cards_line(player.hand)
        return f"{len(player.hand)} cards"

    def _format_cards_line(self, cards: list[Card]) -> str:
        """Return a textual representation of card collection."""
        if not cards:
            return ""
        ordered = sorted(cards, key=lambda card: (SUIT_DISPLAY_ORDER[card.suit], -card.value))
        return " ".join(str(card) for card in ordered)

    def _format_call(self, call: Call) -> str:
        """Return a printable auction entry."""
        if call.call_type == CallType.BID and call.bid is not None:
            symbol = SUIT_SYMBOLS.get(call.bid.suit, "")
            text = f"{call.player.position}: {call.bid.level}{symbol}"
        elif call.call_type == CallType.DOUBLE:
            text = f"{call.player.position}: Double"
        elif call.call_type == CallType.REDOUBLE:
            text = f"{call.player.position}: Redouble"
        else:
            text = f"{call.player.position}: Pass"
        if call.forced and call.call_type == CallType.PASS:
            text += " (forced)"
        if call.explanation:
            text += f" [{call.explanation}]"
        return text

    def _format_contract(self, contract: Contract) -> str:
        """Return a human-friendly description of the contract."""
        symbol = SUIT_SYMBOLS.get(contract.bid.suit, "")
        suffix = ""
        if contract.redoubled:
            suffix = " XX"
        elif contract.doubled:
            suffix = " X"
        return f"{contract.bid.level}{symbol}{suffix}"

    def _controller_for_player(self, player: BridgePlayer) -> BridgePlayer:
        """Return the controlling seat for ``player``'s plays."""

        if self.contract is None:
            return player
        dummy = self.players[self.contract.declarer.partner_index]
        if player == dummy:
            return self.contract.declarer
        return player

    def _handle_claim_dialog(self) -> None:
        """Allow the human player to claim remaining tricks."""

        if self.hand_complete or self.contract is None or simpledialog is None or messagebox is None:
            return
        if self.game.current_trick:
            messagebox.showinfo("Claim", "Finish the current trick before claiming.", parent=self.root)
            return
        remaining = self.game.tricks_remaining()
        if remaining <= 0:
            messagebox.showinfo("Claim", "No tricks remain to claim.", parent=self.root)
            return
        value = simpledialog.askinteger(
            "Claim Tricks",
            f"Enter the number of tricks to claim (1-{remaining})",
            minvalue=1,
            maxvalue=remaining,
            parent=self.root,
        )
        if value is None:
            return
        claimant = self.players[2]
        if self.game.claim_tricks(claimant, value):
            self._append_log(f"Claimed {value} tricks by {claimant.position}")
            self._finalize_hand()
        else:
            messagebox.showinfo("Claim", "Claim could not be processed.", parent=self.root)

    def _show_trick_history_dialog(self) -> None:
        """Display the recorded trick history in a dialog."""

        if messagebox is None:
            return
        summary = self.game.trick_history_summary()
        text = "\n".join(summary) if summary else "No completed tricks yet."
        messagebox.showinfo("Trick History", text, parent=self.root)

    def _append_log(self, message: str) -> None:
        """Append ``message`` to the deal log."""
        if self.log_text is None:
            return
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _clear_log(self) -> None:
        """Remove all content from the deal log."""
        if self.log_text is None:
            return
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")


def run_app() -> None:
    """Launch the Bridge GUI application."""

    def _fallback_to_cli(message: str) -> None:
        from card_games.bridge.cli import game_loop

        print(message)
        game_loop()

    if not TKINTER_AVAILABLE:
        _fallback_to_cli("Tkinter is unavailable. Falling back to CLI interface.")
        return

    try:
        root = tk.Tk()
    except tk.TclError:
        _fallback_to_cli("Tkinter could not open a display. Falling back to CLI interface.")
        return

    config = GUIConfig(
        window_title="Contract Bridge",
        window_width=1100,
        window_height=720,
        font_family="Segoe UI",
        font_size=11,
        theme_name="dark",
        enable_sounds=False,
        enable_animations=True,
    )
    BridgeGUI(root, config=config)
    root.mainloop()
