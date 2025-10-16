"""Command-line interface for the Sokoban puzzle game."""

from __future__ import annotations

from typing import Iterable

from .sokoban import SokobanGame


def _render_board(game: SokobanGame) -> None:
    """Render the current board state along with move statistics."""

    print()
    for row in game.get_board():
        print(row.rstrip())
    print(f"\nMoves: {game.moves} | Pushes: {game.pushes}")
    valid_moves = " ".join(game.get_valid_moves()) or "(none)"
    print(f"Valid moves: {valid_moves}")


def _print_help() -> None:
    """Display available commands for interacting with the puzzle."""

    commands: Iterable[tuple[str, str]] = (
        ("u/d/l/r", "Move the warehouse worker up, down, left, or right"),
        ("undo", "Rewind the previous move"),
        ("restart", "Reset the current level to its initial state"),
        ("next / prev", "Cycle through the curated level set"),
        ("help", "Show this help text again"),
        ("quit", "Exit the game"),
    )
    print("\nAvailable commands:")
    for shortcut, description in commands:
        print(f"  {shortcut:<10} {description}")


def main() -> None:
    """Run the Sokoban CLI with realistic level navigation and undo support."""

    print("SOKOBAN".center(60, "="))
    print("Guide the warehouse worker (@) to push every crate ($) onto storage goals (.)")
    print("Crates that rest on goals become * while the worker stands on a goal as +.\n")

    level_index = 0
    game = SokobanGame(level_index=level_index)
    _print_help()

    while True:
        total_levels = len(SokobanGame.LEVELS)
        print(f"\nLevel {level_index + 1}/{total_levels}: {game.level_name}")
        _render_board(game)

        if game.is_game_over():
            choice = input("Solved! Press Enter for the next level, type 'restart' to replay, or 'quit' to exit: ").strip().lower()
            if choice in {"quit", "q"}:
                break
            if choice in {"restart", "reset"}:
                game.reset()
                continue
            level_index = (level_index + 1) % total_levels
            game.load_level(level_index)
            continue

        command = input("Command: ").strip().lower()
        if command in {"quit", "q"}:
            break
        if command in {"help", "h"}:
            _print_help()
            continue
        if command in {"undo", "z"}:
            if not game.undo_last_move():
                print("Nothing to undo.")
            continue
        if command in {"restart", "reset"}:
            game.reset()
            print("Level restarted.")
            continue
        if command in {"next", "n"}:
            level_index = (level_index + 1) % total_levels
            game.load_level(level_index)
            continue
        if command in {"prev", "p"}:
            level_index = (level_index - 1) % total_levels
            game.load_level(level_index)
            continue
        if command in game.get_valid_moves():
            if not game.make_move(command):
                print("You cannot move in that direction.")
            continue

        print("Unrecognised command. Type 'help' to see all options.")


if __name__ == "__main__":
    main()
