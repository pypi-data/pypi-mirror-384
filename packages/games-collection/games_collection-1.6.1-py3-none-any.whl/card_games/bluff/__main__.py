"""Main entry point for running the Bluff card game application.

This script serves as the executable entry point for the Bluff game, allowing it
to be run directly from the command line using Python's ``-m`` flag.

Usage:
    $ python -m card_games.bluff --difficulty Hard

This script simply imports and calls the ``main`` function from the ``bluff``
module, which handles command-line argument parsing and game launch.
"""

# Reuse the CLI orchestration defined in the ``bluff`` module to make this
# package executable.
from .bluff import main

if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
