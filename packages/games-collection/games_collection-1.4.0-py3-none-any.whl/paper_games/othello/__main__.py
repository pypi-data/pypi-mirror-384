"""Command line entry for the Othello game."""

from __future__ import annotations

from .othello import OthelloCLI


def main() -> None:
    """Launch the Othello CLI."""

    OthelloCLI().run()


if __name__ == "__main__":
    main()
