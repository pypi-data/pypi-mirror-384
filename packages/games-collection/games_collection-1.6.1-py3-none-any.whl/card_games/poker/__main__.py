"""Main entry point for running the Poker card game.

This script serves as the executable entry point for the Poker game, allowing
it to be run directly using the ``-m`` flag with Python. For example:

    python -m card_games.poker --difficulty Hard

It simply imports and calls the ``main`` function from the ``poker`` module.
"""

# Importing inside the module keeps the command-line entry point lightweight
# while still reusing the richer CLI defined in ``poker.main``.
from .poker import main

if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
