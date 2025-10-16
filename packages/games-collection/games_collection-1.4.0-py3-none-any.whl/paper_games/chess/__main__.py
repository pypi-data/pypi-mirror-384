"""Command line interface for Chess."""

from __future__ import annotations

from .chess import ChessCLI


def main() -> None:
    """Run the Chess command line interface."""
    ChessCLI().run()


if __name__ == "__main__":
    main()
