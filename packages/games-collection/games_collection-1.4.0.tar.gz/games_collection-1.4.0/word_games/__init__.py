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
    "AnagramsGame",
    "AsyncWordPlaySession",
    "CrosswordClue",
    "CrosswordGame",
    "CrosswordPackManager",
    "DictionaryValidator",
    "TriviaAPIClient",
    "TriviaCache",
    "TriviaGame",
    "TriviaQuestion",
    "WordBuilderGame",
    "WordPlaySession",
]

from .anagrams import AnagramsGame
from .crossword import CrosswordClue, CrosswordGame, CrosswordPackManager
from .trivia import TriviaAPIClient, TriviaCache, TriviaGame, TriviaQuestion
from .wordbuilder import AsyncWordPlaySession, DictionaryValidator, WordBuilderGame, WordPlaySession
