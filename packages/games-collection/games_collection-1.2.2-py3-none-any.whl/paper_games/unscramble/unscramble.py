"""Game engine and logic for the Unscramble-the-word party game.

This module provides the core game logic for Unscramble, including word
selection, scrambling, and guess validation.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

from ..hangman import load_default_words

# Path to word data files
WORDLIST_PATH = Path(__file__).with_name("wordlist.json")
THEMED_WORDS_PATH = Path(__file__).with_name("themed_words.json")

# Caches for word data
_DEFAULT_WORD_CACHE: List[str] | None = None
_THEMED_WORD_CACHE: Dict[str, List[str]] | None = None


def _load_words_from_disk() -> List[str]:
    """Load the wordlist from the JSON file."""
    if not WORDLIST_PATH.exists():
        # Fallback to hangman words if wordlist doesn't exist
        return load_default_words()

    data = json.loads(WORDLIST_PATH.read_text(encoding="utf-8"))
    collected: Set[str] = set()
    # Collect words from all difficulty levels
    for difficulty in ("easy", "medium", "hard"):
        collected.update(word.lower() for word in data.get(difficulty, ()))
    if not collected:
        return load_default_words()
    return sorted(collected)


def load_unscramble_words() -> List[str]:
    """Return a copy of the bundled unscramble words, using a cache."""
    global _DEFAULT_WORD_CACHE
    if _DEFAULT_WORD_CACHE is None:
        _DEFAULT_WORD_CACHE = _load_words_from_disk()
    return list(_DEFAULT_WORD_CACHE)


def load_words_by_difficulty(difficulty: str = "all") -> List[str]:
    """Load words filtered by difficulty level.

    Args:
        difficulty: One of "easy", "medium", "hard", or "all"

    Returns:
        List of words matching the difficulty level.
    """
    if not WORDLIST_PATH.exists():
        # Fallback to categorizing hangman words by length
        words = load_default_words()
        if difficulty == "easy":
            return [w for w in words if len(w) >= 6]
        elif difficulty == "medium":
            return [w for w in words if 4 <= len(w) <= 5]
        elif difficulty == "hard":
            return [w for w in words if len(w) == 3]
        else:
            return words

    data = json.loads(WORDLIST_PATH.read_text(encoding="utf-8"))
    if difficulty == "all":
        collected: Set[str] = set()
        for diff in ("easy", "medium", "hard"):
            collected.update(word.lower() for word in data.get(diff, ()))
        return sorted(collected)
    elif difficulty in ("easy", "medium", "hard"):
        return [word.lower() for word in data.get(difficulty, [])]
    else:
        raise ValueError(f"Invalid difficulty: {difficulty}. Must be 'easy', 'medium', 'hard', or 'all'")


def load_themed_words(theme: Optional[str] = None) -> List[str] | Dict[str, List[str]]:
    """Load themed word lists.

    Args:
        theme: Optional theme name. If None, returns all themes.

    Returns:
        List of words for the specified theme, or dict of all themes.
    """
    global _THEMED_WORD_CACHE
    if _THEMED_WORD_CACHE is None:
        if not THEMED_WORDS_PATH.exists():
            _THEMED_WORD_CACHE = {}
        else:
            _THEMED_WORD_CACHE = json.loads(THEMED_WORDS_PATH.read_text(encoding="utf-8"))

    if theme is None:
        return dict(_THEMED_WORD_CACHE)

    if theme not in _THEMED_WORD_CACHE:
        raise ValueError(f"Theme '{theme}' not found. Available themes: {list(_THEMED_WORD_CACHE.keys())}")

    return list(_THEMED_WORD_CACHE[theme])


def list_themes() -> str:
    """List all available themes.

    Returns:
        Formatted string listing all themes with word counts.
    """
    themes = load_themed_words()
    if not themes:
        return "No themes available."

    lines = ["Available themes:"]
    for theme_name, words in sorted(themes.items()):
        lines.append(f"  - {theme_name}: {len(words)} words")
    return "\n".join(lines)


@dataclass
class UnscrambleGame:
    """Present a scrambled word and track guesses."""

    words: Iterable[str] = field(default_factory=load_unscramble_words)
    rng: random.Random = field(default_factory=random.Random)
    difficulty: Optional[str] = None
    theme: Optional[str] = None

    def __post_init__(self) -> None:
        """Initializes the game state after the dataclass is created."""
        self.words = [word.lower() for word in self.words]
        if not self.words:
            raise ValueError("Provide at least one word to scramble.")
        self.secret_word = ""
        self.scrambled = ""

    def new_round(self) -> str:
        """Starts a new round with a new secret word."""
        self.secret_word = self.rng.choice(self.words)
        letters = list(self.secret_word)
        self.rng.shuffle(letters)
        # Ensure the scrambled word is different from the original word.
        if letters == list(self.secret_word):
            # A simple way to ensure it's different is to move the last letter to the front.
            letters.insert(0, letters.pop())
        self.scrambled = "".join(letters)
        return self.scrambled

    def guess(self, word: str) -> bool:
        """Checks if a guessed word matches the secret word."""
        if not self.secret_word:
            raise ValueError("Start a round before guessing.")
        return word.lower().strip() == self.secret_word
