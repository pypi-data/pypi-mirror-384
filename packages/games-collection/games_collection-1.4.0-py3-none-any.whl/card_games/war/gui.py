"""Graphical interface for the War card game.

This module defines :class:`WarGUI`, a Tkinter-based interface that builds on
the common :class:`~common.gui_base.BaseGUI` helpers. The GUI presents deck
sizes, the current face-up cards, a battle log, and interactive controls for
playing single rounds or starting an auto-play loop. When wars occur, the
interface animates stacked facedown cards and flashes alerts to emphasize the
event.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from card_games.common.soundscapes import initialize_game_soundscape
from card_games.war.game import WarGame
from common.architecture.persistence import SaveLoadManager
from common.gui_base import TKINTER_AVAILABLE, BaseGUI, GUIConfig

try:  # pragma: no cover - optional dependency
    from card_games.common.stats import CardGameStats

    STATS_AVAILABLE = True
except ImportError:  # pragma: no cover - executed when stats package missing
    STATS_AVAILABLE = False
    CardGameStats = None  # type: ignore[assignment]

if not TKINTER_AVAILABLE:  # pragma: no cover - defensive runtime guard
    raise ImportError("Tkinter is required for the War GUI but is not available.")

import tkinter as tk
from tkinter import messagebox, ttk


class WarGUI(BaseGUI):
    """Tkinter GUI for the War card game."""

    _CARD_STACK_WIDTH = 48
    _CARD_STACK_HEIGHT = 70
    _CARD_STACK_OFFSET = 9

    def __init__(
        self,
        root: tk.Tk,
        game: Optional[WarGame] = None,
        *,
        enable_sounds: bool = True,
        config: Optional[GUIConfig] = None,
    ) -> None:
        """Initialize the War GUI.

        Args:
            root: Root Tk instance.
            game: Optional pre-configured :class:`WarGame` engine.
            config: Optional GUI configuration overrides.
        """

        war_config = config or GUIConfig(
            window_title="War Card Game",
            window_width=900,
            window_height=720,
            log_height=14,
            log_width=70,
            enable_sounds=enable_sounds,
            enable_animations=True,
        )
        super().__init__(root, war_config)
        self.sound_manager = initialize_game_soundscape(
            "war",
            module_file=__file__,
            enable_sounds=war_config.enable_sounds,
            existing_manager=self.sound_manager,
        )

        self.game = game or WarGame()
        self._start_time = time.time()
        self._auto_job: Optional[str] = None
        self._flash_job: Optional[str] = None
        self._flash_cycles_remaining = 0

        # Tkinter variables for dynamic elements
        self.player1_cards_var = tk.StringVar()
        self.player2_cards_var = tk.StringVar()
        self.pile_cards_var = tk.StringVar()
        self.rounds_var = tk.StringVar()
        self.wars_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Click Play Round to begin.")
        self.player1_card_var = tk.StringVar(value="—")
        self.player2_card_var = tk.StringVar(value="—")
        self.speed_var = tk.IntVar(value=700)
        self.speed_display_var = tk.StringVar()
        self.auto_button_text = tk.StringVar(value="Start Auto Play")

        self._last_result: Optional[dict[str, object]] = None
        self._auto_running = False
        self._save_load_manager = SaveLoadManager()

        self.build_layout()
        self.update_display()

    def build_layout(self) -> None:
        """Construct the War GUI layout."""

        bg_color = self.current_theme.colors.background

        container = tk.Frame(self.root, bg=bg_color)
        container.pack(fill=tk.BOTH, expand=True)

        header = self.create_header(container, "War")
        header.configure(bg=bg_color, fg=self.current_theme.colors.primary)
        header.pack(pady=(10, 0))

        stats_frame = tk.Frame(container, bg=bg_color)
        stats_frame.pack(fill=tk.X, padx=16, pady=8)

        self._create_deck_panel(stats_frame)
        self._create_summary_panel(stats_frame)

        cards_frame = self.create_label_frame(container, "Current Battle")
        cards_frame.configure(bg=bg_color)
        cards_frame.pack(fill=tk.X, padx=16, pady=8)

        self._create_card_display(cards_frame)

        self.animation_canvas = tk.Canvas(
            cards_frame,
            height=120,
            bg=self.current_theme.colors.canvas_bg,
            highlightthickness=0,
        )
        self.animation_canvas.pack(fill=tk.X, padx=8, pady=(8, 4))

        self.war_alert_label = tk.Label(
            cards_frame,
            text="",
            font=(self.config.font_family, self.config.font_size + 2, "bold"),
            bg=bg_color,
            fg=self.current_theme.colors.error,
        )
        self.war_alert_label.pack(pady=(0, 6))

        log_frame = self.create_label_frame(container, "Battle Log")
        log_frame.configure(bg=bg_color)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        self.log_widget = self.create_log_widget(log_frame)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

        controls = self.create_label_frame(container, "Controls")
        controls.configure(bg=bg_color)
        controls.pack(fill=tk.X, padx=16, pady=(0, 16))

        self._create_controls(controls)

        status_label = tk.Label(
            container,
            textvariable=self.status_var,
            anchor="w",
            bg=bg_color,
            fg=self.current_theme.colors.foreground,
            font=(self.config.font_family, self.config.font_size),
        )
        status_label.pack(fill=tk.X, padx=20, pady=(0, 14))

    def _create_deck_panel(self, parent: tk.Widget) -> None:
        """Create the deck size display panel."""

        bg_color = self.current_theme.colors.background

        player_panel = self.create_label_frame(parent, "Deck Sizes")
        player_panel.configure(bg=bg_color)
        player_panel.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=8)

        tk.Label(
            player_panel,
            text="Player 1",
            font=(self.config.font_family, self.config.font_size + 2, "bold"),
            bg=bg_color,
        ).pack(anchor="w")
        tk.Label(
            player_panel,
            textvariable=self.player1_cards_var,
            font=(self.config.font_family, self.config.font_size + 4),
            bg=bg_color,
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            player_panel,
            text="Player 2",
            font=(self.config.font_family, self.config.font_size + 2, "bold"),
            bg=bg_color,
        ).pack(anchor="w")
        tk.Label(
            player_panel,
            textvariable=self.player2_cards_var,
            font=(self.config.font_family, self.config.font_size + 4),
            bg=bg_color,
        ).pack(anchor="w")

    def _create_summary_panel(self, parent: tk.Widget) -> None:
        """Create the statistics summary panel."""

        bg_color = self.current_theme.colors.background

        summary_panel = self.create_label_frame(parent, "Statistics")
        summary_panel.configure(bg=bg_color)
        summary_panel.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=8)

        tk.Label(
            summary_panel,
            textvariable=self.rounds_var,
            font=(self.config.font_family, self.config.font_size + 1),
            bg=bg_color,
        ).pack(anchor="w")
        tk.Label(
            summary_panel,
            textvariable=self.wars_var,
            font=(self.config.font_family, self.config.font_size + 1),
            bg=bg_color,
        ).pack(anchor="w")
        tk.Label(
            summary_panel,
            textvariable=self.pile_cards_var,
            font=(self.config.font_family, self.config.font_size + 1),
            bg=bg_color,
        ).pack(anchor="w")

    def _create_card_display(self, parent: tk.Widget) -> None:
        """Create the face-up card display widgets."""

        bg_color = self.current_theme.colors.background

        card_row = tk.Frame(parent, bg=bg_color)
        card_row.pack(fill=tk.X, padx=4, pady=6)

        card_style = {
            "font": (self.config.font_family, self.config.font_size + 12, "bold"),
            "width": 6,
            "pady": 4,
        }

        left = tk.Frame(card_row, bg=bg_color)
        left.pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Label(left, text="Player 1", bg=bg_color).pack()
        self.player1_card_label = tk.Label(
            left,
            textvariable=self.player1_card_var,
            bg=self.current_theme.colors.canvas_bg,
            fg=self.current_theme.colors.primary,
            **card_style,
        )
        self.player1_card_label.pack(pady=(2, 0))

        right = tk.Frame(card_row, bg=bg_color)
        right.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        tk.Label(right, text="Player 2", bg=bg_color).pack()
        self.player2_card_label = tk.Label(
            right,
            textvariable=self.player2_card_var,
            bg=self.current_theme.colors.canvas_bg,
            fg=self.current_theme.colors.secondary,
            **card_style,
        )
        self.player2_card_label.pack(pady=(2, 0))

    def _create_controls(self, parent: tk.Widget) -> None:
        """Create game control buttons and speed slider."""

        bg_color = self.current_theme.colors.background

        button_bar = tk.Frame(parent, bg=bg_color)
        button_bar.pack(fill=tk.X, padx=4, pady=6)

        self.play_button = tk.Button(button_bar, text="Play Round", command=self._on_play_clicked)
        self.play_button.pack(side=tk.LEFT, padx=(0, 8))

        self.auto_button = tk.Button(button_bar, textvariable=self.auto_button_text, command=self._toggle_auto_play)
        self.auto_button.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(button_bar, text="Save Game", command=self._save_game).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(button_bar, text="Load Game", command=self._load_game).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(button_bar, text="Show Shortcuts", command=self.show_shortcuts_help).pack(side=tk.LEFT)

        speed_panel = tk.Frame(parent, bg=bg_color)
        speed_panel.pack(fill=tk.X, padx=4, pady=(4, 2))

        tk.Label(
            speed_panel,
            text="Auto-play speed (ms between rounds)",
            bg=bg_color,
            font=(self.config.font_family, self.config.font_size),
        ).pack(anchor="w")

        scale_frame = tk.Frame(speed_panel, bg=bg_color)
        scale_frame.pack(fill=tk.X)

        speed_scale = ttk.Scale(
            scale_frame,
            from_=150,
            to=2000,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            command=lambda _: self._update_speed_display(),
        )
        speed_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.speed_display_label = tk.Label(
            scale_frame,
            textvariable=self.speed_display_var,
            width=8,
            bg=bg_color,
            anchor="e",
        )
        self.speed_display_label.pack(side=tk.RIGHT)

        self._update_speed_display()

        self.register_shortcut("space", self._on_play_clicked, "Play a round")
        self.register_shortcut("Control-a", self._toggle_auto_play, "Toggle auto-play")

    def update_display(self) -> None:
        """Refresh labels to match the current game state."""

        summary = self.game.get_state_summary()
        self.player1_cards_var.set(f"Cards: {summary['player1_cards']}")
        self.player2_cards_var.set(f"Cards: {summary['player2_cards']}")
        self.pile_cards_var.set(f"Pile size: {summary['pile_cards']}")
        self.rounds_var.set(f"Rounds played: {summary['rounds_played']}")
        self.wars_var.set(f"Wars fought: {summary['wars_fought']}")

        if self._last_result and "player1_card" in self._last_result:
            self.player1_card_var.set(str(self._last_result["player1_card"]))
            self.player2_card_var.set(str(self._last_result["player2_card"]))
        elif summary["state"] == "PLAYING":
            self.player1_card_var.set("—")
            self.player2_card_var.set("—")

        if summary["state"] == "GAME_OVER":
            self.status_var.set(f"Game over. Player {summary['winner']} wins!")
            self.play_button.configure(state=tk.DISABLED)
            self.auto_button.configure(state=tk.DISABLED)

    def _on_play_clicked(self) -> None:
        """Handle the Play Round button click."""

        self._stop_auto_loop()
        self._play_round()

    def _play_round(self) -> None:
        """Execute a single game round and update the UI."""

        if self.game.is_game_over():
            self._handle_game_over()
            return

        result = self.game.play_round()
        self._last_result = result

        if "player1_card" in result:
            summary_line = f"Round {self.game.rounds_played}: {result['player1_card']} vs {result['player2_card']}"
            if result["round_type"] == "war":
                summary_line += " — WAR!"
            self.log_message(self.log_widget, summary_line)
            self.log_message(
                self.log_widget,
                f"Player {result['winner']} claims {result['cards_won']} cards.",
            )

        if result.get("round_type") == "war":
            self._animate_war(result)
        else:
            self._clear_war_animation()

        self.status_var.set(f"Player {result.get('winner', '—')} won the round.")
        self.update_display()

        if result.get("game_over"):
            self._handle_game_over(result)

    def _animate_war(self, result: dict[str, object]) -> None:
        """Draw stacked cards and flash an alert when a war occurs."""

        self.animation_canvas.delete("all")
        self.animation_canvas.update_idletasks()

        width = max(self.animation_canvas.winfo_width(), 360)
        height = self.animation_canvas.winfo_height() or 110

        left_x = width * 0.2
        right_x = width * 0.6
        top_y = (height - self._CARD_STACK_HEIGHT) / 2

        for idx in range(3):
            offset = idx * self._CARD_STACK_OFFSET
            self._draw_card(left_x + offset, top_y + offset, fill=self.current_theme.colors.secondary)
            self._draw_card(right_x + offset, top_y + offset, fill=self.current_theme.colors.primary)

        self._draw_card(left_x + self._CARD_STACK_OFFSET * 3, top_y, outline=self.current_theme.colors.error)
        self._draw_card(right_x + self._CARD_STACK_OFFSET * 3, top_y, outline=self.current_theme.colors.error)

        war_text = "WAR! Cards matched"
        if result.get("nested_war"):
            war_text = "WAR continues! Another tie"
        if result.get("reason") == "insufficient_cards":
            war_text = "War ends: insufficient cards"

        self._start_flash(war_text)

    def _clear_war_animation(self) -> None:
        """Remove war drawings and stop alert flashing."""

        self.animation_canvas.delete("all")
        self._stop_flash()
        self.war_alert_label.configure(text="")

    def _draw_card(self, x: float, y: float, *, fill: Optional[str] = None, outline: Optional[str] = None) -> None:
        """Draw a simple rectangle card on the animation canvas."""

        fill_color = fill or self.current_theme.colors.canvas_bg
        outline_color = outline or self.current_theme.colors.border
        self.animation_canvas.create_rectangle(
            x,
            y,
            x + self._CARD_STACK_WIDTH,
            y + self._CARD_STACK_HEIGHT,
            fill=fill_color,
            outline=outline_color,
            width=2,
        )

    def _start_flash(self, text: str, cycles: int = 8) -> None:
        """Begin flashing the war alert label."""

        self.war_alert_label.configure(text=text)
        self._flash_cycles_remaining = cycles
        self._toggle_flash()

    def _toggle_flash(self) -> None:
        """Alternate the alert label colors."""

        if self._flash_cycles_remaining <= 0:
            self.war_alert_label.configure(bg=self.current_theme.colors.background)
            self._flash_job = None
            return

        current_bg = self.war_alert_label.cget("bg")
        new_bg = self.current_theme.colors.error if current_bg == self.current_theme.colors.background else self.current_theme.colors.background
        fg_color = self.current_theme.colors.background if new_bg == self.current_theme.colors.error else self.current_theme.colors.error
        self.war_alert_label.configure(bg=new_bg, fg=fg_color)
        self._flash_cycles_remaining -= 1
        self._flash_job = self.root.after(220, self._toggle_flash)

    def _stop_flash(self) -> None:
        """Stop any pending alert flashing jobs."""

        if self._flash_job is not None:
            self.root.after_cancel(self._flash_job)
            self._flash_job = None
        self.war_alert_label.configure(bg=self.current_theme.colors.background, fg=self.current_theme.colors.error)
        self._flash_cycles_remaining = 0

    def _toggle_auto_play(self) -> None:
        """Toggle the auto-play loop on or off."""

        if self._auto_running:
            self._stop_auto_loop()
            return

        if self.game.is_game_over():
            self.status_var.set("Game finished. Start a new game to auto-play again.")
            return

        self._auto_running = True
        self.auto_button_text.set("Stop Auto Play")
        self.play_button.configure(state=tk.DISABLED)
        self._schedule_next_round()
        self.status_var.set("Auto-play running…")

    def _schedule_next_round(self) -> None:
        """Schedule the next auto-play round."""

        delay = max(int(self.speed_var.get()), 150)
        self._auto_job = self.root.after(delay, self._auto_step)

    def _auto_step(self) -> None:
        """Play a round as part of the auto-play loop."""

        self._play_round()
        if not self.game.is_game_over() and self._auto_running:
            self._schedule_next_round()
        else:
            self._stop_auto_loop()

    def _stop_auto_loop(self) -> None:
        """Stop the auto-play loop if it is active."""

        if self._auto_job is not None:
            self.root.after_cancel(self._auto_job)
            self._auto_job = None
        self._auto_running = False
        self.auto_button_text.set("Start Auto Play")
        self.play_button.configure(state=tk.NORMAL if not self.game.is_game_over() else tk.DISABLED)

    def _update_speed_display(self) -> None:
        """Update the label describing the auto-play delay."""

        self.speed_display_var.set(f"{int(self.speed_var.get())} ms")

    def _handle_game_over(self, result: Optional[dict[str, object]] = None) -> None:
        """Display summary information when the game ends."""

        self._stop_auto_loop()
        summary = self.game.get_state_summary()
        winner = summary.get("winner")
        rounds = summary.get("rounds_played")
        wars = summary.get("wars_fought")
        duration = time.time() - self._start_time

        if result and result.get("reason") == "insufficient_cards":
            message = "A player ran out of cards during war."
        else:
            message = "One player captured the entire deck."

        detail = f"Player {winner} wins after {rounds} rounds with {wars} wars fought.\n" f"Game duration: {duration:.1f} seconds.\n{message}"

        messagebox.showinfo("War - Game Over", detail)

        if STATS_AVAILABLE and winner in {1, 2}:
            self._maybe_save_stats(duration, winner)

    def _maybe_save_stats(self, duration: float, winner: int) -> None:
        """Prompt the user to persist game statistics if supported."""

        should_save = messagebox.askyesno("Save Statistics", "Save this result to your War stats?")
        if not should_save:
            self.status_var.set("Statistics not saved.")
            return

        try:
            assert CardGameStats is not None  # For type checkers
            stats = CardGameStats("war")
            stats.record_win(f"Player {winner}", duration)
            stats.record_loss(f"Player {3 - winner}", duration)
            stats.save()
            self.status_var.set("Game statistics saved successfully.")
        except Exception as exc:  # pragma: no cover - user specific environments
            self.status_var.set(f"Could not save statistics: {exc}")

    def _save_game(self) -> None:
        """Save the current game state."""
        if self.game.is_game_over():
            messagebox.showwarning("Cannot Save", "Game is already over. Nothing to save.")
            return

        try:
            state = self.game.to_dict()
            filepath = self._save_load_manager.save("war", state)
            self.status_var.set(f"Game saved to {filepath.name}")
            self.log_message(self.log_widget, f"Game saved successfully to {filepath}")
            messagebox.showinfo("Save Successful", f"Game saved to:\n{filepath}")
        except Exception as e:
            error_msg = f"Failed to save game: {e}"
            self.status_var.set(error_msg)
            self.log_message(self.log_widget, error_msg)
            messagebox.showerror("Save Failed", error_msg)

    def _load_game(self) -> None:
        """Load a saved game state."""
        try:
            # Get list of saves
            saves = self._save_load_manager.list_saves("war")
            if not saves:
                messagebox.showinfo("No Saves", "No saved games found.")
                return

            # Show dialog to choose save file
            from tkinter import filedialog

            save_dir = Path("./saves")
            filepath = filedialog.askopenfilename(
                title="Load War Game",
                initialdir=save_dir,
                filetypes=[("Save files", "*.save"), ("All files", "*.*")],
            )

            if not filepath:
                return

            # Load the game state
            data = self._save_load_manager.load(Path(filepath))
            if data.get("game_type") != "war":
                messagebox.showerror("Invalid Save", "This save file is not for War game.")
                return

            # Stop auto-play if running
            self._stop_auto_loop()

            # Restore the game
            self.game = WarGame.from_dict(data["state"])
            self._last_result = None
            self._start_time = time.time()

            # Re-enable buttons if they were disabled
            self.play_button.configure(state=tk.NORMAL)
            self.auto_button.configure(state=tk.NORMAL)

            # Update display
            self.update_display()
            self.status_var.set(f"Game loaded from {Path(filepath).name}")
            self.log_message(self.log_widget, f"Game loaded successfully from {filepath}")
            messagebox.showinfo("Load Successful", "Game loaded successfully!")

        except Exception as e:
            error_msg = f"Failed to load game: {e}"
            self.status_var.set(error_msg)
            self.log_message(self.log_widget, error_msg)
            messagebox.showerror("Load Failed", error_msg)


def run_app(*, game: Optional[WarGame] = None, enable_sounds: bool = True) -> None:
    """Launch the War GUI application."""

    root = tk.Tk()
    config = GUIConfig(
        window_title="War Card Game",
        window_width=900,
        window_height=720,
        enable_sounds=enable_sounds,
        enable_animations=True,
    )
    gui = WarGUI(root, game=game, config=config)
    gui.apply_theme()
    root.mainloop()


__all__ = ["WarGUI", "run_app"]
