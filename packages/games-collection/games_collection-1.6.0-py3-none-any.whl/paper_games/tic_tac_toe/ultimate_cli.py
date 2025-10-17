"""Command-line interface for Ultimate Tic-Tac-Toe."""

from __future__ import annotations

import random

from .ultimate import UltimateTicTacToeGame


def play_ultimate() -> None:
    """Run the ultimate tic-tac-toe game loop."""
    print("=== Ultimate Tic-Tac-Toe ===")
    print("Win small boards to claim cells on the meta-board.")
    print("Get three in a row on the meta-board to win!")
    print()

    # Get player's choice of symbol
    human_symbol = input("Choose your symbol (X or O) [X]: ").strip().upper() or "X"
    if human_symbol not in {"X", "O"}:
        print("Invalid symbol. Defaulting to X.")
        human_symbol = "X"
    computer_symbol = "O" if human_symbol == "X" else "X"

    # Get player's choice of who goes first
    wants_first = input("Do you want to go first? [Y/n]: ").strip().lower()
    if wants_first in {"n", "no"}:
        starting_symbol = computer_symbol
    elif wants_first in {"y", "yes", ""}:
        starting_symbol = human_symbol
    else:
        starting_symbol = random.choice([human_symbol, computer_symbol])
        print(f"Coin toss: {'You' if starting_symbol == human_symbol else 'Computer'} start(s)!")

    game = UltimateTicTacToeGame(
        human_symbol=human_symbol,
        computer_symbol=computer_symbol,
        starting_symbol=starting_symbol,
    )

    print("\n" + game.render())
    print("\nBoards are numbered 0-8 (left to right, top to bottom)")
    print("Cells within each board are also numbered 0-8")
    print("Example: '4 5' plays on board 4 (center), cell 5 (middle-right)\n")

    # Main game loop
    while True:
        if game.winner() or game.is_draw():
            break

        if game.current_turn == game.human_symbol:
            # Human's turn
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
            # Computer's turn
            print("Computer is thinking...")
            board_idx, cell_idx = game.computer_move()
            print(f"Computer played on board {board_idx}, cell {cell_idx}")

        print("\n" + game.render())

        if game.winner() or game.is_draw():
            break

        game.swap_turn()

    # Announce result
    print("\n=== Game Over ===")
    winner = game.winner()
    if winner == game.human_symbol:
        print("Congratulations! You won!")
    elif winner == game.computer_symbol:
        print("Computer wins!")
    else:
        print("It's a draw!")


if __name__ == "__main__":
    play_ultimate()
