"""A collection of interactive logic and puzzle game implementations.

This package provides a suite of classic logic puzzles and brain teasers,
each with its own game engine, difficulty levels, and user interfaces.
The games are designed to be modular and extensible, allowing for easy
integration into various application front-ends.

The available games include:
- **Minesweeper**: The classic mine detection game with multiple difficulty levels.
- **Sokoban**: A warehouse puzzle focused on box-pushing mechanics.
- **Sliding Puzzle**: The 15-puzzle and its variants with a solvability check.
- **Lights Out**: A toggle-based puzzle with a unique physical simulation.
- **Picross/Nonograms**: Picture logic puzzles solved by deducing row and column hints.

Each game can be run as a standalone application from the command line,
and the package also provides a centralized progression system for tracking
player achievements and unlocking new challenges.

Key Modules:
    - `progression`: Manages player progress, unlocks, and leaderboards.
    - `registry`: Registers the available games with the progression service.
    - `gui`: Provides Tkinter and PyQt5 front-ends for the game hub.
"""

from __future__ import annotations

# Define the public API for the logic_games package.
# This makes the main game classes and services directly accessible
# to consumers of the package.
__all__ = [
    "MinesweeperGame",
    "SokobanGame",
    "SlidingPuzzleGame",
    "LightsOutGame",
    "LightBulb",
    "PicrossGame",
    "LOGIC_PUZZLE_SERVICE",
    "register_default_logic_games",
]

from .lights_out import LightBulb, LightsOutGame
from .minesweeper import MinesweeperGame
from .picross import PicrossGame
from .progression import LOGIC_PUZZLE_SERVICE
from .registry import register_default_logic_games
from .sliding_puzzle import SlidingPuzzleGame
from .sokoban import SokobanGame

# Ensure that the default game registrations are loaded when the package
# is imported. This makes the games available to the progression service
# immediately.
register_default_logic_games()
