"""Interactive command-line interface for the Picross (Nonogram) game.

This module provides a text-based user interface for solving Picross puzzles.
It features a dynamically rendered board with row and column hints, progress
indicators, and mistake tracking.

Players can interact with the board by filling, marking, or clearing cells
using simple text commands. The interface provides feedback on the validity
of moves and the overall progress of the puzzle.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from .picross import CellState, PicrossGame


def _format_hints(hints: Sequence[int]) -> str:
    """Return a printable string for a list of hints.

    Args:
        hints: A sequence of integers representing the hints for a line.

    Returns:
        A space-separated string of the hints.
    """
    display_hints = hints if hints != [0] else [0]
    return " ".join(str(hint) for hint in display_hints)


def _render_board(game: PicrossGame) -> None:
    """Render the game board, including row and column hints.

    This function dynamically adjusts the layout to accommodate the size
    of the hints, ensuring a clean and readable display.

    Args:
        game: The `PicrossGame` instance to render.
    """
    row_hint_width = max(len(_format_hints(hints)) for hints in game.row_hints)
    col_hint_height = max(len(hints if hints != [0] else [0]) for hints in game.col_hints)

    # Render the column hints above the board.
    for level in range(col_hint_height):
        line = " " * (row_hint_width + 5)
        for hints in game.col_hints:
            display_hints = hints if hints != [0] else [0]
            padding = col_hint_height - len(display_hints)
            value = str(display_hints[level - padding]) if level >= padding else ""
            line += f"{value:^3}"
        print(line)

    # Render the board rows, each prefixed with its hints and status.
    for row_idx, row in enumerate(game.grid):
        progress = game.get_line_progress(row_idx, is_row=True)
        satisfied = progress.is_satisfied and progress.filled_cells == progress.expected_filled and all(cell != CellState.UNKNOWN for cell in row)
        status = "✔" if satisfied else " "
        hint_block = _format_hints(game.row_hints[row_idx]).rjust(row_hint_width)
        cell_block = "".join(f" {cell.render()} " for cell in row)
        print(f"{hint_block} {status} |{cell_block}  {row_idx}")

    # Render the column index footer.
    footer = " " * (row_hint_width + 5) + "".join(f" {col:>2}" for col in range(game.size))
    print(footer)


def _print_help() -> None:
    """Display the list of available commands to the player."""
    print(
        "Available commands:\n"
        "  f <row> <col>  - Fill a cell\n"
        "  m <row> <col>  - Mark a cell as empty\n"
        "  c <row> <col>  - Clear a cell back to unknown\n"
        "  t <row> <col>  - Cycle through fill → empty → unknown\n"
        "  h row <idx>    - Show progress for a row\n"
        "  h col <idx>    - Show progress for a column\n"
        "  s              - Show current mistake statistics\n"
        "  q              - Quit the puzzle"
    )


def _print_progress(title: str, hints: Sequence[int], segments: Iterable[int], filled: int, expected: int) -> None:
    """Print a detailed summary of a row or column's progress.

    Args:
        title: The title for the progress summary (e.g., "Row 5").
        hints: The hints for the line.
        segments: The current contiguous groups of filled cells.
        filled: The number of cells currently filled.
        expected: The total number of cells that should be filled.
    """
    segment_list = list(segments)
    display_segments = segment_list or [0]
    print(f"{title} hints: {list(hints)}")
    print(f"Current groups: {display_segments}")
    print(f"Filled cells: {filled}/{expected}")


def main() -> None:
    """Run the main loop for the Picross command-line interface."""
    print("PICROSS".center(60, "="))
    print("Solve the nonogram by using the numeric hints to deduce the picture.\n")

    game = PicrossGame()
    _print_help()

    # Main game loop, continues until the puzzle is solved.
    while not game.is_game_over():
        print()
        _render_board(game)
        print(f"Mistakes: {game.total_mistakes} (current incorrect cells: {len(game.incorrect_cells)})")

        raw_command = input("Command: ").strip().lower()
        if not raw_command:
            continue

        if raw_command in {"q", "quit"}:
            print("Goodbye!")
            return

        if raw_command in {"s", "status"}:
            print(f"Total mistakes so far: {game.total_mistakes}. \n" f"Cells currently conflicting with the solution: {sorted(game.incorrect_cells)}")
            continue

        if raw_command in {"help", "?"}:
            _print_help()
            continue

        parts = raw_command.split()
        if parts[0] == "h" and len(parts) == 3:
            # Handle the hint/progress command.
            axis, index_text = parts[1], parts[2]
            try:
                index = int(index_text)
                is_row = axis in {"row", "r"}
                if axis not in {"row", "r", "col", "c"}:
                    raise ValueError
                progress = game.get_line_progress(index, is_row=is_row)
                _print_progress(
                    f"{'Row' if is_row else 'Column'} {index}",
                    progress.hints,
                    progress.segments,
                    progress.filled_cells,
                    progress.expected_filled,
                )
            except (ValueError, IndexError):
                print("Invalid line for hint command.")
            continue

        if parts[0] in {"f", "m", "c", "t"} and len(parts) == 3:
            # Handle cell manipulation commands.
            try:
                row = int(parts[1])
                col = int(parts[2])
            except ValueError:
                print("Row and column must be numbers.")
                continue

            action_map = {"f": "fill", "m": "mark", "c": "clear", "t": "toggle"}
            action = action_map[parts[0]]
            if not game.make_move((row, col, action)):
                print("Invalid move.")
                continue

            if not game.is_cell_correct(row, col) and game.grid[row][col] != CellState.UNKNOWN:
                print("⚠️ That move contradicts the hidden image. You may clear or toggle it.")
            continue

        print("Unknown command. Type 'help' for a list of available actions.")

    # Game over sequence.
    print("\nCongratulations! You completed the nonogram.")
    if game.total_mistakes:
        print(f"Final score: {game.total_mistakes} mistake(s) made along the way.")
    else:
        print("Flawless victory: no mistakes recorded!")


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
