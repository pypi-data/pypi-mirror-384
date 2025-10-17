"""Bunco Game Package.

This package contains all modules related to the Bunco dice game, including the
game engine, command-line interface, and graphical user interface.

Modules:
    bunco: Core game logic and tournament simulation.
    cli: Command-line entry point for the game.
    gui: Tkinter-based graphical user interface.
"""

from .bunco import BuncoGame, BuncoMatchResult, BuncoPlayerSummary, BuncoTournament
from .gui import BuncoGUI

__all__ = [
    "BuncoGame",
    "BuncoTournament",
    "BuncoPlayerSummary",
    "BuncoMatchResult",
    "BuncoGUI",
]
