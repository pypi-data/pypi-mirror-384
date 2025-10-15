"""Graphical interface for the Gin Rummy card game."""

from __future__ import annotations

from typing import Optional

from card_games.common.cards import Card, format_cards
from card_games.gin_rummy.game import GinRummyGame, GinRummyPlayer, HandAnalysis, Meld, MeldType
from common.gui_base import TKINTER_AVAILABLE, BaseGUI, GUIConfig

if TKINTER_AVAILABLE:  # pragma: no cover - UI specific branch
    import tkinter as tk
else:  # pragma: no cover - fallback for headless environments
    tk = None  # type: ignore


def _format_meld(meld: Meld) -> str:
    """Return a short textual description for ``meld``."""

    label = "Set" if meld.meld_type == MeldType.SET else "Run"
    return f"{label}: {format_cards(meld.cards)}"


class GinRummyGUI(BaseGUI):
    """Tkinter-powered interface that visualises a Gin Rummy match."""

    def __init__(
        self,
        root: tk.Tk,
        *,
        players: Optional[list[GinRummyPlayer]] = None,
        config: Optional[GUIConfig] = None,
    ) -> None:
        if not TKINTER_AVAILABLE:  # pragma: no cover - defensive guard
            raise RuntimeError("tkinter is required to launch the Gin Rummy GUI")

        config = config or GUIConfig(
            window_title="Gin Rummy",
            window_width=1024,
            window_height=780,
            log_height=12,
            log_width=100,
        )

        self.players = players or [
            GinRummyPlayer(name="You", is_ai=False),
            GinRummyPlayer(name="AI", is_ai=True),
        ]
        self.game = GinRummyGame(self.players)
        self.round_number = 0
        self.round_over = False
        self.phase: str = "waiting"
        self.selected_card: Optional[Card] = None
        self.log_index = 0

        super().__init__(root, config)

        # Tkinter variables populated after ``BaseGUI`` initialisation
        self.status_var = tk.StringVar(value="Click 'Start Next Round' to begin.")
        self.top_discard_var = tk.StringVar(value="Discard pile: —")
        self.stock_count_var = tk.StringVar(value="Stock remaining: —")
        self.selection_var = tk.StringVar(value="No card selected.")
        self.melds_var = tk.StringVar(value="Melds will appear here once available.")
        self.deadwood_cards_var = tk.StringVar(value="Deadwood cards will be highlighted during play.")

        self.score_vars: list[tk.StringVar] = []
        self.deadwood_vars: list[tk.StringVar] = []
        self.player_status_labels: list[tk.Label] = []

        self.hand_container: tk.Frame
        self.log_widget: tk.Widget  # set in build_layout

        self.build_layout()
        self._update_controls()

    # ------------------------------------------------------------------
    # Layout and display helpers
    # ------------------------------------------------------------------
    def build_layout(self) -> None:
        theme = self.current_theme
        main_frame = tk.Frame(self.root, bg=theme.colors.background)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Player information panels -------------------------------------------------
        info_frame = tk.Frame(main_frame, bg=theme.colors.background)
        info_frame.pack(fill=tk.X, pady=(0, 12))

        for player in self.players:
            panel = self.create_label_frame(info_frame, player.name)
            panel.configure(bg=theme.colors.background)
            panel.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=6)

            score_var = tk.StringVar(value="Score: 0")
            deadwood_var = tk.StringVar(value="Deadwood: —")

            tk.Label(
                panel,
                textvariable=score_var,
                font=(theme.font_family, theme.font_size + 2, "bold"),
                bg=theme.colors.background,
                fg=theme.colors.foreground,
            ).pack(anchor=tk.W)

            tk.Label(
                panel,
                textvariable=deadwood_var,
                font=(theme.font_family, theme.font_size),
                bg=theme.colors.background,
                fg=theme.colors.secondary,
            ).pack(anchor=tk.W, pady=(2, 4))

            badge = tk.Label(
                panel,
                text="Waiting",
                font=(theme.font_family, theme.font_size - 1, "bold"),
                relief="groove",
                padx=8,
                pady=4,
                bg=theme.colors.secondary,
                fg=theme.colors.foreground,
            )
            badge.pack(anchor=tk.W)

            self.score_vars.append(score_var)
            self.deadwood_vars.append(deadwood_var)
            self.player_status_labels.append(badge)

        # Status and pile information ---------------------------------------------
        status_frame = tk.Frame(main_frame, bg=theme.colors.background)
        status_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=(theme.font_family, theme.font_size + 1),
            bg=theme.colors.background,
            fg=theme.colors.info,
            wraplength=900,
            justify=tk.LEFT,
        ).pack(anchor=tk.W)

        pile_frame = tk.Frame(main_frame, bg=theme.colors.background)
        pile_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            pile_frame,
            textvariable=self.top_discard_var,
            font=(theme.font_family, theme.font_size),
            bg=theme.colors.background,
            fg=theme.colors.foreground,
        ).pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(
            pile_frame,
            textvariable=self.stock_count_var,
            font=(theme.font_family, theme.font_size),
            bg=theme.colors.background,
            fg=theme.colors.foreground,
        ).pack(side=tk.LEFT)

        tk.Label(
            pile_frame,
            textvariable=self.selection_var,
            font=(theme.font_family, theme.font_size - 1),
            bg=theme.colors.background,
            fg=theme.colors.secondary,
        ).pack(side=tk.RIGHT)

        # Hand and meld visualisation ---------------------------------------------
        hand_frame = self.create_label_frame(main_frame, "Your Hand")
        hand_frame.pack(fill=tk.X, pady=(0, 10))
        self.hand_container = tk.Frame(hand_frame, bg=theme.colors.background)
        self.hand_container.pack(fill=tk.X)

        meld_frame = self.create_label_frame(main_frame, "Meld Analysis")
        meld_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            meld_frame,
            textvariable=self.melds_var,
            font=(theme.font_family, theme.font_size),
            bg=theme.colors.background,
            fg=theme.colors.foreground,
            justify=tk.LEFT,
            wraplength=900,
        ).pack(anchor=tk.W)

        tk.Label(
            meld_frame,
            textvariable=self.deadwood_cards_var,
            font=(theme.font_family, theme.font_size - 1),
            bg=theme.colors.background,
            fg=theme.colors.secondary,
            justify=tk.LEFT,
            wraplength=900,
        ).pack(anchor=tk.W, pady=(6, 0))

        # Action buttons ----------------------------------------------------------
        actions = tk.Frame(main_frame, bg=theme.colors.background)
        actions.pack(fill=tk.X, pady=(0, 12))

        self.take_upcard_button = tk.Button(
            actions,
            text="Take Upcard",
            command=self.on_take_initial_upcard,
            bg=theme.colors.button_bg,
            fg=theme.colors.button_fg,
            relief=self.current_theme.button_relief,
        )
        self.take_upcard_button.pack(side=tk.LEFT, padx=4)

        self.pass_upcard_button = tk.Button(
            actions,
            text="Pass Upcard",
            command=self.on_pass_initial_upcard,
            bg=theme.colors.button_bg,
            fg=theme.colors.button_fg,
            relief=self.current_theme.button_relief,
        )
        self.pass_upcard_button.pack(side=tk.LEFT, padx=4)

        self.draw_stock_button = tk.Button(
            actions,
            text="Draw Stock",
            command=self.on_draw_from_stock,
            bg=theme.colors.button_bg,
            fg=theme.colors.button_fg,
            relief=self.current_theme.button_relief,
        )
        self.draw_stock_button.pack(side=tk.LEFT, padx=4)

        self.draw_discard_button = tk.Button(
            actions,
            text="Draw Discard",
            command=self.on_draw_from_discard,
            bg=theme.colors.button_bg,
            fg=theme.colors.button_fg,
            relief=self.current_theme.button_relief,
        )
        self.draw_discard_button.pack(side=tk.LEFT, padx=4)

        self.knock_button = tk.Button(
            actions,
            text="Knock / Gin",
            command=self.on_knock,
            bg=theme.colors.button_bg,
            fg=theme.colors.button_fg,
            relief=self.current_theme.button_relief,
        )
        self.knock_button.pack(side=tk.LEFT, padx=4)

        self.discard_button = tk.Button(
            actions,
            text="Discard Selected",
            command=self.on_discard,
            bg=theme.colors.button_bg,
            fg=theme.colors.button_fg,
            relief=self.current_theme.button_relief,
        )
        self.discard_button.pack(side=tk.LEFT, padx=4)

        self.next_round_button = tk.Button(
            actions,
            text="Start Next Round",
            command=self.start_next_round,
            bg=theme.colors.button_bg,
            fg=theme.colors.button_fg,
            relief=self.current_theme.button_relief,
        )
        self.next_round_button.pack(side=tk.RIGHT, padx=4)

        # Log ---------------------------------------------------------------------
        log_frame = self.create_label_frame(main_frame, "Round Log")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_widget = self.create_log_widget(log_frame)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

    def update_display(self) -> None:
        for idx, player in enumerate(self.players):
            analysis = self.game.analyze_hand(player.hand)
            self.score_vars[idx].set(f"Score: {player.score}")
            self.deadwood_vars[idx].set(f"Deadwood: {analysis.deadwood_total}")
            if idx == 0:
                self._update_meld_display(analysis)

        self._render_hand()

        if self.game.discard_pile:
            top_card = self.game.discard_pile[-1]
            self.top_discard_var.set(f"Discard pile: {top_card} (total {len(self.game.discard_pile)})")
        else:
            self.top_discard_var.set("Discard pile: empty")

        self.stock_count_var.set(f"Stock remaining: {len(self.game.deck.cards)}")

        # Update selection helper text
        if self.selected_card and self.phase == "discard":
            self.selection_var.set(f"Selected discard: {self.selected_card}")
        elif self.phase == "discard":
            self.selection_var.set("Select a card to discard or knock.")
        else:
            self.selection_var.set("No card selected.")

        self._update_player_badges()

    # ------------------------------------------------------------------
    # Shortcut registration
    # ------------------------------------------------------------------
    def _setup_shortcuts(self) -> None:
        super()._setup_shortcuts()
        if not TKINTER_AVAILABLE:  # pragma: no cover - defensive
            return
        self.register_shortcut("s", self.on_draw_from_stock, "Draw from stock")
        self.register_shortcut("d", self.on_draw_from_discard, "Draw from discard")
        self.register_shortcut("k", self.on_knock, "Knock or declare gin")
        self.register_shortcut("g", self.on_knock, "Knock or declare gin")

    # ------------------------------------------------------------------
    # Game control logic
    # ------------------------------------------------------------------
    def start_next_round(self) -> None:
        if self.game.is_game_over():
            self.status_var.set("Game over. Close the window to exit.")
            return

        self.round_number += 1
        self.round_over = False
        self.selected_card = None
        self.phase = "waiting"
        self.game.deal_cards()
        self.log_index = 0

        self.log_message(
            self.log_widget,
            f"--- Round {self.round_number} begins. Dealer: {self.players[self.game.dealer_idx].name} ---",
        )
        if self.game.discard_pile:
            self.log_message(
                self.log_widget,
                f"Opening upcard: {self.game.discard_pile[-1]}",
            )

        self._prepare_next_action()
        self.update_display()
        self._update_controls()
        self._process_ai_turns()

    def on_take_initial_upcard(self) -> None:
        if self.round_over or not self.game.initial_upcard_phase:
            return
        if not self.game.can_take_initial_upcard(0):
            self.status_var.set("You cannot take the upcard right now.")
            return
        card = self.game.take_initial_upcard(0)
        self._flush_turn_log()
        self.players[0].hand.sort(key=lambda c: (c.suit.value, c.value))
        self.phase = "discard"
        self.status_var.set(f"You take {card}. Select a different card to discard or knock.")
        self.update_display()
        self._update_controls()

    def on_pass_initial_upcard(self) -> None:
        if self.round_over or not self.game.initial_upcard_phase:
            return
        if not self.game.can_take_initial_upcard(0):
            self.status_var.set("It is not your turn to act on the upcard.")
            return
        self.game.pass_initial_upcard(0)
        self._flush_turn_log()
        self._prepare_next_action(override_message="Waiting for opponent's decision...")
        self.update_display()
        self._update_controls()
        self._process_ai_turns()

    def on_draw_from_stock(self) -> None:
        if self.round_over or self.phase != "draw":
            return
        card = self.game.draw_from_stock()
        self.players[0].hand.append(card)
        self.players[0].hand.sort(key=lambda c: (c.suit.value, c.value))
        self._flush_turn_log()
        self.phase = "discard"
        self.status_var.set(f"You draw {card} from the stock.")
        self.update_display()
        self._update_controls()

    def on_draw_from_discard(self) -> None:
        if self.round_over or self.phase != "draw":
            return
        if not self.game.discard_pile or not self.game.can_draw_from_discard(0):
            self.status_var.set("You cannot draw from the discard pile right now.")
            return
        card = self.game.draw_from_discard()
        self.players[0].hand.append(card)
        self.players[0].hand.sort(key=lambda c: (c.suit.value, c.value))
        self._flush_turn_log()
        self.phase = "discard"
        self.status_var.set(f"You take {card} from the discard pile. Choose a discard or knock.")
        self.update_display()
        self._update_controls()

    def on_select_card(self, card: Card) -> None:
        if self.phase != "discard" or self.round_over:
            return
        if self.selected_card == card:
            self.selected_card = None
        else:
            self.selected_card = card
        self.update_display()
        self._update_controls()

    def on_discard(self) -> None:
        if self.round_over or self.phase != "discard":
            return
        if not self.selected_card:
            self.status_var.set("Select a card to discard first.")
            return
        try:
            self.game.discard(0, self.selected_card)
        except ValueError as exc:
            self.status_var.set(str(exc))
            return
        self.players[0].hand.sort(key=lambda c: (c.suit.value, c.value))
        discarded = self.selected_card
        self.selected_card = None
        self._flush_turn_log()
        self._prepare_next_action(override_message=f"You discard {discarded}. Waiting for opponent...")
        self.update_display()
        self._update_controls()
        self._process_ai_turns()

    def on_knock(self) -> None:
        if self.round_over or self.phase != "discard":
            return
        analysis = self.game.analyze_hand(self.players[0].hand)
        if analysis.deadwood_total > 10:
            self.status_var.set("You need 10 or fewer deadwood points to knock.")
            return
        if analysis.deadwood_total == 0:
            self.log_message(self.log_widget, f"{self.players[0].name} declares GIN!")
        else:
            self.log_message(
                self.log_widget,
                f"{self.players[0].name} knocks with {analysis.deadwood_total} deadwood.",
            )
        self._finish_round(knocker_idx=0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _render_hand(self) -> None:
        for widget in self.hand_container.winfo_children():
            widget.destroy()

        theme = self.current_theme
        for card in sorted(self.players[0].hand, key=lambda c: (c.suit.value, c.value)):
            btn = tk.Button(
                self.hand_container,
                text=str(card),
                width=4,
                command=lambda c=card: self.on_select_card(c),
                bg=theme.colors.button_bg,
                fg=theme.colors.button_fg,
                relief="sunken" if card == self.selected_card else theme.button_relief,
                padx=6,
                pady=6,
            )
            if card == self.selected_card:
                btn.configure(bg=theme.colors.highlight, fg=theme.colors.foreground)
            btn.pack(side=tk.LEFT, padx=3, pady=3)

    def _update_meld_display(self, analysis: HandAnalysis) -> None:
        if analysis.melds:
            meld_lines = "\n".join(_format_meld(meld) for meld in analysis.melds)
            self.melds_var.set(meld_lines)
        else:
            self.melds_var.set("No melds detected yet.")

        if analysis.deadwood_cards:
            self.deadwood_cards_var.set(f"Deadwood cards: {format_cards(analysis.deadwood_cards)}")
        else:
            self.deadwood_cards_var.set("No deadwood cards!")

    def _update_player_badges(self) -> None:
        for idx, badge in enumerate(self.player_status_labels):
            text = "Waiting"
            bg = self.current_theme.colors.secondary
            fg = self.current_theme.colors.foreground

            if self.round_over:
                text = "Round Complete"
                bg = self.current_theme.colors.info
                fg = self.current_theme.colors.background
            elif self.game.initial_upcard_phase and self.game.can_take_initial_upcard(idx):
                text = "Upcard Decision"
                bg = self.current_theme.colors.warning
                fg = self.current_theme.colors.background
            elif not self.game.initial_upcard_phase and self.game.current_player_idx == idx:
                if idx == 0 and self.phase == "discard":
                    text = "Choose Discard"
                    bg = self.current_theme.colors.warning
                    fg = self.current_theme.colors.background
                elif idx == 0 and self.phase == "draw":
                    text = "Draw Now"
                    bg = self.current_theme.colors.warning
                    fg = self.current_theme.colors.background
                else:
                    text = "Active Turn"
                    bg = self.current_theme.colors.primary
                    fg = self.current_theme.colors.background

            badge.configure(text=text, bg=bg, fg=fg)

    def _prepare_next_action(self, *, override_message: Optional[str] = None) -> None:
        if self.round_over:
            message = "Round complete. Review the summary and start the next round."
            if self.game.is_game_over():
                winner = self.game.get_winner()
                message = f"Game over! {winner.name} wins with {winner.score} points."
            self.phase = "round-complete"
        elif self.game.initial_upcard_phase:
            if self.game.can_take_initial_upcard(0):
                top_card = self.game.discard_pile[-1] if self.game.discard_pile else "the upcard"
                message = f"Opening upcard {top_card}: take it or pass."
                self.phase = "initial-offer"
            else:
                message = "Waiting for opponent's decision..."
                self.phase = "waiting"
        else:
            if self.game.current_player_idx == 0:
                if self.game.current_turn_draw is None:
                    message = "Draw from the stock or the discard pile."
                    self.phase = "draw"
                else:
                    message = "Select a discard or declare knock/gin."
                    self.phase = "discard"
            else:
                message = "Waiting for opponent..."
                self.phase = "waiting"

        if override_message is not None:
            message = override_message
        self.status_var.set(message)

    def _flush_turn_log(self) -> None:
        while self.log_index < len(self.game.turn_log):
            entry = self.game.turn_log[self.log_index]
            self.log_message(self.log_widget, entry)
            self.log_index += 1

    def _execute_ai_turn(self, player_idx: int) -> None:
        player = self.players[player_idx]
        if self.game.current_turn_draw is None:
            top_card = self.game.discard_pile[-1] if self.game.discard_pile else None
            if top_card and self.game.can_draw_from_discard(player_idx) and self.game.should_draw_discard(player, top_card):
                card = self.game.draw_from_discard()
            else:
                card = self.game.draw_from_stock()
            player.hand.append(card)
            player.hand.sort(key=lambda c: (c.suit.value, c.value))
            self._flush_turn_log()

        analysis = self.game.analyze_hand(player.hand)
        if analysis.deadwood_total == 0:
            self.log_message(self.log_widget, f"{player.name} declares GIN!")
            self._finish_round(knocker_idx=player_idx)
            return
        if analysis.deadwood_total <= 5:
            self.log_message(
                self.log_widget,
                f"{player.name} knocks with {analysis.deadwood_total} deadwood.",
            )
            self._finish_round(knocker_idx=player_idx)
            return

        discard_card = self.game.suggest_discard(player)
        self.game.discard(player_idx, discard_card)
        player.hand.sort(key=lambda c: (c.suit.value, c.value))
        self._flush_turn_log()

    def _process_ai_turns(self) -> None:
        while not self.round_over:
            if self.game.initial_upcard_phase:
                idx = self.game.initial_offer_order[self.game.initial_offer_position]
                player = self.players[idx]
                if not player.is_ai:
                    break
                top_card = self.game.discard_pile[-1] if self.game.discard_pile else None
                if top_card and self.game.should_draw_discard(player, top_card):
                    self.game.take_initial_upcard(idx)
                    self._flush_turn_log()
                    self._execute_ai_turn(idx)
                else:
                    self.game.pass_initial_upcard(idx)
                    self._flush_turn_log()
                continue

            current_idx = self.game.current_player_idx
            if current_idx >= len(self.players) or not self.players[current_idx].is_ai:
                break
            self._execute_ai_turn(current_idx)
            if self.round_over:
                break

        self._prepare_next_action()
        self.update_display()
        self._update_controls()

    def _finish_round(self, knocker_idx: int) -> None:
        if self.round_over:
            return

        opponent_idx = (knocker_idx + 1) % len(self.players)
        knocker = self.players[knocker_idx]
        opponent = self.players[opponent_idx]

        summary = self.game.calculate_round_summary(knocker, opponent)
        self.game.record_points(summary)
        self.round_over = True
        self._flush_turn_log()

        knock_label = summary.knock_type.name.replace("_", " ").title()
        self.log_message(
            self.log_widget,
            f"Round ends: {summary.knocker} ({knock_label}).",
        )
        self.log_message(
            self.log_widget,
            "Deadwood — "
            f"{summary.knocker}: {summary.knocker_deadwood}, "
            f"{summary.opponent}: {summary.opponent_deadwood} "
            f"(was {summary.opponent_initial_deadwood}).",
        )

        if summary.melds_shown:
            self.log_message(self.log_widget, "Melds shown:")
            for meld in summary.melds_shown:
                self.log_message(self.log_widget, f"  • {_format_meld(meld)}")
        else:
            self.log_message(self.log_widget, "No melds were revealed.")

        if summary.layoff_cards:
            self.log_message(
                self.log_widget,
                f"Layoff cards: {format_cards(summary.layoff_cards)}",
            )
        else:
            self.log_message(self.log_widget, "No layoff cards were played.")

        self.log_message(self.log_widget, "Points awarded:")
        for name, points in summary.points_awarded.items():
            delta = f"+{points}" if points >= 0 else str(points)
            total = next(p.score for p in self.players if p.name == name)
            self.log_message(self.log_widget, f"  {name}: {delta} (total {total})")

        if self.game.is_game_over():
            winner = self.game.get_winner()
            self.log_message(
                self.log_widget,
                f"Game over! {winner.name} reaches {winner.score} points.",
            )

        self._prepare_next_action()
        self.update_display()
        self._update_controls()

    def _update_controls(self) -> None:
        state_initial = "normal" if (not self.round_over and self.phase == "initial-offer") else "disabled"
        self.take_upcard_button.config(state=state_initial)
        self.pass_upcard_button.config(state=state_initial)

        state_draw_stock = "normal" if (not self.round_over and self.phase == "draw") else "disabled"
        self.draw_stock_button.config(state=state_draw_stock)

        can_draw_discard = not self.round_over and self.phase == "draw" and bool(self.game.discard_pile) and self.game.can_draw_from_discard(0)
        self.draw_discard_button.config(state="normal" if can_draw_discard else "disabled")

        analysis = self.game.analyze_hand(self.players[0].hand)
        can_knock = not self.round_over and self.phase == "discard" and analysis.deadwood_total <= 10
        self.knock_button.config(state="normal" if can_knock else "disabled")
        if analysis.deadwood_total == 0:
            self.knock_button.config(text="Declare Gin")
        else:
            self.knock_button.config(text="Knock / Gin")

        can_discard = not self.round_over and self.phase == "discard" and self.selected_card is not None
        self.discard_button.config(state="normal" if can_discard else "disabled")

        next_state = "normal" if self.round_over and not self.game.is_game_over() else "disabled"
        self.next_round_button.config(state=next_state)


def run_app(*, player_name: str = "You", opponent_name: str = "AI") -> None:
    """Launch the Gin Rummy GUI application."""

    if not TKINTER_AVAILABLE:  # pragma: no cover - defensive branch
        raise RuntimeError("tkinter is not available in this environment")

    root = tk.Tk()
    players = [
        GinRummyPlayer(name=player_name, is_ai=False),
        GinRummyPlayer(name=opponent_name, is_ai=True),
    ]
    app = GinRummyGUI(root, players=players)
    app.start_next_round()
    root.mainloop()


__all__ = ["GinRummyGUI", "run_app"]
