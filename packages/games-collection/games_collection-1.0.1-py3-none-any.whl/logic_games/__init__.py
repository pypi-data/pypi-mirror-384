"""A collection of interactive logic and puzzle game implementations.

This package provides a suite of logic puzzles and brain teasers, each with its own engine,
difficulty levels, and user interface. The games include:
- Minesweeper - Classic mine detection game with difficulty levels
- Sokoban - Warehouse puzzle with box-pushing mechanics
- Sliding Puzzle (15-puzzle) - Number tile sliding game with solvability
- Lights Out - Toggle-based puzzle with pattern solving
- Picross/Nonograms - Picture logic puzzles with row/column hints

Each game can be run as a standalone application from the command line.
"""

from __future__ import annotations

# Export the subpackages so ``import logic_games`` presents the available games
# in a discoverable list.
__all__ = [
    "MinesweeperGame",
    "SokobanGame",
    "SlidingPuzzleGame",
    "LightsOutGame",
    "LightBulb",
    "PicrossGame",
]

from .lights_out import LightBulb, LightsOutGame
from .minesweeper import MinesweeperGame
from .picross import PicrossGame
from .sliding_puzzle import SlidingPuzzleGame
from .sokoban import SokobanGame
