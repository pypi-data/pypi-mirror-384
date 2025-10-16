"""Blackjack game package."""

# Re-export core types so ``card_games.blackjack`` behaves like a facade for
# both the engine and the GUI helper functions.
from .game import BlackjackGame, BlackjackHand, Outcome

# Always export core engine types
__all__ = ["BlackjackGame", "BlackjackHand", "Outcome"]

# Optional Tkinter GUI
try:  # pragma: no cover - optional dependency
    from .gui import BlackjackApp, run_app

    __all__.extend(["BlackjackApp", "run_app"])
except ImportError:  # pragma: no cover - optional dependency
    BlackjackApp = None  # type: ignore[assignment]
    run_app = None  # type: ignore[assignment]

# Optional PyQt5 GUI
try:  # pragma: no cover - optional dependency
    from .gui_pyqt import BlackjackTable, run_gui

    __all__.extend(["BlackjackTable", "run_gui"])
except ImportError:  # pragma: no cover - optional dependency
    BlackjackTable = None  # type: ignore[assignment]
    run_gui = None  # type: ignore[assignment]
