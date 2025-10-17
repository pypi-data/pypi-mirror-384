"""Farkle game engine implementation.

This module implements the core logic for the Farkle dice game, a classic
"push-your-luck" game where players score points by rolling dice. The goal is
to be the first to reach a target score, typically 10,000.

The `FarkleGame` class manages the game state, player turns, scoring, and the
risk-reward decision-making process. It also includes a simple heuristic AI
for automated play.

Classes:
    FarkleGame: The main engine for the Farkle game.

Functions:
    _farkle_move_heuristic: A heuristic function for the AI strategy.
"""

from __future__ import annotations

import random
from collections import Counter
from typing import List, Tuple

from common.ai_strategy import HeuristicStrategy
from common.architecture.events import GameEventType
from common.game_engine import GameEngine, GameState


class FarkleGame(GameEngine[Tuple[List[int], bool], int]):
    """Farkle dice game engine.

    This class encapsulates the rules and state of a game of Farkle. Players
    roll six dice and set aside scoring combinations. They can then choose to
    bank their points or re-roll the remaining dice to score more. If a roll
    yields no scoring dice, the player "farkles" and loses all points for that
    turn.

    Scoring Combinations:
    - A single 1 is 100 points.
    - A single 5 is 50 points.
    - Three of a kind (e.g., three 4s) is worth 100 times the die number (400).
        - Three 1s are a special case, worth 1000 points.
    - Four, five, or six of a kind double the three-of-a-kind score for each
      additional die.
    - A straight (1-2-3-4-5-6) is worth 1500 points.
    - Three pairs (e.g., 2-2, 4-4, 5-5) are worth 1500 points.
    """

    def __init__(
        self,
        num_players: int = 2,
        winning_score: int = 10000,
        rng: random.Random | None = None,
    ) -> None:
        """Initializes the Farkle game.

        Args:
            num_players: The number of players, between 2 and 6.
            winning_score: The score required to win the game.
            rng: An optional random number generator for deterministic runs.
        """
        super().__init__()
        self.num_players = max(2, min(6, num_players))
        self.winning_score = winning_score
        self.rng = rng or random.Random()
        self.reset()

    def reset(self) -> None:
        """Resets the game to its initial state."""
        self.state = GameState.NOT_STARTED
        self.scores = [0] * self.num_players
        self.current_player_idx = 0
        self.turn_score = 0
        self.dice_in_hand = 6
        self.last_roll: List[int] = []

        self.emit_event(
            GameEventType.GAME_INITIALIZED,
            {"num_players": self.num_players, "winning_score": self.winning_score},
        )

    def is_game_over(self) -> bool:
        """Checks if the game has ended.

        The game is over when at least one player has reached the winning score.

        Returns:
            True if the game is over, False otherwise.
        """
        return any(score >= self.winning_score for score in self.scores)

    def get_current_player(self) -> int:
        """Returns the index of the current player.

        Returns:
            The zero-based index of the current player.
        """
        return self.current_player_idx

    def get_valid_moves(self) -> List[Tuple[List[int], bool]]:
        """Gets the list of valid moves for the current state.

        A move is represented as a tuple: `(dice_to_bank, continue_rolling)`.
        - If no roll has been made, the only move is to roll: `([], True)`.
        - If a roll results in a Farkle, the only move is to end the turn: `([], False)`.
        - Otherwise, the player can choose any valid scoring subset of dice to
          bank and either continue rolling or end their turn.

        Returns:
            A list of valid move tuples.
        """
        if not self.last_roll:
            return [([], True)]  # Must make an initial roll.

        valid_selections = self._get_valid_selections(self.last_roll)
        if not valid_selections:
            return [([], False)]  # Farkled, must end the turn.

        moves = []
        for selection in valid_selections:
            moves.append((selection, True))  # Bank dice and continue rolling.
            moves.append((selection, False))  # Bank dice and end the turn.
        return moves

    def make_move(self, move: Tuple[List[int], bool]) -> bool:
        """Executes a player's move.

        Args:
            move: A tuple containing the dice to bank and whether to continue rolling.

        Returns:
            True if the move was valid and processed, False otherwise.
        """
        dice_to_bank, continue_rolling = move

        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS
            self.emit_event(GameEventType.GAME_START, {"player": self.current_player_idx, "scores": self.scores.copy()})

        # If no dice have been rolled yet, perform the initial roll.
        if not self.last_roll:
            self.last_roll = [self.rng.randint(1, 6) for _ in range(self.dice_in_hand)]
            self.emit_event(
                GameEventType.ACTION_PROCESSED,
                {"action": "roll", "roll": self.last_roll.copy(), "dice_in_hand": self.dice_in_hand},
            )
            return True

        # Check if the player has farkled.
        if not self._has_scoring_dice(self.last_roll):
            self.turn_score = 0
            self._end_turn()
            return True

        # Bank the selected dice and update the turn score.
        if dice_to_bank:
            score = self._calculate_score(dice_to_bank)
            if score == 0:
                return False  # Invalid selection of non-scoring dice.

            self.turn_score += score
            self.dice_in_hand -= len(dice_to_bank)
            self.emit_event(
                GameEventType.ACTION_PROCESSED,
                {"action": "bank_dice", "dice": dice_to_bank, "turn_score": self.turn_score},
            )

            # If all dice have been used for scoring ("hot dice"), the player gets all 6 back.
            if self.dice_in_hand == 0:
                self.dice_in_hand = 6

        if continue_rolling:
            # Player chooses to re-roll the remaining dice.
            self.last_roll = [self.rng.randint(1, 6) for _ in range(self.dice_in_hand)]
            self.emit_event(
                GameEventType.ACTION_PROCESSED,
                {"action": "roll", "roll": self.last_roll.copy(), "dice_in_hand": self.dice_in_hand},
            )
        else:
            # Player chooses to end their turn and bank the accumulated score.
            self.scores[self.current_player_idx] += self.turn_score
            self.emit_event(
                GameEventType.SCORE_UPDATED,
                {
                    "player": self.current_player_idx,
                    "scores": self.scores.copy(),
                    "turn_score": self.turn_score,
                },
            )
            self._end_turn()

        return True

    def get_winner(self) -> int | None:
        """Determines the winner of the game.

        The winner is the player with the highest score after the game is over.

        Returns:
            The index of the winning player, or None if the game is not over.
        """
        if not self.is_game_over():
            return None
        return max(range(self.num_players), key=lambda i: self.scores[i])

    def get_game_state(self) -> GameState:
        """Returns the current state of the game.

        Returns:
            The current `GameState`.
        """
        return self.state

    def create_adaptive_ai(self) -> HeuristicStrategy[Tuple[List[int], bool], "FarkleGame"]:
        """Creates an adaptive AI strategy for the current game state.

        This AI uses a heuristic function to evaluate the risk and reward of
        different moves.

        Returns:
            A `HeuristicStrategy` instance configured for Farkle.
        """
        return HeuristicStrategy(heuristic_fn=_farkle_move_heuristic)

    def _end_turn(self) -> None:
        """Ends the current turn and advances to the next player."""
        self.current_player_idx = (self.current_player_idx + 1) % self.num_players
        self.turn_score = 0
        self.dice_in_hand = 6
        self.last_roll = []

        self.emit_event(
            GameEventType.TURN_COMPLETE,
            {"next_player": self.current_player_idx, "scores": self.scores.copy()},
        )

        if self.is_game_over():
            winner = self.get_winner()
            self.emit_event(
                GameEventType.GAME_OVER,
                {"winner": winner, "scores": self.scores.copy()},
            )

    def _has_scoring_dice(self, dice: List[int]) -> bool:
        """Checks if a roll of dice contains any scoring combinations.

        Args:
            dice: A list of integers representing the dice roll.

        Returns:
            True if there are scoring dice, False otherwise.
        """
        return self._calculate_score(dice) > 0

    def _calculate_score(self, dice: List[int]) -> int:
        """Calculates the score for a given set of dice.

        This method evaluates all possible scoring combinations.

        Args:
            dice: A list of dice values.

        Returns:
            The total score for the given dice.
        """
        if not dice:
            return 0

        counts = Counter(dice)
        score = 0

        # Check for a straight (1-2-3-4-5-6).
        if len(counts) == 6 and all(counts[i] == 1 for i in range(1, 7)):
            return 1500

        # Check for three pairs.
        if len(counts) == 3 and all(c == 2 for c in counts.values()):
            return 1500

        # Score multiples (three of a kind or more).
        for num, count in counts.items():
            if count >= 3:
                base_score = 1000 if num == 1 else num * 100
                # Score doubles for each additional die over three.
                multiplier = 2 ** (count - 3)
                score += base_score * multiplier
                counts[num] = 0  # Remove scored dice from consideration.

        # Score single 1s and 5s that were not part of a multiple.
        score += counts.get(1, 0) * 100
        score += counts.get(5, 0) * 50

        return score

    def _get_valid_selections(self, dice: List[int]) -> List[List[int]]:
        """Gets all valid scoring subsets from a roll of dice.

        Args:
            dice: The current dice roll.

        Returns:
            A list of all valid dice selections.
        """
        valid = []

        # Generate all possible non-empty subsets of the dice.
        for i in range(1, 2 ** len(dice)):
            subset = [dice[j] for j in range(len(dice)) if i & (1 << j)]
            if self._calculate_score(subset) > 0:
                valid.append(sorted(subset))

        # Remove duplicate selections.
        unique_valid = []
        for selection in valid:
            if selection not in unique_valid:
                unique_valid.append(selection)

        return unique_valid


