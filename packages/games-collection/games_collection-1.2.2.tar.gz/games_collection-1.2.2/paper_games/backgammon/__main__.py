"""Command line interface for Backgammon."""

from __future__ import annotations

from .backgammon import BackgammonCLI


def main() -> None:
    """Run the Backgammon command line interface."""
    BackgammonCLI().run()


if __name__ == "__main__":
    main()
