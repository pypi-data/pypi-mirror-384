"""Canasta card game implementation with shared CLI and GUI front ends.

This package provides the core engine and components for playing Canasta.
The main classes are re-exported here for easy access.

Core Components:
- ``CanastaGame``: The main game engine.
- ``CanastaPlayer``: Represents a player in the game.
- ``CanastaTeam``: Represents a team of two players.
- ``CanastaDeck``: The specific deck used for Canasta.
- ``Meld``: Represents a meld of cards.
- ``JokerCard``: A special card type for jokers.
"""

from __future__ import annotations

from .game import (
    CanastaDeck,
    CanastaGame,
    CanastaPlayer,
    CanastaTeam,
    JokerCard,
    Meld,
    MeldValidation,
)

__all__ = [
    "CanastaDeck",
    "CanastaGame",
    "CanastaPlayer",
    "CanastaTeam",
    "JokerCard",
    "Meld",
    "MeldValidation",
]
