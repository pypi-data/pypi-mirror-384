"""Command-line interface for playing Ultimate Tic-Tac-Toe.

This module provides a terminal-based interactive experience for the
Ultimate Tic-Tac-Toe game. It handles user input for game setup and moves,
manages the game loop, and displays the game state to the console.

The CLI guides the player through the game, indicating which board they
must play on and validating their moves. It uses the `UltimateTicTacToeGame`
class from the `ultimate` module to manage the game's logic.

Functions:
    play_ultimate(): Runs the main game loop for a terminal-based Ultimate
                     Tic-Tac-Toe match.
"""

from __future__ import annotations

import random

from .ultimate import UltimateTicTacToeGame


def play_ultimate() -> None:
    """Runs the main game loop for an Ultimate Tic-Tac-Toe game.

    This function orchestrates the entire game flow, from welcoming the player
    and setting up the game to handling turns and announcing the final result.
    It prompts the user for their symbol, who goes first, and their moves
    throughout the game.
    """
    print("=== Ultimate Tic-Tac-Toe ===")
    print("Win small boards to claim cells on the meta-board.")
    print("Get three in a row on the meta-board to win!")
    print()

    # Get the player's choice of symbol (X or O).
    human_symbol = input("Choose your symbol (X or O) [X]: ").strip().upper() or "X"
    if human_symbol not in {"X", "O"}:
        print("Invalid symbol. Defaulting to X.")
        human_symbol = "X"
    computer_symbol = "O" if human_symbol == "X" else "X"

    # Determine who goes first.
    wants_first = input("Do you want to go first? [Y/n]: ").strip().lower()
    if wants_first in {"n", "no"}:
        starting_symbol = computer_symbol
    elif wants_first in {"y", "yes", ""}:
        starting_symbol = human_symbol
    else:
        # If the input is ambiguous, randomize the starting player.
        starting_symbol = random.choice([human_symbol, computer_symbol])
        print(f"Coin toss: {'You' if starting_symbol == human_symbol else 'Computer'} start(s)!")

    # Initialize the game engine with the chosen settings.
    game = UltimateTicTacToeGame(
        human_symbol=human_symbol,
        computer_symbol=computer_symbol,
        starting_symbol=starting_symbol,
    )

    print("\n" + game.render())
    print("\nBoards are numbered 0-8 (left to right, top to bottom)")
    print("Cells within each board are also numbered 0-8")
    print("Example: '4 5' plays on board 4 (center), cell 5 (middle-right)\n")

    # The main game loop continues until there is a winner or a draw.
    while True:
        if game.winner() or game.is_draw():
            break

        if game.current_turn == game.human_symbol:
            # It's the human's turn.
            if game.active_board is not None:
                print(f"You must play on board {game.active_board}")
            else:
                print("You can play on any available board")

            move_str = input("Your move (board cell): ").strip()
            parts = move_str.split()

            if len(parts) != 2:
                print("Enter two numbers: board index and cell index (e.g., '4 5')")
                continue

            try:
                board_idx = int(parts[0])
                cell_idx = int(parts[1])
            except ValueError:
                print("Please enter valid numbers.")
                continue

            if board_idx not in range(9) or cell_idx not in range(9):
                print("Board and cell indices must be 0-8.")
                continue

            if not game.human_move(board_idx, cell_idx):
                print("Invalid move. Try again.")
                continue

            print(f"\nYou played on board {board_idx}, cell {cell_idx}")
        else:
            # It's the computer's turn.
            print("Computer is thinking...")
            board_idx, cell_idx = game.computer_move()
            print(f"Computer played on board {board_idx}, cell {cell_idx}")

        print("\n" + game.render())

        if game.winner() or game.is_draw():
            break

        game.swap_turn()

    # Announce the final result of the game.
    print("\n=== Game Over ===")
    winner = game.winner()
    if winner == game.human_symbol:
        print("Congratulations! You won!")
    elif winner == game.computer_symbol:
        print("Computer wins!")
    else:
        print("It's a draw!")


if __name__ == "__main__":
    # This allows the script to be run directly to play the game.
    play_ultimate()
