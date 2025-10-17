"""Nim game package.

Classic Nim with configurable rules and an optimal computer opponent.
Re-exports core types so ``paper_games.nim`` behaves like a facade for
both the game engine and the CLI.

Also includes Nim variants:
- NorthcottGame: Players slide pieces towards each other on rows
- WythoffGame: Two heaps with diagonal moves allowed
"""

from .cli import play
from .nim import NimGame, NorthcottGame, WythoffGame

__all__ = ["NimGame", "NorthcottGame", "WythoffGame", "play"]
