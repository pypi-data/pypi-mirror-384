"""Unscramble game package.

Unscramble-the-word party game.
Re-exports core types so ``paper_games.unscramble`` behaves like a facade for
both the game engine and the CLI.
"""

from .cli import play
from .stats import GameStats
from .unscramble import UnscrambleGame, list_themes, load_themed_words, load_unscramble_words, load_words_by_difficulty

__all__ = [
    "UnscrambleGame",
    "GameStats",
    "play",
    "load_unscramble_words",
    "load_words_by_difficulty",
    "load_themed_words",
    "list_themes",
]
