"""Uno game implementation with console and GUI front-ends."""

# Public re-exports make it easy for callers to discover the primary
# interfaces without digging through submodules.
from .network import NetworkGameInterface, NetworkProtocolError, UnoNetworkClient, UnoNetworkServer
from .uno import (
    ConsoleUnoInterface,
    CustomDeckLoader,
    CustomDeckValidationError,
    HouseRules,
    PlayerDecision,
    UnoCard,
    UnoDeck,
    UnoGame,
    UnoInterface,
    UnoPlayer,
    build_players,
    main,
)

# GUI components are imported conditionally to avoid tkinter dependency
__all__ = [
    "ConsoleUnoInterface",
    "CustomDeckLoader",
    "CustomDeckValidationError",
    "HouseRules",
    "PlayerDecision",
    "UnoCard",
    "UnoDeck",
    "UnoInterface",
    "UnoGame",
    "UnoPlayer",
    "build_players",
    "main",
    "NetworkGameInterface",
    "NetworkProtocolError",
    "UnoNetworkClient",
    "UnoNetworkServer",
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
