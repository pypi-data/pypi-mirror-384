"""Dots and Boxes game package.

Dots and Boxes for the terminal with a chain-aware AI opponent.
Re-exports core types so ``paper_games.dots_and_boxes`` behaves like a facade for
both the game engine and the CLI.
"""

from .cli import play
from .dots_and_boxes import DotsAndBoxes
from .network import host_game, join_game
from .tournament import Tournament, play_tournament

# GUI is optional (requires tkinter)
try:
    from .gui import run_gui

    __all__ = ["DotsAndBoxes", "play", "run_gui", "Tournament", "play_tournament", "host_game", "join_game"]
except ImportError:
    __all__ = ["DotsAndBoxes", "play", "Tournament", "play_tournament", "host_game", "join_game"]
