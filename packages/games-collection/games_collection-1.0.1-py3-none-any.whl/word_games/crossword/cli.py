"""CLI for Crossword."""

from __future__ import annotations

from .crossword import CrosswordGame


def main() -> None:
    """Run Crossword game."""
    print("CROSSWORD".center(50, "="))
    print("\nSolve the crossword puzzle!")

    game = CrosswordGame()
    game.state = game.state.IN_PROGRESS

    while not game.is_game_over():
        print(f"\nSolved: {len(game.solved)}/{len(game.PUZZLE)}")
        print("\nClues:")

        for cid, (r, c, dir, ans, clue) in game.PUZZLE.items():
            status = "✓" if cid in game.solved else " "
            print(f"  [{status}] {cid}. {dir.capitalize()}: {clue}")

        try:
            cid = int(input("\nClue number: "))
            guess = input("Answer: ").strip()

            if not game.make_move((cid, guess)):
                print("Incorrect or already solved!")
        except ValueError:
            print("Invalid input!")

    print("\nPuzzle complete!")


if __name__ == "__main__":
    main()
