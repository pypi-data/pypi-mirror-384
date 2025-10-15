"""A collection of interactive, text-based and GUI-based card game implementations.

This package provides a suite of classic card games, each with its own engine,
bot AI, and user interface. The games included are:
- Blackjack
- Bluff (also known as Cheat or I Doubt It)
- Poker (Texas Hold'em)
- Uno

Each game can be run as a standalone application from the command line.
"""

# Export the subpackages so ``import card_games`` presents the available games
# in a discoverable list.
__all__ = ["poker", "bluff", "uno", "blackjack"]
