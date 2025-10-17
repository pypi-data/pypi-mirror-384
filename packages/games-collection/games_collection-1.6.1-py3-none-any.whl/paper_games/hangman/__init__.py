"""Hangman game package.

Terminal-based hangman implementation with tactile feedback.
Re-exports core types so ``paper_games.hangman`` behaves like a facade for
both the game engine and the CLI.
"""

from .cli import play
from .hangman import HANGMAN_ART_STYLES, HANGMAN_STAGES, HangmanGame, load_default_words, load_themed_words, load_words_by_difficulty

__all__ = [
    "HangmanGame",
    "HANGMAN_STAGES",
    "HANGMAN_ART_STYLES",
    "load_default_words",
    "load_words_by_difficulty",
    "load_themed_words",
    "play",
]
