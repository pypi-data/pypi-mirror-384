"""Sudoku puzzle generator with multiple difficulties and hint system."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, Generator, List, Optional, Tuple

Grid = List[List[int]]


@dataclass
class SudokuPuzzle:
    """Representation of a Sudoku puzzle instance."""

    starting_board: Grid
    solution: Grid
    difficulty: str
    board: Grid = field(init=False)

    def __post_init__(self) -> None:
        self.board = [row[:] for row in self.starting_board]

    def reset(self) -> None:
        """Reset the puzzle to its initial state."""

        self.board = [row[:] for row in self.starting_board]

    def place_value(self, row: int, column: int, value: int) -> bool:
        """Attempt to place a value on the board."""

        if self.starting_board[row][column] != 0:
            return False
        if not self._is_valid_value(value):
            return False
        if not self._is_valid_move(row, column, value):
            return False
        self.board[row][column] = value
        return True

    def get_hint(self, apply: bool = False) -> Optional[Tuple[int, int, int]]:
        """Return a hint as (row, column, value)."""

        for row in range(9):
            for column in range(9):
                if self.board[row][column] == 0:
                    value = self.solution[row][column]
                    if apply:
                        self.board[row][column] = value
                    return row, column, value
        return None

    def is_solved(self) -> bool:
        """Check whether the puzzle is solved."""

        return self.board == self.solution

    def _is_valid_value(self, value: int) -> bool:
        return 1 <= value <= 9

    def _is_valid_move(self, row: int, column: int, value: int) -> bool:
        if any(self.board[row][index] == value for index in range(9)):
            return False
        if any(self.board[index][column] == value for index in range(9)):
            return False
        start_row = (row // 3) * 3
        start_column = (column // 3) * 3
        for r in range(start_row, start_row + 3):
            for c in range(start_column, start_column + 3):
                if self.board[r][c] == value:
                    return False
        return True


class SudokuGenerator:
    """Generate Sudoku puzzles across multiple difficulty levels."""

    def __init__(self, rng: Optional[random.Random] = None) -> None:
        self.rng = rng or random.Random()
        self._difficulty_map: Dict[str, int] = {
            "easy": 36,
            "medium": 46,
            "hard": 52,
            "expert": 58,
        }

    def generate(self, difficulty: str = "medium") -> SudokuPuzzle:
        """Generate a Sudoku puzzle for the requested difficulty."""

        difficulty_key = difficulty.lower()
        if difficulty_key not in self._difficulty_map:
            raise ValueError(f"Unknown difficulty level: {difficulty}")
        solution = self._create_complete_board()
        puzzle_board = self._carve_puzzle([row[:] for row in solution], self._difficulty_map[difficulty_key])
        return SudokuPuzzle(starting_board=puzzle_board, solution=solution, difficulty=difficulty_key)

    def _create_complete_board(self) -> Grid:
        base = 3
        side = base * base
        board = [[self._pattern(row, column, base) for column in range(side)] for row in range(side)]
        self._shuffle_rows(board, base)
        self._shuffle_columns(board, base)
        self._shuffle_numbers(board)
        return board

    def _pattern(self, row: int, column: int, base: int) -> int:
        return (base * (row % base) + row // base + column) % (base * base) + 1

    def _shuffle_rows(self, board: Grid, base: int) -> None:
        rows = [row for row in range(base)]
        self.rng.shuffle(rows)
        row_groups = []
        for group_index in rows:
            indices = list(range(group_index * base, (group_index + 1) * base))
            self.rng.shuffle(indices)
            row_groups.extend(indices)
        board[:] = [board[index] for index in row_groups]

    def _shuffle_columns(self, board: Grid, base: int) -> None:
        columns = [column for column in range(base)]
        self.rng.shuffle(columns)
        column_groups = []
        for group_index in columns:
            indices = list(range(group_index * base, (group_index + 1) * base))
            self.rng.shuffle(indices)
            column_groups.extend(indices)
        for row_index in range(len(board)):
            row = board[row_index]
            board[row_index] = [row[index] for index in column_groups]

    def _shuffle_numbers(self, board: Grid) -> None:
        numbers = list(range(1, 10))
        shuffled = numbers[:]
        self.rng.shuffle(shuffled)
        mapping = {original: shuffled[index] for index, original in enumerate(numbers)}
        for row_index, row in enumerate(board):
            board[row_index] = [mapping[value] for value in row]

    def _carve_puzzle(self, board: Grid, cells_to_remove: int) -> Grid:
        positions = [(row, column) for row in range(9) for column in range(9)]
        self.rng.shuffle(positions)
        removed = 0
        for row, column in positions:
            if removed >= cells_to_remove:
                break
            backup = board[row][column]
            if backup == 0:
                continue
            board[row][column] = 0
            if not self._has_unique_solution([line[:] for line in board]):
                board[row][column] = backup
                continue
            removed += 1
        return board

    def _has_unique_solution(self, board: Grid) -> bool:
        solutions_found = 0
        for _ in self._solve_generator(board):
            solutions_found += 1
            if solutions_found > 1:
                return False
        return solutions_found == 1

    def _solve_generator(self, board: Grid) -> Generator[Grid, None, None]:
        empty = self._find_empty(board)
        if empty is None:
            yield [row[:] for row in board]
            return
        row, column = empty
        for value in range(1, 10):
            if self._is_valid(board, row, column, value):
                board[row][column] = value
                yield from self._solve_generator(board)
                board[row][column] = 0

    def _find_empty(self, board: Grid) -> Optional[Tuple[int, int]]:
        for row in range(9):
            for column in range(9):
                if board[row][column] == 0:
                    return row, column
        return None

    def _is_valid(self, board: Grid, row: int, column: int, value: int) -> bool:
        if any(board[row][index] == value for index in range(9)):
            return False
        if any(board[index][column] == value for index in range(9)):
            return False
        start_row = (row // 3) * 3
        start_column = (column // 3) * 3
        for r in range(start_row, start_row + 3):
            for c in range(start_column, start_column + 3):
                if board[r][c] == value:
                    return False
        return True


class SudokuCLI:
    """Simple command line experience for Sudoku."""

    def __init__(self) -> None:
        self._generator = SudokuGenerator()
        self._puzzle = self._generator.generate("easy")

    def run(self) -> None:
        print("Sudoku CLI - type 'hint', 'set r c v', 'reset', or 'quit'.")
        while True:
            self._display_board()
            if self._puzzle.is_solved():
                print("Congratulations, puzzle solved!")
                break
            command = input("> ").strip().lower()
            if command == "quit":
                break
            if command == "reset":
                self._puzzle.reset()
                continue
            if command == "hint":
                hint = self._puzzle.get_hint(apply=True)
                if hint:
                    print(f"Hint applied at row {hint[0]}, column {hint[1]} with value {hint[2]}")
                else:
                    print("No hints available. Puzzle solved!")
                continue
            if command.startswith("set"):
                parts = command.split()
                if len(parts) != 4:
                    print("Usage: set row column value")
                    continue
                try:
                    row, column, value = map(int, parts[1:])
                except ValueError:
                    print("Row, column, and value must be integers")
                    continue
                if not self._puzzle.place_value(row, column, value):
                    print("Invalid move. Check row, column, or existing givens.")
            else:
                print("Unknown command.")

    def _display_board(self) -> None:
        board = self._puzzle.board
        for row_index, row in enumerate(board):
            if row_index % 3 == 0 and row_index != 0:
                print("------+-------+------")
            row_chunks = [row[0:3], row[3:6], row[6:9]]
            formatted = []
            for chunk in row_chunks:
                formatted.append(" ".join(str(value) if value != 0 else "." for value in chunk))
            print(" | ".join(formatted))
