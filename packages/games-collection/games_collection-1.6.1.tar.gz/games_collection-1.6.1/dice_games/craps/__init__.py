"""Craps Game Package.

This package contains all modules related to the Craps dice game, including the
game engine and command-line interface.

Modules:
    craps: Core game logic and betting engine.
    cli: Command-line entry point for playing Craps.
"""

from .craps import CrapsGame

__all__ = ["CrapsGame"]
