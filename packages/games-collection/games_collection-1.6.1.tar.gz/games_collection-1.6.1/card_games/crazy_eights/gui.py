"""Graphical interface for the Crazy Eights card game.

The GUI is built with Tkinter and layers on top of :class:`CrazyEightsGame`.
It focuses on presenting the discard pile, draw pile, and a scoreboard while
keeping the player's hand fully interactive. Clicking a card plays it when
legal; eights prompt a suit selector popover to choose the next suit. The log
mirrors all engine actions, including the automated opponents that play out
their turns immediately after the human move.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Optional

from card_games.common.cards import Card, Suit
from card_games.common.soundscapes import initialize_game_soundscape
from card_games.crazy_eights.game import CrazyEightsGame, Player
from common.gui_base import TKINTER_AVAILABLE, BaseGUI, GUIConfig, tk, ttk

if not TKINTER_AVAILABLE:  # pragma: no cover - Tkinter unavailable environments
    raise ImportError("Tkinter is required to use the Crazy Eights GUI")


class CrazyEightsGUI(BaseGUI):
    """Tkinter GUI that visualises and runs a Crazy Eights match."""

    def __init__(
        self,
        root: tk.Tk,
        game: CrazyEightsGame,
        *,
        enable_sounds: bool = True,
        config: Optional[GUIConfig] = None,
    ) -> None:
        """Initialise the Crazy Eights GUI.

        Args:
            root: The Tkinter root window.
            game: Game engine instance to visualise.
            config: Optional configuration overrides for the GUI.
        """
        gui_config = config or GUIConfig(
            window_title="Crazy Eights",
            window_width=1080,
            window_height=720,
            log_height=14,
            log_width=70,
            enable_sounds=enable_sounds,
            enable_animations=True,
        )
        super().__init__(root, gui_config)
        self.sound_manager = initialize_game_soundscape(
            "crazy_eights",
            module_file=__file__,
            enable_sounds=gui_config.enable_sounds,
            existing_manager=self.sound_manager,
        )

        self.game = game
        self._current_turn_name: str = ""
        self._draws_this_turn: int = 0
        self._game_over: bool = False
        self._suit_dialog: Optional[tk.Toplevel] = None

        self.turn_var = tk.StringVar(value="Preparing table...")
        self.active_card_var = tk.StringVar(value="Top card: —")
        self.deck_var = tk.StringVar(value="Draw pile: 52")
        self.status_message = tk.StringVar(value="Welcome to Crazy Eights! Click a card to play.")

        self.build_layout()
        self.update_display()
        self._log("Game ready. You go first!")
        self.root.after(400, self._advance_ai_turns)

    def build_layout(self) -> None:
        """Create the complete window layout."""
        theme = self.current_theme
        colors = theme.colors

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        container = tk.Frame(self.root, bg=colors.background)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        # Header with turn information and pile summaries
        header = tk.Frame(container, bg=colors.background, padx=16, pady=12)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        tk.Label(
            header,
            textvariable=self.turn_var,
            font=(theme.font_family, theme.font_size + 4, "bold"),
            bg=colors.background,
            fg=colors.foreground,
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            header,
            textvariable=self.active_card_var,
            font=(theme.font_family, theme.font_size + 2),
            bg=colors.background,
            fg=colors.primary,
        ).grid(row=0, column=1, sticky="w", padx=20)

        tk.Label(
            header,
            textvariable=self.deck_var,
            font=(theme.font_family, theme.font_size + 2),
            bg=colors.background,
            fg=colors.secondary,
        ).grid(row=0, column=2, sticky="e")

        # Central board with scoreboard and log
        board = tk.Frame(container, bg=colors.background, padx=16, pady=10)
        board.grid(row=1, column=0, sticky="nsew")
        board.columnconfigure(0, weight=1)
        board.columnconfigure(1, weight=2)
        board.rowconfigure(0, weight=1)

        scoreboard_frame = self.create_label_frame(board, "Table scoreboard")
        scoreboard_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        scoreboard_frame.columnconfigure(0, weight=1)
        self.scoreboard_body = tk.Frame(scoreboard_frame, bg=colors.background)
        self.scoreboard_body.pack(fill=tk.BOTH, expand=True)

        log_frame = self.create_label_frame(board, "Game log")
        log_frame.grid(row=0, column=1, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_widget = self.create_log_widget(log_frame)
        self.log_widget.grid(row=0, column=0, sticky="nsew")

        # Hand and controls
        hand_section = self.create_label_frame(container, "Your hand")
        hand_section.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        hand_section.columnconfigure(0, weight=1)

        tk.Label(
            hand_section,
            textvariable=self.status_message,
            font=(theme.font_family, theme.font_size + 1),
            bg=colors.background,
            fg=colors.info,
            anchor="w",
            pady=4,
        ).grid(row=0, column=0, sticky="ew")

        self.hand_frame = tk.Frame(hand_section, bg=colors.background)
        self.hand_frame.grid(row=1, column=0, sticky="ew", pady=(6, 4))
        for column in range(12):
            self.hand_frame.columnconfigure(column, weight=1)

        controls = tk.Frame(hand_section, bg=colors.background)
        controls.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)

        self.draw_button = ttk.Button(controls, text="Draw card", command=self._on_draw_card)
        self.draw_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.pass_button = ttk.Button(controls, text="Pass", command=self._on_pass_turn)
        self.pass_button.grid(row=0, column=1, sticky="ew")

    def update_display(self) -> None:
        """Refresh labels, scoreboard, and hand to match the engine state."""
        summary = self.game.get_state_summary()
        theme = self.current_theme
        colors = theme.colors

        self.turn_var.set(f"Current player: {summary['current_player']}")
        top_card_text = summary["top_card"] or "—"
        if summary["active_suit"]:
            top_card_text = f"{top_card_text} (Suit in play: {summary['active_suit']})"
        self.active_card_var.set(f"Top card: {top_card_text}")
        self.deck_var.set(f"Draw pile: {summary['deck_cards']} cards")

        if summary["current_player"] != self._current_turn_name:
            self._current_turn_name = summary["current_player"]
            if self._is_human_turn():
                self._draws_this_turn = 0

        self._render_scoreboard(summary, colors)
        self._render_hand()
        self._update_controls(summary)

        if summary["state"] == "GAME_OVER" and not self._game_over:
            self._handle_game_over()

    def _render_scoreboard(self, summary: dict[str, Any], colors: Any) -> None:
        """Render scoreboard rows for each player."""
        for widget in self.scoreboard_body.winfo_children():
            widget.destroy()

        current = summary["current_player"]
        max_score = max((player["score"] for player in summary["players"]), default=0)

        for index, player in enumerate(summary["players"]):
            is_current = player["name"] == current and summary["state"] != "GAME_OVER"
            is_winner = summary["state"] == "GAME_OVER" and player["score"] == max_score and max_score > 0
            row_bg = colors.highlight if is_current else colors.background
            if is_winner:
                row_bg = colors.success
            text_fg = colors.foreground if not is_winner else "#FFFFFF"
            row = tk.Frame(self.scoreboard_body, bg=row_bg, padx=6, pady=4)
            row.grid(row=index, column=0, sticky="ew", pady=2)
            row.columnconfigure(1, weight=1)

            name_label = tk.Label(row, text=player["name"], bg=row_bg, fg=text_fg, anchor="w")
            name_label.grid(row=0, column=0, sticky="w")

            info_text = f"Cards: {player['hand_size']}"
            if player["score"]:
                info_text += f" | Score: {player['score']}"
            tk.Label(row, text=info_text, bg=row_bg, fg=text_fg, anchor="w").grid(row=0, column=1, sticky="w")
        self.animate_highlight(self.scoreboard_body)

    def _render_hand(self) -> None:
        """Show the human player's hand as clickable card buttons."""
        for widget in self.hand_frame.winfo_children():
            widget.destroy()

        human = self.game.players[0]
        playable = human.get_playable_cards(self.game.active_suit, self.game.active_rank)
        is_turn = self._is_human_turn()

        if not human.hand:
            tk.Label(
                self.hand_frame,
                text="(No cards)",
                bg=self.current_theme.colors.background,
                fg=self.current_theme.colors.secondary,
            ).grid(row=0, column=0, sticky="w")
            return

        for index, card in enumerate(sorted(human.hand, key=lambda c: (c.suit.value, c.value))):
            state = tk.NORMAL if is_turn and card in playable else tk.DISABLED
            btn = tk.Button(
                self.hand_frame,
                text=str(card),
                width=6,
                relief=tk.RAISED,
                state=state,
                command=lambda c=card: self._on_card_clicked(c),
                font=(self.current_theme.font_family, self.current_theme.font_size + 2, "bold"),
                bg="#ffffff" if card.rank != "8" else "#fde68a",
            )
            btn.grid(row=index // 12, column=index % 12, padx=4, pady=4, sticky="ew")
            if card in playable:
                btn.configure(bg="#d1fae5")
        self.animate_highlight(self.hand_frame)

    def _update_controls(self, summary: dict[str, Any]) -> None:
        """Enable/disable draw and pass controls based on turn context."""
        human_turn = self._is_human_turn() and not self._game_over
        if human_turn:
            self.draw_button.state(["!disabled"])
            human = self.game.players[0]
            playable = human.get_playable_cards(self.game.active_suit, self.game.active_rank)
            if playable:
                self.status_message.set("Choose a card to play or draw from the pile.")
            else:
                self.status_message.set("No playable cards. Draw from the pile.")
            allow_pass = False
            if not playable:
                if self.game.draw_limit == 0:
                    allow_pass = summary["deck_cards"] == 0 and self._draws_this_turn > 0
                else:
                    allow_pass = self._draws_this_turn >= self.game.draw_limit
            if allow_pass:
                self.pass_button.state(["!disabled"])
            else:
                self.pass_button.state(["disabled"])
        else:
            self.draw_button.state(["disabled"])
            self.pass_button.state(["disabled"])
            if not self._game_over:
                self.status_message.set("Waiting for opponents...")

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
            self.status_message.set(result["message"])
            self._log(result["message"])
            return

        self._log(result["message"])
        self._draws_this_turn = 0
        self.update_display()

        if result.get("game_over"):
            self._handle_game_over()
        else:
            self.root.after(450, self._advance_ai_turns)

    def _prompt_suit_selection(self, card: Card) -> None:
        """Open a modal dialog to choose a suit when an eight is played."""
        if self._suit_dialog is not None:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Choose a suit")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.configure(bg=self.current_theme.colors.background, padx=16, pady=12)

        tk.Label(
            dialog,
            text="Select the suit to continue:",
            font=(self.current_theme.font_family, self.current_theme.font_size + 2, "bold"),
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.foreground,
        ).pack(anchor="w", pady=(0, 8))

        for suit in Suit:
            tk.Button(
                dialog,
                text=f"{suit.name.title()} {suit.value}",
                width=18,
                command=lambda s=suit: self._finalise_suit_choice(dialog, card, s),
            ).pack(fill=tk.X, pady=4)

        dialog.protocol("WM_DELETE_WINDOW", lambda: self._finalise_suit_choice(dialog, card, None))
        self._suit_dialog = dialog

    def _finalise_suit_choice(self, dialog: tk.Toplevel, card: Card, suit: Optional[Suit]) -> None:
        """Close the suit dialog and play the eight with the chosen suit."""
        dialog.grab_release()
        dialog.destroy()
        self._suit_dialog = None
        if suit is None:
            self.status_message.set("Suit selection cancelled. Choose again.")
            return
        self._play_card(card, suit)

    def _on_draw_card(self) -> None:
        """Draw a card for the human player."""
        if not self._is_human_turn() or self._game_over:
            return
        result = self.game.draw_card()
        self._draws_this_turn += 1 if result["success"] else 0
        if result["success"]:
            card = result.get("card")
            card_text = f" ({card})" if isinstance(card, Card) else ""
            self._log(result["message"] + card_text)
        else:
            self._log(result["message"])
            self.status_message.set(result["message"])
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
            self.root.after(450, self._advance_ai_turns)
        else:
            self.status_message.set(result["message"])
            self._log(result["message"])

    def _advance_ai_turns(self) -> None:
        """Automatically resolve AI turns until the human is active again."""
        if self._game_over:
            return
        if self._is_human_turn():
            self.update_display()
            return

        current_player = self.game.get_current_player()
        self.status_message.set(f"{current_player.name} is thinking...")
        self.root.after(350, self._execute_ai_turn)

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
            self.root.after(450, self._advance_ai_turns)
            return

        draws = 0
        drew_card = False
        while self.game.draw_limit == 0 or draws < self.game.draw_limit:
            draw_result = self.game.draw_card()
            if not draw_result["success"]:
                self._log(draw_result["message"])
                break
            draws += 1
            drew_card = True
            card = draw_result.get("card")
            card_desc = f" ({card})" if isinstance(card, Card) else ""
            self._log(draw_result["message"] + card_desc)
            if player.has_playable_card(self.game.active_suit, self.game.active_rank):
                break

            if self.game.draw_limit == 0:
                continue

        if player.has_playable_card(self.game.active_suit, self.game.active_rank):
            self.root.after(350, self._advance_ai_turns)
            return

        if drew_card:
            result = self.game.pass_turn()
            if result["success"]:
                self._log(result["message"])
        else:
            # No cards available to draw; prevent infinite loop
            result = self.game.pass_turn()
            if result["success"]:
                self._log(result["message"])

        self.update_display()
        if self._game_over:
            return
        self.root.after(450, self._advance_ai_turns)

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
        self.status_message.set(f"Game over! {winner['name']} wins with {winner['score']} points.")
        self._log(self.status_message.get())
        self.draw_button.state(["disabled"])
        self.pass_button.state(["disabled"])
        self.update_display()

    def _log(self, message: str) -> None:
        """Append a message to the game log widget."""
        self.log_message(self.log_widget, message)
