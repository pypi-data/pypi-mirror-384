"""Minesweeper game engine implementation.

This module provides the core logic for the classic Minesweeper game. It
includes functionality for board generation, mine placement, cell state
management, and the rules for revealing cells and winning the game.

The `MinesweeperGame` class is the main entry point, offering a complete,
framework-agnostic implementation of the game's mechanics. It supports
both standard difficulty levels and custom board configurations.

Classes:
    CellState: An enumeration of the possible states for a cell.
    Difficulty: An enumeration of standard game difficulty levels.
    MinesweeperGame: The main game engine for Minesweeper.
"""

from __future__ import annotations

import random
from enum import Enum
from typing import List, Optional, Set, Tuple

from common.game_engine import GameEngine, GameState


class CellState(Enum):
    """An enumeration of the possible states for a single Minesweeper cell."""

    HIDDEN = "hidden"
    REVEALED = "revealed"
    FLAGGED = "flagged"
    QUESTION = "question"
    UNKNOWN = "unknown"
    FILLED = "filled"
    EMPTY = "empty"

    def render(self) -> str:
        """Return a printable character token suitable for textual boards.

        Returns:
            A single character representation of the cell state.
        """
        return {
            CellState.UNKNOWN: "?",
            CellState.FILLED: "█",
            CellState.EMPTY: "·",
        }.get(self, str(self.value))


class Difficulty(Enum):
    """An enumeration of the standard Minesweeper difficulty levels.

    Each difficulty level defines the board dimensions (rows and columns) and
    the number of mines.
    """

    BEGINNER = (9, 9, 10)
    INTERMEDIATE = (16, 16, 40)
    EXPERT = (16, 30, 99)

    @property
    def rows(self) -> int:
        """Return the number of rows for this difficulty."""
        return self.value[0]

    @property
    def cols(self) -> int:
        """Return the number of columns for this difficulty."""
        return self.value[1]

    @property
    def mines(self) -> int:
        """Return the number of mines for this difficulty."""
        return self.value[2]


