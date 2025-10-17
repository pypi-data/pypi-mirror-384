"""Command line entry point for the Checkers game."""

from __future__ import annotations

from .checkers import CheckersCLI


def main() -> None:
    """Launch the Checkers CLI."""

    CheckersCLI().run()


if __name__ == "__main__":
    main()
