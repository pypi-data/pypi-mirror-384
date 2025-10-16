"""Command-line interface for Farkle game."""

from __future__ import annotations

from .farkle import FarkleGame


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

    # Get number of players
    while True:
        try:
            num_players = int(input("Enter number of players (2-6): "))
            if 2 <= num_players <= 6:
                break
            print("Please enter a number between 2 and 6.")
        except ValueError:
            print("Please enter a valid number.")

    game = FarkleGame(num_players=num_players)
    game.state = game.state.IN_PROGRESS

    # Game loop
    while not game.is_game_over():
        player = game.get_current_player()
        print(f"\n{'=' * 50}")
        print(f"Player {player + 1}'s turn")
        print(f"Current scores: {', '.join(f'P{i+1}: {s}' for i, s in enumerate(game.scores))}")
        print(f"Turn score: {game.turn_score}")
        print(f"Dice in hand: {game.dice_in_hand}")

        # Roll dice
        input("\nPress Enter to roll dice...")
        game.make_move(([], True))  # Roll

        print(f"Roll: {game.last_roll}")

        # Check if farkled
        if not game._has_scoring_dice(game.last_roll):
            print("\nFARKLE! No scoring dice. Turn over.")
            game.make_move(([], False))
            continue

        # Show scoring options
        score = game._calculate_score(game.last_roll)
        print(f"Total roll score: {score}")

        # Player decision
        while True:
            choice = input("\nBank and (C)ontinue, or bank and (E)nd turn? ").strip().upper()
            if choice in ["C", "E"]:
                break
            print("Please enter C or E.")

        # Bank all scoring dice
        continue_rolling = choice == "C"
        game.make_move((game.last_roll, continue_rolling))

    # Game over
    winner = game.get_winner()
    print(f"\n{'=' * 50}")
    print(f"Player {winner + 1} wins with {game.scores[winner]} points!")
    print(f"Final scores: {', '.join(f'P{i+1}: {s}' for i, s in enumerate(game.scores))}")


if __name__ == "__main__":
    main()
