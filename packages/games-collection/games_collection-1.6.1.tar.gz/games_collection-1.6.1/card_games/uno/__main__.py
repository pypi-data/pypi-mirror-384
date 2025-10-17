"""Main entry point for running the Uno card game.

This script serves as the executable entry point for the Uno game, allowing it
to be run directly using the ``-m`` flag with Python. For example:

    python -m card_games.uno --players 4 --bots 3

It simply imports and calls the ``main`` function from the ``uno`` module.
"""

# Keep imports minimal so ``python -m card_games.uno`` starts quickly while
# delegating all heavy lifting to :func:`card_games.uno.main`.
from .uno import main

if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
