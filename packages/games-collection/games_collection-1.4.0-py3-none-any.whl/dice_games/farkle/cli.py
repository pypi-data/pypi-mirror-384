"""Command-line interface for Farkle game."""

from __future__ import annotations

from typing import Dict, List, Tuple

from common.ai_strategy import HeuristicStrategy
from common.game_engine import GameState

from .farkle import FarkleGame


def _prompt_player_configuration() -> Tuple[int, int]:
    """Prompt for player and AI counts."""

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
            ai_players = int(input("How many AI opponents should join? "))
            if 0 <= ai_players < total_players:
                break
            print("AI opponents must be fewer than the total players.")
        except ValueError:
            print("Please enter a valid number.")

    return total_players, ai_players


def _render_scoreboard(scores: List[int]) -> str:
    """Format a scoreboard string."""

    return ", ".join(f"P{i + 1}: {score}" for i, score in enumerate(scores))


def _execute_ai_turn(game: FarkleGame, strategy) -> None:
    """Play out a full AI turn using the provided strategy."""

    player = game.get_current_player()
    print(f"\nAI Player {player + 1} is rolling...")

    while True:
        valid_moves = game.get_valid_moves()
        move = strategy.select_move(valid_moves, game)
        dice_to_bank, continue_rolling = move
        if dice_to_bank:
            print(f"AI banks {dice_to_bank} ({game._calculate_score(dice_to_bank)} pts)")
        else:
            print("AI chooses to roll")
        game.make_move(move)

        if game.get_current_player() != player:
            break
        if not continue_rolling:
            break
        if not game.last_roll:
            break

        print(f"New roll: {game.last_roll}")
        if not game._has_scoring_dice(game.last_roll):
            print("AI farkled!")
            game.make_move(([], False))
            break


def main() -> None:
    """Run Farkle game in CLI mode."""

    print("=" * 50)
    print("FARKLE".center(50))
    print("=" * 50)
    print("\nWelcome to Farkle!")
    print("\nScoring Rules:")
    print("  Single 1: 100 points")
    print("  Single 5: 50 points")
    print("  Three of a kind: number × 100 (three 1s = 1000)")
    print("  Four/Five/Six of a kind: doubles each time")
    print("  Straight (1-6): 1500 points")
    print("  Three pairs: 1500 points")
    print("\nFirst player to 10,000 wins!")
    print()

    total_players, ai_players = _prompt_player_configuration()
    game = FarkleGame(num_players=total_players)
    game.state = GameState.IN_PROGRESS

    ai_indices = set(range(total_players - ai_players, total_players)) if ai_players else set()
    ai_strategies: Dict[int, HeuristicStrategy[Tuple[List[int], bool], FarkleGame]] = {idx: game.create_adaptive_ai() for idx in ai_indices}

    while not game.is_game_over():
        player = game.get_current_player()
        print(f"\n{'=' * 50}")
        print(f"Player {player + 1}'s turn")
        print(f"Scores: {_render_scoreboard(game.scores)}")
        print(f"Turn score: {game.turn_score}")
        print(f"Dice in hand: {game.dice_in_hand}")

        if player in ai_indices:
            if not game.last_roll:
                game.make_move(([], True))
                print(f"AI rolled: {game.last_roll}")
            _execute_ai_turn(game, ai_strategies[player])
            continue

        input("\nPress Enter to roll dice...")
        game.make_move(([], True))
        print(f"Roll: {game.last_roll}")

        if not game._has_scoring_dice(game.last_roll):
            print("\nFARKLE! No scoring dice. Turn over.")
            game.make_move(([], False))
            continue

        score = game._calculate_score(game.last_roll)
        print(f"Total roll score: {score}")

        while True:
            choice = input("\nBank and (C)ontinue, or bank and (E)nd turn? ").strip().upper()
            if choice in {"C", "E"}:
                break
            print("Please enter C or E.")

        continue_rolling = choice == "C"
        game.make_move((game.last_roll, continue_rolling))

    winner = game.get_winner()
    assert winner is not None
    print(f"\n{'=' * 50}")
    print(f"Player {winner + 1} wins with {game.scores[winner]} points!")
    print(f"Final scores: {_render_scoreboard(game.scores)}")


if __name__ == "__main__":
    main()