def _farkle_move_heuristic(move: Tuple[List[int], bool], game: FarkleGame) -> float:
    """Provides a heuristic evaluation for an AI's move in Farkle.

    This function weighs the potential score of a move against the risk of
    farkling on the next roll. It encourages more cautious play when close to
    winning.

    Args:
        move: The move to be evaluated.
        game: The current state of the Farkle game.

    Returns:
        A float representing the desirability of the move. Higher is better.
    """
    dice_to_bank, continue_rolling = move

    if not game.last_roll:
        return 1.0  # Always make the first roll.

    # Calculate key metrics for the heuristic.
    score = game._calculate_score(dice_to_bank)
    potential_total = game.turn_score + score
    remaining_dice = game.dice_in_hand - len(dice_to_bank) if dice_to_bank else game.dice_in_hand
    player_score = game.scores[game.current_player_idx]
    distance_to_win = max(0, game.winning_score - (player_score + potential_total))

    # Add a bonus for being close to winning, encouraging safer play.
    caution_bonus = 150.0 if distance_to_win <= 500 else 0.0

    if continue_rolling:
        # Evaluate the risk of continuing to roll.
        risk_penalty = remaining_dice * (40.0 + game.turn_score / 25.0)
        reward = potential_total + score * 0.3
        return reward - risk_penalty - caution_bonus
    else:
        # Evaluate the value of banking the current score.
        bank_value = potential_total
        if potential_total >= 500:
            bank_value += 500.0  # Bonus for reaching a significant threshold.
        bank_value += caution_bonus
        bank_value -= remaining_dice * 5.0  # Small penalty for leaving dice on the table.
        return bank_value