class MinesweeperGame(GameEngine[Tuple[int, int, str], int]):
    """The game engine for the classic Minesweeper puzzle.

    This class encapsulates the complete logic for a game of Minesweeper,
    including board setup, player moves, and win/loss conditions. It is
    designed to be independent of any specific user interface.

    The move format is a tuple of (row, col, action), where the action
    can be 'reveal', 'flag', 'question', 'unflag', or 'chord'.
    """

    def __init__(
        self,
        difficulty: Difficulty = Difficulty.BEGINNER,
        *,
        custom_rows: Optional[int] = None,
        custom_cols: Optional[int] = None,
        custom_mines: Optional[int] = None,
    ) -> None:
        """Initialize the Minesweeper game.

        Args:
            difficulty: The difficulty level to use if no custom dimensions
                are provided.
            custom_rows: The number of rows for a custom board.
            custom_cols: The number of columns for a custom board.
            custom_mines: The number of mines for a custom board.

        Raises:
            ValueError: If custom dimensions are partially specified or invalid.
        """
        if any(value is not None for value in (custom_rows, custom_cols, custom_mines)):
            if custom_rows is None or custom_cols is None or custom_mines is None:
                raise ValueError("Custom rows, cols and mines must all be provided together.")
            if custom_rows <= 0 or custom_cols <= 0:
                raise ValueError("Custom board dimensions must be positive.")
            if custom_mines <= 0 or custom_mines >= custom_rows * custom_cols:
                raise ValueError("Custom mine count must be positive and less than total cells.")
            self.difficulty = difficulty
            self.rows = int(custom_rows)
            self.cols = int(custom_cols)
            self.num_mines = int(custom_mines)
        else:
            self.difficulty = difficulty
            self.rows = difficulty.rows
            self.cols = difficulty.cols
            self.num_mines = difficulty.mines
        self.reset()

    def reset(self) -> None:
        """Reset the game to its initial state with a new board."""
        self.state = GameState.NOT_STARTED
        self.board: List[List[bool]] = []  # True if a cell contains a mine.
        self.cell_states: List[List[CellState]] = []
        self.numbers: List[List[int]] = []  # Number of adjacent mines.
        self.revealed_count = 0
        self.flagged_positions: Set[Tuple[int, int]] = set()
        self.game_won = False
        self.game_lost = False
        self._initialize_board()

    def _initialize_board(self) -> None:
        """Initialize the board with empty cells."""
        self.board = [[False] * self.cols for _ in range(self.rows)]
        self.cell_states = [[CellState.HIDDEN] * self.cols for _ in range(self.rows)]
        self.numbers = [[0] * self.cols for _ in range(self.rows)]

    def _adjacent_positions(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Return a list of valid adjacent positions for a given cell.

        Args:
            row: The row of the cell.
            col: The column of the cell.

        Returns:
            A list of (row, col) tuples for all valid neighbors.
        """
        neighbors: List[Tuple[int, int]] = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    neighbors.append((nr, nc))
        return neighbors

    def _place_mines(self, first_row: int, first_col: int) -> None:
        """Place mines on the board, ensuring the first click is safe.

        Args:
            first_row: The row of the player's first click.
            first_col: The column of the player's first click.
        """
        # Exclude the first-clicked cell and its neighbors from mine placement.
        forbidden = {(first_row, first_col)}
        for nr, nc in self._adjacent_positions(first_row, first_col):
            forbidden.add((nr, nc))

        available = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) not in forbidden]

        # Place mines randomly in the available positions.
        mine_positions = random.sample(available, min(self.num_mines, len(available)))
        for row, col in mine_positions:
            self.board[row][col] = True

        # Calculate the number of adjacent mines for each cell.
        for row in range(self.rows):
            for col in range(self.cols):
                if not self.board[row][col]:
                    self.numbers[row][col] = self._count_adjacent_mines(row, col)

    def _count_adjacent_mines(self, row: int, col: int) -> int:
        """Count the number of mines adjacent to a given cell.

        Args:
            row: The row of the cell.
            col: The column of the cell.

        Returns:
            The number of adjacent mines.
        """
        count = 0
        for nr, nc in self._adjacent_positions(row, col):
            if self.board[nr][nc]:
                count += 1
        return count

    def _count_adjacent_flags(self, row: int, col: int) -> int:
        """Count the number of flagged cells adjacent to a given position."""
        return sum(1 for nr, nc in self._adjacent_positions(row, col) if self.cell_states[nr][nc] == CellState.FLAGGED)

    def _reveal_all_mines(self) -> None:
        """Reveal all mine locations, typically after a loss."""
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col]:
                    self.cell_states[row][col] = CellState.REVEALED

    def _reveal_remaining_safe_cells(self) -> None:
        """Reveal all remaining safe cells, typically when the game is won."""
        for row in range(self.rows):
            for col in range(self.cols):
                if not self.board[row][col] and self.cell_states[row][col] != CellState.REVEALED:
                    self.cell_states[row][col] = CellState.REVEALED
                    self.revealed_count += 1

    def _chord_cell(self, row: int, col: int) -> bool:
        """Reveal surrounding cells if the number of adjacent flags matches the cell's number.

        This action, known as "chording," is a common feature in many
        Minesweeper implementations that speeds up gameplay.

        Args:
            row: The row of the cell to chord.
            col: The column of the cell to chord.

        Returns:
            True if the chord action was successful, False otherwise.
        """
        if self.cell_states[row][col] != CellState.REVEALED:
            return False

        required_flags = self.numbers[row][col]
        if required_flags == 0:
            return False

        if self._count_adjacent_flags(row, col) != required_flags:
            return False

        success = False
        for nr, nc in self._adjacent_positions(row, col):
            neighbor_state = self.cell_states[nr][nc]
            if neighbor_state == CellState.FLAGGED:
                continue
            if self.board[nr][nc]:
                self.cell_states[nr][nc] = CellState.REVEALED
                self.game_lost = True
                self.state = GameState.FINISHED
                self._reveal_all_mines()
                return True
            if neighbor_state != CellState.REVEALED:
                self._reveal_cell(nr, nc)
                success = True

        total_cells = self.rows * self.cols
        if not self.game_lost and self.revealed_count == total_cells - self.num_mines:
            self.game_won = True
            self.state = GameState.FINISHED
            self._reveal_remaining_safe_cells()
        return success

    def is_game_over(self) -> bool:
        """Return True if the game is over (won or lost), False otherwise."""
        return self.game_won or self.game_lost

    def get_current_player(self) -> int:
        """Return the current player. In this single-player game, it is always 0."""
        return 0

    def get_valid_moves(self) -> List[Tuple[int, int, str]]:
        """Return a list of all valid moves for the current game state.

        Returns:
            A list of (row, col, action) tuples representing all valid moves.
        """
        moves: List[Tuple[int, int, str]] = []
        for row in range(self.rows):
            for col in range(self.cols):
                state = self.cell_states[row][col]
                if state == CellState.HIDDEN:
                    moves.append((row, col, "reveal"))
                    moves.append((row, col, "flag"))
                    moves.append((row, col, "question"))
                elif state == CellState.FLAGGED:
                    moves.append((row, col, "unflag"))
                    moves.append((row, col, "question"))
                elif state == CellState.QUESTION:
                    moves.append((row, col, "reveal"))
                    moves.append((row, col, "flag"))
                    moves.append((row, col, "unflag"))
                elif state == CellState.REVEALED and self.numbers[row][col] > 0:
                    moves.append((row, col, "chord"))
        return moves

    def make_move(self, move: Tuple[int, int, str]) -> bool:
        """Execute a player's move and update the game state.

        Args:
            move: A tuple of (row, col, action) representing the move.

        Returns:
            True if the move was valid and applied, False otherwise.
        """
        row, col, action = move

        # Validate the move coordinates.
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return False

        # Place mines on the first move.
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS
            self._place_mines(row, col)

        cell_state = self.cell_states[row][col]

        if action == "reveal":
            if cell_state == CellState.FLAGGED:
                return False

            # If the player hits a mine, the game is over.
            if self.board[row][col]:
                self.cell_states[row][col] = CellState.REVEALED
                self.game_lost = True
                self.state = GameState.FINISHED
                self._reveal_all_mines()
                return True

            # Reveal the cell and cascade if it has no adjacent mines.
            self._reveal_cell(row, col)

            # Check for a win condition.
            total_cells = self.rows * self.cols
            if self.revealed_count == total_cells - self.num_mines:
                self.game_won = True
                self.state = GameState.FINISHED
                self._reveal_remaining_safe_cells()

            return True

        elif action == "flag":
            if cell_state == CellState.REVEALED:
                return False
            if cell_state == CellState.FLAGGED:
                return True
            if cell_state == CellState.QUESTION:
                self.cell_states[row][col] = CellState.FLAGGED
                self.flagged_positions.add((row, col))
                return True
            self.cell_states[row][col] = CellState.FLAGGED
            self.flagged_positions.add((row, col))
            return True

        elif action == "unflag":
            if cell_state == CellState.FLAGGED:
                self.cell_states[row][col] = CellState.HIDDEN
                self.flagged_positions.discard((row, col))
                return True
            if cell_state == CellState.QUESTION:
                self.cell_states[row][col] = CellState.HIDDEN
                return True
            return False

        elif action == "question":
            if cell_state == CellState.REVEALED:
                return False
            if cell_state == CellState.FLAGGED:
                self.flagged_positions.discard((row, col))
            self.cell_states[row][col] = CellState.QUESTION
            return True

        elif action == "chord":
            return self._chord_cell(row, col)

        return False

    def _reveal_cell(self, row: int, col: int) -> None:
        """Recursively reveal a cell and its neighbors if it's a zero.

        Args:
            row: The row of the cell to reveal.
            col: The column of the cell to reveal.
        """
        if self.cell_states[row][col] in {CellState.REVEALED, CellState.FLAGGED}:
            return

        self.cell_states[row][col] = CellState.REVEALED
        self.revealed_count += 1

        # If the cell has no adjacent mines, cascade the reveal.
        if self.numbers[row][col] == 0:
            for nr, nc in self._adjacent_positions(row, col):
                self._reveal_cell(nr, nc)

    def get_winner(self) -> int | None:
        """Return the winner of the game.

        Returns:
            0 if the game is won, otherwise None.
        """
        if self.game_won:
            return 0
        return None

    def get_game_state(self) -> GameState:
        """Return the current state of the game.

        Returns:
            The current `GameState` enum member.
        """
        return self.state

    def get_cell_display(self, row: int, col: int) -> str:
        """Return the display character for a given cell.

        Args:
            row: The row of the cell.
            col: The column of the cell.

        Returns:
            A string representing the cell for display in a text-based UI.
        """
        state = self.cell_states[row][col]

        if state == CellState.HIDDEN:
            return "·"
        elif state == CellState.FLAGGED:
            if self.game_lost and not self.board[row][col]:
                return "✗"  # Incorrectly flagged mine
            return "F"
        elif state == CellState.QUESTION:
            return "?"
        elif state == CellState.REVEALED:
            if self.board[row][col]:
                return "*"  # A revealed mine
            num = self.numbers[row][col]
            return str(num) if num > 0 else " "
        return "?"
