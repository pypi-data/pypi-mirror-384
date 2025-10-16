"""Command line interface for Sprouts."""

from __future__ import annotations

from .sprouts import SproutsCLI


def main() -> None:
    """Run the Sprouts command line interface."""
    SproutsCLI().run()


if __name__ == "__main__":
    main()
