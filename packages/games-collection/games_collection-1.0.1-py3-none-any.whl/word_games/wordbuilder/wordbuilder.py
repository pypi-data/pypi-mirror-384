"""WordBuilder game engine."""

from __future__ import annotations

import random
from typing import List

from common.game_engine import GameEngine, GameState


class WordBuilderGame(GameEngine[str, int]):
    """Tile-based word building game (Scrabble-like)."""

    TILE_VALUES = {
        "A": 1,
        "E": 1,
        "I": 1,
        "O": 1,
        "U": 1,
        "L": 1,
        "N": 1,
        "S": 1,
        "T": 1,
        "R": 1,
        "D": 2,
        "G": 2,
        "B": 3,
        "C": 3,
        "M": 3,
        "P": 3,
        "F": 4,
        "H": 4,
        "V": 4,
        "W": 4,
        "Y": 4,
        "K": 5,
        "J": 8,
        "X": 8,
        "Q": 10,
        "Z": 10,
    }

    COMMON_WORDS = ["CAT", "DOG", "HAT", "BAT", "RAT", "MAT", "SAT"]

    def __init__(self) -> None:
        """Initialize game."""
        self.reset()

    def reset(self) -> None:
        """Reset game."""
        self.state = GameState.NOT_STARTED
        self.hand = self._draw_tiles(7)
        self.score = 0
        self.turns = 0

    def _draw_tiles(self, count: int) -> List[str]:
        """Draw random tiles."""
        letters = list(self.TILE_VALUES.keys())
        return [random.choice(letters) for _ in range(count)]

    def is_game_over(self) -> bool:
        """Check if game over."""
        return self.turns >= 10

    def get_current_player(self) -> int:
        """Get current player."""
        return 0

    def get_valid_moves(self) -> List[str]:
        """Get valid moves (any word)."""
        return ["any_word"]

    def make_move(self, move: str) -> bool:
        """Play a word."""
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        if self.is_game_over():
            return False

        word = move.upper()

        # Check if can make word from hand
        hand_copy = self.hand.copy()
        for letter in word:
            if letter in hand_copy:
                hand_copy.remove(letter)
            else:
                return False

        # Calculate score
        points = sum(self.TILE_VALUES.get(letter, 0) for letter in word)
        self.score += points

        # Remove used tiles and draw new ones
        for letter in word:
            self.hand.remove(letter)
        self.hand.extend(self._draw_tiles(len(word)))

        self.turns += 1

        if self.is_game_over():
            self.state = GameState.FINISHED

        return True

    def get_winner(self) -> int | None:
        """Get winner."""
        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Get current game state.

        Returns:
            Current state of the game
        """
        return self.state
