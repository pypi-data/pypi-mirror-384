"""CLI for Crossword."""

from __future__ import annotations

import argparse
from pathlib import Path

from .crossword import CrosswordGame, CrosswordPackManager


def build_parser() -> argparse.ArgumentParser:
    """Create a parser for crossword CLI options."""

    parser = argparse.ArgumentParser(description="Play or manage crossword packs.")
    parser.add_argument("--pack", type=Path, default=None, help="Import a crossword pack from the provided JSON file")
    parser.add_argument(
        "--export",
        type=Path,
        default=None,
        help="Write the active crossword pack to the specified JSON file",
    )
    return parser


def main() -> None:
    """Run Crossword game."""

    parser = build_parser()
    args = parser.parse_args()

    print("CROSSWORD".center(50, "="))
    print("\nSolve the crossword puzzle or manage packs!")

    if args.pack is not None:
        clues = CrosswordPackManager.load(args.pack)
        print(f"\nLoaded crossword pack from {args.pack}")
    else:
        clues = None

    game = CrosswordGame(clues)
    game.state = game.state.IN_PROGRESS

    while not game.is_game_over():
        print(f"\nSolved: {len(game.solved)}/{len(game.get_clues())}")
        print("\nClues:")

        for cid, clue in game.get_clues().items():
            status = "✓" if cid in game.solved else " "
            direction = clue.direction.capitalize()
            location = f"(r{clue.row}, c{clue.column})"
            print(f"  [{status}] {cid}. {direction} {location}: {clue.clue}")

        try:
            cid = int(input("\nClue number: "))
            guess = input("Answer: ").strip()

            if not game.make_move((cid, guess)):
                print("Incorrect or already solved!")
        except ValueError:
            print("Invalid input!")

    print("\nPuzzle complete!")

    if args.export is not None:
        CrosswordPackManager.dump(game.get_clues(), args.export)
        print(f"Pack exported to {args.export}")


if __name__ == "__main__":
    main()
