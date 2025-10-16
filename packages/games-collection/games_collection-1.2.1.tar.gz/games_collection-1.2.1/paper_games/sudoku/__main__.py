"""Command line entry point for Sudoku puzzle generation."""

from __future__ import annotations

from .sudoku import SudokuCLI


def main() -> None:
    """Run the Sudoku CLI."""

    SudokuCLI().run()


if __name__ == "__main__":
    main()
