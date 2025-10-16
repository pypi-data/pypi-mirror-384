"""Battleship game package.

Battleship implementation with full fleets and a hunting AI opponent.
Re-exports core types so ``paper_games.battleship`` behaves like a facade for
both the game engine and the CLI.
"""

from .battleship import DEFAULT_FLEET, EXTENDED_FLEET, SMALL_FLEET, BattleshipGame, Board, Coordinate, Ship
from .cli import play

# GUI is optional. Prefer PyQt5 implementation when available.
try:
    from .gui_pyqt import run_gui

    __all__ = [
        "BattleshipGame",
        "Board",
        "Ship",
        "Coordinate",
        "DEFAULT_FLEET",
        "EXTENDED_FLEET",
        "SMALL_FLEET",
        "play",
        "run_gui",
    ]
except ImportError:
    try:
        from .gui import run_gui

        __all__ = [
            "BattleshipGame",
            "Board",
            "Ship",
            "Coordinate",
            "DEFAULT_FLEET",
            "EXTENDED_FLEET",
            "SMALL_FLEET",
            "play",
            "run_gui",
        ]
    except ImportError:
        __all__ = [
            "BattleshipGame",
            "Board",
            "Ship",
            "Coordinate",
            "DEFAULT_FLEET",
            "EXTENDED_FLEET",
            "SMALL_FLEET",
            "play",
        ]
