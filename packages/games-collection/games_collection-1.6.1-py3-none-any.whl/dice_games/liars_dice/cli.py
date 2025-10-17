"""Command-line interface for the Liar's Dice game.

This module provides a text-based interface to play Liar's Dice. It allows users
to play against AI opponents, make bids, and challenge other players' bids.

The CLI handles user input for game configuration, displays the game state,
and orchestrates turns for both human and AI players.

Functions:
    _prompt_configuration: Gets player and AI counts from the user.
    _prompt_int: Prompts the user for an integer within a specified range.
    _print_table_state: Displays the number of dice each player has left.
    _summarize_challenge: Prints a detailed summary of a challenge outcome.
    _handle_ai_turn: Executes a turn for an AI player.
    _handle_human_turn: Manages a turn for a human player.
    main: The main entry point for the CLI application.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from common.ai_strategy import HeuristicStrategy
from common.game_engine import GameState

from .liars_dice import LiarsDiceGame


def _prompt_configuration() -> Tuple[int, int]:
    """Prompts the user for the total number of players and AI opponents.

    Returns:
        A tuple containing the total number of players and AI opponents.
    """
    while True:
        try:
            players = int(input("Enter the number of players (2-6): "))
            if 2 <= players <= 6:
                break
            print("Please choose a number of players between 2 and 6.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    while True:
        try:
            ai_players = int(input(f"How many AI opponents should there be (0-{players - 1})? "))
            if 0 <= ai_players < players:
                break
            print(f"The number of AI opponents must be between 0 and {players - 1}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    return players, ai_players


def _prompt_int(prompt: str, minimum: int, maximum: int) -> int:
    """Prompts the user for an integer within a specified range.

    Args:
        prompt: The message to display to the user.
        minimum: The minimum acceptable value (inclusive).
        maximum: The maximum acceptable value (inclusive).

    Returns:
        The validated integer provided by the user.
    """
    while True:
        try:
            value = int(input(prompt))
            if minimum <= value <= maximum:
                return value
            print(f"Please enter a value between {minimum} and {maximum}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def _print_table_state(game: LiarsDiceGame) -> None:
    """Displays the number of dice remaining for each player.

    Args:
        game: The current `LiarsDiceGame` instance.
    """
    summaries = []
    for idx, dice in enumerate(game.player_dice):
        status = f"Player {idx + 1}: {len(dice)} dice"
        if game.eliminated[idx]:
            status += " (Eliminated)"
        summaries.append(status)
    print("Current dice count: " + ", ".join(summaries))


def _summarize_challenge(game: LiarsDiceGame, bid: Tuple[int, int], before_challenge_dice: List[int]) -> None:
    """Prints a detailed summary of the outcome of a challenge.

    Args:
        game: The `LiarsDiceGame` instance after the challenge.
        bid: The bid that was challenged.
        before_challenge_dice: The dice counts of each player before the challenge.
    """
    quantity, face = bid
    actual_count = sum(d.count(face) for d in game.player_dice)
    after_challenge_dice = [len(d) for d in game.player_dice]
    loser_idx = next((i for i, (b, a) in enumerate(zip(before_challenge_dice, after_challenge_dice)) if a < b), None)

    if actual_count >= quantity:
        print(f"Challenge failed! There were actually {actual_count} dice showing {face}.")
    else:
        print(f"Challenge succeeded! There were only {actual_count} dice showing {face}.")

    if loser_idx is not None:
        print(f"Player {loser_idx + 1} loses a die and now has {after_challenge_dice[loser_idx]} remaining.")


def _handle_ai_turn(game: LiarsDiceGame, strategy: HeuristicStrategy) -> None:
    """Executes a full turn for an AI player using its strategy.

    Args:
        game: The current `LiarsDiceGame` instance.
        strategy: The AI's decision-making strategy.
    """
    player_idx = game.get_current_player()
    print(f"\n--- AI Player {player_idx + 1}'s Turn ---")
    if game.current_bid:
        print(f"The current bid is: {game.current_bid[0]}x {game.current_bid[1]}'s")

    valid_moves = game.get_valid_moves()
    move = strategy.select_move(valid_moves, game)

    if move == (-1, -1):
        print("AI chooses to challenge the bid!")
        dice_counts_before = [len(d) for d in game.player_dice]
        challenged_bid = game.current_bid
        game.make_move(move)
        if challenged_bid:
            _summarize_challenge(game, challenged_bid, dice_counts_before)
    else:
        quantity, face = move
        print(f"AI bids {quantity}x {face}'s.")
        game.make_move(move)


def _handle_human_turn(game: LiarsDiceGame) -> None:
    """Manages a turn for a human player, prompting for actions.

    Args:
        game: The current `LiarsDiceGame` instance.
    """
    player_idx = game.get_current_player()
    print(f"\n--- Your Turn (Player {player_idx + 1}) ---")
    print(f"Your dice: {sorted(game.player_dice[player_idx])}")

    if game.current_bid:
        print(f"The current bid is: {game.current_bid[0]}x {game.current_bid[1]}'s")
        choice = input("Would you like to (B)id higher or (C)hallenge? ").strip().upper()
        if choice == "C":
            dice_counts_before = [len(d) for d in game.player_dice]
            challenged_bid = game.current_bid
            game.make_move((-1, -1))
            if challenged_bid:
                _summarize_challenge(game, challenged_bid, dice_counts_before)
            return

    # Prompt for a new bid.
    while True:
        quantity = _prompt_int("Enter your bid quantity: ", 1, game.get_active_dice_total())
        face = _prompt_int("Enter your bid face value (1-6): ", 1, 6)
        if game.make_move((quantity, face)):
            break
        print("Invalid bid. Your bid must be higher than the previous one. Please try again.")


def main() -> None:
    """Runs the main loop for the Liar's Dice command-line game."""
    print("=" * 50)
    print("LIAR'S DICE".center(50))
    print("=" * 50)
    print("\nWelcome to Liar's Dice! The last player with dice wins.")

    # Set up the game.
    total_players, ai_players = _prompt_configuration()
    game = LiarsDiceGame(num_players=total_players)
    game.state = GameState.IN_PROGRESS

    # Configure AI players.
    ai_indices = set(range(total_players - ai_players, total_players))
    ai_strategies: Dict[int, HeuristicStrategy] = {idx: game.create_adaptive_ai() for idx in ai_indices}

    # Main game loop.
    while not game.is_game_over():
        print("-" * 20)
        _print_table_state(game)
        player_idx = game.get_current_player()

        if player_idx in ai_indices:
            _handle_ai_turn(game, ai_strategies[player_idx])
        else:
            _handle_human_turn(game)

    # Game over: announce the winner.
    winner = game.get_winner()
    assert winner is not None, "Game should have a winner."
    print(f"\n{'=' * 50}")
    print(f"Player {winner + 1} is the last one standing and wins the game!")


if __name__ == "__main__":
    main()
