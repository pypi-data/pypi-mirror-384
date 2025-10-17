"""Liar's Dice Game Package.

This package contains all modules related to the Liar's Dice game, including
the game engine and command-line interface.

Modules:
    liars_dice: Core game logic and bluffing engine.
    cli: Command-line entry point for playing Liar's Dice.
"""

from .liars_dice import LiarsDiceGame

__all__ = ["LiarsDiceGame"]
