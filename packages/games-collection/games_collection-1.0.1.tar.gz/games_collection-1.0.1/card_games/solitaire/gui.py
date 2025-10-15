"""Graphical interface for the Klondike Solitaire game.

This module provides a Tkinter-powered interface that visualises the
``SolitaireGame`` engine on a classic tableau. The GUI renders all public
elements (stock, waste, tableau columns, and foundations), exposes the same
actions as the CLI, and keeps the scoreboard synchronised with the engine's
``get_state_summary`` data.

Key features implemented here:

* Toolbar with draw, auto-play, recycle, and new game actions.
* Click-selection workflow that highlights legal drop targets before applying
  the move through the game engine.
* Canvas rendering for piles to keep the interface responsive and pleasant on
  varying window sizes.
* Status and scoreboard widgets that continuously reflect score, moves, and
  recycle usage.
"""

from __future__ import annotations

import random
from typing import Callable, Optional, Tuple

try:
    import tkinter as tk
except ImportError:  # pragma: no cover - handled gracefully by run_app()
    tk = None  # type: ignore

from card_games.common.cards import Card
from card_games.common.gui_base import TKINTER_AVAILABLE, BaseGUI, GUIConfig
from card_games.solitaire.game import Pile, SolitaireGame

CARD_WIDTH = 90
CARD_HEIGHT = 120
FACE_DOWN_HEIGHT = 42
FACE_DOWN_SPACING = 18
FACE_UP_SPACING = 32


SelectedSource = Tuple[str, int, int]
TargetKey = Tuple[str, int]


