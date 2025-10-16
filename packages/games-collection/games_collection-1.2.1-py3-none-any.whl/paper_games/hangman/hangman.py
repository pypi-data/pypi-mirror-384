"""Game engine and logic for Hangman with tactile feedback.

This module provides the core game logic for Hangman, including word selection,
guess validation, state tracking, and ASCII art rendering of the gallows.
"""

from __future__ import annotations

import json
import random
import string
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence, Set

# The path to the JSON file containing the wordlist.
WORDLIST_PATH = Path(__file__).with_name("wordlist.json")
THEMED_WORDS_PATH = Path(__file__).with_name("themed_words.json")
# A cache for the default wordlist to avoid reading from disk multiple times.
_DEFAULT_WORD_CACHE: List[str] | None = None
_THEMED_WORD_CACHE: dict[str, List[str]] | None = None


def _load_words_from_disk() -> List[str]:
    """Loads the wordlist from the JSON file."""
    data = json.loads(WORDLIST_PATH.read_text(encoding="utf-8"))
    collected: Set[str] = set()
    # Collect words from all difficulty levels.
    for difficulty in ("easy", "medium", "hard"):
        collected.update(word.lower() for word in data.get(difficulty, ()))
    if not collected:
        raise ValueError("No words found in bundled wordlist.json")
    return sorted(collected)


def load_default_words() -> List[str]:
    """Return a copy of the bundled hangman words, using a cache to avoid re-reading the file."""
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


def load_themed_words(theme: str | None = None) -> List[str] | dict[str, List[str]]:
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
        available = ", ".join(sorted(_THEMED_WORD_CACHE.keys()))
        raise ValueError(f"Unknown theme: {theme}. Available themes: {available}")

    return list(_THEMED_WORD_CACHE[theme])


# The ASCII art stages of the hangman drawing.
HANGMAN_STAGES: Sequence[str] = (
    r"""
      _______
     |/      |
     |
     |
     |
     |
    _|___
    """.rstrip(),
    r"""
      _______
     |/      |
     |      (_)
     |
     |
     |
    _|___
    """.rstrip(),
    r"""
      _______
     |/      |
     |      (_)
     |       |
     |       |
     |
    _|___
    """.rstrip(),
    r"""
      _______
     |/      |
     |      (_)
     |      \|
     |       |
     |
    _|___
    """.rstrip(),
    r"""
      _______
     |/      |
     |      (_)
     |      \|/
     |       |
     |
    _|___
    """.rstrip(),
    r"""
      _______
     |/      |
     |      (_)
     |      \|/
     |       |
     |      /
    _|___
    """.rstrip(),
    r"""
      _______
     |/      |
     |      (_)
     |      \|/
     |       |
     |      / \
    _|___
    """.rstrip(),
)

# Alternative ASCII art style - "simple"
HANGMAN_STAGES_SIMPLE: Sequence[str] = (
    r"""
    +---+
    |   |
        |
        |
        |
        |
    ========
    """.rstrip(),
    r"""
    +---+
    |   |
    O   |
        |
        |
        |
    ========
    """.rstrip(),
    r"""
    +---+
    |   |
    O   |
    |   |
        |
        |
    ========
    """.rstrip(),
    r"""
    +---+
    |   |
    O   |
   /|   |
        |
        |
    ========
    """.rstrip(),
    r"""
    +---+
    |   |
    O   |
   /|\  |
        |
        |
    ========
    """.rstrip(),
    r"""
    +---+
    |   |
    O   |
   /|\  |
   /    |
        |
    ========
    """.rstrip(),
    r"""
    +---+
    |   |
    O   |
   /|\  |
   / \  |
        |
    ========
    """.rstrip(),
)

# Alternative ASCII art style - "minimal"
HANGMAN_STAGES_MINIMAL: Sequence[str] = (
    r"""





    ___
    """.rstrip(),
    r"""


    O


    ___
    """.rstrip(),
    r"""


    O
    |

    ___
    """.rstrip(),
    r"""


    O
   \|

    ___
    """.rstrip(),
    r"""


    O
   \|/

    ___
    """.rstrip(),
    r"""


    O
   \|/
   /
    ___
    """.rstrip(),
    r"""


    O
   \|/
   / \
    ___
    """.rstrip(),
)

# Map of available art styles
HANGMAN_ART_STYLES: dict[str, Sequence[str]] = {
    "classic": HANGMAN_STAGES,
    "simple": HANGMAN_STAGES_SIMPLE,
    "minimal": HANGMAN_STAGES_MINIMAL,
}


