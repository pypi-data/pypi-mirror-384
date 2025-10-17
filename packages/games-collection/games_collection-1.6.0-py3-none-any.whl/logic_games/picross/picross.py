"""Picross game engine implementation.

This module contains a feature-complete Picross/Nonogram engine that mirrors
the behaviour of popular handheld and digital versions of the puzzle. Players
can fill, mark or clear cells, track mistakes, and inspect line progress while
solving the puzzle purely from the row and column hints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from common.game_engine import GameEngine, GameState
from logic_games.minesweeper.minesweeper import CellState


@dataclass(frozen=True)
class LineProgress:
    """Representation of a row or column's progress toward completion."""

    hints: Sequence[int]
    segments: Sequence[int]
    filled_cells: int
    expected_filled: int

    @property
    def is_satisfied(self) -> bool:
        """Return True if the current segments match the official hints."""

        return list(self.segments) == list(self.hints)


class PicrossGame(GameEngine[Tuple[int, int, str], int]):
    """Picross/Nonogram picture logic puzzle."""

    # 10x10 lantern-style puzzle (1 = filled, 0 = empty)
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
            solution: Optional custom solution grid using 1 for filled cells and
                0 for empty cells. When omitted, a default 10x10 puzzle is used.
        """

        if solution is None:
            solution = self.SOLUTION
        self._solution = self._validate_solution(solution)
        self.size = len(self._solution)
        self.row_hints = [self._get_hints(row) for row in self._solution]
        self.col_hints = [self._get_hints(column) for column in zip(*self._solution)]
        self.reset()

    def _validate_solution(self, solution: Sequence[Sequence[int]]) -> List[List[int]]:
        """Validate the provided solution grid."""

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
        """Reset the puzzle to its initial unsolved state."""

        self.state = GameState.NOT_STARTED
        self.grid: List[List[CellState]] = [[CellState.UNKNOWN for _ in range(self.size)] for _ in range(self.size)]
        self.total_mistakes = 0
        self.incorrect_cells: set[Tuple[int, int]] = set()

    @staticmethod
    def _get_hints(line: Iterable[int]) -> List[int]:
        """Generate Picross hints for a row or column."""

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
        """Return progress information for a given row or column."""

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
        """Return True when the board matches the hidden solution."""

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
        """Picross is a single-player puzzle."""

        return 0

    def get_valid_moves(self) -> List[Tuple[int, int, str]]:
        """Return a list of all possible actions for each cell."""

        moves: List[Tuple[int, int, str]] = []
        for r in range(self.size):
            for c in range(self.size):
                moves.extend(((r, c, "fill"), (r, c, "mark"), (r, c, "clear"), (r, c, "toggle")))
        return moves

    def _apply_cell_state(self, row: int, col: int, state: CellState) -> None:
        """Update a cell and book-keep mistakes."""

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
        """Update a cell with the chosen action."""

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
        """Return True if the visible state matches the solution."""

        if not (0 <= row < self.size and 0 <= col < self.size):
            raise IndexError("Cell coordinates are out of range")

        cell = self.grid[row][col]
        if cell == CellState.UNKNOWN:
            return True
        expected_filled = bool(self._solution[row][col])
        return (cell == CellState.FILLED) == expected_filled

    def get_winner(self) -> int | None:
        """Return the player index when the puzzle is solved."""

        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Return the current lifecycle state of the puzzle."""

        return self.state

    def get_state_representation(self) -> List[List[str]]:
        """Return a printable representation of the board."""

        return [[cell.render() for cell in row] for row in self.grid]
