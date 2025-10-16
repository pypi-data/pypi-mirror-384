"""Bunco game engine."""

from __future__ import annotations

import random
from typing import List

from common.game_engine import GameEngine, GameState


class BuncoGame(GameEngine[str, int]):
    """Bunco party dice game.

    Roll three dice trying to match the round number.
    Bunco = all three dice match round number (21 points).
    """

    def __init__(self, num_players: int = 4) -> None:
        """Initialize game."""
        self.num_players = max(2, num_players)
        self.reset()

    def reset(self) -> None:
        """Reset game."""
        self.state = GameState.NOT_STARTED
        self.round_num = 1
        self.current_player_idx = 0
        self.scores = [0] * self.num_players
        self.round_points = 0

    def is_game_over(self) -> bool:
        """Check if game over."""
        return self.round_num > 6

    def get_current_player(self) -> int:
        """Get current player."""
        return self.current_player_idx

    def get_valid_moves(self) -> List[str]:
        """Get valid moves."""
        return ["roll"]

    def make_move(self, move: str) -> bool:
        """Roll dice."""
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        if move == "roll":
            dice = [random.randint(1, 6) for _ in range(3)]
            points = 0

            # Bunco: all three match round
            if all(d == self.round_num for d in dice):
                points = 21
            # Mini-bunco: all three match (but not round)
            elif dice[0] == dice[1] == dice[2]:
                points = 5
            # Matches: count dice matching round
            else:
                points = dice.count(self.round_num)

            self.scores[self.current_player_idx] += points

            # Next player or next round
            if points == 0:
                self.current_player_idx = (self.current_player_idx + 1) % self.num_players
                if self.current_player_idx == 0:
                    self.round_num += 1

            return True
        return False

    def get_winner(self) -> int | None:
        """Get winner."""
        if not self.is_game_over():
            return None
        return max(range(self.num_players), key=lambda i: self.scores[i])

    def get_game_state(self) -> GameState:
        """Get current game state.

        Returns:
            Current state of the game
        """
        return self.state
