"""Farkle Game Package.

This package contains all modules related to the Farkle dice game, including the
game engine and command-line interface.

Modules:
    farkle: Core game logic and scoring engine.
    cli: Command-line entry point for playing Farkle.
"""

from .farkle import FarkleGame

__all__ = ["FarkleGame"]
