"""CLI for Bunco."""

from __future__ import annotations

from .bunco import BuncoGame


def main() -> None:
    """Run Bunco."""
    print("BUNCO".center(50, "="))
    game = BuncoGame(num_players=2)
    game.state = game.state.IN_PROGRESS

    while not game.is_game_over():
        player = game.get_current_player()
        print(f"\nRound {game.round_num} - Player {player + 1}")
        print(f"Scores: {game.scores}")
        input("Press Enter to roll...")
        game.make_move("roll")

    winner = game.get_winner()
    print(f"\nPlayer {winner + 1} wins with {game.scores[winner]} points!")


if __name__ == "__main__":
    main()
