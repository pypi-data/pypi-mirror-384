"""Craps game engine implementation."""

from __future__ import annotations

import random
from enum import Enum
from typing import Callable, Dict, List, Optional

from common.architecture.events import GameEventType
from common.game_engine import GameEngine, GameState


class BetType(Enum):
    """Types of bets in Craps."""

    PASS_LINE = "pass"
    DONT_PASS = "dont_pass"


class CrapsGame(GameEngine[str, int]):
    """Craps casino dice game with extended betting support.

    Players can place pass/don't pass, odds, and place bets. Pass line wins on
    7/11 on the come-out roll, loses on 2/3/12, otherwise a point is established
    and must be rolled again before a 7. Analytics hooks provide detailed
    betting telemetry for external dashboards.
    """

    def __init__(self, rng: Optional[random.Random] = None) -> None:
        """Initialize Craps game."""
        super().__init__()
        self.rng = rng or random.Random()
        self.analytics_hooks: List[Callable[[str, Dict[str, int | str | None]], None]] = []
        self.reset()

    def reset(self) -> None:
        """Reset game state."""
        self.state = GameState.NOT_STARTED
        self.point: int | None = None
        self.bankroll = 1000
        self.current_bet = 0
        self.bet_type = BetType.PASS_LINE
        self.odds_bet = 0
        self.place_bets: Dict[int, int] = {4: 0, 5: 0, 6: 0, 8: 0, 9: 0, 10: 0}
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
        moves = ["roll"]
        if self.point is None:
            moves.extend(["bet_pass", "bet_dont_pass"])
        else:
            moves.append("bet_odds")
        moves.extend(f"bet_place_{number}" for number in self.place_bets)
        moves.extend(f"remove_place_{number}" for number, amount in self.place_bets.items() if amount > 0)
        return moves

    def make_move(self, move: str) -> bool:
        """Execute move."""
        parts = move.split()
        command = parts[0]
        amount = None
        if len(parts) > 1:
            try:
                amount = int(parts[1])
            except ValueError:
                return False

        if command == "roll":
            return self._roll_dice()
        if command == "bet_pass":
            return self._place_line_bet(BetType.PASS_LINE, amount)
        if command == "bet_dont_pass":
            return self._place_line_bet(BetType.DONT_PASS, amount)
        if command == "bet_odds":
            return self._place_odds_bet(amount)
        if command.startswith("bet_place_"):
            try:
                number = int(command.split("_")[-1])
            except ValueError:
                return False
            return self._place_place_bet(number, amount)
        if command.startswith("remove_place_"):
            try:
                number = int(command.split("_")[-1])
            except ValueError:
                return False
            return self._remove_place_bet(number)
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

        roll = self.rng.randint(1, 6) + self.rng.randint(1, 6)
        self._notify_analytics(
            "roll",
            {
                "roll": roll,
                "point": self.point,
                "bankroll": self.bankroll,
            },
        )

        if self.point is None:
            # Come-out roll
            if roll in (7, 11):
                if self.bet_type == BetType.PASS_LINE and self.current_bet > 0:
                    self._resolve_line_win(outcome="win", roll=roll)
                else:
                    self._resolve_place_bets(roll)
            elif roll in (2, 3):
                if self.bet_type == BetType.PASS_LINE and self.current_bet > 0:
                    self._resolve_line_loss(roll)
                elif self.bet_type == BetType.DONT_PASS and self.current_bet > 0:
                    self._resolve_line_win(outcome="win", roll=roll)
                self._resolve_place_bets(roll)
            elif roll == 12:
                if self.bet_type == BetType.PASS_LINE and self.current_bet > 0:
                    self._resolve_line_loss(roll)
                elif self.bet_type == BetType.DONT_PASS and self.current_bet > 0:
                    self._resolve_line_win(outcome="push", roll=roll)
                self._resolve_place_bets(roll)
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
                self._notify_analytics(
                    "point_established",
                    {
                        "point": self.point,
                        "bankroll": self.bankroll,
                    },
                )
                self._resolve_place_bets(roll)
        else:
            # Point established
            if roll == self.point:
                if self.bet_type == BetType.PASS_LINE and self.current_bet > 0:
                    self._resolve_line_win(outcome="win", roll=roll)
                else:
                    self._resolve_line_loss(roll)
                self._resolve_place_bets(roll)
                self.point = None
            elif roll == 7:
                if self.bet_type == BetType.DONT_PASS and self.current_bet > 0:
                    self._resolve_line_win(outcome="win", roll=roll)
                else:
                    self._resolve_line_loss(roll)
                self._resolve_place_bets(roll)
                self.point = None
            else:
                self._resolve_place_bets(roll)

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

    def register_analytics_hook(self, callback: Callable[[str, Dict[str, int | str | None]], None]) -> None:
        """Register a callback for analytics events."""

        self.analytics_hooks.append(callback)

    def _notify_analytics(self, event: str, payload: Dict[str, int | str | None]) -> None:
        """Send analytics payloads to registered hooks."""

        for hook in self.analytics_hooks:
            hook(event, payload.copy())

    def _place_line_bet(self, bet_type: BetType, amount: Optional[int]) -> bool:
        """Place a pass or don't pass line bet."""

        if amount is None or amount <= 0 or self.point is not None or self.current_bet > 0:
            return False
        if self.bankroll < amount:
            return False

        self.bet_type = bet_type
        self.bankroll -= amount
        self.current_bet = amount
        self.emit_event(
            GameEventType.ACTION_PROCESSED,
            {
                "action": "set_bet_type",
                "bet_type": self.bet_type.value,
                "bet_amount": amount,
            },
        )
        self._notify_analytics(
            "line_bet_placed",
            {
                "bet_type": self.bet_type.value,
                "amount": amount,
                "bankroll": self.bankroll,
            },
        )
        return True

    def _place_odds_bet(self, amount: Optional[int]) -> bool:
        """Place an odds bet behind the active line bet."""

        if amount is None or amount <= 0 or self.point is None or self.current_bet <= 0:
            return False
        if self.bankroll < amount:
            return False

        self.bankroll -= amount
        self.odds_bet += amount
        self._notify_analytics(
            "odds_bet_placed",
            {
                "point": self.point,
                "amount": amount,
                "bankroll": self.bankroll,
            },
        )
        return True

    def _place_place_bet(self, number: int, amount: Optional[int]) -> bool:
        """Place a bet directly on a point number."""

        if number not in self.place_bets or amount is None or amount <= 0:
            return False
        if self.bankroll < amount:
            return False

        self.bankroll -= amount
        self.place_bets[number] += amount
        self._notify_analytics(
            "place_bet_placed",
            {
                "number": number,
                "amount": amount,
                "bankroll": self.bankroll,
            },
        )
        return True

    def _remove_place_bet(self, number: int) -> bool:
        """Remove an existing place bet and return funds to bankroll."""

        if number not in self.place_bets or self.place_bets[number] <= 0:
            return False

        amount = self.place_bets[number]
        self.place_bets[number] = 0
        self.bankroll += amount
        self._notify_analytics(
            "place_bet_removed",
            {
                "number": number,
                "amount": amount,
                "bankroll": self.bankroll,
            },
        )
        return True

    def _resolve_line_win(self, *, outcome: str, roll: int) -> None:
        """Handle line bet wins and pushes."""

        payout = 0
        if outcome == "win":
            payout = self.current_bet * 2
            self.bankroll += payout
        elif outcome == "push":
            payout = self.current_bet
            self.bankroll += payout

        self._notify_analytics(
            "line_bet_resolved",
            {
                "outcome": outcome,
                "roll": roll,
                "bet_type": self.bet_type.value,
                "amount": self.current_bet,
                "payout": payout,
                "bankroll": self.bankroll,
            },
        )
        if payout:
            self.emit_event(
                GameEventType.SCORE_UPDATED,
                {
                    "bankroll": self.bankroll,
                    "roll": roll,
                },
            )
        self.current_bet = 0

        if outcome == "win" and self.odds_bet:
            odds_return = self._calculate_odds_return(pass_line=self.bet_type == BetType.PASS_LINE)
            if odds_return:
                self.bankroll += odds_return
                self.emit_event(
                    GameEventType.SCORE_UPDATED,
                    {
                        "bankroll": self.bankroll,
                        "roll": roll,
                    },
                )
            self._notify_analytics(
                "odds_bet_resolved",
                {
                    "outcome": "win",
                    "point": self.point,
                    "payout": odds_return,
                    "bankroll": self.bankroll,
                },
            )
            self.odds_bet = 0
        elif self.odds_bet:
            self._notify_analytics(
                "odds_bet_resolved",
                {
                    "outcome": "lose",
                    "point": self.point,
                    "payout": 0,
                    "bankroll": self.bankroll,
                },
            )
            self.odds_bet = 0

    def _resolve_line_loss(self, roll: int) -> None:
        """Handle losing line bets."""

        if self.current_bet > 0:
            self._notify_analytics(
                "line_bet_resolved",
                {
                    "outcome": "lose",
                    "roll": roll,
                    "bet_type": self.bet_type.value,
                    "amount": self.current_bet,
                    "payout": 0,
                    "bankroll": self.bankroll,
                },
            )
        self.current_bet = 0
        if self.odds_bet:
            self._notify_analytics(
                "odds_bet_resolved",
                {
                    "outcome": "lose",
                    "point": self.point,
                    "payout": 0,
                    "bankroll": self.bankroll,
                },
            )
            self.odds_bet = 0

    def _resolve_place_bets(self, roll: int) -> None:
        """Evaluate place bets based on the latest roll."""

        if roll == 7:
            if any(amount > 0 for amount in self.place_bets.values()):
                self._notify_analytics(
                    "place_bets_cleared",
                    {
                        "roll": roll,
                        "bankroll": self.bankroll,
                    },
                )
            for number in self.place_bets:
                self.place_bets[number] = 0
            return

        if roll in self.place_bets and self.place_bets[roll] > 0:
            amount = self.place_bets[roll]
            profit = self._calculate_place_profit(roll, amount)
            self.bankroll += profit
            self._notify_analytics(
                "place_bet_paid",
                {
                    "number": roll,
                    "profit": profit,
                    "bankroll": self.bankroll,
                },
            )
            if profit:
                self.emit_event(
                    GameEventType.SCORE_UPDATED,
                    {
                        "bankroll": self.bankroll,
                        "roll": roll,
                    },
                )

    def _calculate_odds_return(self, *, pass_line: bool) -> int:
        """Calculate the total return for an odds bet, including stake."""

        if self.point is None or self.odds_bet <= 0:
            return 0

        payouts = {4: (2, 1), 5: (3, 2), 6: (6, 5), 8: (6, 5), 9: (3, 2), 10: (2, 1)}
        num, den = payouts[self.point]
        amount = self.odds_bet
        if pass_line:
            profit = amount * num // den
        else:
            profit = amount * den // num
        return amount + profit

    def _calculate_place_profit(self, number: int, amount: int) -> int:
        """Compute profit for a place bet when it hits."""

        payouts = {4: (9, 5), 5: (7, 5), 6: (7, 6), 8: (7, 6), 9: (7, 5), 10: (9, 5)}
        if number not in payouts:
            return 0
        num, den = payouts[number]
        return amount * num // den
