"""Command line interface for Pentago."""

from __future__ import annotations

from .pentago import PentagoCLI


def main() -> None:
    """Run the Pentago command line interface."""
    PentagoCLI().run()


if __name__ == "__main__":
    main()
