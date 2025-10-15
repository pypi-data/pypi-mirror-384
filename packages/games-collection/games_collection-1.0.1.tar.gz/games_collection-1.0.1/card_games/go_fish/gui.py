"""Graphical interface for the Go Fish card game.

This module implements a Tkinter-based interface that visualizes the Go Fish
engine. The GUI focuses on making round progression easy to follow by providing
three dedicated areas:

* **Scoreboard** – Lists each player's remaining cards and completed books.
* **Control cluster** – Lets the active player pick an opponent and a rank via
  comboboxes before requesting cards.
* **Hand view** – Groups the current player's cards by rank and celebrates new
  books with subtle animations so achievements are noticeable without being
  distracting.

The GUI synchronizes itself with :func:`GoFishGame.get_state_summary` whenever
an action is taken to ensure the display accurately reflects the underlying
game state.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from card_games.common.cards import RANKS
from card_games.go_fish.game import GoFishGame, Player
from common.gui_base import TKINTER_AVAILABLE, BaseGUI, GUIConfig, tk, ttk

if not TKINTER_AVAILABLE:  # pragma: no cover - import guard for optional GUI
    raise RuntimeError("Tkinter is required to use the Go Fish GUI.")


@dataclass
class ScoreboardRow:
    """Container tracking widgets related to a player in the scoreboard."""

    frame: tk.Frame
    name_label: tk.Label
    cards_var: tk.StringVar
    books_var: tk.StringVar
    book_icons_var: tk.StringVar
    widgets: List[tk.Widget]


class GoFishGUI(BaseGUI):
    """Tkinter interface that visualizes and drives a :class:`GoFishGame`.

    The GUI manages layout construction, user interactions, and log updates.
    It keeps the interface synchronized with the game engine by repeatedly
    querying :func:`GoFishGame.get_state_summary` and applying the latest data
    to the widgets.
    """

    def __init__(self, root: tk.Tk, game: GoFishGame, config: Optional[GUIConfig] = None) -> None:
        """Initialize the Go Fish GUI.

        Args:
            root: The root Tkinter window hosting the GUI.
            game: The Go Fish engine to display and control.
            config: Optional GUI configuration overrides.
        """

        gui_config = config or GUIConfig(
            window_title="Card Games - Go Fish",
            window_width=1100,
            window_height=720,
            log_height=20,
            log_width=44,
            enable_animations=True,
            theme_name="light",
        )

        super().__init__(root, gui_config)

        self.game = game
        self.turn_var = tk.StringVar()
        self.deck_var = tk.StringVar()
        self.state_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Welcome to Go Fish! Select an opponent and rank to begin.")

        self.player_rows: Dict[str, ScoreboardRow] = {}
        self._deck_empty_logged = False

        self.opponent_var = tk.StringVar()
        self.rank_var = tk.StringVar()

        self.build_layout()
        self.update_display()
        self.log_message(self.log_widget, "Game initialized. Waiting for the first move...")

    def build_layout(self) -> None:
        """Build the full Go Fish interface layout."""

        bg_color = self.current_theme.colors.background
        fg_color = self.current_theme.colors.foreground

        container = tk.Frame(self.root, bg=bg_color)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=3)
        container.columnconfigure(1, weight=2)
        container.rowconfigure(3, weight=1)

        header = tk.Frame(container, bg=bg_color, pady=10)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10)
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)
        header.columnconfigure(2, weight=1)

        tk.Label(
            header,
            textvariable=self.turn_var,
            font=(self.config.font_family, self.config.font_size + 4, "bold"),
            bg=bg_color,
            fg=fg_color,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            header,
            textvariable=self.deck_var,
            font=(self.config.font_family, self.config.font_size + 2),
            bg=bg_color,
            fg=fg_color,
        ).grid(row=0, column=1, sticky="n")
        tk.Label(
            header,
            textvariable=self.state_var,
            font=(self.config.font_family, self.config.font_size + 2),
            bg=bg_color,
            fg=fg_color,
        ).grid(row=0, column=2, sticky="e")

        # Scoreboard setup
        scoreboard_frame = self.create_label_frame(container, "Scoreboard")
        scoreboard_frame.configure(bg=bg_color)
        scoreboard_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        scoreboard_frame.columnconfigure(0, weight=1)

        header_row = tk.Frame(scoreboard_frame, bg=bg_color)
        header_row.grid(row=0, column=0, sticky="ew")
        for idx, title in enumerate(["Player", "Cards", "Books", "Celebration"]):
            tk.Label(
                header_row,
                text=title,
                font=(self.config.font_family, self.config.font_size, "bold"),
                bg=bg_color,
                fg=fg_color,
                width=14 if idx == 0 else 10,
                anchor="w" if idx == 0 else "center",
            ).grid(row=0, column=idx, padx=2, pady=2, sticky="w" if idx == 0 else "nsew")

        for idx, player in enumerate(self.game.players, start=1):
            row_frame = tk.Frame(scoreboard_frame, bg=bg_color, pady=2)
            row_frame.grid(row=idx, column=0, sticky="ew")
            row_frame.columnconfigure(0, weight=1)

            name_label = tk.Label(
                row_frame,
                text=player.name,
                bg=bg_color,
                fg=fg_color,
                anchor="w",
                font=(self.config.font_family, self.config.font_size + 1, "bold"),
            )
            name_label.grid(row=0, column=0, sticky="w", padx=4)

            cards_var = tk.StringVar()
            cards_label = tk.Label(row_frame, textvariable=cards_var, bg=bg_color, fg=fg_color)
            cards_label.grid(row=0, column=1, padx=4)

            books_var = tk.StringVar()
            books_label = tk.Label(row_frame, textvariable=books_var, bg=bg_color, fg=fg_color)
            books_label.grid(row=0, column=2, padx=4)

            book_icons_var = tk.StringVar()
            book_icons_label = tk.Label(
                row_frame,
                textvariable=book_icons_var,
                bg=bg_color,
                fg="#F7B500",
                font=(self.config.font_family, self.config.font_size + 2),
            )
            book_icons_label.grid(row=0, column=3, padx=4)

            widgets = [name_label, cards_label, books_label, book_icons_label]
            self.player_rows[player.name] = ScoreboardRow(
                frame=row_frame,
                name_label=name_label,
                cards_var=cards_var,
                books_var=books_var,
                book_icons_var=book_icons_var,
                widgets=widgets,
            )

        # Controls for requesting cards
        controls_frame = self.create_label_frame(container, "Ask for Cards")
        controls_frame.configure(bg=bg_color)
        controls_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        controls_frame.columnconfigure(1, weight=1)

        tk.Label(controls_frame, text="Opponent", bg=bg_color, fg=fg_color).grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.opponent_combo = ttk.Combobox(controls_frame, textvariable=self.opponent_var, state="readonly")
        self.opponent_combo.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        tk.Label(controls_frame, text="Rank", bg=bg_color, fg=fg_color).grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.rank_combo = ttk.Combobox(controls_frame, textvariable=self.rank_var, state="readonly")
        self.rank_combo.grid(row=1, column=1, sticky="ew", padx=4, pady=4)

        self.ask_button = ttk.Button(controls_frame, text="Ask", command=self.handle_request)
        self.ask_button.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(6, 0))

        self.status_label = tk.Label(
            controls_frame,
            textvariable=self.status_var,
            wraplength=420,
            justify=tk.LEFT,
            bg=bg_color,
            fg=fg_color,
            font=(self.config.font_family, self.config.font_size - 1),
        )
        self.status_label.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=(10, 0))

        # Hand visualization
        hand_frame = self.create_label_frame(container, "Your Hand")
        hand_frame.configure(bg=bg_color)
        hand_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))
        hand_frame.columnconfigure(0, weight=1)
        hand_frame.rowconfigure(0, weight=1)

        self.hand_container = tk.Frame(hand_frame, bg=bg_color)
        self.hand_container.grid(row=0, column=0, sticky="nsew")
        self.hand_container.columnconfigure(0, weight=1)

        # Action log on the right side
        log_frame = self.create_label_frame(container, "Action Log")
        log_frame.configure(bg=bg_color)
        log_frame.grid(row=1, column=1, rowspan=3, sticky="nsew", padx=(0, 10), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_widget = self.create_log_widget(log_frame)
        self.log_widget.grid(row=0, column=0, sticky="nsew")

    def update_display(self) -> None:
        """Refresh the scoreboard, hand view, and control state."""

        summary = self.game.get_state_summary()
        self.turn_var.set(f"Turn: {summary['current_player']}")
        deck_count = summary["deck_cards"]
        deck_text = "Deck depleted" if deck_count == 0 else f"Deck: {deck_count} cards remaining"
        self.deck_var.set(deck_text)
        state_readable = summary["state"].replace("_", " ").title()
        self.state_var.set(f"State: {state_readable}")

        if deck_count == 0 and not self._deck_empty_logged:
            self.log_message(self.log_widget, "The draw pile is empty. Every card is now in someone's hand!")
            self._deck_empty_logged = True

        for info in summary["players"]:
            row = self.player_rows[info["name"]]
            row.cards_var.set(f"Cards: {info['hand_size']}")
            row.books_var.set(f"Books: {info['books']}")
            row.book_icons_var.set("⭐" * info["books"])

            font_weight = "bold" if info["name"] == summary["current_player"] else "normal"
            row.name_label.configure(font=(self.config.font_family, self.config.font_size + 1, font_weight))
            base_color = self.current_theme.colors.background
            for widget in row.widgets:
                widget.configure(bg=base_color)
            row.frame.configure(bg=base_color)

        self._render_hand(self.game.get_current_player())
        self._update_controls(summary)

    def handle_request(self) -> None:
        """Execute an ask-for-cards action using the selected controls."""

        actor = self.game.get_current_player()
        target = self.opponent_var.get()
        rank = self.rank_var.get()

        if not target or not rank:
            self.status_var.set("Select both an opponent and a rank to continue.")
            return

        result = self.game.ask_for_cards(target, rank)
        self.log_message(self.log_widget, result["message"])
        self.status_var.set(result["message"])

        self.update_display()

        if result.get("new_books", 0) > 0:
            self._celebrate_books(actor.name, result["new_books"])

        if result.get("game_over"):
            self._handle_game_over(result)

    def _update_controls(self, summary: Dict[str, Any]) -> None:
        """Synchronize combobox choices with the latest game state."""

        current_player_name = summary["current_player"]
        opponents = [info["name"] for info in summary["players"] if info["name"] != current_player_name]
        self.opponent_combo.configure(values=opponents)

        if opponents:
            if self.opponent_var.get() not in opponents:
                self.opponent_var.set(opponents[0])
        else:
            self.opponent_var.set("")

        current_player = self.game.get_current_player()
        rank_counts: Dict[str, int] = defaultdict(int)
        for card in current_player.hand:
            rank_counts[card.rank] += 1

        available_ranks = [rank for rank in RANKS if rank_counts.get(rank)]
        self.rank_combo.configure(values=available_ranks)

        if available_ranks:
            if self.rank_var.get() not in available_ranks:
                self.rank_var.set(available_ranks[0])
        else:
            self.rank_var.set("")

        disable_controls = summary["state"] != "PLAYING" or not opponents or not available_ranks
        new_state = tk.NORMAL if not disable_controls else tk.DISABLED
        self.ask_button.configure(state=new_state)
        self.opponent_combo.configure(state="readonly" if opponents else "disabled")
        self.rank_combo.configure(state="readonly" if available_ranks else "disabled")

    def _render_hand(self, player: Player) -> None:
        """Display the current player's hand grouped by rank."""

        for child in self.hand_container.winfo_children():
            child.destroy()

        bg_color = self.current_theme.colors.background
        fg_color = self.current_theme.colors.foreground

        if not player.hand:
            tk.Label(self.hand_container, text="No cards remaining.", bg=bg_color, fg=fg_color).pack(anchor="w", padx=6, pady=4)
            return

        rank_groups: Dict[str, List[str]] = defaultdict(list)
        for card in player.hand:
            rank_groups[card.rank].append(str(card))

        for rank in RANKS:
            cards = rank_groups.get(rank)
            if not cards:
                continue

            row_frame = tk.Frame(self.hand_container, bg=bg_color)
            row_frame.pack(fill="x", padx=6, pady=2)

            badge = tk.Label(
                row_frame,
                text=f"{rank} ",
                bg="#2C7A7B",
                fg="#FFFFFF",
                font=(self.config.font_family, self.config.font_size + 1, "bold"),
                width=4,
                anchor="center",
            )
            badge.pack(side=tk.LEFT, padx=(0, 8))

            cards_label = tk.Label(
                row_frame,
                text="  ".join(cards),
                bg=bg_color,
                fg=fg_color,
                font=("Courier New", self.config.font_size + 1),
                anchor="w",
            )
            cards_label.pack(side=tk.LEFT)

            count_label = tk.Label(
                row_frame,
                text=f"×{len(cards)}",
                bg=bg_color,
                fg="#4A5568",
                font=(self.config.font_family, self.config.font_size),
            )
            count_label.pack(side=tk.RIGHT, padx=(8, 0))

    def _celebrate_books(self, player_name: str, new_books: int) -> None:
        """Animate a short celebration when a player forms new books."""

        row = self.player_rows.get(player_name)
        if not row:
            return

        self.status_var.set(f"{player_name} completed {new_books} new book(s)! 🎉")

        highlight_color = "#FDE68A"
        base_color = self.current_theme.colors.background

        def flash(remaining: int) -> None:
            if remaining <= 0:
                for widget in row.widgets:
                    widget.configure(bg=base_color)
                row.frame.configure(bg=base_color)
                return

            color = highlight_color if remaining % 2 else base_color
            for widget in row.widgets:
                widget.configure(bg=color)
            row.frame.configure(bg=color)
            self.root.after(180, lambda: flash(remaining - 1))

        flash(8 if self.config.enable_animations else 1)

    def _handle_game_over(self, result: Dict[str, Any]) -> None:
        """Disable inputs and report the winner when the game concludes."""

        summary = self.game.get_state_summary()
        winner = result.get("winner", "")
        final_books = {info["name"]: info["books"] for info in summary["players"]}

        standings = ", ".join(f"{name}: {books} books" for name, books in sorted(final_books.items(), key=lambda item: item[1], reverse=True))
        message = f"Game over! {winner} wins. Final books – {standings}."
        self.status_var.set(message)
        self.log_message(self.log_widget, message)

        self.ask_button.configure(state=tk.DISABLED)
        self.opponent_combo.configure(state="disabled")
        self.rank_combo.configure(state="disabled")
