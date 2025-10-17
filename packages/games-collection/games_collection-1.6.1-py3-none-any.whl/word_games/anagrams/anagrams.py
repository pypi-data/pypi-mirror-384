"""Anagrams game engine."""

from __future__ import annotations

import random
from typing import List

from common.game_engine import GameEngine, GameState


class AnagramsGame(GameEngine[str, int]):
    """Anagrams word rearrangement game."""

    WORD_PAIRS = [
        ("listen", "silent"),
        ("earth", "heart"),
        ("dairy", "diary"),
        ("study", "dusty"),
        ("night", "thing"),
        ("below", "elbow"),
        ("state", "taste"),
        ("worth", "throw"),
        ("angel", "angle"),
        ("read", "dear"),
    ]

    def __init__(self, num_rounds: int = 5) -> None:
        """Initialize game."""
        self.num_rounds = min(num_rounds, len(self.WORD_PAIRS))
        self.reset()

    def reset(self) -> None:
        """Reset game."""
        self.state = GameState.NOT_STARTED
        self.pairs = random.sample(self.WORD_PAIRS, self.num_rounds)
        self.current_round = 0
        self.score = 0

    def is_game_over(self) -> bool:
        """Check if game over."""
        return self.current_round >= len(self.pairs)

    def get_current_player(self) -> int:
        """Get current player."""
        return 0

    def get_valid_moves(self) -> List[str]:
        """Get valid moves (any string)."""
        return ["any_string"]

    def make_move(self, move: str) -> bool:
        """Submit word guess."""
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        if self.is_game_over():
            return False

        scrambled, answer = self.pairs[self.current_round]
        if move.lower() == answer.lower():
            self.score += 1

        self.current_round += 1

        if self.is_game_over():
            self.state = GameState.FINISHED

        return True

    def get_current_scrambled(self) -> str:
        """Get current scrambled word."""
        if self.is_game_over():
            return ""
        return self.pairs[self.current_round][0]

    def get_winner(self) -> int | None:
        """Get winner."""
        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Get current game state.

        Returns:
            Current state of the game
        """
        return self.state
