"""Core logic and CLI utilities for Connect Four.

The module implements the gravity based token dropping mechanics, win
detection for horizontal, vertical, and diagonal lines of four, and a small
command line interface for local play.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from common.game_engine import GameEngine, GameState


@dataclass(frozen=True)
class ConnectFourMove:
    """Representation of a Connect Four move."""

    column: int


class ConnectFourGame(GameEngine[ConnectFourMove, int]):
    """Connect Four implementation with gravity and win detection."""

    def __init__(self, rows: int = 6, columns: int = 7, connect_length: int = 4) -> None:
        self.rows = rows
        self.columns = columns
        self.connect_length = connect_length
        self._board: List[List[int]] = []
        self._current_player = 1
        self._winner: Optional[int] = None
        self._state = GameState.NOT_STARTED
        self.reset()

    def reset(self) -> None:
        """Reset the board to the initial empty state."""

        self._board = [[0 for _ in range(self.columns)] for _ in range(self.rows)]
        self._current_player = 1
        self._winner = None
        self._state = GameState.IN_PROGRESS

    def is_game_over(self) -> bool:
        """Return whether the game has finished."""

        return self._state == GameState.FINISHED

    def get_current_player(self) -> int:
        """Return the identifier of the current player (1 or 2)."""

        return self._current_player

    def get_valid_moves(self) -> List[ConnectFourMove]:
        """Return all valid column drops for the current board state."""

        if self.is_game_over():
            return []
        moves = [ConnectFourMove(column=index) for index in range(self.columns) if self._board[0][index] == 0]
        return moves

    def make_move(self, move: ConnectFourMove) -> bool:
        """Drop a token in the requested column if the move is valid."""

        if self.is_game_over():
            return False
        if move.column < 0 or move.column >= self.columns:
            return False
        drop_row = self._find_drop_row(move.column)
        if drop_row is None:
            return False
        self._board[drop_row][move.column] = self._current_player
        if self._check_winner(drop_row, move.column):
            self._winner = self._current_player
            self._state = GameState.FINISHED
        elif not any(cell == 0 for cell in self._board[0]):
            self._winner = None
            self._state = GameState.FINISHED
        else:
            self._current_player = 2 if self._current_player == 1 else 1
        return True

    def get_winner(self) -> Optional[int]:
        """Return the winner if the game is finished."""

        return self._winner

    def get_game_state(self) -> GameState:
        """Return the current game state."""

        return self._state

    def get_state_representation(self) -> Sequence[Sequence[int]]:
        """Return a tuple-based representation of the board for serialization."""

        return tuple(tuple(row) for row in self._board)

    def _find_drop_row(self, column: int) -> Optional[int]:
        """Return the row index where the token will land for the given column."""

        for index in range(self.rows - 1, -1, -1):
            if self._board[index][column] == 0:
                return index
        return None

    def _check_winner(self, row: int, column: int) -> bool:
        """Check if the last move created a connect-length line."""

        player = self._board[row][column]
        directions = ((1, 0), (0, 1), (1, 1), (1, -1))
        for delta_row, delta_col in directions:
            if self._count_consecutive(row, column, delta_row, delta_col, player) >= self.connect_length:
                return True
        return False

    def _count_consecutive(self, row: int, column: int, delta_row: int, delta_column: int, player: int) -> int:
        """Count consecutive pieces in both directions for a given vector."""

        total = 1
        total += self._count_single_direction(row, column, delta_row, delta_column, player)
        total += self._count_single_direction(row, column, -delta_row, -delta_column, player)
        return total

    def _count_single_direction(self, row: int, column: int, delta_row: int, delta_column: int, player: int) -> int:
        """Count consecutive pieces in a single direction."""

        count = 0
        current_row, current_column = row + delta_row, column + delta_column
        while 0 <= current_row < self.rows and 0 <= current_column < self.columns:
            if self._board[current_row][current_column] != player:
                break
            count += 1
            current_row += delta_row
            current_column += delta_column
        return count


class ConnectFourCLI:
    """Simple text-based interface for Connect Four."""

    def __init__(self, rows: int = 6, columns: int = 7) -> None:
        self._game = ConnectFourGame(rows=rows, columns=columns)

    def run(self) -> None:
        """Run a blocking command-line game until completion."""

        while not self._game.is_game_over():
            self._render_board()
            column = self._prompt_move()
            if column is None:
                print("Invalid input. Please try again.")
                continue
            if not self._game.make_move(ConnectFourMove(column=column)):
                print("Column is full or invalid. Try another column.")
        self._render_board()
        winner = self._game.get_winner()
        if winner is None:
            print("The game ended in a draw.")
        else:
            print(f"Player {winner} wins!")

    def _render_board(self) -> None:
        """Display the current board state to the console."""

        for row in self._game.get_state_representation():
            print("|" + " ".join("." if cell == 0 else ("X" if cell == 1 else "O") for cell in row) + "|")
        print(" " + " ".join(str(index) for index in range(self._game.columns)))

    def _prompt_move(self) -> Optional[int]:
        """Prompt the user for a move and validate the input."""

        try:
            value = input(f"Player {self._game.get_current_player()}, choose a column: ")
        except EOFError:
            return None
        if not value.isdigit():
            return None
        return int(value)
