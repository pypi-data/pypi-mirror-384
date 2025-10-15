"""Command line entry point for Mancala."""

from __future__ import annotations

from .mancala import MancalaCLI


def main() -> None:
    """Launch the Mancala command line interface."""

    MancalaCLI().run()


if __name__ == "__main__":
    main()
