"""Craps game engine implementation."""

from __future__ import annotations

import random
from enum import Enum
from typing import List

from common.architecture.events import GameEventType
from common.game_engine import GameEngine, GameState


class BetType(Enum):
    """Types of bets in Craps."""

    PASS_LINE = "pass"
    DONT_PASS = "dont_pass"


class CrapsGame(GameEngine[str, int]):
    """Craps casino dice game.

    Players bet on dice rolls. Pass line wins on 7/11 on come-out,
    loses on 2/3/12. Otherwise, point is established and must be
    rolled again before a 7.
    """

    def __init__(self) -> None:
        """Initialize Craps game."""
        super().__init__()
        self.reset()

    def reset(self) -> None:
        """Reset game state."""
        self.state = GameState.NOT_STARTED
        self.point: int | None = None
        self.bankroll = 1000
        self.current_bet = 0
        self.bet_type = BetType.PASS_LINE
        self.emit_event(
            GameEventType.GAME_INITIALIZED,
            {
                "bankroll": self.bankroll,
                "bet_type": self.bet_type.value,
            },
        )

    def is_game_over(self) -> bool:
        """Check if game over."""
        return self.bankroll <= 0

    def get_current_player(self) -> int:
        """Get current player."""
        return 0

    def get_valid_moves(self) -> List[str]:
        """Get valid moves."""
        if self.point is None:
            return ["roll", "bet_pass", "bet_dont_pass"]
        return ["roll"]

    def make_move(self, move: str) -> bool:
        """Execute move."""
        if move == "roll":
            return self._roll_dice()
        elif move.startswith("bet_"):
            self.bet_type = BetType.PASS_LINE if "pass" in move and "dont" not in move else BetType.DONT_PASS
            self.emit_event(
                GameEventType.ACTION_PROCESSED,
                {
                    "action": "set_bet_type",
                    "bet_type": self.bet_type.value,
                },
            )
            return True
        return False

    def _roll_dice(self) -> bool:
        """Roll two dice and process result."""
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS
            self.emit_event(
                GameEventType.GAME_START,
                {
                    "bet_type": self.bet_type.value,
                    "current_bet": self.current_bet,
                },
            )

        roll = random.randint(1, 6) + random.randint(1, 6)

        if self.point is None:
            # Come-out roll
            if roll in (7, 11):
                if self.bet_type == BetType.PASS_LINE:
                    self.bankroll += self.current_bet
                    self.emit_event(
                        GameEventType.SCORE_UPDATED,
                        {
                            "bankroll": self.bankroll,
                            "roll": roll,
                        },
                    )
            elif roll in (2, 3, 12):
                if self.bet_type == BetType.DONT_PASS:
                    self.bankroll += self.current_bet
                    self.emit_event(
                        GameEventType.SCORE_UPDATED,
                        {
                            "bankroll": self.bankroll,
                            "roll": roll,
                        },
                    )
            else:
                self.point = roll
                self.emit_event(
                    GameEventType.ACTION_PROCESSED,
                    {
                        "action": "set_point",
                        "point": self.point,
                        "roll": roll,
                    },
                )
        else:
            # Point established
            if roll == self.point:
                if self.bet_type == BetType.PASS_LINE:
                    self.bankroll += self.current_bet
                    self.emit_event(
                        GameEventType.SCORE_UPDATED,
                        {
                            "bankroll": self.bankroll,
                            "roll": roll,
                        },
                    )
                self.point = None
            elif roll == 7:
                if self.bet_type == BetType.DONT_PASS:
                    self.bankroll += self.current_bet
                    self.emit_event(
                        GameEventType.SCORE_UPDATED,
                        {
                            "bankroll": self.bankroll,
                            "roll": roll,
                        },
                    )
                self.point = None

        self.emit_event(
            GameEventType.TURN_COMPLETE,
            {
                "point": self.point,
                "roll": roll,
                "bankroll": self.bankroll,
            },
        )

        if self.is_game_over():
            self.emit_event(GameEventType.GAME_OVER, {"bankroll": self.bankroll})

        return True

    def get_winner(self) -> int | None:
        """Get winner."""
        return None if not self.is_game_over() else 0

    def get_game_state(self) -> GameState:
        """Get current game state.

        Returns:
            Current state of the game
        """
        return self.state