@dataclass
class HangmanGame:
    """Encapsulates the state and logic of a hangman round."""

    words: Iterable[str] = field(default_factory=load_default_words)
    max_attempts: int = 6
    theme: str | None = None
    hints_enabled: bool = True
    max_hints: int = 3
    art_style: str = "classic"

    def __post_init__(self) -> None:
        """Validates the initial game state after the dataclass is created."""
        self.words = [word.lower() for word in self.words]
        if not self.words:
            raise ValueError("At least one word must be supplied.")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least one.")
        self.hints_used: int = 0
        self.reset()

    def reset(self) -> None:
        """Select a new word and reset guesses for a new game."""
        self.secret_word: str = random.choice(list(self.words))
        self.guessed_letters: Set[str] = set()
        self.guessed_words: Set[str] = set()
        self.wrong_guesses: Set[str] = set()

    def guess(self, entry: str) -> bool:
        """Process a player's guessed letter or full word.

        Returns:
            bool: True if the guess was correct, False otherwise.
        """
        entry = entry.lower().strip()
        if not entry or any(ch not in string.ascii_lowercase for ch in entry):
            raise ValueError("Guesses must contain only letters.")

        # Handle single-letter guesses.
        if len(entry) == 1:
            if entry in self.guessed_letters or entry in self.wrong_guesses:
                raise ValueError(f"Letter '{entry}' has already been guessed.")
            if entry in self.secret_word:
                self.guessed_letters.add(entry)
                return True
            self.wrong_guesses.add(entry)
            return False

        # Handle full-word guesses.
        if entry == self.secret_word:
            self.guessed_letters.update(set(self.secret_word))
            self.guessed_words.add(entry)
            return True

        if entry in self.guessed_words:
            raise ValueError(f"Word '{entry}' has already been attempted.")

        self.guessed_words.add(entry)
        self.wrong_guesses.add(entry)
        return False

    @property
    def attempts_left(self) -> int:
        """Return how many incorrect guesses remain."""
        return self.max_attempts - len(self.wrong_guesses)

    @property
    def obscured_word(self) -> str:
        """Return the secret word with unguessed letters hidden by underscores."""
        return " ".join(letter if letter in self.guessed_letters else "_" for letter in self.secret_word)

    @property
    def stage(self) -> str:
        """Return the ASCII gallows that reflects the current danger level."""
        wrong = self.max_attempts - self.attempts_left
        stages = HANGMAN_ART_STYLES.get(self.art_style, HANGMAN_STAGES)
        if self.max_attempts <= 0:
            return stages[-1]
        # Scale the number of wrong guesses to the number of hangman stages.
        scale = (len(stages) - 1) / self.max_attempts
        index = min(len(stages) - 1, int(round(wrong * scale)))
        return stages[index]

    def status_lines(self) -> List[str]:
        """Human-friendly summary of the current round."""
        wrong_letters = sorted(guess for guess in self.wrong_guesses if len(guess) == 1)
        wrong_words = sorted(guess for guess in self.wrong_guesses if len(guess) > 1)
        lines = [self.stage, f"Word: {self.obscured_word}"]
        if self.theme:
            lines.append(f"Theme: {self.theme}")
        if wrong_letters:
            lines.append(f"Wrong letters: {' '.join(wrong_letters)}")
        if wrong_words:
            lines.append("Wrong words: " + ", ".join(wrong_words))
        lines.append(f"Attempts left: {self.attempts_left}")
        if self.hints_enabled:
            hints_left = self.max_hints - self.hints_used
            lines.append(f"Hints remaining: {hints_left}")
        return lines

    def is_won(self) -> bool:
        """Return True if all letters in the secret word have been guessed."""
        return all(letter in self.guessed_letters for letter in set(self.secret_word))

    def is_lost(self) -> bool:
        """Return True if the player has exhausted the allowed attempts."""
        return self.attempts_left <= 0

    def get_hint(self) -> str | None:
        """Reveal an unguessed letter as a hint.

        Returns:
            The revealed letter, or None if no hints available.
        """
        if not self.hints_enabled:
            return None
        if self.hints_used >= self.max_hints:
            return None

        # Find letters that haven't been guessed yet
        unguessed = [letter for letter in set(self.secret_word) if letter not in self.guessed_letters]

        if not unguessed:
            return None

        # Reveal a random unguessed letter
        hint_letter = random.choice(unguessed)
        self.guessed_letters.add(hint_letter)
        self.hints_used += 1
        return hint_letter
