"""Main entry point for running the Canasta game application.

This script allows the Canasta game to be run directly from the command line
using Python's ``-m`` flag.

Usage:
    $ python -m card_games.canasta
"""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":  # pragma: no cover - manual entry point
    main()
