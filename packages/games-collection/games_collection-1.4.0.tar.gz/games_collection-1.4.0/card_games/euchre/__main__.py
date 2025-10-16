"""Entry point for Euchre card game."""

from __future__ import annotations

import argparse
from random import Random

from card_games.euchre.cli import game_loop
from card_games.euchre.game import EuchreGame


def main() -> None:
    """Main entry point for Euchre."""
    parser = argparse.ArgumentParser(description="Play Euchre")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible games")
    args = parser.parse_args()

    rng = Random(args.seed) if args.seed is not None else None
    game = EuchreGame(rng=rng)
    game_loop(game)


if __name__ == "__main__":
    main()
