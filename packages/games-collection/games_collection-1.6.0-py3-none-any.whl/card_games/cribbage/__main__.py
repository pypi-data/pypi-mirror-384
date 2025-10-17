"""Entry point for Cribbage card game."""

from __future__ import annotations

import argparse

from card_games.cribbage.cli import game_loop
from card_games.cribbage.game import CribbageGame


def main() -> None:
    """Main entry point for the Cribbage game."""
    parser = argparse.ArgumentParser(description="Play Cribbage")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible games")
    args = parser.parse_args()

    from random import Random

    rng = Random(args.seed) if args.seed is not None else None
    game = CribbageGame(rng=rng)
    game_loop(game)


if __name__ == "__main__":
    main()
