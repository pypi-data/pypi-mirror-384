"""Uno game implementation with console and GUI front-ends."""

# Public re-exports make it easy for callers to discover the primary
# interfaces without digging through submodules.
from .uno import ConsoleUnoInterface, PlayerDecision, UnoCard, UnoDeck, UnoGame, build_players, main

# GUI components are imported conditionally to avoid tkinter dependency
__all__ = [
    "ConsoleUnoInterface",
    "PlayerDecision",
    "UnoCard",
    "UnoDeck",
    "UnoGame",
    "build_players",
    "main",
]

# Try to import GUI components, but don't fail if tkinter is unavailable
try:
    from .gui import TkUnoInterface, launch_uno_gui

    __all__.extend(["TkUnoInterface", "launch_uno_gui"])
except ImportError:
    # tkinter not available, GUI components won't be exported
    pass

try:
    from .gui_pyqt import PyQtUnoInterface, launch_uno_gui_pyqt

    __all__.extend(["PyQtUnoInterface", "launch_uno_gui_pyqt"])
except ImportError:
    # PyQt5 not available, PyQt GUI components won't be exported
    pass
