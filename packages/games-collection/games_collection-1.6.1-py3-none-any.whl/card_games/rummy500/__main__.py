"""Entry point for Rummy 500."""

from __future__ import annotations

import argparse
from random import Random

from card_games.rummy500.cli import game_loop
from card_games.rummy500.game import Rummy500Game


def main() -> None:
    """Main entry point for Rummy 500."""
    parser = argparse.ArgumentParser(description="Play Rummy 500")
    parser.add_argument("--players", type=int, default=2, help="Number of players (2-4)")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible games")
    args = parser.parse_args()

    rng = Random(args.seed) if args.seed is not None else None
    game = Rummy500Game(num_players=args.players, rng=rng)
    game_loop(game)


if __name__ == "__main__":
    main()
