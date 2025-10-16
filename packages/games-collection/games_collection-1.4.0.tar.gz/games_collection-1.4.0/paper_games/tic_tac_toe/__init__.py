"""Tic-tac-toe game package.

Tic-tac-toe with a minimax-powered computer opponent.
Re-exports core types so ``paper_games.tic_tac_toe`` behaves like a facade for
both the game engine and the CLI.
"""

from .cli import play
from .tic_tac_toe import COORDINATES, INDEX_TO_COORD, TicTacToeGame

__all__ = ["TicTacToeGame", "COORDINATES", "INDEX_TO_COORD", "play"]
