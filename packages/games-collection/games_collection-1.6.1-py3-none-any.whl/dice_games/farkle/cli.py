"""Command-line interface for the Farkle dice game.

This script provides a text-based interface for playing Farkle against other
human players or AI opponents. It handles user input, displays game state,
and manages the game flow.

Functions:
    _prompt_player_configuration: Gets the number of human and AI players.
    _render_scoreboard: Formats and displays the current scores.
    _execute_ai_turn: Manages a full turn for an AI player.
    main: The main entry point for the CLI application.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from common.ai_strategy import HeuristicStrategy
from common.game_engine import GameState

from .farkle import FarkleGame


def _prompt_player_configuration() -> Tuple[int, int]:
    """Prompts the user for the number of total players and AI opponents.

    This function ensures that the input is valid (e.g., within the allowed
    range of players).

    Returns:
        A tuple containing the total number of players and the number of AI players.
    """
    while True:
        try:
            total_players = int(input("Enter total number of players (2-6): "))
            if 2 <= total_players <= 6:
                break
            print("Please enter a number between 2 and 6.")
        except ValueError:
            print("Please enter a valid number.")

    while True:
        try:
            ai_players = int(input(f"How many AI opponents should join (0-{total_players - 1})? "))
            if 0 <= ai_players < total_players:
                break
            print(f"AI opponents must be between 0 and {total_players - 1}.")
        except ValueError:
            print("Please enter a valid number.")

    return total_players, ai_players


def _render_scoreboard(scores: List[int]) -> str:
    """Formats a scoreboard string from a list of scores.

    Args:
        scores: A list of integers representing player scores.

    Returns:
        A formatted string showing the score for each player.
    """
    return ", ".join(f"Player {i + 1}: {score}" for i, score in enumerate(scores))


def _execute_ai_turn(game: FarkleGame, strategy: HeuristicStrategy) -> None:
    """Plays out a full AI turn using the provided heuristic strategy.

    The AI will continue to roll or bank based on the decisions made by its
    strategy until its turn is over.

    Args:
        game: The `FarkleGame` instance.
        strategy: The AI's decision-making strategy.
    """
    player_index = game.get_current_player()
    print(f"\n--- AI Player {player_index + 1}'s Turn ---")

    # The AI's turn loop.
    while game.get_current_player() == player_index:
        # Get the best move from the AI strategy.
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            break  # Should not happen if logic is correct.

        move = strategy.select_move(valid_moves, game)
        dice_to_bank, continue_rolling = move

        if dice_to_bank:
            score = game._calculate_score(dice_to_bank)
            print(f"AI banks {dice_to_bank} for {score} points. Turn total: {game.turn_score + score}")
        else:
            # This case handles the initial roll of a turn.
            print("AI starts its turn by rolling...")

        game.make_move(move)

        if not game.last_roll:  # Turn ended
            break

        print(f"AI's new roll: {game.last_roll}")

        if not game._has_scoring_dice(game.last_roll):
            print("AI Farkled!")
            game.make_move(([], False))  # End the turn officially after a farkle.
            break

        if not continue_rolling:
            print("AI decides to bank its score and end the turn.")
            break


def main() -> None:
    """Runs the main loop for the Farkle command-line game."""
    # Print welcome message and rules.
    print("=" * 50)
    print("FARKLE".center(50))
    print("=" * 50)
    print("\nWelcome to Farkle, the game of guts and luck!")
    print("\n--- Scoring Rules ---")
    print("  - Single 1: 100 points")
    print("  - Single 5: 50 points")
    print("  - Three of a kind: 100 × die number (except three 1s = 1000)")
    print("  - Four, Five, or Six of a kind: Doubles the previous score")
    print("  - Straight (1-6): 1500 points")
    print("  - Three pairs: 1500 points")
    print("\nFirst player to reach 10,000 points wins!")
    print()

    # Set up the game.
    total_players, ai_players = _prompt_player_configuration()
    game = FarkleGame(num_players=total_players)
    game.state = GameState.IN_PROGRESS

    # Configure AI players.
    ai_indices = set(range(total_players - ai_players, total_players))
    ai_strategies: Dict[int, HeuristicStrategy] = {idx: game.create_adaptive_ai() for idx in ai_indices}

    # Main game loop.
    while not game.is_game_over():
        player_index = game.get_current_player()
        print(f"\n{'=' * 50}")
        print(f"--- Player {player_index + 1}'s Turn ---")
        print(f"Scores: {_render_scoreboard(game.scores)}")
        print(f"Current turn score: {game.turn_score}")
        print(f"Dice to roll: {game.dice_in_hand}")

        # Handle AI or human turn.
        if player_index in ai_indices:
            _execute_ai_turn(game, ai_strategies[player_index])
            continue

        # Human player's turn.
        input("\nPress Enter to roll the dice...")
        game.make_move(([], True))  # Initial roll.
        print(f"You rolled: {game.last_roll}")

        if not game._has_scoring_dice(game.last_roll):
            print("\nFARKLE! No scoring dice. Your turn is over.")
            game.make_move(([], False))  # End the turn.
            continue

        roll_score = game._calculate_score(game.last_roll)
        print(f"This roll is worth {roll_score} points.")

        # Ask the player whether to continue or bank.
        while True:
            choice = input("\nBank these dice and (C)ontinue rolling, or (E)nd turn? ").strip().upper()
            if choice in {"C", "E"}:
                break
            print("Invalid input. Please enter 'C' to continue or 'E' to end.")

        continue_rolling = choice == "C"
        game.make_move((game.last_roll, continue_rolling))

    # Game over: announce the winner.
    winner = game.get_winner()
    assert winner is not None, "Game should have a winner."
    print(f"\n{'=' * 50}")
    print(f"Player {winner + 1} wins the game with {game.scores[winner]} points!")
    print(f"Final Scores: {_render_scoreboard(game.scores)}")


if __name__ == "__main__":
    main()
