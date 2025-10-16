"""Tests for common base classes and utilities.

This module tests the abstract base classes and utility functions provided
in the common module.
"""

import unittest
from typing import Any, List, Optional

from common import GameEngine, GamePhase, GameState, HeuristicStrategy, RandomStrategy


class SimpleTestGame(GameEngine):
    """A simple test game implementation for testing the GameEngine base class."""

    def __init__(self) -> None:
        """Initialize the test game."""
        super().__init__()
        self.board: List[str] = [" "] * 9
        self.current_player_val: str = "X"
        self._state = GameState(phase=GamePhase.RUNNING)

    def initialize(self, **kwargs: Any) -> None:
        """Initialize the game."""
        self.reset()

    def reset(self) -> None:
        """Reset the game."""
        self.board = [" "] * 9
        self.current_player_val = "X"
        self._state = GameState(phase=GamePhase.RUNNING)

    def is_finished(self) -> bool:
        """Check if game is finished."""
        return self._state.phase == GamePhase.FINISHED

    def is_game_over(self) -> bool:
        """Check if game is over (alias for is_finished)."""
        return self.is_finished()

    def get_current_player(self) -> str:
        """Get current player."""
        return self.current_player_val

    def get_valid_actions(self) -> List[int]:
        """Get valid actions (moves)."""
        return [i for i, cell in enumerate(self.board) if cell == " "]

    def get_valid_moves(self) -> List[int]:
        """Get valid moves (alias for get_valid_actions)."""
        return self.get_valid_actions()

    def is_valid_move(self, move: int) -> bool:
        """Check if move is valid."""
        return move in self.get_valid_moves()

    def execute_action(self, action: int) -> bool:
        """Execute an action (move)."""
        return self.make_move(action)

    def make_move(self, move: int) -> bool:
        """Make a move."""
        if not self.is_valid_move(move):
            return False
        self.board[move] = self.current_player_val
        self.current_player_val = "O" if self.current_player_val == "X" else "X"
        # Check if board is full
        if not self.get_valid_moves():
            self._state = GameState(phase=GamePhase.FINISHED)
        return True

    def get_winner(self) -> Optional[str]:
        """Get winner (simplified - just checks if game is over)."""
        if self.is_game_over():
            return None  # Draw
        return None

    def get_game_state(self) -> GamePhase:
        """Get game state."""
        return self._state.phase


class TestGameEngine(unittest.TestCase):
    """Tests for GameEngine base class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.game = SimpleTestGame()

    def test_initial_state(self) -> None:
        """Test initial game state."""
        self.assertEqual(self.game.get_current_player(), "X")
        self.assertFalse(self.game.is_game_over())
        self.assertEqual(self.game.get_game_state(), GamePhase.RUNNING)
        self.assertEqual(len(self.game.get_valid_moves()), 9)

    def test_make_move(self) -> None:
        """Test making moves."""
        self.assertTrue(self.game.make_move(0))
        self.assertEqual(self.game.board[0], "X")
        self.assertEqual(self.game.get_current_player(), "O")

    def test_invalid_move(self) -> None:
        """Test invalid move handling."""
        self.game.make_move(0)
        self.assertFalse(self.game.make_move(0))  # Same position

    def test_is_valid_move(self) -> None:
        """Test move validation."""
        self.assertTrue(self.game.is_valid_move(0))
        self.game.make_move(0)
        self.assertFalse(self.game.is_valid_move(0))

    def test_reset(self) -> None:
        """Test game reset."""
        self.game.make_move(0)
        self.game.make_move(1)
        self.game.reset()
        self.assertEqual(len(self.game.get_valid_moves()), 9)
        self.assertEqual(self.game.get_current_player(), "X")

    def test_game_over(self) -> None:
        """Test game over state."""
        # Fill the board
        for i in range(9):
            self.game.make_move(i)
        self.assertTrue(self.game.is_game_over())
        self.assertEqual(self.game.get_game_state(), GamePhase.FINISHED)


class TestRandomStrategy(unittest.TestCase):
    """Tests for RandomStrategy."""

    def test_select_move(self) -> None:
        """Test random move selection."""
        strategy = RandomStrategy()
        valid_moves = [0, 1, 2, 3, 4]
        game_state = None

        # Test multiple selections
        for _ in range(10):
            move = strategy.select_move(valid_moves, game_state)
            self.assertIn(move, valid_moves)

    def test_no_valid_moves(self) -> None:
        """Test behavior with no valid moves."""
        strategy = RandomStrategy()
        with self.assertRaises(ValueError):
            strategy.select_move([], None)

    def test_single_move(self) -> None:
        """Test with single valid move."""
        strategy = RandomStrategy()
        valid_moves = [5]
        move = strategy.select_move(valid_moves, None)
        self.assertEqual(move, 5)


class TestHeuristicStrategy(unittest.TestCase):
    """Tests for HeuristicStrategy."""

    def test_select_best_move(self) -> None:
        """Test selection of best move based on heuristic."""

        def simple_heuristic(move: int, state: None) -> float:
            # Prefer higher numbers
            return float(move)

        strategy = HeuristicStrategy(heuristic_fn=simple_heuristic)
        valid_moves = [1, 2, 3, 4, 5]
        move = strategy.select_move(valid_moves, None)
        self.assertEqual(move, 5)  # Highest score

    def test_tie_breaking(self) -> None:
        """Test random selection among equal-score moves."""

        def constant_heuristic(move: int, state: None) -> float:
            # All moves have same score
            return 1.0

        strategy = HeuristicStrategy(heuristic_fn=constant_heuristic)
        valid_moves = [1, 2, 3, 4, 5]
        move = strategy.select_move(valid_moves, None)
        self.assertIn(move, valid_moves)

    def test_evaluate_move(self) -> None:
        """Test move evaluation."""

        def scoring_heuristic(move: int, state: None) -> float:
            return move * 2.0

        strategy = HeuristicStrategy(heuristic_fn=scoring_heuristic)
        score = strategy.evaluate_move(3, None)
        self.assertEqual(score, 6.0)


if __name__ == "__main__":
    unittest.main()
