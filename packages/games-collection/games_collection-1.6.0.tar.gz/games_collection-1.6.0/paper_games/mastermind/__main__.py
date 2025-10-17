"""Command line interface for Mastermind."""

from __future__ import annotations

from .mastermind import MastermindCLI


def main() -> None:
    """Run the Mastermind command line interface."""
    MastermindCLI().run()


if __name__ == "__main__":
    main()
