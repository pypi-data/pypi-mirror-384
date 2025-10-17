"""Sliding puzzle game engine.

This module contains a realistic implementation of the classic 15-puzzle. The
game consists of a grid of numbered tiles with a single empty space. Players
slide adjacent tiles into the empty space to arrange the numbers in ascending
order, finishing with the empty space in the bottom-right corner.
"""

from __future__ import annotations

import random
from typing import Dict, List

from common.game_engine import GameEngine, GameState


class SlidingPuzzleGame(GameEngine[str, int]):
    """Logic engine for the sliding puzzle.

    The implementation keeps track of the puzzle board, validates moves, and
    guarantees that a freshly reset board is solvable. Moves can be expressed as
    traditional direction commands (``"u"``, ``"d"``, ``"l"``, ``"r"``) or by the
    number of the tile a player wishes to slide into the empty space.
    """

    _DIRECTION_VECTORS: Dict[str, tuple[int, int]] = {
        "u": (-1, 0),
        "d": (1, 0),
        "l": (0, -1),
        "r": (0, 1),
    }
    _OPPOSITE_DIRECTIONS: Dict[str, str] = {"u": "d", "d": "u", "l": "r", "r": "l"}

    def __init__(self, size: int = 4, shuffle_moves: int = 200) -> None:
        """Create a new sliding puzzle instance.

        Args:
            size: Length of one side of the square board. The classic 15-puzzle
                uses ``size=4``. Values greater than two are supported.
            shuffle_moves: Number of random valid moves applied during reset to
                produce a solvable board. Higher numbers create a more mixed
                starting position.

        Raises:
            ValueError: If ``size`` is less than three.
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
        """Reset the board to a freshly shuffled, solvable state."""

        self.board = self._create_solved_board()
        self.moves = 0
        self.state = GameState.NOT_STARTED
        self._shuffle_board()

    def _create_solved_board(self) -> List[int]:
        """Return the solved configuration for the current board size."""

        return list(range(1, self.size * self.size)) + [0]

    def _shuffle_board(self) -> None:
        """Shuffle the board by applying random valid moves.

        The shuffling procedure repeatedly performs random legal moves starting
        from the solved configuration. This guarantees that the resulting board
        is solvable while avoiding simple back-and-forth moves that undo the
        previous action.
        """

        previous_direction: str | None = None
        for _ in range(self.shuffle_moves):
            moves = self.get_valid_moves()
            if previous_direction and len(moves) > 1:
                opposite = self._OPPOSITE_DIRECTIONS[previous_direction]
                moves = [m for m in moves if m != opposite]
            direction = random.choice(moves)
            self._move_blank(direction)
            previous_direction = direction

        if self.is_game_over():
            alternative_moves = self.get_valid_moves()
            first_move = random.choice(alternative_moves)
            self._move_blank(first_move)
            second_move_candidates = [move for move in self.get_valid_moves() if move != self._OPPOSITE_DIRECTIONS[first_move]]
            if second_move_candidates:
                self._move_blank(random.choice(second_move_candidates))

    def _move_blank(self, direction: str) -> bool:
        """Slide the blank space in the provided direction."""

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
        """Slide a numbered tile into the blank space if it is adjacent."""

        if tile <= 0 or tile >= self.size * self.size:
            return False

        try:
            tile_idx = self.board.index(tile)
        except ValueError:
            return False

        zero_idx = self.board.index(0)
        tile_row, tile_col = divmod(tile_idx, self.size)
        zero_row, zero_col = divmod(zero_idx, self.size)
        if abs(tile_row - zero_row) + abs(tile_col - zero_col) != 1:
            return False

        self.board[zero_idx], self.board[tile_idx] = self.board[tile_idx], self.board[zero_idx]
        return True

    def is_game_over(self) -> bool:
        """Return True when the puzzle is solved."""

        return self.board == self._create_solved_board()

    def get_current_player(self) -> int:
        """Return the identifier of the (single) player."""

        return 0

    def get_valid_moves(self) -> List[str]:
        """Return all valid directional moves for the blank space."""

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
        """Apply a move expressed as a direction or tile number."""

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
        """Return 0 when the puzzle is solved, otherwise ``None``."""

        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Return the current game state."""

        return self.state
