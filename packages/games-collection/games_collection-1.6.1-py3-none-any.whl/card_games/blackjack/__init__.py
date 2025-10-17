"""Blackjack game package.

This package provides the core engine for playing Blackjack, along with optional
graphical user interfaces (GUIs) built with Tkinter and PyQt5.

The main components are re-exported here to provide a simplified facade for
importing. This allows users to import core classes like ``BlackjackGame``
directly from ``card_games.blackjack``.

Core Components:
- ``BlackjackGame``: The main game engine.
- ``BlackjackHand``: Represents a player's or dealer's hand.
- ``Outcome``: An enumeration of possible hand outcomes.

Optional GUI Components:
- ``BlackjackApp`` (Tkinter): A simple Tkinter-based GUI for the game.
- ``BlackjackTable`` (PyQt5): A more advanced PyQt5-based GUI.
"""

# Re-export core types so ``card_games.blackjack`` behaves like a facade for
# both the engine and the GUI helper functions.
from .game import BlackjackGame, BlackjackHand, Outcome

# Always export core engine types.
__all__ = ["BlackjackGame", "BlackjackHand", "Outcome"]

# Attempt to import and expose the optional Tkinter GUI.
try:  # pragma: no cover - optional dependency
    from .gui import BlackjackApp, run_app

    __all__.extend(["BlackjackApp", "run_app"])
except ImportError:  # pragma: no cover - optional dependency
    # If Tkinter is not available, define placeholders.
    BlackjackApp = None  # type: ignore[assignment]
    run_app = None  # type: ignore[assignment]

# Attempt to import and expose the optional PyQt5 GUI.
try:  # pragma: no cover - optional dependency
    from .gui_pyqt import BlackjackTable, run_gui

    __all__.extend(["BlackjackTable", "run_gui"])
except ImportError:  # pragma: no cover - optional dependency
    # If PyQt5 is not available, define placeholders.
    BlackjackTable = None  # type: ignore[assignment]
    run_gui = None  # type: ignore[assignment]
