"""Command line interface for Boggle."""

from __future__ import annotations

from .boggle import BoggleCLI


def main() -> None:
    """Run the Boggle command line interface."""
    BoggleCLI().run()


if __name__ == "__main__":
    main()