class SolitaireGUI(BaseGUI):
    """Interactive GUI front-end for the ``SolitaireGame`` engine."""

    def __init__(
        self,
        root: tk.Tk,
        game: SolitaireGame,
        *,
        config: Optional[GUIConfig] = None,
        new_game_factory: Optional[Callable[[], SolitaireGame]] = None,
    ) -> None:
        if not TKINTER_AVAILABLE:
            raise RuntimeError("Tkinter is not available on this system.")

        gui_config = config or GUIConfig(
            window_title="Klondike Solitaire",
            window_width=1100,
            window_height=760,
        )

        super().__init__(root, gui_config)
        self.game = game
        self._new_game_factory = new_game_factory

        # GUI state
        self.selected_source: Optional[SelectedSource] = None
        self.legal_targets: set[TargetKey] = set()

        # Tk variables for dynamic labels
        self.status_var = tk.StringVar(value="Welcome to Klondike Solitaire!")
        self.score_var = tk.StringVar()
        self.moves_var = tk.StringVar()
        self.recycle_var = tk.StringVar()
        self.draw_mode_var = tk.StringVar()

        # Rendering containers populated in build_layout()
        self.main_frame: Optional[tk.Frame] = None
        self.stock_frame: Optional[tk.Frame] = None
        self.waste_frame: Optional[tk.Frame] = None
        self.stock_canvas: Optional[tk.Canvas] = None
        self.waste_canvas: Optional[tk.Canvas] = None
        self.foundation_frames: list[tk.Frame] = []
        self.foundation_canvases: list[tk.Canvas] = []
        self.tableau_frames: list[tk.Frame] = []
        self.tableau_canvases: list[tk.Canvas] = []
        self.tableau_card_positions: list[list[Tuple[float, float, int]]] = []

        colors = self.current_theme.colors
        self._default_border = colors.border or "#CCCCCC"
        self._target_border = colors.highlight or colors.primary or "#FFD700"
        self._selection_border = colors.primary or "#007BFF"
        self._card_face_color = "#FFFFFF"
        self._card_back_color = "#1e3a5f"
        self._card_back_accent = "#f7b733"

        self.build_layout()
        self.update_display()

    # ------------------------------------------------------------------
    # Layout & rendering helpers
    # ------------------------------------------------------------------
    def build_layout(self) -> None:
        """Build the main layout for the Solitaire board."""

        bg = self.current_theme.colors.background
        canvas_bg = self.current_theme.colors.canvas_bg

        self.main_frame = tk.Frame(self.root, bg=bg)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)

        header = tk.Frame(self.main_frame, bg=bg)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header.columnconfigure(1, weight=1)

        title_label = tk.Label(
            header,
            text="Klondike Solitaire",
            font=(self.config.font_family, self.config.font_size + 10, "bold"),
            bg=bg,
        )
        title_label.grid(row=0, column=0, sticky="w")

        toolbar = tk.Frame(header, bg=bg)
        toolbar.grid(row=0, column=1, sticky="e")

        button_specs = [
            ("Draw", self.handle_draw),
            ("Auto", self.handle_auto),
            ("Reset", self.handle_reset),
            ("New Game", self.handle_new_game),
        ]

        for i, (label, command) in enumerate(button_specs):
            btn = tk.Button(
                toolbar,
                text=label,
                command=command,
                padx=12,
                pady=6,
            )
            btn.grid(row=0, column=i, padx=4)

        scoreboard = tk.Frame(self.main_frame, bg=bg)
        scoreboard.grid(row=1, column=0, sticky="ew", padx=16, pady=(8, 12))

        stats = [
            ("Score", self.score_var),
            ("Moves", self.moves_var),
            ("Recycles", self.recycle_var),
            ("Draw Mode", self.draw_mode_var),
        ]

        for idx, (label, variable) in enumerate(stats):
            frame = tk.Frame(scoreboard, bg=bg)
            frame.grid(row=0, column=idx, padx=10)
            tk.Label(
                frame,
                text=label,
                font=(self.config.font_family, self.config.font_size - 1, "bold"),
                bg=bg,
            ).pack(anchor="w")
            tk.Label(
                frame,
                textvariable=variable,
                font=(self.config.font_family, self.config.font_size + 2),
                bg=bg,
            ).pack(anchor="w")

        board_frame = tk.Frame(self.main_frame, bg=bg)
        board_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(8, 16))
        board_frame.rowconfigure(1, weight=1)
        board_frame.columnconfigure(0, weight=1)

        top_row = tk.Frame(board_frame, bg=bg)
        top_row.grid(row=0, column=0, sticky="ew")
        top_row.columnconfigure(1, weight=1)

        piles_left = tk.Frame(top_row, bg=bg)
        piles_left.grid(row=0, column=0, sticky="w", padx=(0, 40))

        self.stock_frame = self._create_pile_frame(piles_left, canvas_bg)
        self.stock_frame.grid(row=0, column=0, padx=8)
        self.stock_canvas = tk.Canvas(
            self.stock_frame,
            width=CARD_WIDTH + 20,
            height=CARD_HEIGHT + 20,
            bg=canvas_bg,
            highlightthickness=0,
        )
        self.stock_canvas.pack()
        self.stock_canvas.bind("<Button-1>", lambda _event: self.handle_draw())

        self.waste_frame = self._create_pile_frame(piles_left, canvas_bg)
        self.waste_frame.grid(row=0, column=1, padx=8)
        self.waste_canvas = tk.Canvas(
            self.waste_frame,
            width=CARD_WIDTH + 20,
            height=CARD_HEIGHT + 20,
            bg=canvas_bg,
            highlightthickness=0,
        )
        self.waste_canvas.pack()
        self.waste_canvas.bind("<Button-1>", lambda event: self._on_waste_click(event))

        foundation_area = tk.Frame(top_row, bg=bg)
        foundation_area.grid(row=0, column=2, sticky="e")

        for i in range(4):
            frame = self._create_pile_frame(foundation_area, canvas_bg)
            frame.grid(row=0, column=i, padx=8)
            canvas = tk.Canvas(
                frame,
                width=CARD_WIDTH + 20,
                height=CARD_HEIGHT + 20,
                bg=canvas_bg,
                highlightthickness=0,
            )
            canvas.pack()
            canvas.bind("<Button-1>", lambda event, idx=i: self._on_foundation_click(idx))
            self.foundation_frames.append(frame)
            self.foundation_canvases.append(canvas)

        tableau_area = tk.Frame(board_frame, bg=bg)
        tableau_area.grid(row=1, column=0, sticky="nsew", pady=(20, 0))

        for i in range(7):
            frame = self._create_pile_frame(tableau_area, canvas_bg)
            frame.grid(row=0, column=i, padx=8, sticky="ns")
            canvas = tk.Canvas(
                frame,
                width=CARD_WIDTH + 20,
                height=540,
                bg=canvas_bg,
                highlightthickness=0,
            )
            canvas.pack(fill="both", expand=True)
            canvas.bind("<Button-1>", lambda event, idx=i: self._on_tableau_click(idx, event))
            self.tableau_frames.append(frame)
            self.tableau_canvases.append(canvas)
            self.tableau_card_positions.append([])

        status_bar = tk.Frame(self.main_frame, bg=bg)
        status_bar.grid(row=3, column=0, sticky="ew", padx=16, pady=(4, 12))
        tk.Label(
            status_bar,
            textvariable=self.status_var,
            anchor="w",
            justify="left",
            bg=bg,
            font=(self.config.font_family, self.config.font_size - 1),
        ).pack(fill="x")

        self.register_shortcut("<space>", self.handle_draw, "Draw from stock")
        self.register_shortcut("<KeyPress-a>", self.handle_auto, "Auto move to foundation")
        self.register_shortcut("<KeyPress-r>", self.handle_reset, "Recycle waste onto stock")

    def update_display(self) -> None:
        """Refresh the GUI components based on the current game state."""

        summary = self.game.get_state_summary()
        self.score_var.set(str(summary["score"]))
        self.moves_var.set(f"{summary['moves_made']} (auto: {summary['auto_moves']})")

        if summary["recycles_remaining"] is None:
            recycle_text = f"{summary['recycles_used']} used"
        else:
            recycle_text = f"{summary['recycles_used']} / {summary['recycles_remaining']}"
        self.recycle_var.set(recycle_text)
        self.draw_mode_var.set(f"Draw {summary['draw_count']}")

        self._draw_stock()
        self._draw_waste()
        self._draw_foundations()
        self._draw_tableau()
        self._apply_highlights()

        if self.game.is_won():
            self.status_var.set("🎉 You won! Move cards to foundations to play again or start a new game.")

    # ------------------------------------------------------------------
    # Rendering primitives
    # ------------------------------------------------------------------
    def _draw_stock(self) -> None:
        if not self.stock_canvas:
            return
        canvas = self.stock_canvas
        canvas.delete("all")
        count = len(self.game.stock.cards)
        if count:
            canvas.create_rectangle(
                10,
                10,
                10 + CARD_WIDTH,
                10 + CARD_HEIGHT,
                fill=self._card_back_color,
                outline=self._card_back_accent,
                width=3,
            )
            canvas.create_text(
                10 + CARD_WIDTH / 2,
                10 + CARD_HEIGHT / 2,
                text=str(count),
                font=(self.config.font_family, self.config.font_size + 8, "bold"),
                fill="white",
            )
        else:
            canvas.create_rectangle(
                10,
                10,
                10 + CARD_WIDTH,
                10 + CARD_HEIGHT,
                outline=self._card_back_accent,
                dash=(5, 3),
                width=2,
            )
            canvas.create_text(
                10 + CARD_WIDTH / 2,
                10 + CARD_HEIGHT / 2,
                text="Empty",
                font=(self.config.font_family, self.config.font_size),
            )

    def _draw_waste(self) -> None:
        if not self.waste_canvas:
            return
        canvas = self.waste_canvas
        canvas.delete("all")

        if not self.game.waste.cards:
            canvas.create_rectangle(
                10,
                10,
                10 + CARD_WIDTH,
                10 + CARD_HEIGHT,
                outline=self._card_back_accent,
                dash=(5, 3),
                width=2,
            )
            canvas.create_text(
                10 + CARD_WIDTH / 2,
                10 + CARD_HEIGHT / 2,
                text="Waste",
                font=(self.config.font_family, self.config.font_size),
            )
            return

        card = self.game.waste.cards[-1]
        self._draw_face_up_card(canvas, card)

    def _draw_foundations(self) -> None:
        for idx, canvas in enumerate(self.foundation_canvases):
            canvas.delete("all")
            pile = self.game.foundations[idx]
            top = pile.top_card()
            if top:
                self._draw_face_up_card(canvas, top)
                canvas.create_text(
                    10 + CARD_WIDTH / 2,
                    10 + CARD_HEIGHT + 12,
                    text=f"{len(pile.cards)} cards",
                    font=(self.config.font_family, self.config.font_size - 1),
                )
            else:
                canvas.create_rectangle(
                    10,
                    10,
                    10 + CARD_WIDTH,
                    10 + CARD_HEIGHT,
                    outline=self._card_back_accent,
                    dash=(5, 3),
                    width=2,
                )
                canvas.create_text(
                    10 + CARD_WIDTH / 2,
                    10 + CARD_HEIGHT / 2,
                    text="Foundation",
                    font=(self.config.font_family, self.config.font_size - 1),
                )

    def _draw_tableau(self) -> None:
        for idx, canvas in enumerate(self.tableau_canvases):
            canvas.delete("all")
            pile = self.game.tableau[idx]
            positions: list[Tuple[float, float, int]] = []
            y = 12
            face_up_start = len(pile.cards) - pile.face_up_count
            if face_up_start < 0:
                face_up_start = 0

            for card_index, card in enumerate(pile.cards):
                is_face_up = card_index >= face_up_start
                height = CARD_HEIGHT if is_face_up else FACE_DOWN_HEIGHT
                if is_face_up:
                    self._draw_face_up_card(canvas, card, y=y, height=height)
                else:
                    canvas.create_rectangle(
                        10,
                        y,
                        10 + CARD_WIDTH,
                        y + height,
                        fill=self._card_back_color,
                        outline=self._card_back_accent,
                        width=2,
                    )
                positions.append((y, y + height, card_index))
                y += FACE_UP_SPACING if is_face_up else FACE_DOWN_SPACING

            if not pile.cards:
                canvas.create_rectangle(
                    10,
                    y,
                    10 + CARD_WIDTH,
                    y + CARD_HEIGHT,
                    outline=self._card_back_accent,
                    dash=(5, 3),
                    width=2,
                )
                positions.clear()

            self.tableau_card_positions[idx] = positions

    def _draw_face_up_card(self, canvas: tk.Canvas, card: Card, *, y: float = 10, height: float = CARD_HEIGHT) -> None:
        canvas.create_rectangle(
            10,
            y,
            10 + CARD_WIDTH,
            y + height,
            fill=self._card_face_color,
            outline=self._card_back_accent,
            width=2,
        )
        canvas.create_text(
            22,
            y + 20,
            anchor="w",
            text=str(card),
            font=(self.config.font_family, self.config.font_size + 6, "bold"),
            fill="#D32F2F" if card.suit.name in {"HEARTS", "DIAMONDS"} else "#1B1B1B",
        )

    def _create_pile_frame(self, parent: tk.Widget, bg: str) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=bg,
            highlightbackground=self._default_border,
            highlightcolor=self._default_border,
            highlightthickness=2,
            bd=0,
            padx=4,
            pady=4,
        )

    # ------------------------------------------------------------------
    # Event handling & move logic
    # ------------------------------------------------------------------
    def handle_draw(self) -> None:
        """Draw cards from the stock, updating status accordingly."""

        if self.game.draw_from_stock():
            self._set_status("Drew from the stock pile.")
        else:
            if self.game.can_reset_stock():
                self._set_status("Stock is empty—use Reset to recycle the waste.")
            else:
                self._set_status("No cards left to draw.")
        self.clear_selection()
        self.update_display()

    def handle_reset(self) -> None:
        """Recycle the waste back into the stock."""

        if self.game.reset_stock():
            self._set_status("Recycled the waste pile onto the stock.")
        else:
            self._set_status("Cannot reset the stock right now.")
        self.clear_selection()
        self.update_display()

    def handle_auto(self) -> None:
        """Trigger automatic moves to the foundations."""

        if self.game.auto_move_to_foundation():
            self._set_status("Moved all available cards to the foundations.")
        else:
            self._set_status("No automatic foundation moves available.")
        self.clear_selection()
        self.update_display()

    def handle_new_game(self) -> None:
        """Start a fresh game using the provided factory."""

        if not self._new_game_factory:
            self._set_status("New game factory not provided.")
            return
        self.game = self._new_game_factory()
        self.clear_selection()
        self._set_status("Dealt a new game. Good luck!")
        self.update_display()

    def _on_waste_click(self, _event: tk.Event) -> None:
        if self.selected_source and self.selected_source[0] == "waste":
            self.clear_selection()
            return
        if not self.game.waste.cards:
            self._set_status("Waste pile is empty.")
            self.clear_selection()
            self.update_display()
            return
        self._set_selection(("waste", 0, 1))

    def _on_foundation_click(self, index: int) -> None:
        if self.selected_source and ("foundation", index) in self.legal_targets:
            if self._execute_move(("foundation", index)):
                return

        pile = self.game.foundations[index]
        if not pile.cards:
            self._set_status("Foundation is empty.")
            return
        if self.game.scoring_mode == "vegas":
            self._set_status("Vegas scoring does not allow moving cards off foundations.")
            return
        self._set_selection(("foundation", index, 1))

    def _on_tableau_click(self, index: int, event: tk.Event) -> None:
        target_key = ("tableau", index)
        if self.selected_source and target_key in self.legal_targets:
            if self._execute_move(target_key):
                return

        pile = self.game.tableau[index]
        if not pile.cards:
            self._set_status("Empty column selected." if not self.selected_source else "")
            if self.selected_source and target_key in self.legal_targets:
                self._execute_move(target_key)
            return

        positions = self.tableau_card_positions[index]
        clicked_index = self._find_card_index(event.y, positions)
        if clicked_index is None:
            self.clear_selection()
            self.update_display()
            return

        face_up_start = len(pile.cards) - pile.face_up_count
        if face_up_start < 0:
            face_up_start = 0

        if clicked_index < face_up_start:
            self._set_status("You can only move face-up cards.")
            self.clear_selection()
            self.update_display()
            return

        num_cards = len(pile.cards) - clicked_index
        self._set_selection(("tableau", index, num_cards))

    def _find_card_index(self, y: float, positions: list[Tuple[float, float, int]]) -> Optional[int]:
        for start_y, end_y, card_index in positions[::-1]:
            if start_y <= y <= end_y:
                return card_index
        if positions:
            return positions[-1][2]
        return None

    def _execute_move(self, target: TargetKey) -> bool:
        if not self.selected_source:
            return False

        source_type, source_index, num_cards = self.selected_source
        source_pile = self._get_pile(source_type, source_index)
        if source_pile is None:
            return False

        target_type, target_index = target
        moved = False
        if target_type == "foundation":
            moved = self.game.move_to_foundation(source_pile, target_index)
            if moved:
                self._set_status("Moved card to the foundation.")
        elif target_type == "tableau":
            moved = self.game.move_to_tableau(source_pile, target_index, num_cards)
            if moved:
                self._set_status(f"Moved {num_cards} card(s) to tableau column {target_index}.")

        if moved:
            self.clear_selection()
            self.update_display()
        else:
            self._set_status("That move isn't allowed.")
            self.update_display()
        return moved

    def _get_pile(self, source_type: str, index: int) -> Optional[Pile]:
        if source_type == "waste":
            return self.game.waste
        if source_type == "foundation":
            return self.game.foundations[index]
        if source_type == "tableau":
            return self.game.tableau[index]
        return None

    def _set_selection(self, selection: SelectedSource) -> None:
        if self.selected_source == selection:
            self.clear_selection()
            self.update_display()
            return
        self.selected_source = selection
        self.legal_targets = self._compute_legal_targets(selection)
        self.update_display()

    def clear_selection(self) -> None:
        """Clear the currently selected pile and target highlights."""

        self.selected_source = None
        self.legal_targets.clear()

    def _compute_legal_targets(self, selection: SelectedSource) -> set[TargetKey]:
        source_type, index, num_cards = selection
        source_pile = self._get_pile(source_type, index)
        if not source_pile:
            return set()

        targets: set[TargetKey] = set()
        top_card = source_pile.top_card()

        if source_type == "tableau":
            cards_to_move = source_pile.cards[-num_cards:]
            if not cards_to_move:
                return set()
            top_card = cards_to_move[-1]
            bottom_card = cards_to_move[0]
            for t_index, tableau_pile in enumerate(self.game.tableau):
                if t_index == index:
                    continue
                if tableau_pile.can_add_to_tableau(bottom_card):
                    targets.add(("tableau", t_index))
            if num_cards == 1 and top_card:
                for f_index, foundation in enumerate(self.game.foundations):
                    if foundation.can_add_to_foundation(top_card):
                        targets.add(("foundation", f_index))

        elif source_type == "waste":
            if top_card:
                for f_index, foundation in enumerate(self.game.foundations):
                    if foundation.can_add_to_foundation(top_card):
                        targets.add(("foundation", f_index))
                for t_index, tableau_pile in enumerate(self.game.tableau):
                    if tableau_pile.can_add_to_tableau(top_card):
                        targets.add(("tableau", t_index))

        elif source_type == "foundation":
            if top_card:
                for t_index, tableau_pile in enumerate(self.game.tableau):
                    if tableau_pile.can_add_to_tableau(top_card):
                        targets.add(("tableau", t_index))

        return targets

    def _apply_highlights(self) -> None:
        frames = []
        if self.stock_frame:
            frames.append((self.stock_frame, ("stock", 0)))
        if self.waste_frame:
            frames.append((self.waste_frame, ("waste", 0)))
        frames.extend((frame, ("foundation", idx)) for idx, frame in enumerate(self.foundation_frames))
        frames.extend((frame, ("tableau", idx)) for idx, frame in enumerate(self.tableau_frames))

        for frame, _ in frames:
            frame.configure(highlightbackground=self._default_border, highlightcolor=self._default_border)

        if self.selected_source:
            source_type, index, _ = self.selected_source
            frame = self._lookup_frame(source_type, index)
            if frame:
                frame.configure(highlightbackground=self._selection_border, highlightcolor=self._selection_border)

        for target in self.legal_targets:
            frame = self._lookup_frame(*target)
            if frame:
                frame.configure(highlightbackground=self._target_border, highlightcolor=self._target_border)

    def _lookup_frame(self, target_type: str, index: int) -> Optional[tk.Frame]:
        if target_type == "waste":
            return self.waste_frame
        if target_type == "foundation":
            return self.foundation_frames[index]
        if target_type == "tableau":
            return self.tableau_frames[index]
        if target_type == "stock":
            return self.stock_frame
        return None

    def _set_status(self, message: str) -> None:
        if message:
            self.status_var.set(message)


def run_app(
    *,
    draw_count: int = 3,
    max_recycles: Optional[int] = None,
    scoring_mode: str = "standard",
    seed: Optional[int] = None,
) -> None:
    """Launch the Solitaire GUI application."""

    if not TKINTER_AVAILABLE:
        raise RuntimeError("Tkinter is not available; install it to use the GUI.")

    def make_game() -> SolitaireGame:
        rng = random.Random(seed) if seed is not None else None
        return SolitaireGame(
            draw_count=draw_count,
            max_recycles=max_recycles,
            scoring_mode=scoring_mode,
            rng=rng,
        )

    root = tk.Tk()
    gui = SolitaireGUI(root, make_game(), new_game_factory=make_game)
    gui.update_display()
    root.mainloop()
