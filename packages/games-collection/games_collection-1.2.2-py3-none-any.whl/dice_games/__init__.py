"""A collection of interactive dice-based game implementations.

This package provides a suite of classic dice games, each with its own engine,
bot AI, and user interface. The games include:
- Craps - Casino dice game with pass/don't pass betting
- Farkle - Risk-based scoring with push-your-luck mechanics
- Liar's Dice - Bluffing game with dice bidding mechanics
- Bunco - Party dice game with rounds and team scoring

Each game can be run as a standalone application from the command line.
"""

from __future__ import annotations

# Export the subpackages so ``import dice_games`` presents the available games
# in a discoverable list.
__all__ = [
    "FarkleGame",
    "CrapsGame",
    "LiarsDiceGame",
    "BuncoGame",
]

from .bunco import BuncoGame
from .craps import CrapsGame
from .farkle import FarkleGame
from .liars_dice import LiarsDiceGame
