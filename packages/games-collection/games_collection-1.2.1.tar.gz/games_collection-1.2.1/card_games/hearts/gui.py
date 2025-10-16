"""Graphical user interface for the Hearts card game.

This module provides a Tkinter-based interface that mirrors the standard
four-seat Hearts table. The layout focuses on clarity for trick taking: the
human player sits in the south seat, opponents occupy the remaining seats, and
the current trick is displayed in the centre. The interface is split into three
primary areas:

* **Passing phase panel** – allows the human to multi-select exactly three
  cards before the round begins.
* **Trick arena** – surfaces the four played cards alongside a "hearts broken"
  indicator so players know when hearts may be led.
* **Scoreboard sidebar** – updates live with each trick, summarising scores and
  the number of penalty cards ("bags") captured so far in the round.

Accessibility is handled through :class:`~common.gui_base.GUIConfig` so that high
contrast themes and keyboard shortcuts can be toggled from the entry point. The
GUI automatically queues AI actions while validating human choices to ensure the
engine and presentation layer stay in sync.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional, Sequence

try:
    import tkinter as tk
    from tkinter import messagebox, scrolledtext, ttk
except ImportError as exc:  # pragma: no cover - Tkinter availability is environment specific
    raise RuntimeError("Tkinter is required to use the Hearts GUI") from exc

from card_games.common.cards import Card, Suit, format_cards
from card_games.common.soundscapes import initialize_game_soundscape
from common import Settings, SettingsManager
from common.gui_base import BaseGUI, GUIConfig

from .game import QUEEN_OF_SPADES, HeartsGame, HeartsPlayer, PassDirection

PhaseName = Literal["passing", "playing", "round_end"]


@dataclass
class _TrickSeat:
    """Represents the widgets bound to a table seat."""

    frame: ttk.Frame
    name_var: tk.StringVar
    card_var: tk.StringVar


class HeartsGUI(BaseGUI):
    """Tkinter GUI for a single round of Hearts."""

    def __init__(
        self,
        root: tk.Tk,
        game: HeartsGame,
        *,
        human_index: int = 0,
        enable_sounds: bool = True,
        config: Optional[GUIConfig] = None,
        settings_manager: Optional[SettingsManager] = None,
    ) -> None:
        """Create the GUI and immediately start the first round.

        Args:
            root: Tk root window.
            game: Hearts game engine instance.
            human_index: Index of the human player within ``game.players``.
            enable_sounds: Default sound playback preference when no saved settings exist.
            config: Optional configuration overriding the defaults.
            settings_manager: Optional settings manager used to persist GUI preferences.
        """
        default_config = GUIConfig(
            window_title="Hearts – Four Seat Table",
            window_width=1080,
            window_height=780,
            background_color="#0B1622",
            font_family="Segoe UI",
            font_size=12,
            log_height=12,
            log_width=70,
            enable_sounds=enable_sounds,
            enable_animations=True,
            theme_name="midnight",
            language="en",
            accessibility_mode=config.accessibility_mode if config else False,
        )
        self._preferences_namespace = "card_games.hearts.gui"
        self.settings_manager: SettingsManager = settings_manager or SettingsManager()
        self._preferences_defaults = {
            "theme": (config or default_config).theme_name,
            "enable_sounds": (config or default_config).enable_sounds,
            "enable_animations": (config or default_config).enable_animations,
        }
        self._preferences: Settings = self.settings_manager.load_settings(
            self._preferences_namespace,
            defaults=self._preferences_defaults,
        )

        active_config = config or default_config
        active_config.theme_name = str(self._preferences.get("theme", active_config.theme_name))
        active_config.enable_sounds = bool(self._preferences.get("enable_sounds", active_config.enable_sounds))
        active_config.enable_animations = bool(self._preferences.get("enable_animations", active_config.enable_animations))

        super().__init__(root, active_config)
        self.sound_manager = initialize_game_soundscape(
            "hearts",
            module_file=__file__,
            enable_sounds=self.config.enable_sounds,
            existing_manager=self.sound_manager,
        )

        self.game = game
        self.human_index = human_index
        self.phase: PhaseName = "passing"
        self.pending_passes: Dict[HeartsPlayer, Sequence[Card]] = {}
        self.pass_selection: set[Card] = set()
        self.current_player_index: Optional[int] = None
        self.table_seats: Dict[int, _TrickSeat] = {}
        self.status_var = tk.StringVar(value="Setting up table…")
        self.pass_direction_var = tk.StringVar(value="")
        self.heart_state_var = tk.StringVar(value="Hearts are unbroken")
        self.round_var = tk.StringVar(value="Round 1")
        self.shortcut_hint_var = tk.StringVar(value="Press Ctrl+H for accessibility help")

        self.log_widget: Optional[scrolledtext.ScrolledText] = None
        self.pass_button: Optional[ttk.Button] = None
        self.play_hint_label: Optional[ttk.Label] = None
        self.next_round_button: Optional[ttk.Button] = None
        self.hand_frame: Optional[ttk.Frame] = None
        self.pass_frame: Optional[ttk.LabelFrame] = None
        self.play_frame: Optional[ttk.LabelFrame] = None
        self.score_tree: Optional[ttk.Treeview] = None

        self._preferences_menu: Optional[tk.Menu] = None
        self._theme_var = tk.StringVar(value=self.config.theme_name)
        self._sound_var = tk.BooleanVar(value=self.config.enable_sounds)
        self._animation_var = tk.BooleanVar(value=self.config.enable_animations)

        self._build_layout()
        self.accessibility_manager.enable_keyboard_navigation(self.root)
        self._build_preferences_menu()
        self._start_new_round()

    # ------------------------------------------------------------------
    # BaseGUI overrides
    # ------------------------------------------------------------------
    def build_layout(self) -> None:  # pragma: no cover - structure is tested via update_display
        """Provided for ``BaseGUI`` compatibility. ``_build_layout`` performs the work."""

    def update_display(self) -> None:
        """Refresh scoreboard, trick view, and instructions based on game state."""
        self._refresh_scoreboard()
        self._update_trick_cards()
        self._update_status_banner()

    def _setup_shortcuts(self) -> None:
        """Register keyboard shortcuts for accessibility and speed play."""
        self.shortcut_manager.register(
            "<Control-n>",
            self._handle_shortcut_new_round,
            "Start the next round once scoring is complete",
        )
        self.shortcut_manager.register(
            "<Control-l>",
            self._focus_log,
            "Move focus to the action log",
        )
        self.shortcut_manager.register(
            "<Control-h>",
            self._show_accessibility_tips,
            "Show accessibility options for the Hearts table",
        )

    # ------------------------------------------------------------------
    # Layout construction helpers
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        """Construct the static layout of the application."""
        container = ttk.Frame(self.root, padding=16)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=3)
        container.columnconfigure(1, weight=2)
        container.rowconfigure(1, weight=1)

        # Header banner
        header = ttk.Frame(container)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)
        header.columnconfigure(2, weight=1)

        title = self.create_header(header, "Hearts Table")
        title.grid(row=0, column=0, sticky="w")
        round_label = ttk.Label(
            header,
            textvariable=self.round_var,
            font=(self.config.font_family, self.config.font_size + 2, "bold"),
        )
        round_label.grid(row=0, column=1, sticky="e")
        ttk.Label(header, textvariable=self.heart_state_var).grid(row=0, column=2, sticky="e")

        status_bar = ttk.Frame(container)
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        status_bar.columnconfigure(0, weight=2)
        status_bar.columnconfigure(1, weight=1)
        ttk.Label(status_bar, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        ttk.Label(status_bar, textvariable=self.shortcut_hint_var, justify="right").grid(row=0, column=1, sticky="e")

        # Table area and scoreboard
        table_area = ttk.Frame(container)
        table_area.grid(row=2, column=0, sticky="nsew", padx=(0, 12))
        table_area.columnconfigure(0, weight=1)
        table_area.rowconfigure(0, weight=1)
        table_area.rowconfigure(1, weight=2)
        table_area.rowconfigure(2, weight=1)

        self._build_table(table_area)

        sidebar = ttk.Frame(container)
        sidebar.grid(row=2, column=1, sticky="nsew")
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(1, weight=1)

        self._build_scoreboard(sidebar)
        self._build_log(sidebar)

        # Control panels
        controls = ttk.Frame(container)
        controls.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)

        self.pass_frame = ttk.LabelFrame(controls, text="Passing phase", padding=12)
        self.pass_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.pass_frame.columnconfigure(0, weight=1)
        self.pass_frame.columnconfigure(1, weight=1)
        ttk.Label(self.pass_frame, textvariable=self.pass_direction_var).grid(row=0, column=0, sticky="w")
        self.pass_button = ttk.Button(self.pass_frame, text="Pass selected cards", command=self._finalise_pass_selection, state="disabled")
        self.pass_button.grid(row=0, column=1, sticky="e")

        self.hand_frame = ttk.Frame(self.pass_frame)
        self.hand_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        self.play_frame = ttk.LabelFrame(controls, text="Play a card", padding=12)
        self.play_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.play_frame.columnconfigure(0, weight=1)
        self.play_hint_label = ttk.Label(self.play_frame, text="Waiting for your turn…")
        self.play_hint_label.grid(row=0, column=0, sticky="w")
        self.play_frame.grid_remove()

        self._render_human_hand_for_passing()

    def _build_table(self, parent: ttk.Frame) -> None:
        """Create the table layout that shows the four seats."""
        table = ttk.Frame(parent)
        table.grid(row=1, column=0, sticky="nsew")
        table.columnconfigure(0, weight=1)
        table.columnconfigure(1, weight=1)
        table.columnconfigure(2, weight=1)
        table.rowconfigure(0, weight=1)
        table.rowconfigure(1, weight=1)
        table.rowconfigure(2, weight=1)

        seat_indices = [self.human_index, (self.human_index + 1) % 4, (self.human_index + 2) % 4, (self.human_index + 3) % 4]
        seat_positions = {
            seat_indices[0]: (2, 1),  # South (human)
            seat_indices[1]: (1, 2),  # West
            seat_indices[2]: (0, 1),  # North
            seat_indices[3]: (1, 0),  # East
        }

        for index, (row, col) in seat_positions.items():
            frame = ttk.Frame(table, padding=8, borderwidth=2, relief="groove")
            frame.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            frame.columnconfigure(0, weight=1)

            name_var = tk.StringVar(value=self._format_player_name(index))
            card_var = tk.StringVar(value="–")

            ttk.Label(frame, textvariable=name_var, font=(self.config.font_family, self.config.font_size, "bold")).grid(row=0, column=0)
            ttk.Label(frame, textvariable=card_var, font=("Consolas", self.config.font_size + 4)).grid(row=1, column=0)

            seat = _TrickSeat(frame=frame, name_var=name_var, card_var=card_var)
            self.table_seats[index] = seat

    def _build_scoreboard(self, parent: ttk.Frame) -> None:
        """Create the live scoreboard tree."""
        ttk.Label(parent, text="Scores", font=(self.config.font_family, self.config.font_size + 2, "bold")).grid(row=0, column=0, sticky="w")
        tree = ttk.Treeview(parent, columns=("player", "score", "penalties", "tricks"), show="headings", height=8)
        tree.heading("player", text="Player")
        tree.heading("score", text="Score")
        tree.heading("penalties", text="Penalty cards")
        tree.heading("tricks", text="Tricks won")
        tree.column("player", width=140, anchor="w")
        tree.column("score", width=80, anchor="center")
        tree.column("penalties", width=120, anchor="center")
        tree.column("tricks", width=100, anchor="center")
        tree.grid(row=1, column=0, sticky="nsew", pady=(4, 12))
        self.accessibility_manager.add_focus_indicator(tree)
        self.accessibility_manager.add_screen_reader_label(tree, "Scoreboard with totals and penalty counts")
        self.score_tree = tree

    def _build_log(self, parent: ttk.Frame) -> None:
        """Create the scrolling action log."""
        ttk.Label(parent, text="Action log", font=(self.config.font_family, self.config.font_size + 2, "bold")).grid(row=2, column=0, sticky="w")
        self.log_widget = scrolledtext.ScrolledText(parent, height=self.config.log_height, width=self.config.log_width, state="disabled", wrap="word")
        self.log_widget.grid(row=3, column=0, sticky="nsew")

    # ------------------------------------------------------------------
    # Round management
    # ------------------------------------------------------------------
    def _start_new_round(self) -> None:
        """Deal cards, determine passing direction, and prepare UI for the round."""
        self.game.deal_cards()
        self.round_var.set(f"Round {self.game.round_number + 1}")
        self.pass_selection.clear()
        self.pending_passes = {}
        self.phase = "passing"
        self.heart_state_var.set("Hearts are unbroken")
        self.shortcut_hint_var.set("Ctrl+H: accessibility help | Ctrl+L: focus log")
        self._log(f"--- Starting round {self.game.round_number + 1} ---")
        if self.play_frame:
            self.play_frame.grid_remove()
        if self.pass_frame:
            self.pass_frame.grid()

        pass_direction = self.game.get_pass_direction()
        if pass_direction is PassDirection.NONE:
            self.pass_direction_var.set("No passing this round. Waiting for the 2♣.")
            self.pass_frame.configure(text="Passing skipped")
            self.pass_frame.grid_remove()
            self.phase = "playing"
            self.current_player_index = self.game.players.index(self.game.find_starting_player())
            self._prepare_play_phase()
        else:
            direction_text = {
                PassDirection.LEFT: "left",
                PassDirection.RIGHT: "right",
                PassDirection.ACROSS: "across",
            }[pass_direction]
            self.pass_direction_var.set(f"Pass three cards to the {direction_text}.")
            self.pass_frame.configure(text="Passing phase")
            self.pass_frame.grid()
            self._render_human_hand_for_passing()
            for idx, player in enumerate(self.game.players):
                if idx == self.human_index:
                    continue
                self.pending_passes[player] = self.game.select_cards_to_pass(player)
            self.status_var.set("Select exactly three cards to pass.")
        self.update_display()

    def _prepare_play_phase(self) -> None:
        """Switch from the passing panel to the trick-taking controls."""
        assert self.current_player_index is not None
        self.phase = "playing"
        if self.pass_frame:
            self.pass_frame.grid_remove()
        if self.play_frame:
            self.play_frame.grid()
        self._render_human_hand_for_play()
        starting_player = self.game.players[self.current_player_index]
        if starting_player.hand:
            self.status_var.set(f"{starting_player.name} will lead the trick.")
        self.root.after(300, self._continue_turn_sequence)

    # ------------------------------------------------------------------
    # Passing logic
    # ------------------------------------------------------------------
    def _render_human_hand_for_passing(self) -> None:
        """Render the human hand as check buttons during the passing phase."""
        if not self.hand_frame:
            return
        for widget in self.hand_frame.winfo_children():
            widget.destroy()

        player = self.game.players[self.human_index]
        for column, card in enumerate(player.hand):
            var = tk.BooleanVar(value=card in self.pass_selection)
            check = ttk.Checkbutton(
                self.hand_frame,
                text=str(card),
                variable=var,
                command=lambda c=card, v=var: self._toggle_pass_card(c, v),
            )
            check.grid(row=0, column=column, padx=4, pady=4)
            self.accessibility_manager.add_focus_indicator(check)
            self.accessibility_manager.add_screen_reader_label(check, f"Toggle {card} for passing")

    def _toggle_pass_card(self, card: Card, var: tk.BooleanVar) -> None:
        """Toggle the selection of a passing card and enforce the limit of three."""
        if var.get():
            if len(self.pass_selection) >= 3:
                var.set(False)
                if messagebox:
                    messagebox.showinfo("Hearts", "You can only pass three cards.")
                return
            self.pass_selection.add(card)
        else:
            self.pass_selection.discard(card)
        if self.pass_button:
            self.pass_button.configure(state="normal" if len(self.pass_selection) == 3 else "disabled")

    def _finalise_pass_selection(self) -> None:
        """Apply the selected passing cards and transition to playing."""
        if len(self.pass_selection) != 3:
            return
        human = self.game.players[self.human_index]
        ordered_cards = sorted(self.pass_selection, key=lambda c: (c.suit.value, c.value))
        self.pending_passes[human] = ordered_cards
        self.game.pass_cards(self.pending_passes)
        self._log(f"You passed {format_cards(ordered_cards)}")
        self.pass_selection.clear()
        self.current_player_index = self.game.players.index(self.game.find_starting_player())
        self._prepare_play_phase()
        self.update_display()

    # ------------------------------------------------------------------
    # Playing logic
    # ------------------------------------------------------------------
    def _render_human_hand_for_play(self) -> None:
        """Render the human hand as buttons, enabling only valid plays."""
        if not self.play_frame:
            return
        for widget in self.play_frame.winfo_children():
            if widget is self.play_hint_label:
                continue
            widget.destroy()

        player = self.game.players[self.human_index]
        valid_cards = set(self.game.get_valid_plays(player))

        hand_container = ttk.Frame(self.play_frame)
        hand_container.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        hand_container.columnconfigure(tuple(range(len(player.hand))), weight=1)

        for column, card in enumerate(player.hand):
            button = ttk.Button(
                hand_container,
                text=str(card),
                command=lambda c=card: self._handle_human_play(c),
                state="normal" if card in valid_cards else "disabled",
            )
            button.grid(row=0, column=column, padx=4, pady=4)
            self.accessibility_manager.add_focus_indicator(button)
            self.accessibility_manager.add_screen_reader_label(button, f"Play {card}")

    def _handle_human_play(self, card: Card) -> None:
        """Handle the human selecting a card to play."""
        if self.phase != "playing" or self.current_player_index != self.human_index:
            return
        player = self.game.players[self.human_index]
        if card not in self.game.get_valid_plays(player):
            self.status_var.set("That card is not valid right now.")
            return
        self.game.play_card(player, card)
        self._log(f"You played {card}")
        self._update_trick_card_display(self.human_index, card)
        self._advance_after_play()

    def _continue_turn_sequence(self) -> None:
        """Advance through AI turns automatically until it is the human's move."""
        if self.phase != "playing" or self.current_player_index is None:
            return
        player = self.game.players[self.current_player_index]
        if not player.hand and not self.game.current_trick:
            return
        if player.is_ai:
            card = self.game.select_card_to_play(player)
            self.game.play_card(player, card)
            self._log(f"{player.name} played {card}")
            self._update_trick_card_display(self.current_player_index, card)
            self._advance_after_play(delay_ms=500)
        else:
            valid_cards = format_cards(self.game.get_valid_plays(player))
            self.status_var.set(f"Your turn. Valid cards: {valid_cards}")
            self._render_human_hand_for_play()

    def _advance_after_play(self, delay_ms: int = 0) -> None:
        """Move to the next player or resolve the trick when four cards are present."""
        if len(self.game.current_trick) == 4:
            self.root.after(max(200, delay_ms), self._resolve_trick)
            return
        assert self.current_player_index is not None
        self.current_player_index = (self.current_player_index + 1) % 4
        self.root.after(max(200, delay_ms), self._continue_turn_sequence)
        self.update_display()

    def _resolve_trick(self) -> None:
        """Resolve the trick, award cards to the winner, and continue play."""
        winner = self.game.complete_trick()
        self._log(f"{winner.name} won the trick")
        for seat in self.table_seats.values():
            seat.card_var.set("–")
        self.current_player_index = self.game.players.index(winner)
        if self.game.hearts_broken:
            self.heart_state_var.set("Hearts have been broken")
        self.update_display()
        if all(not player.hand for player in self.game.players):
            self._complete_round()
        else:
            self.root.after(600, self._continue_turn_sequence)

    def _complete_round(self) -> None:
        """Handle scoring at the end of a round and present a summary."""
        self.phase = "round_end"
        round_scores = self.game.calculate_scores()
        self._log("Round complete. Scores:")
        for player in self.game.players:
            points = round_scores[player.name]
            self._log(f"  {player.name}: {points} points (total {player.score})")
        self.game.round_number += 1
        if self.next_round_button is None:
            self.next_round_button = ttk.Button(self.play_frame, text="Start next round", command=self._handle_next_round)
            self.next_round_button.grid(row=2, column=0, pady=(12, 0))
            self.accessibility_manager.add_focus_indicator(self.next_round_button)
            self.accessibility_manager.add_screen_reader_label(self.next_round_button, "Start the next round")
        self.next_round_button.configure(state="normal")
        if self.game.is_game_over():
            winner = self.game.get_winner()
            self.status_var.set(f"Game over. {winner.name} wins with {winner.score} points!")
            if self.next_round_button:
                self.next_round_button.configure(state="disabled")
        else:
            self.status_var.set("Round finished. Press the button or Ctrl+N to continue.")
        self.update_display()

    def _handle_next_round(self) -> None:
        """Start the next round when the button or shortcut is triggered."""
        if self.phase != "round_end" or self.game.is_game_over():
            return
        if self.next_round_button:
            self.next_round_button.configure(state="disabled")
        self._start_new_round()

    # ------------------------------------------------------------------
    # Shortcuts & accessibility helpers
    # ------------------------------------------------------------------
    def _handle_shortcut_new_round(self) -> None:
        """Keyboard shortcut handler for starting a new round."""
        if self.phase == "round_end" and not self.game.is_game_over():
            self._handle_next_round()

    def _focus_log(self) -> None:
        """Bring focus to the action log widget."""
        if self.log_widget:
            self.log_widget.focus_set()

    def _show_accessibility_tips(self) -> None:
        """Display a help message describing accessibility options."""
        tips = (
            "Keyboard shortcuts:\n"
            "  Ctrl+L – Focus the action log\n"
            "  Ctrl+N – Start the next round\n"
            "  Ctrl+H – Show this help dialog\n\n"
            "High contrast mode is available via the --high-contrast flag or by enabling accessibility mode."
        )
        if messagebox:
            messagebox.showinfo("Hearts accessibility", tips)
        else:
            self._log(tips)

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------
    def _refresh_scoreboard(self) -> None:
        """Populate the scoreboard tree with live values."""
        if not self.score_tree:
            return
        self.score_tree.delete(*self.score_tree.get_children())
        for player in self.game.players:
            penalties = sum(1 for card in player.tricks_won if card.suit == Suit.HEARTS or card == QUEEN_OF_SPADES)
            tricks_captured = len(player.tricks_won) // 4 if player.tricks_won else 0
            name = f"{player.name} (You)" if player == self.game.players[self.human_index] else player.name
            self.score_tree.insert("", "end", values=(name, player.score, penalties, tricks_captured))

    def _update_trick_cards(self) -> None:
        """Refresh the trick labels for each seat."""
        for idx, seat in self.table_seats.items():
            seat.name_var.set(self._format_player_name(idx))
            seat.card_var.set("–")
        for player, card in self.game.current_trick:
            idx = self.game.players.index(player)
            self._update_trick_card_display(idx, card)

    def _update_trick_card_display(self, player_index: int, card: Card) -> None:
        """Update a single seat to show the played card."""
        seat = self.table_seats.get(player_index)
        if seat:
            seat.card_var.set(str(card))

    def _update_status_banner(self) -> None:
        """Update status text for hearts-broken indicator and focus hints."""
        if self.game.hearts_broken:
            self.heart_state_var.set("Hearts have been broken")

    def _format_player_name(self, index: int) -> str:
        """Return the table label for a player index."""
        player = self.game.players[index]
        suffix = " (You)" if index == self.human_index else ""
        return f"{player.name}{suffix}"

    def _log(self, message: str) -> None:
        """Append a line to the action log."""
        if not self.log_widget:
            return
        self.log_widget.configure(state="normal")
        self.log_widget.insert(tk.END, f"{message}\n")
        self.log_widget.see(tk.END)
        self.log_widget.configure(state="disabled")

    # ------------------------------------------------------------------
    # Preferences management
    # ------------------------------------------------------------------
    def _build_preferences_menu(self) -> None:
        """Create the preferences menu exposing theme, sound, and animation settings."""

        if self._preferences_menu is not None:
            return

        menu_bar = tk.Menu(self.root)
        preferences = tk.Menu(menu_bar, tearoff=0)

        theme_menu = tk.Menu(preferences, tearoff=0)
        for theme_name in self.theme_manager.list_themes():
            theme_menu.add_radiobutton(
                label=self._format_theme_label(theme_name),
                value=theme_name,
                variable=self._theme_var,
                command=lambda name=theme_name: self.update_user_preferences(theme=name),
            )
        preferences.add_cascade(label="Theme", menu=theme_menu)

        preferences.add_checkbutton(
            label="Enable sounds",
            variable=self._sound_var,
            command=lambda: self.update_user_preferences(enable_sounds=bool(self._sound_var.get())),
        )
        preferences.add_checkbutton(
            label="Enable animations",
            variable=self._animation_var,
            command=lambda: self.update_user_preferences(enable_animations=bool(self._animation_var.get())),
        )
        preferences.add_separator()
        preferences.add_command(label="Reset to defaults", command=self.reset_user_preferences)

        menu_bar.add_cascade(label="Preferences", menu=preferences)
        self.root.config(menu=menu_bar)
        self._preferences_menu = menu_bar

    def _format_theme_label(self, theme_name: str) -> str:
        """Return a human readable label for ``theme_name``."""

        return theme_name.replace("_", " ").title()

    def update_user_preferences(
        self,
        *,
        theme: Optional[str] = None,
        enable_sounds: Optional[bool] = None,
        enable_animations: Optional[bool] = None,
        persist: bool = True,
    ) -> None:
        """Update runtime preferences and persist them if requested.

        Args:
            theme: Optional theme identifier to activate.
            enable_sounds: Optional flag controlling sound playback.
            enable_animations: Optional flag controlling highlight animations.
            persist: Whether the change should be written to the settings store.
        """

        if theme is not None and self.set_theme(theme):
            self.config.theme_name = theme
            self._theme_var.set(theme)

        if enable_sounds is not None:
            sounds_enabled = bool(enable_sounds)
            self.config.enable_sounds = sounds_enabled
            if sounds_enabled:
                self.sound_manager = initialize_game_soundscape(
                    "hearts",
                    module_file=__file__,
                    enable_sounds=True,
                    existing_manager=self.sound_manager,
                )
                if self.sound_manager:
                    self.sound_manager.set_enabled(True)
            elif self.sound_manager:
                self.sound_manager.set_enabled(False)
            self._sound_var.set(sounds_enabled)

        if enable_animations is not None:
            animations_enabled = bool(enable_animations)
            self.config.enable_animations = animations_enabled
            self._animation_var.set(animations_enabled)

        if not persist:
            return

        if theme is not None:
            self._preferences.set("theme", self.config.theme_name)
        if enable_sounds is not None:
            self._preferences.set("enable_sounds", self.config.enable_sounds)
        if enable_animations is not None:
            self._preferences.set("enable_animations", self.config.enable_animations)
        self.settings_manager.save_settings(self._preferences_namespace, self._preferences)

    def reset_user_preferences(self) -> None:
        """Reset stored preferences to their defaults and apply them immediately."""

        self._preferences.reset()
        self.update_user_preferences(
            theme=str(self._preferences.get("theme", self._preferences_defaults["theme"])),
            enable_sounds=bool(self._preferences.get("enable_sounds", self._preferences_defaults["enable_sounds"])),
            enable_animations=bool(self._preferences.get("enable_animations", self._preferences_defaults["enable_animations"])),
            persist=True,
        )


def run_app(
    *,
    player_name: str = "Player",
    high_contrast: bool = False,
    accessibility_mode: bool = False,
) -> None:
    """Launch the Hearts GUI with optional accessibility configuration.

    Args:
        player_name: Name to display for the human player.
        high_contrast: Enable a high contrast palette.
        accessibility_mode: Enable full accessibility mode (screen reader and focus aids).
    """
    root = tk.Tk()
    config = GUIConfig(
        window_title="Hearts – Four Seat Table",
        window_width=1080,
        window_height=780,
        accessibility_mode=accessibility_mode or high_contrast,
        theme_name="high_contrast" if high_contrast else "midnight",
        font_size=14 if accessibility_mode else 12,
        enable_sounds=True,
        enable_animations=True,
    )
    players = [
        HeartsPlayer(name=player_name, is_ai=False),
        HeartsPlayer(name="AI West", is_ai=True),
        HeartsPlayer(name="AI North", is_ai=True),
        HeartsPlayer(name="AI East", is_ai=True),
    ]
    game = HeartsGame(players)
    HeartsGUI(root, game, human_index=0, config=config)
    root.mainloop()
