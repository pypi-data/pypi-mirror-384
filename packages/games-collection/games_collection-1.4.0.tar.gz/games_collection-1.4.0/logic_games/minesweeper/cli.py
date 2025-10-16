"""Command-line interface for Minesweeper game."""

from __future__ import annotations

from .minesweeper import Difficulty, MinesweeperGame


def main() -> None:
    """Run Minesweeper game in CLI mode."""
    print("=" * 50)
    print("MINESWEEPER".center(50))
    print("=" * 50)
    print("\nWelcome to Minesweeper!")
    print("\nSelect difficulty:")
    print("1. Beginner (9x9, 10 mines)")
    print("2. Intermediate (16x16, 40 mines)")
    print("3. Expert (16x30, 99 mines)")

    while True:
        try:
            choice = int(input("\nEnter choice (1-3): "))
            if choice == 1:
                difficulty = Difficulty.BEGINNER
                break
            elif choice == 2:
                difficulty = Difficulty.INTERMEDIATE
                break
            elif choice == 3:
                difficulty = Difficulty.EXPERT
                break
            print("Please enter 1, 2, or 3.")
        except ValueError:
            print("Please enter a valid number.")

    game = MinesweeperGame(difficulty)

    print("\nControls:")
    print("  Enter row col action")
    print("  Actions: r (reveal), f (flag), u (clear mark), q (question mark), o (chord)")
    print("  Example: 3 5 r  (reveal row 3, col 5)")
    print("  Chord reveals neighbors when adjacent flags match the number.")
    print()

    # Game loop
    while not game.is_game_over():
        # Display board
        print("\n" + "  " + " ".join(f"{i:2}" for i in range(game.cols)))
        for row in range(game.rows):
            cells = " ".join(f"{game.get_cell_display(row, col):2}" for col in range(game.cols))
            print(f"{row:2} {cells}")

        print(f"\nMines: {game.num_mines}  Flagged: {len(game.flagged_positions)}")
        print(f"Revealed: {game.revealed_count}/{game.rows * game.cols - game.num_mines}")

        # Get move
        while True:
            try:
                move_input = input("\nEnter move (row col action): ").strip().split()
                if len(move_input) != 3:
                    print("Please enter row, col, and action.")
                    continue

                row = int(move_input[0])
                col = int(move_input[1])
                action_char = move_input[2].lower()

                action = {"r": "reveal", "f": "flag", "u": "unflag", "q": "question", "o": "chord"}.get(action_char)
                if not action:
                    print("Action must be r, f, u, q, or o.")
                    continue

                if game.make_move((row, col, action)):
                    break
                print("Invalid move. Try again.")
            except (ValueError, IndexError):
                print("Invalid input. Use format: row col action")

    # Game over
    print("\n" + "=" * 50)

    # Show final board
    print("\nFinal board:")
    print("  " + " ".join(f"{i:2}" for i in range(game.cols)))
    for row in range(game.rows):
        cells = " ".join(f"{game.get_cell_display(row, col):2}" for col in range(game.cols))
        print(f"{row:2} {cells}")

    if game.game_won:
        print("\n🎉 Congratulations! You won!")
    else:
        print("\n💥 Game Over! You hit a mine.")


if __name__ == "__main__":
    main()
