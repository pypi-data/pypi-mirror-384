"""Bluff (Cheat) card game engine and user interfaces.

This package provides the core engine for the card game Bluff (also known as
Cheat or I Doubt It), along with optional graphical user interfaces (GUIs).

The main components are re-exported here to provide a simplified facade for
easy importing.

Core Components:
- ``BluffGame``: The main game engine.
- ``DifficultyLevel``: Configuration for bot difficulty.
- ``Phase``: An enumeration for the different phases of the game.
- ``run_cli``: A function to launch the command-line interface.

Optional GUI Components:
- ``BluffGUI`` (Tkinter): A Tkinter-based GUI for the game.
- ``run_gui``: A function to launch the Tkinter GUI.
- ``BluffPyQtGUI`` (PyQt5): A PyQt5-based GUI for the game.
"""

from .bluff import BluffGame, DifficultyLevel, Phase, run_cli

# Attempt to import and expose the optional Tkinter GUI.
try:  # pragma: no cover - optional GUI dependency
    from .gui import BluffGUI, run_gui
except ImportError:  # pragma: no cover - degrade gracefully
    BluffGUI = None  # type: ignore[assignment, misc]

    def run_gui(*args, **kwargs):  # type: ignore[misc]
        """Placeholder for the Tkinter GUI runner."""
        raise RuntimeError("Tkinter is required for the Bluff GUI but is not available.")


# Attempt to import and expose the optional PyQt5 GUI.
try:  # pragma: no cover - optional PyQt5 dependency
    from .gui_pyqt import BluffPyQtGUI
except ImportError:  # pragma: no cover - degrade gracefully
    BluffPyQtGUI = None  # type: ignore[assignment, misc]


__all__ = [
    "BluffGame",
    "DifficultyLevel",
    "Phase",
    "run_cli",
    "BluffGUI",
    "run_gui",
    "BluffPyQtGUI",
]
