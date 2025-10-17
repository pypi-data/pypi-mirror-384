"""Graphical interfaces for the logic games progression hub."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from common.gui_base import TKINTER_AVAILABLE, tk, ttk
from common.gui_base import BaseGUI as TkBaseGUI
from common.gui_base import GUIConfig as TkGUIConfig
from common.gui_base_pyqt import PYQT5_AVAILABLE
from common.gui_base_pyqt import BaseGUI as QtBaseGUI
from common.gui_base_pyqt import GUIConfig as QtGUIConfig
from common.i18n import _

from .progression import LOGIC_PUZZLE_SERVICE, LogicPuzzleService, PuzzleDifficulty

if PYQT5_AVAILABLE:  # pragma: no cover - exercised in integration environments
    from PyQt5.QtWidgets import (  # type: ignore
        QComboBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )


@dataclass(slots=True)
class _SessionState:
    """Runtime state shared by the GUI implementations."""

    active_game: Optional[str] = None
    active_difficulty: Optional[str] = None
    session_start: Optional[float] = None


class _LogicGameGUIController:
    """Utility mixin providing business logic for GUI front-ends."""

    def __init__(self, service: LogicPuzzleService, player_id: str) -> None:
        self.service = service
        self.player_id = player_id
        self.state = _SessionState()
        self._active_engine = None
        games = self.service.registered_games()
        if games:
            self.state.active_game = games[0]

    # ------------------------------------------------------------------
    # Progress helpers
    # ------------------------------------------------------------------
    def available_games(self) -> List[str]:
        return self.service.registered_games()

    def set_active_game(self, game_key: str) -> None:
        self.state.active_game = game_key
        available = self.available_difficulties()
        self.state.active_difficulty = available[0].key if available else None

    def available_difficulties(self) -> List[PuzzleDifficulty]:
        if not self.state.active_game:
            return []
        return self.service.get_available_difficulties(self.state.active_game, self.player_id)

    def completion_summary(self) -> Dict[str, int]:
        if not self.state.active_game:
            return {}
        return self.service.completion_summary(self.state.active_game, self.player_id)

    def upcoming_unlock(self) -> Optional[str]:
        if not self.state.active_game:
            return None
        definition = self.service.get_definition(self.state.active_game)
        progress = self.completion_summary()
        return self.service.get_next_locked_difficulty(definition, progress)

    def leaderboard_text(self) -> str:
        if not self.state.active_game:
            return _("Select a puzzle to view the leaderboard.")
        leaderboard = self.service.leaderboard(self.state.active_game, limit=5)
        if not leaderboard:
            return _("No completions have been recorded yet. Be the first!")
        rows = [_("Leaderboard:")]
        for entry in leaderboard:
            rows.append(f"{entry['player']} – {entry['wins']} wins ({entry['win_rate']:.0f}% win rate, {entry['average_duration']:.1f}s avg)")
        return "\n".join(rows)

    # ------------------------------------------------------------------
    # Gameplay lifecycle helpers
    # ------------------------------------------------------------------
    def start_new_puzzle(self) -> str:
        if not self.state.active_game or not self.state.active_difficulty:
            return _("Please select a puzzle and difficulty to begin.")
        engine = self.service.generate_puzzle(self.state.active_game, self.state.active_difficulty)
        self.state.session_start = time.perf_counter()
        self._active_engine = engine
        definition = self.service.get_definition(self.state.active_game)
        diff = next(
            (d for pack in definition.level_packs for d in pack.difficulties if d.key == self.state.active_difficulty),
            None,
        )
        difficulty_name = diff.display_name if diff else self.state.active_difficulty
        return _("Started {difficulty} puzzle for {game}. Use the hint button to consult the tutorial registry.").format(
            difficulty=difficulty_name, game=definition.display_name
        )

    def complete_puzzle(self) -> str:
        if not self.state.active_game or not self.state.active_difficulty:
            return _("No puzzle is currently active.")
        if self.state.session_start is None:
            return _("Start a puzzle before completing it.")
        duration = max(0.1, time.perf_counter() - self.state.session_start)
        engine = getattr(self, "_active_engine", None)
        mistakes = int(getattr(engine, "total_mistakes", 0)) if engine is not None else 0
        metadata: Dict[str, int] = {}
        for attr in ("moves", "pushes", "total_time_seconds"):
            value = getattr(engine, attr, None)
            if isinstance(value, (int, float)):
                metadata[attr] = int(value)
        self.service.record_completion(
            self.state.active_game,
            self.state.active_difficulty,
            self.player_id,
            duration=duration,
            mistakes=mistakes,
            metadata=metadata or None,
        )
        self.state.session_start = None
        self._active_engine = None
        return _("Recorded completion in {duration:.1f}s with {mistakes} mistakes. Keep solving to unlock the next pack!").format(
            duration=duration, mistakes=mistakes
        )

    def request_hint(self) -> str:
        if not self.state.active_game or not self.state.active_difficulty:
            return _("Select a puzzle before requesting hints.")
        hint = self.service.get_hint(self.state.active_game, self.state.active_difficulty)
        if not hint:
            return _("No hints are registered for this puzzle yet.")
        return f"{hint['title']}: {hint['hint']}"


class LogicGamesTkinterGUI(TkBaseGUI, _LogicGameGUIController):
    """Tkinter GUI showcasing progression and hints for logic puzzles."""

    def __init__(
        self,
        root: Optional[tk.Tk] = None,
        *,
        config: Optional[TkGUIConfig] = None,
        service: LogicPuzzleService = LOGIC_PUZZLE_SERVICE,
        player_id: str = "solo",
    ) -> None:
        if not TKINTER_AVAILABLE:  # pragma: no cover - defensive guard
            raise RuntimeError("Tkinter is not available in this environment.")
        root = root or tk.Tk()
        TkBaseGUI.__init__(self, root, config)
        _LogicGameGUIController.__init__(self, service, player_id)
        self._difficulty_display_map: Dict[str, str] = {}
        self._build_layout()
        self.update_display()

    def build_layout(self) -> None:  # pragma: no cover - layout tested via update_display
        self._build_layout()

    def _build_layout(self) -> None:
        self.root.configure(padx=12, pady=12)
        self.main_frame = tk.Frame(self.root, bg=self.current_theme.colors.background)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        header = self.create_header(self.main_frame, _("Logic Puzzle Hub"))
        header.pack(anchor=tk.CENTER)

        selection = self.create_label_frame(self.main_frame, _("Puzzle Selection"))
        selection.pack(fill=tk.X, pady=8)

        tk.Label(selection, text=_("Game:"), bg=self.current_theme.colors.background).grid(row=0, column=0, sticky="w")
        self.game_var = tk.StringVar(value=self.state.active_game)
        self.game_menu = ttk.Combobox(selection, textvariable=self.game_var, values=self.available_games(), state="readonly")
        self.game_menu.grid(row=0, column=1, sticky="ew", padx=6)
        self.game_menu.bind("<<ComboboxSelected>>", lambda _event: self._on_game_changed())

        tk.Label(selection, text=_("Difficulty:"), bg=self.current_theme.colors.background).grid(row=1, column=0, sticky="w")
        self.difficulty_var = tk.StringVar()
        self.difficulty_menu = ttk.Combobox(selection, textvariable=self.difficulty_var, state="readonly")
        self.difficulty_menu.grid(row=1, column=1, sticky="ew", padx=6)
        selection.columnconfigure(1, weight=1)

        actions = self.create_button_frame(
            self.main_frame,
            [
                {"text": _("Start Puzzle"), "command": self._handle_start},
                {"text": _("Complete"), "command": self._handle_complete},
                {"text": _("Hint"), "command": self._handle_hint},
            ],
        )
        actions.pack(fill=tk.X, pady=10)

        self.status_label = self.create_status_label(self.main_frame, "")
        self.status_label.pack(fill=tk.X, pady=6)

        log_frame = self.create_label_frame(self.main_frame, _("Activity Log"))
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_widget = self.create_log_widget(log_frame)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

    def _on_game_changed(self) -> None:
        self.set_active_game(self.game_var.get())
        self.update_display()

    def _handle_start(self) -> None:
        if not self.difficulty_var.get() and self.available_difficulties():
            first = next(iter(self._difficulty_display_map), "")
            self.difficulty_var.set(first)
        selected = self.difficulty_var.get()
        if selected:
            self.state.active_difficulty = self._difficulty_display_map.get(selected, self.state.active_difficulty)
        message = self.start_new_puzzle()
        self.log_message(self.log_widget, message)
        self.update_display()

    def _handle_complete(self) -> None:
        message = self.complete_puzzle()
        self.log_message(self.log_widget, message)
        self.update_display()

    def _handle_hint(self) -> None:
        message = self.request_hint()
        self.log_message(self.log_widget, message)

    def update_display(self) -> None:
        games = self.available_games()
        self.game_menu["values"] = games
        if self.state.active_game not in games and games:
            self.set_active_game(games[0])
            self.game_var.set(games[0])

        difficulties = self.available_difficulties()
        display_labels = []
        for difficulty in difficulties:
            display_labels.append(difficulty.display_name)
        self._difficulty_display_map = {difficulty.display_name: difficulty.key for difficulty in difficulties}
        self.difficulty_menu["values"] = list(self._difficulty_display_map.keys())
        if difficulties:
            current_key = self.state.active_difficulty
            if current_key:
                for label, key in self._difficulty_display_map.items():
                    if key == current_key:
                        self.difficulty_var.set(label)
                        break
            if not self.difficulty_var.get():
                first_label, first_key = next(iter(self._difficulty_display_map.items()))
                self.difficulty_var.set(first_label)
                self.state.active_difficulty = first_key

        summary = self.completion_summary()
        summary_text = ", ".join(f"{key}: {value}" for key, value in summary.items()) if summary else _("No completions yet.")
        next_unlock = self.upcoming_unlock()
        if next_unlock:
            unlock_text = _("Next unlock: {difficulty}").format(difficulty=next_unlock)
        else:
            unlock_text = _("All packs unlocked!")
        status = f"{summary_text}\n{unlock_text}\n{self.leaderboard_text()}"
        self.status_label.configure(text=status)


class LogicGamesPyQtGUI(QtBaseGUI, _LogicGameGUIController):
    """PyQt5 GUI companion for the logic puzzle progression system."""

    def __init__(
        self,
        root: Optional[QWidget] = None,
        *,
        config: Optional[QtGUIConfig] = None,
        service: LogicPuzzleService = LOGIC_PUZZLE_SERVICE,
        player_id: str = "solo",
    ) -> None:
        if not PYQT5_AVAILABLE:  # pragma: no cover - defensive guard
            raise RuntimeError("PyQt5 is not available in this environment.")
        root = root or QWidget()
        QtBaseGUI.__init__(self, root=root, config=config)
        _LogicGameGUIController.__init__(self, service, player_id)
        self._build_layout()
        self.update_display()

    def build_layout(self) -> None:  # pragma: no cover - layout handled in _build_layout
        self._build_layout()

    def _build_layout(self) -> None:
        layout = QVBoxLayout()
        header = self.create_header(self.root, _("Logic Puzzle Hub"))
        layout.addWidget(header)

        selection = QWidget(self.root)
        selection_layout = QHBoxLayout(selection)

        self.game_combo = QComboBox(selection)
        self.game_combo.currentTextChanged.connect(self._on_game_changed)
        selection_layout.addWidget(QLabel(_("Game:"), selection))
        selection_layout.addWidget(self.game_combo)

        self.difficulty_combo = QComboBox(selection)
        selection_layout.addWidget(QLabel(_("Difficulty:"), selection))
        selection_layout.addWidget(self.difficulty_combo)

        layout.addWidget(selection)

        button_bar = QWidget(self.root)
        button_layout = QHBoxLayout(button_bar)
        start_btn = QPushButton(_("Start Puzzle"), button_bar)
        start_btn.clicked.connect(self._handle_start)
        complete_btn = QPushButton(_("Complete"), button_bar)
        complete_btn.clicked.connect(self._handle_complete)
        hint_btn = QPushButton(_("Hint"), button_bar)
        hint_btn.clicked.connect(self._handle_hint)
        for btn in (start_btn, complete_btn, hint_btn):
            button_layout.addWidget(btn)
        layout.addWidget(button_bar)

        self.status_label = QLabel("", self.root)
        layout.addWidget(self.status_label)

        self.log_widget = QTextEdit(self.root)
        self.log_widget.setReadOnly(True)
        layout.addWidget(self.log_widget)

        self.root.setLayout(layout)

    def _on_game_changed(self, value: str) -> None:
        self.set_active_game(value)
        self.update_display()

    def _handle_start(self) -> None:
        if self.difficulty_combo.count() and not self.state.active_difficulty:
            self.state.active_difficulty = self.difficulty_combo.itemData(0)
        selected_index = self.difficulty_combo.currentIndex()
        if selected_index >= 0:
            self.state.active_difficulty = self.difficulty_combo.itemData(selected_index)
        message = self.start_new_puzzle()
        self.log_widget.append(message)
        self.update_display()

    def _handle_complete(self) -> None:
        message = self.complete_puzzle()
        self.log_widget.append(message)
        self.update_display()

    def _handle_hint(self) -> None:
        message = self.request_hint()
        self.log_widget.append(message)

    def update_display(self) -> None:
        games = self.available_games()
        self.game_combo.clear()
        self.game_combo.addItems(games)
        if self.state.active_game:
            index = self.game_combo.findText(self.state.active_game)
            if index >= 0:
                self.game_combo.setCurrentIndex(index)

        difficulties = self.available_difficulties()
        self.difficulty_combo.clear()
        for difficulty in difficulties:
            self.difficulty_combo.addItem(difficulty.display_name, difficulty.key)
        if self.state.active_difficulty:
            index = self.difficulty_combo.findData(self.state.active_difficulty)
            if index >= 0:
                self.difficulty_combo.setCurrentIndex(index)

        summary = self.completion_summary()
        summary_text = ", ".join(f"{key}: {value}" for key, value in summary.items()) if summary else _("No completions yet.")
        next_unlock = self.upcoming_unlock()
        if next_unlock:
            unlock_text = _("Next unlock: {difficulty}").format(difficulty=next_unlock)
        else:
            unlock_text = _("All packs unlocked!")
        status = f"{summary_text}\n{unlock_text}\n{self.leaderboard_text()}"
        self.status_label.setText(status)


__all__ = ["LogicGamesTkinterGUI", "LogicGamesPyQtGUI"]
