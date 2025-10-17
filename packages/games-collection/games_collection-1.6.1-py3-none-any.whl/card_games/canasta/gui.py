"""Tkinter interface for the Canasta game engine."""

from __future__ import annotations

from typing import Optional

from card_games.canasta.game import CanastaGame, CanastaPlayer, DrawSource, MeldError, card_point_value
from card_games.common.soundscapes import initialize_game_soundscape
from common.gui_base import TKINTER_AVAILABLE, BaseGUI, GUIConfig

if TKINTER_AVAILABLE:  # pragma: no cover - UI specific branch
    import tkinter as tk
    from tkinter import messagebox
else:  # pragma: no cover - fallback when Tk is unavailable
    tk = None  # type: ignore
    messagebox = None  # type: ignore


class CanastaGUI(BaseGUI):
    """Simple Tkinter front-end supporting draw, meld, and discard actions."""

    def __init__(
        self,
        root: tk.Tk,
        *,
        game: Optional[CanastaGame] = None,
        enable_sounds: bool = True,
        config: Optional[GUIConfig] = None,
    ) -> None:
        if not TKINTER_AVAILABLE:  # pragma: no cover - defensive guard
            raise RuntimeError("tkinter is required to launch the Canasta GUI")

        config = config or GUIConfig(
            window_title="Card Games - Canasta",
            window_width=960,
            window_height=720,
            log_height=12,
            log_width=90,
            theme_name="ocean",
            enable_animations=True,
            enable_sounds=enable_sounds,
        )

        self.game = game or CanastaGame()
        self.human_index = next((idx for idx, player in enumerate(self.game.players) if not player.is_ai), 0)
        self.phase: str = "draw"

        super().__init__(root, config)
        self.sound_manager = initialize_game_soundscape(
            "canasta",
            module_file=__file__,
            enable_sounds=config.enable_sounds,
            existing_manager=self.sound_manager,
        )

        self.status_var = tk.StringVar(value="Click 'Draw Stock' to begin your turn.")
        self.discard_var = tk.StringVar(value="Discard pile: —")
        self.stock_var = tk.StringVar(value="Stock: —")
        self.team_score_vars = [tk.StringVar(value="Score: 0") for _ in self.game.teams]
        self.requirement_vars = [tk.StringVar(value="Requirement unmet") for _ in self.game.teams]

        self.hand_listbox: tk.Listbox
        self.melds_listbox: tk.Listbox
        self.log_widget = self.create_log_widget(self.root)

        self.build_layout()
        self.update_display()

    def build_layout(self) -> None:
        """Construct the Tk widgets for the interface."""

        theme = self.current_theme
        main_frame = tk.Frame(self.root, bg=theme.colors.background)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        header = tk.Frame(main_frame, bg=theme.colors.background)
        header.pack(fill=tk.X)
        self.status_label = tk.Label(
            header,
            textvariable=self.status_var,
            bg=theme.colors.background,
            fg=theme.colors.info,
            font=(theme.font_family, theme.font_size + 2, "bold"),
        )
        self.status_label.pack(anchor=tk.W)

        piles_frame = tk.Frame(main_frame, bg=theme.colors.background)
        piles_frame.pack(fill=tk.X, pady=(8, 8))
        tk.Label(
            piles_frame,
            textvariable=self.discard_var,
            bg=theme.colors.background,
            fg=theme.colors.foreground,
        ).pack(side=tk.LEFT, padx=(0, 20))
        tk.Label(
            piles_frame,
            textvariable=self.stock_var,
            bg=theme.colors.background,
            fg=theme.colors.foreground,
        ).pack(side=tk.LEFT)

        score_frame = tk.Frame(main_frame, bg=theme.colors.background)
        score_frame.pack(fill=tk.X, pady=(8, 12))
        for idx, team in enumerate(self.game.teams):
            panel = self.create_label_frame(score_frame, team.name)
            panel.configure(bg=theme.colors.background)
            panel.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=6)
            tk.Label(
                panel,
                textvariable=self.team_score_vars[idx],
                bg=theme.colors.background,
                fg=theme.colors.foreground,
                font=(theme.font_family, theme.font_size + 1),
            ).pack(anchor=tk.W)
            tk.Label(
                panel,
                textvariable=self.requirement_vars[idx],
                bg=theme.colors.background,
                fg=theme.colors.secondary,
                font=(theme.font_family, theme.font_size - 1),
            ).pack(anchor=tk.W, pady=(2, 0))

        body = tk.Frame(main_frame, bg=theme.colors.background)
        body.pack(fill=tk.BOTH, expand=True)

        hand_frame = self.create_label_frame(body, "Your Hand")
        hand_frame.configure(bg=theme.colors.background)
        hand_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))
        self.hand_listbox = tk.Listbox(hand_frame, selectmode=tk.MULTIPLE, height=18)
        self.hand_listbox.pack(fill=tk.BOTH, expand=True)

        meld_frame = self.create_label_frame(body, "Team Melds")
        meld_frame.configure(bg=theme.colors.background)
        meld_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.melds_listbox = tk.Listbox(meld_frame, height=18)
        self.melds_listbox.pack(fill=tk.BOTH, expand=True)

        log_frame = self.create_label_frame(main_frame, "Round Log")
        log_frame.configure(bg=theme.colors.background)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.log_widget.pack(in_=log_frame, fill=tk.BOTH, expand=True)

        controls = tk.Frame(main_frame, bg=theme.colors.background)
        controls.pack(fill=tk.X, pady=(12, 0))
        buttons = [
            ("Draw Stock", self.draw_from_stock),
            ("Take Discard", self.draw_from_discard),
            ("Lay Meld", self.lay_selected_meld),
            ("Discard", self.discard_selected_card),
            ("Go Out", self.go_out),
            ("Next Turn", self.end_turn),
        ]
        for text, command in buttons:
            tk.Button(controls, text=text, command=command).pack(side=tk.LEFT, padx=4)

    def update_display(self) -> None:
        """Refresh dynamic widgets to match the current game state."""

        stock_remaining = self.game.deck.remaining()
        self.stock_var.set(f"Stock: {stock_remaining} cards")
        discard_text = "Discard pile: —"
        if self.game.discard_pile:
            discard_text = f"Discard pile: {self.game.discard_pile[-1]} ({len(self.game.discard_pile)} cards)"
        if self.game.discard_frozen:
            discard_text += " – frozen"
        self.discard_var.set(discard_text)

        for idx, team in enumerate(self.game.teams):
            self.team_score_vars[idx].set(f"Score: {team.score}")
            status = "Requirement met" if team.requirement_met else "Requirement unmet"
            self.requirement_vars[idx].set(status)

        self._refresh_hand()
        self._refresh_melds()
        self.animate_highlight(self.hand_listbox)
        self.animate_highlight(self.melds_listbox)

    def _set_status(self, text: str, *, highlight_color: str = "#2f8f9d") -> None:
        """Update and animate the status banner when messaging the player."""

        self.status_var.set(text)
        self.animate_highlight(self.status_label, highlight_color=highlight_color)

    @property
    def human_player(self) -> CanastaPlayer:
        """Return the human-controlled player."""

        return self.game.players[self.human_index]

    def _refresh_hand(self) -> None:
        """Populate the listbox with the human hand."""

        self.hand_listbox.delete(0, tk.END)
        for index, card in enumerate(self.human_player.hand, start=1):
            self.hand_listbox.insert(tk.END, f"{index:2}: {card}")

    def _refresh_melds(self) -> None:
        """Populate meld listbox with team melds."""

        self.melds_listbox.delete(0, tk.END)
        team = self.game.teams[self.human_player.team_index]
        for meld in team.melds:
            wild_label = "natural" if meld.is_natural else "mixed"
            bonus = " (canasta)" if meld.is_canasta else ""
            description = ", ".join(str(card) for card in meld.cards)
            self.melds_listbox.insert(tk.END, f"{meld.rank}s: {description} [{wild_label}{bonus}]")

    def draw_from_stock(self) -> None:
        """Draw the top card from the stock."""

        if self.phase != "draw":
            self._set_status("You must discard before drawing again.")
            return
        card = self.game.draw(self.human_player, DrawSource.STOCK)
        self._set_status(f"You drew {card} from the stock.")
        self.log_message(self.log_widget, f"Player drew {card} from stock.")
        self.phase = "meld"
        self.update_display()

    def draw_from_discard(self) -> None:
        """Attempt to take the discard pile."""

        if self.phase != "draw":
            self._set_status("Drawing is only allowed at the start of your turn.")
            return
        if not self.game.can_take_discard(self.human_player):
            self._set_status("Discard pile cannot be taken at this time.")
            return
        card = self.game.draw(self.human_player, DrawSource.DISCARD)
        self._set_status(f"You took the discard pile; top card was {card}.")
        self.log_message(self.log_widget, "Discard pile collected.")
        self.phase = "meld"
        self.update_display()

    def lay_selected_meld(self) -> None:
        """Lay down the selected cards as a meld."""

        if self.phase not in {"meld", "discard"}:
            self._set_status("Draw a card before melding.")
            return
        selection = self.hand_listbox.curselection()
        if not selection:
            self._set_status("Select cards to meld.")
            return
        indices = [int(index) for index in selection]
        cards = [self.human_player.hand[index] for index in indices]
        try:
            meld = self.game.add_meld(self.human_player, cards)
        except MeldError as exc:
            self._set_status(str(exc), highlight_color="#bf3f5f")
            return
        self._set_status(f"Meld laid: {', '.join(str(card) for card in meld.cards)}")
        self.log_message(self.log_widget, f"Meld laid worth {sum(card_point_value(card) for card in meld.cards)} points.")
        self.phase = "discard"
        self.update_display()

    def discard_selected_card(self) -> None:
        """Discard the highlighted card."""

        if self.phase == "draw":
            self._set_status("Draw before discarding.")
            return
        selection = self.hand_listbox.curselection()
        if not selection:
            self._set_status("Select a card to discard.")
            return
        card_index = int(selection[0])
        card = self.human_player.hand[card_index]
        self.game.discard(self.human_player, card)
        self._set_status(f"Discarded {card}.")
        self.log_message(self.log_widget, f"Player discarded {card}.")
        self.phase = "draw"
        self._complete_ai_cycle()
        self.update_display()

    def end_turn(self) -> None:
        """Pass control to the next player without discarding."""

        if self.phase != "draw":
            self._set_status("Discard before ending your turn.")
            return
        self._complete_ai_cycle()
        self.update_display()

    def go_out(self) -> None:
        """Attempt to end the round."""

        if not self.game.can_go_out(self.human_player.team_index):
            self._set_status("Cannot go out yet; ensure you have a canasta and empty hands.")
            return
        breakdown = self.game.go_out(self.human_player)
        messagebox.showinfo("Round Complete", "Round ended. Scores updated.")
        self._summarise_round(breakdown)
        self.update_display()

    def _complete_ai_cycle(self) -> None:
        """Allow AI players to act until the human turn resumes."""

        while not self.game.round_over:
            self.game.advance_turn()
            if self.game.current_player_index == self.human_index:
                break
            player = self.game.players[self.game.current_player_index]
            drawn = self.game.draw(player, DrawSource.STOCK)
            discard_card = player.hand[0]
            self.game.discard(player, discard_card)
            self.log_message(
                self.log_widget,
                f"{player.name} drew {drawn} and discarded {discard_card}.",
            )
        if self.game.round_over:
            self._set_status("Round complete.")

    def _summarise_round(self, breakdown: dict[int, int]) -> None:
        """Log the scoring summary after going out."""

        for team_index, delta in breakdown.items():
            team = self.game.teams[team_index]
            self.log_message(
                self.log_widget,
                f"{team.name} delta {delta}, total {team.score}.",
            )


__all__ = ["CanastaGUI"]
