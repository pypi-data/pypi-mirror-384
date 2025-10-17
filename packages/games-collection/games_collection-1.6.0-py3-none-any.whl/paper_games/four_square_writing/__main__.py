"""Command line interface for Four Square Writing."""

from __future__ import annotations

from .four_square_writing import FourSquareWritingCLI


def main() -> None:
    """Run the Four Square Writing command line interface."""
    FourSquareWritingCLI().run()


if __name__ == "__main__":
    main()
