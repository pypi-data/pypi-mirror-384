"""Command-line interface for playing Dots and Boxes.

This module provides the terminal-based interactive experience for playing
Dots and Boxes against a chain-aware AI opponent.
"""

from __future__ import annotations

from .dots_and_boxes import DotsAndBoxes


def play(size: int = 2) -> None:
    """Interactive dots and boxes game against a chain-aware AI."""

    game = DotsAndBoxes(size=size)
    print(f"Dots and Boxes on a {size}x{size} board. Coordinates are zero-indexed. " "Enter moves as orientation row col (e.g., 'h 0 1').")
    player_turn = True

    while not game.is_finished():
        print("\n" + game.render())
        print(f"Score - {game.human_name}: {game.scores[game.human_name]} | " f"{game.computer_name}: {game.scores[game.computer_name]}")

        if player_turn:
            move = input("Your move: ").strip().split()
            if len(move) != 3:
                print("Please enter orientation and coordinates like 'v 1 0'.")
                continue
            orientation, row_str, col_str = move
            try:
                row, col = int(row_str), int(col_str)
                completed = game.claim_edge(orientation, row, col, player=game.human_name)
            except (ValueError, KeyError) as exc:
                print(exc)
                continue
            # If the player doesn't complete a box, it's the computer's turn.
            if not completed:
                player_turn = False
        else:
            moves = game.computer_turn()
            for (orientation, row, col), completed in moves:
                message = f"Computer draws {orientation} {row} {col}"
                if completed:
                    message += f" and completes {completed} box{'es' if completed > 1 else ''}!"
                print(message)
            player_turn = True

    # Print the final board and the winner.
    print("\n" + game.render())
    human_score = game.scores[game.human_name]
    computer_score = game.scores[game.computer_name]
    if human_score > computer_score:
        print("You win!")
    elif human_score < computer_score:
        print("Computer wins!")
    else:
        print("It's a tie!")
