"""Command line interface for Snakes and Ladders."""

from __future__ import annotations

from .snakes_and_ladders import SnakesAndLaddersCLI


def main() -> None:
    """Run the Snakes and Ladders command line interface."""
    SnakesAndLaddersCLI().run()


if __name__ == "__main__":
    main()
