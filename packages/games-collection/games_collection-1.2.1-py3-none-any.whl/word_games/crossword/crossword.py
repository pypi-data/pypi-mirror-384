"""Crossword game engine."""

from __future__ import annotations

from typing import Dict, List, Tuple

from common.game_engine import GameEngine, GameState


class CrosswordGame(GameEngine[Tuple[int, str], int]):
    """Simple crossword puzzle game."""

    # Simple puzzle: clue_id -> (row, col, direction, word, clue)
    PUZZLE: Dict[int, Tuple[int, int, str, str, str]] = {
        1: (0, 0, "across", "CAT", "Feline pet"),
        2: (0, 0, "down", "CAN", "Container"),
        3: (2, 0, "across", "NET", "Fishing tool"),
    }

    def __init__(self) -> None:
        """Initialize game."""
        self.reset()

    def reset(self) -> None:
        """Reset game."""
        self.state = GameState.NOT_STARTED
        self.grid = {}  # (row, col) -> letter or None
        self.solved = set()  # Set of solved clue IDs

    def is_game_over(self) -> bool:
        """Check if game over."""
        return len(self.solved) == len(self.PUZZLE)

    def get_current_player(self) -> int:
        """Get current player."""
        return 0

    def get_valid_moves(self) -> List[Tuple[int, str]]:
        """Get valid moves: (clue_id, word_guess)."""
        unsolved = [cid for cid in self.PUZZLE if cid not in self.solved]
        return [(cid, "") for cid in unsolved]

    def make_move(self, move: Tuple[int, str]) -> bool:
        """Submit answer for a clue."""
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        clue_id, guess = move
        if clue_id not in self.PUZZLE or clue_id in self.solved:
            return False

        _, _, _, answer, _ = self.PUZZLE[clue_id]
        if guess.upper() == answer.upper():
            self.solved.add(clue_id)
            if self.is_game_over():
                self.state = GameState.FINISHED
            return True
        return False

    def get_winner(self) -> int | None:
        """Get winner."""
        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Get current game state.

        Returns:
            Current state of the game
        """
        return self.state
