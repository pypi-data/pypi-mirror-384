"""Command-line interface for Craps."""

from __future__ import annotations

from .craps import CrapsGame


def main() -> None:
    """Run Craps game."""
    print("CRAPS".center(50, "="))
    print("\nCasino dice game. Bet on dice rolls!")

    game = CrapsGame()
    game.state = game.state.IN_PROGRESS

    print("\nStarting bankroll: $1000")
    print("Commands: roll, bet_pass, bet_dont_pass, quit")

    while not game.is_game_over():
        print(f"\nBankroll: ${game.bankroll}")
        if game.point:
            print(f"Point: {game.point}")
        else:
            print("Come-out roll")

        cmd = input("Command: ").strip().lower()
        if cmd == "quit":
            break

        if game.make_move(cmd):
            print("Move executed")
        else:
            print("Invalid move")

    print("\nGame over!")


if __name__ == "__main__":
    main()
