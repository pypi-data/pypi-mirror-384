"""Picross (Nonogram) game engine implementation.

This module provides a feature-complete engine for Picross, also known as
Nonograms or Griddlers. It supports puzzles of various sizes and includes
mechanisms for hint generation, move validation, mistake tracking, and line
progress analysis.

The engine is designed to be UI-agnostic, making it suitable for integration
into different front-ends, such as command-line interfaces or graphical
user interfaces.

Classes:
    LineProgress: A data class representing the progress of a row or column.
    PicrossGame: The main game engine for Picross puzzles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from common.game_engine import GameEngine, GameState
from logic_games.minesweeper.minesweeper import CellState


@dataclass(frozen=True)
class LineProgress:
    """A data class representing the progress of a row or column.

    Attributes:
        hints: The sequence of hints for the line.
        segments: The current contiguous groups of filled cells.
        filled_cells: The total number of filled cells in the line.
        expected_filled: The total number of cells that should be filled
            according to the hints.
    """

    hints: Sequence[int]
    segments: Sequence[int]
    filled_cells: int
    expected_filled: int

    @property
    def is_satisfied(self) -> bool:
        """Return True if the current filled segments match the hints."""
        return list(self.segments) == list(self.hints)


class PicrossGame(GameEngine[Tuple[int, int, str], int]):
    """A game engine for Picross/Nonogram picture logic puzzles.

    This class manages the game state, including the solution grid, player
    inputs, and progress tracking. It provides methods for making moves,
    checking for mistakes, and determining the win condition.

    The move format is a tuple of (row, col, action), where the action can be
    'fill', 'mark', 'clear', or 'toggle'.
    """

    # A default 10x10 puzzle solution, represented as a grid of 0s and 1s.
    SOLUTION: List[List[int]] = [
        [0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
        [0, 1, 1, 0, 0, 0, 0, 1, 1, 0],
        [1, 1, 0, 0, 0, 0, 0, 0, 1, 1],
        [1, 0, 0, 1, 1, 1, 1, 0, 0, 1],
        [1, 0, 1, 1, 1, 1, 1, 1, 0, 1],
        [1, 0, 1, 1, 1, 1, 1, 1, 0, 1],
        [1, 0, 0, 1, 1, 1, 1, 0, 0, 1],
        [1, 1, 0, 0, 0, 0, 0, 0, 1, 1],
        [0, 1, 1, 0, 0, 0, 0, 1, 1, 0],
        [0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
    ]

    def __init__(self, solution: Sequence[Sequence[int]] | None = None) -> None:
        """Initialize a Picross puzzle.

        Args:
            solution: An optional custom solution grid, where 1 represents a
                filled cell and 0 represents an empty cell. If omitted, a
                default 10x10 puzzle is used.
        """
        if solution is None:
            solution = self.SOLUTION
        self._solution = self._validate_solution(solution)
        self.size = len(self._solution)
        self.row_hints = [self._get_hints(row) for row in self._solution]
        self.col_hints = [self._get_hints(column) for column in zip(*self._solution)]
        self.reset()

    def _validate_solution(self, solution: Sequence[Sequence[int]]) -> List[List[int]]:
        """Validate the provided solution grid to ensure it is well-formed.

        Args:
            solution: The solution grid to validate.

        Returns:
            The validated solution grid.

        Raises:
            ValueError: If the solution grid is empty, not rectangular, or
                contains invalid values.
        """
        if not solution:
            raise ValueError("Solution grid must contain at least one row")

        size = len(solution[0])
        validated: List[List[int]] = []
        for row in solution:
            if len(row) != size:
                raise ValueError("Solution grid must be rectangular")
            validated_row: List[int] = []
            for cell in row:
                if cell not in (0, 1):
                    raise ValueError("Solution grid values must be 0 or 1")
                validated_row.append(int(cell))
            validated.append(validated_row)
        return validated

    def reset(self) -> None:
        """Reset the puzzle to its initial, unsolved state."""
        self.state = GameState.NOT_STARTED
        self.grid: List[List[CellState]] = [[CellState.UNKNOWN for _ in range(self.size)] for _ in range(self.size)]
        self.total_mistakes = 0
        self.incorrect_cells: set[Tuple[int, int]] = set()

    @staticmethod
    def _get_hints(line: Iterable[int]) -> List[int]:
        """Generate the Picross hints for a single row or column.

        Args:
            line: An iterable of 0s and 1s representing a line of the puzzle.

        Returns:
            A list of integers representing the hints for the line.
        """
        hints: List[int] = []
        count = 0
        for cell in line:
            if cell:
                count += 1
            elif count:
                hints.append(count)
                count = 0
        if count:
            hints.append(count)
        return hints or [0]

    def get_line_progress(self, index: int, *, is_row: bool = True) -> LineProgress:
        """Return progress information for a given row or column.

        Args:
            index: The index of the row or column.
            is_row: True to check a row, False to check a column.

        Returns:
            A `LineProgress` object detailing the state of the line.

        Raises:
            IndexError: If the line index is out of range.
        """
        if not (0 <= index < self.size):
            raise IndexError("Line index is out of range")

        if is_row:
            cells = self.grid[index]
            hints = self.row_hints[index]
        else:
            cells = [self.grid[r][index] for r in range(self.size)]
            hints = self.col_hints[index]

        segments: List[int] = []
        count = 0
        for cell in cells:
            if cell == CellState.FILLED:
                count += 1
            else:
                if count:
                    segments.append(count)
                    count = 0
        if count:
            segments.append(count)

        filled_cells = sum(segments)
        expected_filled = sum(hints)
        return LineProgress(hints=hints, segments=segments or [0], filled_cells=filled_cells, expected_filled=expected_filled)

    def is_game_over(self) -> bool:
        """Return True if the board matches the solution, False otherwise."""
        for r in range(self.size):
            for c in range(self.size):
                cell = self.grid[r][c]
                if cell == CellState.UNKNOWN:
                    return False
                expected_filled = bool(self._solution[r][c])
                if (cell == CellState.FILLED) != expected_filled:
                    return False
        return True

    def get_current_player(self) -> int:
        """Return the current player. In this single-player game, it is always 0."""
        return 0

    def get_valid_moves(self) -> List[Tuple[int, int, str]]:
        """Return a list of all possible actions for each cell on the board.

        Returns:
            A list of (row, col, action) tuples for all possible moves.
        """
        moves: List[Tuple[int, int, str]] = []
        for r in range(self.size):
            for c in range(self.size):
                moves.extend(((r, c, "fill"), (r, c, "mark"), (r, c, "clear"), (r, c, "toggle")))
        return moves

    def _apply_cell_state(self, row: int, col: int, state: CellState) -> None:
        """Update a cell's state and handle mistake tracking.

        Args:
            row: The row of the cell to update.
            col: The column of the cell to update.
            state: The new state to apply to the cell.
        """
        self.grid[row][col] = state
        expected_filled = bool(self._solution[row][col])

        if state == CellState.UNKNOWN:
            self.incorrect_cells.discard((row, col))
            return

        is_correct = (state == CellState.FILLED) == expected_filled
        if is_correct:
            self.incorrect_cells.discard((row, col))
        else:
            if (row, col) not in self.incorrect_cells:
                self.total_mistakes += 1
            self.incorrect_cells.add((row, col))

    def make_move(self, move: Tuple[int, int, str]) -> bool:
        """Update a cell's state based on the chosen action.

        Args:
            move: A tuple of (row, col, action) representing the move.

        Returns:
            True if the move was valid and applied, False otherwise.
        """
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        row, col, action = move
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False

        action = action.lower()
        if action not in {"fill", "mark", "clear", "toggle"}:
            return False

        if action == "clear":
            self._apply_cell_state(row, col, CellState.UNKNOWN)
        elif action == "toggle":
            current = self.grid[row][col]
            next_state = {CellState.UNKNOWN: CellState.FILLED, CellState.FILLED: CellState.EMPTY, CellState.EMPTY: CellState.UNKNOWN}[current]
            self._apply_cell_state(row, col, next_state)
        elif action == "fill":
            self._apply_cell_state(row, col, CellState.FILLED)
        else:
            self._apply_cell_state(row, col, CellState.EMPTY)

        if self.is_game_over():
            self.state = GameState.FINISHED

        return True

    def is_cell_correct(self, row: int, col: int) -> bool:
        """Return True if the cell's visible state matches the solution.

        Args:
            row: The row of the cell to check.
            col: The column of the cell to check.

        Returns:
            True if the cell is correct or unknown, False if it conflicts
            with the solution.

        Raises:
            IndexError: If the cell coordinates are out of range.
        """
        if not (0 <= row < self.size and 0 <= col < self.size):
            raise IndexError("Cell coordinates are out of range")

        cell = self.grid[row][col]
        if cell == CellState.UNKNOWN:
            return True
        expected_filled = bool(self._solution[row][col])
        return (cell == CellState.FILLED) == expected_filled

    def get_winner(self) -> int | None:
        """Return the player index if the puzzle is solved.

        Returns:
            0 if the game is won, otherwise None.
        """
        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Return the current lifecycle state of the puzzle.

        Returns:
            The current `GameState` of the puzzle.
        """
        return self.state

    def get_state_representation(self) -> List[List[str]]:
        """Return a printable, character-based representation of the board.

        Returns:
            A 2D list of strings representing the board state.
        """
        return [[cell.render() for cell in row] for row in self.grid]
