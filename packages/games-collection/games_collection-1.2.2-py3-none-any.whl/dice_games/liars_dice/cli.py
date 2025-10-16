"""CLI for Liar's Dice."""

from __future__ import annotations

from .liars_dice import LiarsDiceGame


def main() -> None:
    """Run Liar's Dice."""
    print("LIAR'S DICE".center(50, "="))
    game = LiarsDiceGame(num_players=2)
    game.state = game.state.IN_PROGRESS

    while not game.is_game_over():
        player = game.get_current_player()
        print(f"\nPlayer {player + 1}'s turn")
        print(f"Your dice: {sorted(game.player_dice[player])}")

        if game.current_bid:
            print(f"Current bid: {game.current_bid[0]}x {game.current_bid[1]}'s")
            choice = input("(B)id higher or (C)hallenge? ").upper()
            if choice == "C":
                game.make_move((-1, -1))
                continue

        q = int(input("Bid quantity: "))
        f = int(input("Bid face value (1-6): "))
        game.make_move((q, f))

    winner = game.get_winner()
    print(f"\nPlayer {winner + 1} wins!")


if __name__ == "__main__":
    main()
