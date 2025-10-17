"""Sliding puzzle game engine.

This module provides a robust implementation of the classic sliding puzzle,
often known as the 15-puzzle. The engine manages the game board, validates
moves, and ensures that every generated puzzle is solvable.

Players can interact with the puzzle by specifying either the direction to
move the blank space or the number of the tile they wish to slide. This
flexibility makes the engine suitable for various user interfaces.

Classes:
    SlidingPuzzleGame: The main logic engine for the sliding puzzle.
"""

from __future__ import annotations

import random
from typing import Dict, List

from common.game_engine import GameEngine, GameState


class SlidingPuzzleGame(GameEngine[str, int]):
    """The logic engine for the sliding puzzle game.

    This class handles the internal representation of the puzzle board,
    move validation, and the shuffling process, which guarantees that every
    generated board is solvable.

    Moves can be specified as directional commands ('u', 'd', 'l', 'r') or
    by the number of the tile to be moved.
    """

    _DIRECTION_VECTORS: Dict[str, tuple[int, int]] = {
        "u": (-1, 0),  # Up
        "d": (1, 0),  # Down
        "l": (0, -1),  # Left
        "r": (0, 1),  # Right
    }
    _OPPOSITE_DIRECTIONS: Dict[str, str] = {"u": "d", "d": "u", "l": "r", "r": "l"}

    def __init__(self, size: int = 4, shuffle_moves: int = 200) -> None:
        """Create a new sliding puzzle instance.

        Args:
            size: The length of one side of the square board. The classic
                15-puzzle uses size=4.
            shuffle_moves: The number of random moves to apply during the
                shuffling process to create a solvable board.

        Raises:
            ValueError: If the specified size is less than 3.
        """
        if size < 3:
            raise ValueError("Sliding puzzles require a board of at least 3x3.")

        self.size = size
        self.shuffle_moves = shuffle_moves
        self.board: List[int] = []
        self.moves = 0
        self.state = GameState.NOT_STARTED
        self.reset()

    def reset(self) -> None:
        """Reset the board to a new, freshly shuffled, and solvable state."""
        self.board = self._create_solved_board()
        self.moves = 0
        self.state = GameState.NOT_STARTED
        self._shuffle_board()

    def _create_solved_board(self) -> List[int]:
        """Return the solved configuration for the current board size.

        The solved state is a list of numbers from 1 to size*size - 1,
        followed by 0 to represent the blank space.
        """
        return list(range(1, self.size * self.size)) + [0]

    def _shuffle_board(self) -> None:
        """Shuffle the board by applying a series of random, valid moves.

        This method starts from the solved state and performs random legal
        moves. This guarantees that the resulting puzzle is always solvable.
        It also avoids simple back-and-forth moves to ensure a better mix.
        """
        previous_direction: str | None = None
        for _ in range(self.shuffle_moves):
            moves = self.get_valid_moves()
            if previous_direction and len(moves) > 1:
                # Avoid immediately undoing the previous move.
                opposite = self._OPPOSITE_DIRECTIONS[previous_direction]
                moves = [m for m in moves if m != opposite]
            direction = random.choice(moves)
            self._move_blank(direction)
            previous_direction = direction

        # If the board is still solved after shuffling, apply a few more moves.
        if self.is_game_over():
            alternative_moves = self.get_valid_moves()
            first_move = random.choice(alternative_moves)
            self._move_blank(first_move)
            second_move_candidates = [move for move in self.get_valid_moves() if move != self._OPPOSITE_DIRECTIONS[first_move]]
            if second_move_candidates:
                self._move_blank(random.choice(second_move_candidates))

    def _move_blank(self, direction: str) -> bool:
        """Slide the blank space in the specified direction.

        Args:
            direction: The direction to move the blank ('u', 'd', 'l', or 'r').

        Returns:
            True if the move was successful, False otherwise.
        """
        delta = self._DIRECTION_VECTORS.get(direction)
        if delta is None:
            return False

        zero_idx = self.board.index(0)
        row, col = divmod(zero_idx, self.size)
        nr, nc = row + delta[0], col + delta[1]

        if not (0 <= nr < self.size and 0 <= nc < self.size):
            return False

        new_idx = nr * self.size + nc
        self.board[zero_idx], self.board[new_idx] = self.board[new_idx], self.board[zero_idx]
        return True

    def _slide_tile_number(self, tile: int) -> bool:
        """Slide a numbered tile into the blank space, if it is adjacent.

        Args:
            tile: The number of the tile to slide.

        Returns:
            True if the move was successful, False otherwise.
        """
        if tile <= 0 or tile >= self.size * self.size:
            return False

        try:
            tile_idx = self.board.index(tile)
        except ValueError:
            return False  # Tile not on the board.

        zero_idx = self.board.index(0)
        tile_row, tile_col = divmod(tile_idx, self.size)
        zero_row, zero_col = divmod(zero_idx, self.size)
        # Check for adjacency (Manhattan distance of 1).
        if abs(tile_row - zero_row) + abs(tile_col - zero_col) != 1:
            return False

        self.board[zero_idx], self.board[tile_idx] = self.board[tile_idx], self.board[zero_idx]
        return True

    def is_game_over(self) -> bool:
        """Return True if the puzzle is in its solved state, False otherwise."""
        return self.board == self._create_solved_board()

    def get_current_player(self) -> int:
        """Return the identifier of the current player (always 0 for single-player)."""
        return 0

    def get_valid_moves(self) -> List[str]:
        """Return a list of all valid directional moves for the blank space.

        Returns:
            A list of strings representing the valid directions.
        """
        zero_idx = self.board.index(0)
        row, col = divmod(zero_idx, self.size)
        moves: List[str] = []
        if row > 0:
            moves.append("u")
        if row < self.size - 1:
            moves.append("d")
        if col > 0:
            moves.append("l")
        if col < self.size - 1:
            moves.append("r")
        return moves

    def make_move(self, move: str) -> bool:
        """Apply a move, specified as either a direction or a tile number.

        Args:
            move: The move to make.

        Returns:
            True if the move was valid and applied, False otherwise.
        """
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        executed = False
        stripped_move = move.strip().lower()
        if stripped_move in self._DIRECTION_VECTORS:
            executed = self._move_blank(stripped_move)
        elif stripped_move.isdigit():
            executed = self._slide_tile_number(int(stripped_move))

        if not executed:
            return False

        self.moves += 1
        if self.is_game_over():
            self.state = GameState.FINISHED
        return True

    def get_winner(self) -> int | None:
        """Return the winner of the game.

        Returns:
            0 if the game is won, otherwise None.
        """
        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Return the current state of the game.

        Returns:
            The current `GameState` of the puzzle.
        """
        return self.state
