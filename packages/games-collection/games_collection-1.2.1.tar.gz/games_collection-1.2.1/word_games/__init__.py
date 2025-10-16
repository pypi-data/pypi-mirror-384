"""A collection of interactive word and trivia game implementations.

This package provides a suite of word-based and trivia games, each with its own engine,
scoring system, and user interface. The games include:
- Trivia Quiz - Multiple choice questions from various categories
- Crossword - Create and solve crossword puzzles with clue system
- Anagrams - Word rearrangement game with scoring system
- WordBuilder - Tile-based word building game (Scrabble-like)

Each game can be run as a standalone application from the command line.
"""

from __future__ import annotations

# Export the subpackages so ``import word_games`` presents the available games
# in a discoverable list.
__all__ = [
    "TriviaGame",
    "CrosswordGame",
    "AnagramsGame",
    "WordBuilderGame",
]

from .anagrams import AnagramsGame
from .crossword import CrosswordGame
from .trivia import TriviaGame
from .wordbuilder import WordBuilderGame
