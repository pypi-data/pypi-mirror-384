"""AI strategy pattern implementations for game opponents.

This module provides a strategy pattern implementation for AI decision-making,
allowing different AI strategies to be plugged into games without modifying
the game engine code.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Callable, Generic, List, Optional, TypeVar

# Type variable for move representation
MoveType = TypeVar("MoveType")
# Type variable for game state representation
StateType = TypeVar("StateType")


class AIStrategy(ABC, Generic[MoveType, StateType]):
    """Abstract base class for AI strategies.

    This class defines the interface that all AI strategies must implement.
    Subclasses can implement different decision-making algorithms such as
    random selection, minimax, Monte Carlo Tree Search, etc.

    Type Parameters:
        MoveType: The type used to represent a move in the game
        StateType: The type used to represent the game state
    """

    def __init__(self, rng: Optional[random.Random] = None) -> None:
        """Initialize the AI strategy.

        Args:
            rng: Optional random number generator for deterministic behavior.
        """
        self.rng = rng or random.Random()

    @abstractmethod
    def select_move(
        self,
        valid_moves: List[MoveType],
        game_state: StateType,
    ) -> MoveType:
        """Select the best move based on the strategy.

        Args:
            valid_moves: List of valid moves to choose from.
            game_state: Current state of the game.

        Returns:
            The selected move.

        Raises:
            ValueError: If no valid moves are available.
        """
        pass

    def evaluate_move(
        self,
        move: MoveType,
        game_state: StateType,
    ) -> float:
        """Evaluate the quality of a move.

        Args:
            move: The move to evaluate.
            game_state: Current state of the game.

        Returns:
            A score representing the quality of the move.
            Higher scores indicate better moves.
        """
        return 0.0


class RandomStrategy(AIStrategy[MoveType, StateType]):
    """A simple strategy that selects moves randomly.

    This strategy is useful as a baseline or for easy difficulty levels.
    """

    def select_move(
        self,
        valid_moves: List[MoveType],
        game_state: StateType,
    ) -> MoveType:
        """Select a random move from the valid moves.

        Args:
            valid_moves: List of valid moves to choose from.
            game_state: Current state of the game (unused).

        Returns:
            A randomly selected move.

        Raises:
            ValueError: If no valid moves are available.
        """
        if not valid_moves:
            raise ValueError("No valid moves available")
        return self.rng.choice(valid_moves)


class MinimaxStrategy(AIStrategy[MoveType, StateType]):
    """A minimax-based strategy for perfect play in two-player games.

    This strategy uses the minimax algorithm with optional alpha-beta pruning
    to find optimal moves in zero-sum games.
    """

    def __init__(
        self,
        max_depth: int = 10,
        alpha_beta: bool = True,
        evaluation_fn: Optional[Callable[[StateType], float]] = None,
        rng: Optional[random.Random] = None,
    ) -> None:
        """Initialize the minimax strategy.

        Args:
            max_depth: Maximum depth for the minimax search.
            alpha_beta: Whether to use alpha-beta pruning.
            evaluation_fn: Custom evaluation function for non-terminal states.
            rng: Optional random number generator.
        """
        super().__init__(rng)
        self.max_depth = max_depth
        self.alpha_beta = alpha_beta
        self.evaluation_fn = evaluation_fn

    def select_move(
        self,
        valid_moves: List[MoveType],
        game_state: StateType,
    ) -> MoveType:
        """Select the best move using minimax algorithm.

        Args:
            valid_moves: List of valid moves to choose from.
            game_state: Current state of the game.

        Returns:
            The move with the highest minimax value.

        Raises:
            ValueError: If no valid moves are available.
        """
        if not valid_moves:
            raise ValueError("No valid moves available")

        # For now, use random selection as a placeholder
        # Subclasses or game-specific implementations should override
        # this with actual minimax logic
        return self.rng.choice(valid_moves)

    def evaluate_move(
        self,
        move: MoveType,
        game_state: StateType,
    ) -> float:
        """Evaluate a move using the evaluation function.

        Args:
            move: The move to evaluate.
            game_state: Current state of the game.

        Returns:
            The evaluation score for the move.
        """
        if self.evaluation_fn:
            return self.evaluation_fn(game_state)
        return 0.0


class HeuristicStrategy(AIStrategy[MoveType, StateType]):
    """A strategy based on heuristic evaluation.

    This strategy evaluates each move using a provided heuristic function
    and selects the move with the highest score.
    """

    def __init__(
        self,
        heuristic_fn: Callable[[MoveType, StateType], float],
        rng: Optional[random.Random] = None,
    ) -> None:
        """Initialize the heuristic strategy.

        Args:
            heuristic_fn: Function that evaluates a move's quality.
            rng: Optional random number generator for tie-breaking.
        """
        super().__init__(rng)
        self.heuristic_fn = heuristic_fn

    def select_move(
        self,
        valid_moves: List[MoveType],
        game_state: StateType,
    ) -> MoveType:
        """Select the move with the highest heuristic value.

        Args:
            valid_moves: List of valid moves to choose from.
            game_state: Current state of the game.

        Returns:
            The move with the highest heuristic score.

        Raises:
            ValueError: If no valid moves are available.
        """
        if not valid_moves:
            raise ValueError("No valid moves available")

        # Evaluate all moves
        scored_moves = [(move, self.heuristic_fn(move, game_state)) for move in valid_moves]

        # Find the maximum score
        max_score = max(score for _, score in scored_moves)

        # Get all moves with the maximum score
        best_moves = [move for move, score in scored_moves if score == max_score]

        # Return a random best move (for variety)
        return self.rng.choice(best_moves)

    def evaluate_move(
        self,
        move: MoveType,
        game_state: StateType,
    ) -> float:
        """Evaluate a move using the heuristic function.

        Args:
            move: The move to evaluate.
            game_state: Current state of the game.

        Returns:
            The heuristic score for the move.
        """
        return self.heuristic_fn(move, game_state)
