"""Craps game engine implementation.

This module provides the core logic for the game of Craps, a popular casino
dice game. It defines the game rules, betting structure, and state management.

The `CrapsGame` class is the main component, inheriting from `GameEngine`. It
manages the game flow, including the come-out roll, point establishment, and
bet resolutions. It supports various bet types such as Pass Line, Don't Pass,
Odds, and Place bets.

The engine is designed with hooks for analytics, allowing external systems to
monitor game events and player behavior for analysis or real-time display.

Classes:
    BetType: An enumeration for the types of bets available in Craps.
    CrapsGame: The main game engine for Craps.
"""

from __future__ import annotations

import random
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from common.architecture.events import GameEventType
from common.game_engine import GameEngine, GameState


class BetType(Enum):
    """Enumerates the fundamental types of line bets in Craps.

    Attributes:
        PASS_LINE: A bet that the shooter will win.
        DONT_PASS: A bet that the shooter will lose.
    """

    PASS_LINE = "pass"
    DONT_PASS = "dont_pass"


class CrapsGame(GameEngine[str, int]):
    """Implements the casino dice game Craps with comprehensive betting.

    This engine manages the game state, player bankroll, and various betting
    options. The game proceeds in rounds, starting with a "come-out" roll.

    Key Features:
    - Pass/Don't Pass line bets.
    - Establishing a "point" number.
    - Placing "odds" bets behind a line bet.
    - Placing "place" bets on specific numbers.
    - Event-driven architecture for state changes and analytics.

    The game ends when the player's bankroll is depleted.
    """

    def __init__(self, rng: Optional[random.Random] = None) -> None:
        """Initializes the Craps game engine.

        Args:
            rng: An optional random number generator for deterministic testing.
                 If not provided, the default `random` module is used.
        """
        super().__init__()
        # The random number generator defaults to the module-level ``random`` so monkeypatching
        # ``random.randint`` during tests works as expected. A custom generator can still be
        # supplied for deterministic scenarios.
        self.rng: Any = rng if rng is not None else random
        self.analytics_hooks: List[Callable[[str, Dict[str, int | str | None]], None]] = []
        self.reset()

    def reset(self) -> None:
        """Resets the game to its initial state.

        This method is called to start a new game, clearing the point,
        resetting the bankroll, and clearing all bets. It emits a
        `GAME_INITIALIZED` event.
        """
        self.state = GameState.NOT_STARTED
        self.point: Optional[int] = None
        self.bankroll = 1000
        self.current_bet = 0
        self.bet_type = BetType.PASS_LINE
        self.odds_bet = 0
        self.place_bets: Dict[int, int] = {4: 0, 5: 0, 6: 0, 8: 0, 9: 0, 10: 0}

        # Notify listeners that the game is ready.
        self.emit_event(
            GameEventType.GAME_INITIALIZED,
            {
                "bankroll": self.bankroll,
                "bet_type": self.bet_type.value,
            },
        )

    def is_game_over(self) -> bool:
        """Checks if the game is over.

        The game concludes when the player's bankroll is zero or less.

        Returns:
            True if the game is over, False otherwise.
        """
        return self.bankroll <= 0

    def get_current_player(self) -> int:
        """Returns the index of the current player.

        In this single-player simulation, it always returns 0.

        Returns:
            The player index (always 0).
        """
        return 0

    def get_valid_moves(self) -> List[str]:
        """Returns a list of valid moves based on the current game state.

        The available moves change depending on whether a point is established.

        Returns:
            A list of strings representing valid moves.
        """
        moves = ["roll"]
        if self.point is None:
            # Come-out roll phase: can place line bets.
            moves.extend(["bet_pass", "bet_dont_pass"])
        else:
            # Point established: can place odds bets.
            moves.append("bet_odds")

        # Place bets can be made or removed at any time.
        moves.extend(f"bet_place_{number}" for number in self.place_bets)
        moves.extend(f"remove_place_{number}" for number, amount in self.place_bets.items() if amount > 0)
        return moves

    def make_move(self, move: str) -> bool:
        """Executes a player's move.

        Parses the move string and delegates to the appropriate handler.

        Args:
            move: The string representing the move (e.g., "roll", "bet_pass 10").

        Returns:
            True if the move was valid and executed, False otherwise.
        """
        parts = move.split()
        command = parts[0]
        amount = None
        if len(parts) > 1:
            try:
                amount = int(parts[1])
            except ValueError:
                return False  # Invalid amount.

        # Route command to the correct internal method.
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
                return False  # Invalid number in command.
            return self._place_place_bet(number, amount)
        if command.startswith("remove_place_"):
            try:
                number = int(command.split("_")[-1])
            except ValueError:
                return False  # Invalid number in command.
            return self._remove_place_bet(number)

        return False  # Unknown command.

    def _roll_dice(self) -> bool:
        """Simulates rolling two dice and processes the outcome."""
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS
            self.emit_event(
                GameEventType.GAME_START,
                {"bet_type": self.bet_type.value, "current_bet": self.current_bet},
            )

        roll = self.rng.randint(1, 6) + self.rng.randint(1, 6)
        self._notify_analytics("roll", {"roll": roll, "point": self.point, "bankroll": self.bankroll})

        if self.point is None:
            self._handle_come_out_roll(roll)
        else:
            self._handle_point_roll(roll)

        self.emit_event(GameEventType.TURN_COMPLETE, {"point": self.point, "roll": roll, "bankroll": self.bankroll})

        if self.is_game_over():
            self.emit_event(GameEventType.GAME_OVER, {"bankroll": self.bankroll})

        return True

    def _handle_come_out_roll(self, roll: int) -> None:
        """Handles the logic for a come-out roll."""
        if roll in (7, 11):
            # Win for Pass Line bets.
            if self.bet_type == BetType.PASS_LINE and self.current_bet > 0:
                self._resolve_line_win(outcome="win", roll=roll)
            else:
                self._resolve_place_bets(roll)
        elif roll in (2, 3):
            # Loss for Pass Line, win for Don't Pass.
            if self.bet_type == BetType.PASS_LINE and self.current_bet > 0:
                self._resolve_line_loss(roll)
            elif self.bet_type == BetType.DONT_PASS and self.current_bet > 0:
                self._resolve_line_win(outcome="win", roll=roll)
            self._resolve_place_bets(roll)
        elif roll == 12:
            # Loss for Pass Line, push for Don't Pass.
            if self.bet_type == BetType.PASS_LINE and self.current_bet > 0:
                self._resolve_line_loss(roll)
            elif self.bet_type == BetType.DONT_PASS and self.current_bet > 0:
                self._resolve_line_win(outcome="push", roll=roll)  # Push, not a win.
            self._resolve_place_bets(roll)
        else:
            # Establish the point.
            self.point = roll
            self.emit_event(GameEventType.ACTION_PROCESSED, {"action": "set_point", "point": self.point, "roll": roll})
            self._notify_analytics("point_established", {"point": self.point, "bankroll": self.bankroll})
            self._resolve_place_bets(roll)

    def _handle_point_roll(self, roll: int) -> None:
        """Handles the logic for a roll when a point is established."""
        if roll == self.point:
            # Point is hit, Pass Line wins.
            if self.bet_type == BetType.PASS_LINE and self.current_bet > 0:
                self._resolve_line_win(outcome="win", roll=roll)
            else:
                self._resolve_line_loss(roll)
            self._resolve_place_bets(roll)
            self.point = None  # Reset for the next come-out roll.
        elif roll == 7:
            # "Seven out," Pass Line loses.
            if self.bet_type == BetType.DONT_PASS and self.current_bet > 0:
                self._resolve_line_win(outcome="win", roll=roll)
            else:
                self._resolve_line_loss(roll)
            self._resolve_place_bets(roll)
            self.point = None  # Reset for the next come-out roll.
        else:
            # No resolution, roll again.
            self._resolve_place_bets(roll)

    def get_winner(self) -> int | None:
        """Determines the winner of the game.

        Since this is a single-player game vs. the house, there is no winner
        in the traditional sense until the game is over.

        Returns:
            0 if the game is over, otherwise None.
        """
        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Returns the current state of the game.

        Returns:
            The current `GameState` enum member.
        """
        return self.state

    def register_analytics_hook(self, callback: Callable[[str, Dict[str, int | str | None]], None]) -> None:
        """Registers a callback function to receive analytics events.

        Args:
            callback: A function that accepts an event name and a data payload.
        """
        self.analytics_hooks.append(callback)

    def _notify_analytics(self, event: str, payload: Dict[str, int | str | None]) -> None:
        """Sends an analytics event to all registered hooks."""
        for hook in self.analytics_hooks:
            hook(event, payload.copy())

    def _place_line_bet(self, bet_type: BetType, amount: Optional[int]) -> bool:
        """Places a Pass or Don't Pass line bet.

        This is only valid during the come-out roll phase.

        Args:
            bet_type: The type of line bet to place.
            amount: The amount to wager.

        Returns:
            True if the bet was successfully placed, False otherwise.
        """
        if amount is None or amount <= 0 or self.point is not None or self.current_bet > 0:
            return False  # Bet invalid or already placed.
        if self.bankroll < amount:
            return False  # Insufficient funds.

        self.bet_type = bet_type
        self.bankroll -= amount
        self.current_bet = amount
        self.emit_event(
            GameEventType.ACTION_PROCESSED,
            {"action": "set_bet_type", "bet_type": self.bet_type.value, "bet_amount": amount},
        )
        self._notify_analytics(
            "line_bet_placed",
            {"bet_type": self.bet_type.value, "amount": amount, "bankroll": self.bankroll},
        )
        return True

    def _place_odds_bet(self, amount: Optional[int]) -> bool:
        """Places an odds bet behind an active line bet.

        This is only valid when a point is established.

        Args:
            amount: The amount to wager on odds.

        Returns:
            True if the bet was successfully placed, False otherwise.
        """
        if amount is None or amount <= 0 or self.point is None or self.current_bet <= 0:
            return False  # No point or no line bet to back.
        if self.bankroll < amount:
            return False  # Insufficient funds.

        self.bankroll -= amount
        self.odds_bet += amount
        self._notify_analytics(
            "odds_bet_placed",
            {"point": self.point, "amount": amount, "bankroll": self.bankroll},
        )
        return True

    def _place_place_bet(self, number: int, amount: Optional[int]) -> bool:
        """Places a bet directly on a point number (4, 5, 6, 8, 9, 10).

        Args:
            number: The number to bet on.
            amount: The amount to wager.

        Returns:
            True if the bet was successfully placed, False otherwise.
        """
        if number not in self.place_bets or amount is None or amount <= 0:
            return False  # Invalid number or amount.
        if self.bankroll < amount:
            return False  # Insufficient funds.

        self.bankroll -= amount
        self.place_bets[number] += amount
        self._notify_analytics(
            "place_bet_placed",
            {"number": number, "amount": amount, "bankroll": self.bankroll},
        )
        return True

    def _remove_place_bet(self, number: int) -> bool:
        """Removes an existing place bet and returns the funds to the bankroll.

        Args:
            number: The number of the place bet to remove.

        Returns:
            True if the bet was successfully removed, False otherwise.
        """
        if number not in self.place_bets or self.place_bets[number] <= 0:
            return False  # No bet to remove.

        amount = self.place_bets[number]
        self.place_bets[number] = 0
        self.bankroll += amount
        self._notify_analytics(
            "place_bet_removed",
            {"number": number, "amount": amount, "bankroll": self.bankroll},
        )
        return True

    def _resolve_line_win(self, *, outcome: str, roll: int) -> None:
        """Handles winning or pushing line bets and associated odds bets.

        Args:
            outcome: The result of the bet ("win" or "push").
            roll: The dice roll that caused the resolution.
        """
        payout = 0
        if outcome == "win":
            payout = self.current_bet * 2  # Bet is returned plus winnings.
            self.bankroll += payout
        elif outcome == "push":
            payout = self.current_bet  # Bet is returned.
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
        if payout > 0:
            self.emit_event(GameEventType.SCORE_UPDATED, {"bankroll": self.bankroll, "roll": roll})
        self.current_bet = 0

        # Resolve odds bet associated with the line bet.
        if outcome == "win" and self.odds_bet > 0:
            odds_return = self._calculate_odds_return(pass_line=(self.bet_type == BetType.PASS_LINE))
            if odds_return > 0:
                self.bankroll += odds_return
                self.emit_event(GameEventType.SCORE_UPDATED, {"bankroll": self.bankroll, "roll": roll})
            self._notify_analytics(
                "odds_bet_resolved",
                {"outcome": "win", "point": self.point, "payout": odds_return, "bankroll": self.bankroll},
            )
            self.odds_bet = 0
        elif self.odds_bet > 0:
            # Odds bet loses if the line bet doesn't win.
            self._notify_analytics(
                "odds_bet_resolved",
                {"outcome": "lose", "point": self.point, "payout": 0, "bankroll": self.bankroll},
            )
            self.odds_bet = 0

    def _resolve_line_loss(self, roll: int) -> None:
        """Handles losing line bets and associated odds bets.

        Args:
            roll: The dice roll that caused the loss.
        """
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

        if self.odds_bet > 0:
            self._notify_analytics(
                "odds_bet_resolved",
                {"outcome": "lose", "point": self.point, "payout": 0, "bankroll": self.bankroll},
            )
            self.odds_bet = 0

    def _resolve_place_bets(self, roll: int) -> None:
        """Evaluates place bets based on the latest dice roll.

        Args:
            roll: The result of the dice roll.
        """
        if roll == 7:
            # All place bets lose on a 7.
            if any(amount > 0 for amount in self.place_bets.values()):
                self._notify_analytics("place_bets_cleared", {"roll": roll, "bankroll": self.bankroll})
            for number in self.place_bets:
                self.place_bets[number] = 0
            return

        if roll in self.place_bets and self.place_bets[roll] > 0:
            # A place bet number was hit.
            amount = self.place_bets[roll]
            profit = self._calculate_place_profit(roll, amount)
            self.bankroll += profit
            self._notify_analytics(
                "place_bet_paid",
                {"number": roll, "profit": profit, "bankroll": self.bankroll},
            )
            if profit > 0:
                self.emit_event(GameEventType.SCORE_UPDATED, {"bankroll": self.bankroll, "roll": roll})

    def _calculate_odds_return(self, *, pass_line: bool) -> int:
        """Calculates the total return for an odds bet, including the original stake.

        Args:
            pass_line: True if the odds are on a Pass Line bet, False for Don't Pass.

        Returns:
            The total amount to be returned to the player (stake + profit).
        """
        if self.point is None or self.odds_bet <= 0:
            return 0

        # Payout ratios for odds bets.
        payouts = {4: (2, 1), 5: (3, 2), 6: (6, 5), 8: (6, 5), 9: (3, 2), 10: (2, 1)}
        num, den = payouts[self.point]
        amount = self.odds_bet

        if pass_line:
            # Payout for a winning Pass Line odds bet.
            profit = (amount * num) // den
        else:
            # Payout for a winning Don't Pass odds bet (lay odds).
            profit = (amount * den) // num

        return amount + profit

    def _calculate_place_profit(self, number: int, amount: int) -> int:
        """Computes the profit for a winning place bet.

        Note: This does not include the original stake.

        Args:
            number: The number on which the place bet was made.
            amount: The amount of the place bet.

        Returns:
            The profit from the bet.
        """
        # Payout ratios for place bets.
        payouts = {4: (9, 5), 5: (7, 5), 6: (7, 6), 8: (7, 6), 9: (7, 5), 10: (9, 5)}
        if number not in payouts:
            return 0

        num, den = payouts[number]
        return (amount * num) // den
