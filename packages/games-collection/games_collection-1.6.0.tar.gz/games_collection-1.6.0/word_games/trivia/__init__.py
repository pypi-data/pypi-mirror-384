"""Trivia Quiz implementation.

Multiple choice trivia questions from various categories
"""

from __future__ import annotations

__all__ = [
    "TriviaAPIClient",
    "TriviaCache",
    "TriviaGame",
    "TriviaQuestion",
]

from .trivia import TriviaAPIClient, TriviaCache, TriviaGame, TriviaQuestion
