"""Command-line interface for playing tic-tac-toe.

This module provides the terminal-based interactive experience for playing
tic-tac-toe against an optimal minimax-based computer opponent.
"""

from __future__ import annotations

import pathlib
import random

from .stats import GameStats
from .themes import get_theme, list_themes
from .tic_tac_toe import TicTacToeGame

# Default location for stats file
STATS_FILE = pathlib.Path.home() / ".games" / "tic_tac_toe_stats.json"


def play() -> None:
    """Run the game loop in the terminal."""
    print("Welcome to Tic-Tac-Toe! Coordinates are letter-row + number-column (e.g. B2).")

    # Load statistics
    stats = GameStats.load(STATS_FILE)

    # Show statistics if there are any games played
    if stats.games_played > 0:
        show_stats = input("View your statistics? [y/N]: ").strip().lower()
        if show_stats in {"y", "yes"}:
            print("\n" + stats.summary() + "\n")

    # Get board size
    board_size_input = input("Choose board size (3, 4, or 5) [3]: ").strip()
    board_size = 3
    if board_size_input in {"3", "4", "5"}:
        board_size = int(board_size_input)
    elif board_size_input:
        print("Invalid board size. Defaulting to 3x3.")

    # Get win length
    win_length_input = input(f"Choose win length (3 to {board_size}) [{board_size}]: ").strip()
    win_length = board_size
    if win_length_input:
        try:
            win_length = int(win_length_input)
            if win_length < 3 or win_length > board_size:
                print(f"Invalid win length. Defaulting to {board_size}.")
                win_length = board_size
        except ValueError:
            print(f"Invalid win length. Defaulting to {board_size}.")

    # Get player's choice of symbols/theme
    use_theme = input("Use a themed board? [y/N]: ").strip().lower()
    if use_theme in {"y", "yes"}:
        print("\n" + list_themes())
        theme_name = input("\nChoose a theme [classic]: ").strip().lower() or "classic"
        try:
            human_symbol, computer_symbol = get_theme(theme_name)
            print(f"Using theme: {theme_name} ({human_symbol} vs {computer_symbol})")
        except ValueError as e:
            print(f"Error: {e}. Using classic theme.")
            human_symbol, computer_symbol = "X", "O"
    else:
        # Get player's choice of symbol.
        human_symbol = input("Choose your symbol (X or O) [X]: ").strip().upper() or "X"
        if human_symbol not in {"X", "O"}:
            print("Invalid symbol chosen. Defaulting to X.")
            human_symbol = "X"
        computer_symbol = "O" if human_symbol == "X" else "X"

    # Get player's choice of who goes first.
    wants_first = input("Do you want to go first? [Y/n]: ").strip().lower()
    if wants_first in {"n", "no"}:
        starting_symbol = computer_symbol
    elif wants_first in {"y", "yes", ""}:
        starting_symbol = human_symbol
    else:
        starting_symbol = random.choice([human_symbol, computer_symbol])
        print(f"We'll toss a coin… {('You' if starting_symbol == human_symbol else 'Computer')} start(s)!")

    game = TicTacToeGame(
        human_symbol=human_symbol,
        computer_symbol=computer_symbol,
        starting_symbol=starting_symbol,
        board_size=board_size,
        win_length=win_length,
    )

    print("\nThe empty board looks like this:")
    print(game.render(show_reference=True))

    # Main game loop.
    while True:
        print("\n" + game.render())
        if game.winner() or game.is_draw():
            break

        if game.current_turn == game.human_symbol:
            prompt = "Choose your move (or 'undo' to undo last move): "
            move_str = input(prompt).strip().lower()

            # Handle undo command
            if move_str == "undo":
                if game.can_undo():
                    # Undo human move
                    if game.undo_last_move():
                        print("Undid your last move.")
                        # Also undo computer's move if there was one
                        if game.can_undo():
                            game.undo_last_move()
                            print("Also undid computer's move.")
                        # Switch turn back
                        game.swap_turn()
                        continue
                else:
                    print("No moves to undo.")
                    continue

            try:
                position = game.parse_coordinate(move_str)
            except ValueError as exc:
                print(exc)
                continue
            if not game.human_move(position):
                print("That square is already taken. Try again.")
                continue
        else:
            print("Computer is thinking…")
            comp_row, comp_col = game.computer_move()
            comp_position = comp_row * game.board_size + comp_col
            coords_map = game._generate_coordinates()
            print(f"Computer chooses {coords_map[comp_position]}.")

        if game.winner() or game.is_draw():
            break
        game.swap_turn()

    # Announce the final result.
    print("\n" + game.render())
    winner = game.winner()
    if winner == game.human_symbol:
        print("You win! Congratulations.")
    elif winner == game.computer_symbol:
        print("Computer wins with perfect play.")
    else:
        print("It's a draw – a classic cat's game.")

    # Record the game result
    stats.record_game(winner, game.human_symbol, game.computer_symbol, game.board_size)
    stats.save(STATS_FILE)

    # Show updated statistics
    print("\n" + stats.summary())
