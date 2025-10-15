"""Farkle game engine implementation.

This module implements the core logic for the Farkle dice game, including
scoring rules, dice rolling, and push-your-luck mechanics.
"""

from __future__ import annotations

import random
from collections import Counter
from typing import List, Tuple

from common.game_engine import GameEngine, GameState


class FarkleGame(GameEngine[Tuple[List[int], bool], int]):
    """Farkle dice game engine.

    Farkle is played with 6 dice. Players roll and can bank scoring dice,
    then re-roll remaining dice. If a roll has no scoring dice, they "farkle"
    and lose all points for that turn.

    Scoring:
    - Single 1: 100 points
    - Single 5: 50 points
    - Three of a kind: (number × 100), except three 1s = 1000
    - Four of a kind: (three of a kind × 2)
    - Five of a kind: (four of a kind × 2)
    - Six of a kind: (five of a kind × 2)
    - Straight (1-6): 1500 points
    - Three pairs: 1500 points
    """

    def __init__(self, num_players: int = 2, winning_score: int = 10000) -> None:
        """Initialize Farkle game.

        Args:
            num_players: Number of players (2-6)
            winning_score: Score needed to win (default 10000)
        """
        self.num_players = max(2, min(6, num_players))
        self.winning_score = winning_score
        self.reset()

    def reset(self) -> None:
        """Reset the game to initial state."""
        self.state = GameState.NOT_STARTED
        self.scores = [0] * self.num_players
        self.current_player_idx = 0
        self.turn_score = 0
        self.dice_in_hand = 6
        self.last_roll: List[int] = []

    def is_game_over(self) -> bool:
        """Check if game is over."""
        return any(score >= self.winning_score for score in self.scores)

    def get_current_player(self) -> int:
        """Get current player index."""
        return self.current_player_idx

    def get_valid_moves(self) -> List[Tuple[List[int], bool]]:
        """Get valid moves.

        Returns list of tuples: (dice_to_bank, continue_rolling)
        """
        if not self.last_roll:
            return [([], True)]  # Must roll

        valid_selections = self._get_valid_selections(self.last_roll)
        if not valid_selections:
            return [([], False)]  # Farkled, must end turn

        moves = []
        for selection in valid_selections:
            moves.append((selection, True))  # Bank and continue
            moves.append((selection, False))  # Bank and end turn
        return moves

    def make_move(self, move: Tuple[List[int], bool]) -> bool:
        """Execute a move.

        Args:
            move: Tuple of (dice_to_bank, continue_rolling)

        Returns:
            True if move was valid
        """
        dice_to_bank, continue_rolling = move

        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        # Roll dice if needed
        if not self.last_roll:
            self.last_roll = [random.randint(1, 6) for _ in range(self.dice_in_hand)]
            return True

        # Check if farkled
        if not self._has_scoring_dice(self.last_roll):
            self.turn_score = 0
            self._end_turn()
            return True

        # Bank the selected dice
        if dice_to_bank:
            score = self._calculate_score(dice_to_bank)
            if score == 0:
                return False  # Invalid selection

            self.turn_score += score
            self.dice_in_hand -= len(dice_to_bank)

            # If all dice used, get all 6 back ("hot dice")
            if self.dice_in_hand == 0:
                self.dice_in_hand = 6

        if continue_rolling:
            self.last_roll = [random.randint(1, 6) for _ in range(self.dice_in_hand)]
        else:
            # Bank turn score and end turn
            self.scores[self.current_player_idx] += self.turn_score
            self._end_turn()

        return True

    def get_winner(self) -> int | None:
        """Get winner if game is over."""
        if not self.is_game_over():
            return None
        return max(range(self.num_players), key=lambda i: self.scores[i])

    def get_game_state(self) -> GameState:
        """Get current game state.

        Returns:
            Current state of the game
        """
        return self.state

    def _end_turn(self) -> None:
        """End current turn and move to next player."""
        self.current_player_idx = (self.current_player_idx + 1) % self.num_players
        self.turn_score = 0
        self.dice_in_hand = 6
        self.last_roll = []

    def _has_scoring_dice(self, dice: List[int]) -> bool:
        """Check if dice contain any scoring combinations."""
        return self._calculate_score(dice) > 0

    def _calculate_score(self, dice: List[int]) -> int:
        """Calculate score for given dice.

        Args:
            dice: List of dice values

        Returns:
            Score for the dice combination
        """
        if not dice:
            return 0

        counts = Counter(dice)
        score = 0

        # Check for straight (1-6)
        if len(counts) == 6 and all(counts[i] == 1 for i in range(1, 7)):
            return 1500

        # Check for three pairs
        if len(counts) == 3 and all(c == 2 for c in counts.values()):
            return 1500

        # Check for multiples
        for num, count in counts.items():
            if count >= 3:
                base_score = 1000 if num == 1 else num * 100
                multiplier = 2 ** (count - 3)
                score += base_score * multiplier
                counts[num] = 0

        # Check for singles (1s and 5s)
        score += counts.get(1, 0) * 100
        score += counts.get(5, 0) * 50

        return score

    def _get_valid_selections(self, dice: List[int]) -> List[List[int]]:
        """Get all valid dice selections from a roll.

        Args:
            dice: Current dice roll

        Returns:
            List of valid dice selections
        """
        valid = []

        # Generate all possible non-empty subsets
        for i in range(1, 2 ** len(dice)):
            subset = [dice[j] for j in range(len(dice)) if i & (1 << j)]
            if self._calculate_score(subset) > 0:
                valid.append(sorted(subset))

        # Remove duplicates
        unique_valid = []
        for selection in valid:
            if selection not in unique_valid:
                unique_valid.append(selection)

        return unique_valid
