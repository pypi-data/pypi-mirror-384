"""Tkinter GUI for Bunco tournaments."""

from __future__ import annotations

from typing import List, Optional

from common.gui_base import TKINTER_AVAILABLE, BaseGUI, GUIConfig

from .bunco import BuncoPlayerSummary, BuncoTournament

if TKINTER_AVAILABLE:
    import tkinter as tk
    from tkinter import messagebox, ttk
else:  # pragma: no cover - executed only when Tkinter is unavailable
    tk = None  # type: ignore
    ttk = None  # type: ignore
    messagebox = None  # type: ignore


class BuncoGUI(BaseGUI):
    """Graphical interface showcasing Bunco tournament brackets."""

    def __init__(
        self,
        root: tk.Tk,
        tournament: Optional[BuncoTournament] = None,
        *,
        config: Optional[GUIConfig] = None,
    ) -> None:
        """Initialize the Bunco GUI."""

        if not TKINTER_AVAILABLE:  # pragma: no cover - ensures clarity in headless tests
            raise RuntimeError("Tkinter is required to launch the Bunco GUI.")

        gui_config = config or GUIConfig(window_title="Bunco Tournament", window_width=960, window_height=720, enable_animations=True)
        super().__init__(root, gui_config)
        self.tournament = tournament
        self.status_var = tk.StringVar(value="Enter player names separated by commas to build the bracket.")
        self.player_entry: ttk.Entry | None = None
        self.bracket_text: tk.Text | None = None
        self.score_tree: ttk.Treeview | None = None
        self.build_layout()
        self.update_display()

    def build_layout(self) -> None:
        """Construct the layout for the tournament controls and summaries."""

        assert TKINTER_AVAILABLE
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        control_frame = ttk.Frame(self.root, padding=12)
        control_frame.grid(row=0, column=0, sticky="ew")
        control_frame.columnconfigure(1, weight=1)

        ttk.Label(control_frame, text="Players (comma separated, power of two):").grid(row=0, column=0, sticky="w")
        self.player_entry = ttk.Entry(control_frame)
        self.player_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ttk.Button(control_frame, text="Simulate Tournament", command=self._run_tournament).grid(row=0, column=2, padx=8)

        ttk.Label(control_frame, textvariable=self.status_var).grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))

        content = ttk.Frame(self.root, padding=12)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        bracket_frame = ttk.LabelFrame(content, text="Bracket")
        bracket_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        bracket_frame.rowconfigure(0, weight=1)
        bracket_frame.columnconfigure(0, weight=1)
        self.bracket_text = tk.Text(bracket_frame, wrap="word", state="disabled")
        self.bracket_text.grid(row=0, column=0, sticky="nsew")

        scoreboard = ttk.LabelFrame(content, text="Score Summary")
        scoreboard.grid(row=0, column=1, sticky="nsew")
        scoreboard.rowconfigure(0, weight=1)
        scoreboard.columnconfigure(0, weight=1)
        columns = ("name", "won", "played", "points", "buncos", "mini")
        self.score_tree = ttk.Treeview(scoreboard, columns=columns, show="headings")
        headings = {
            "name": "Player",
            "won": "Matches Won",
            "played": "Matches",
            "points": "Points",
            "buncos": "Buncos",
            "mini": "Mini Buncos",
        }
        for col, title in headings.items():
            self.score_tree.heading(col, text=title)
            self.score_tree.column(col, anchor="center")
        self.score_tree.grid(row=0, column=0, sticky="nsew")

    def update_display(self) -> None:
        """Refresh bracket and scoreboard widgets."""

        if not TKINTER_AVAILABLE:
            return

        self._update_bracket()
        self._update_scoreboard()

    def _run_tournament(self) -> None:
        """Parse player names and simulate the tournament."""

        if not self.player_entry:
            return

        names_raw = self.player_entry.get()
        names = [name.strip() for name in names_raw.split(",") if name.strip()]

        if not names:
            if messagebox:
                messagebox.showerror("Bunco", "Please enter at least two player names.")
            return

        try:
            self.tournament = BuncoTournament(names)
        except ValueError as exc:
            if messagebox:
                messagebox.showerror("Bunco", str(exc))
            return

        champion = self.tournament.run()
        self.status_var.set(f"Champion: {champion}")
        self.update_display()
        if self.bracket_text:
            self.animate_highlight(self.bracket_text)

    def _update_bracket(self) -> None:
        """Render the textual bracket."""

        if not self.bracket_text:
            return

        self.bracket_text.configure(state="normal")
        self.bracket_text.delete("1.0", tk.END)

        if not self.tournament:
            self.bracket_text.insert(tk.END, "No tournament simulated yet.\n")
        else:
            for round_index, matches in enumerate(self.tournament.get_bracket(), start=1):
                self.bracket_text.insert(tk.END, f"Round {round_index}\n")
                for result in matches:
                    player_summary = " vs ".join(result.players)
                    score_summary = ", ".join(
                        f"{name}: {score} pts ({bunco} bunco, {mini} mini)"
                        for name, score, bunco, mini in zip(result.players, result.scores, result.buncos, result.mini_buncos)
                    )
                    self.bracket_text.insert(
                        tk.END,
                        f"  Table {result.table_number}: {player_summary} -> {result.winner}\n    {score_summary}\n",
                    )
                self.bracket_text.insert(tk.END, "\n")

        self.bracket_text.configure(state="disabled")

    def _update_scoreboard(self) -> None:
        """Update the scoreboard tree view."""

        if not self.score_tree:
            return

        for item in self.score_tree.get_children():
            self.score_tree.delete(item)

        if not self.tournament:
            return

        summaries: List[BuncoPlayerSummary] = self.tournament.get_score_summary()
        for summary in summaries:
            row = summary.to_row()
            self.score_tree.insert(
                "",
                tk.END,
                values=(
                    row["name"],
                    row["won"],
                    row["played"],
                    row["points"],
                    row["buncos"],
                    row["mini_buncos"],
                ),
            )


__all__ = ["BuncoGUI"]
