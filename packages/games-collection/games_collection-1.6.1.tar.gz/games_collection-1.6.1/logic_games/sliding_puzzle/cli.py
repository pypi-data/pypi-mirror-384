"""Command-line interface for the sliding puzzle game.

This module provides an interactive, text-based version of the classic
sliding puzzle (also known as the 15-puzzle). Players can choose the
board size and interact with the puzzle by specifying which tile to move
or the direction of the move.

The main game loop handles user input, renders the board, and provides
feedback on the validity of moves until the puzzle is solved.
"""

from __future__ import annotations

from .sliding_puzzle import SlidingPuzzleGame


def main() -> None:
    """Run the interactive sliding puzzle experience in the command line.

    This function manages the complete game flow, from prompting the user
    for the board size to the main game loop and the final success message.
    """
    print("SLIDING PUZZLE".center(50, "="))
    print("\nArrange the tiles in order with the blank in the bottom-right corner.")

    # Get the desired board size from the user.
    size_input = input("Choose board size (3-6, default 4): ").strip()
    try:
        size = int(size_input) if size_input else 4
    except ValueError:
        size = 4

    if size < 3:
        print("Board sizes below 3 are not supported. Using 4x4 instead.")
        size = 4
    if size > 6:
        print("Large boards can be unwieldy in the terminal. Using 6x6.")
        size = 6

    game = SlidingPuzzleGame(size=size)

    # Determine the width for formatting the tiles based on the largest number.
    tile_width = len(str(game.size * game.size - 1)) + 1

    # Main game loop, continues until the puzzle is solved.
    while not game.is_game_over():
        print(f"\nMoves taken: {game.moves}")

        # Render the current state of the board.
        for row_idx in range(game.size):
            row_tiles = []
            for col_idx in range(game.size):
                value = game.board[row_idx * game.size + col_idx]
                row_tiles.append(f"{value:>{tile_width}}" if value else " " * tile_width)
            print(" ".join(row_tiles))

        # Get the player's next move.
        move = input("\nEnter tile number or direction (u/d/l/r), q to quit: ").strip().lower()
        if move == "q":
            print("Thanks for playing!")
            return

        if not game.make_move(move):
            print("Invalid move. Choose a tile adjacent to the blank or a valid direction.")

    # Print the final success message.
    print(f"\nSolved in {game.moves} moves! Great job!")


if __name__ == "__main__":
    main()
