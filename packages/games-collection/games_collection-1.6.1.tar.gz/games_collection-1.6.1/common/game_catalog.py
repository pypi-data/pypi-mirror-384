"""Metadata catalogue describing the games shipped with the collection.

This lightweight catalogue is consumed by the recommendation system and other
cross-game surfaces (launcher, analytics) that need to reason about the games
without importing their heavy modules.  Each entry exposes high level
characteristics such as mechanics, typical play duration, and optional tagging
that help the recommendation engine justify suggestions to the player.
"""

from __future__ import annotations

from typing import Dict

from common.recommendation_service import GameDescriptor

_DEFAULT_GAME_CATALOGUE: Dict[str, GameDescriptor] = {
    "poker": GameDescriptor(
        game_id="poker",
        name="Poker",
        mechanics=("betting", "hand-evaluation", "bluffing"),
        tags=("card", "multiplayer"),
        average_duration=1800,
        difficulty=4,
    ),
    "blackjack": GameDescriptor(
        game_id="blackjack",
        name="Blackjack",
        mechanics=("betting", "hand-management"),
        tags=("card", "casino"),
        average_duration=900,
        difficulty=2,
    ),
    "uno": GameDescriptor(
        game_id="uno",
        name="Uno",
        mechanics=("shedding", "take-that"),
        tags=("card", "family"),
        average_duration=1200,
        difficulty=1,
    ),
    "go_fish": GameDescriptor(
        game_id="go_fish",
        name="Go Fish",
        mechanics=("set-collection", "memory"),
        tags=("card", "family"),
        average_duration=600,
        difficulty=1,
    ),
    "bridge": GameDescriptor(
        game_id="bridge",
        name="Bridge",
        mechanics=("trick-taking", "bidding"),
        tags=("card", "partnership"),
        average_duration=2400,
        difficulty=5,
    ),
    "tic_tac_toe": GameDescriptor(
        game_id="tic_tac_toe",
        name="Tic-Tac-Toe",
        mechanics=("abstract", "pattern-building"),
        tags=("paper", "classic"),
        average_duration=180,
        difficulty=1,
    ),
    "connect_four": GameDescriptor(
        game_id="connect_four",
        name="Connect Four",
        mechanics=("abstract", "pattern-building"),
        tags=("board", "family"),
        average_duration=480,
        difficulty=2,
    ),
    "sudoku": GameDescriptor(
        game_id="sudoku",
        name="Sudoku",
        mechanics=("logic", "deduction"),
        tags=("puzzle", "solo"),
        average_duration=900,
        difficulty=3,
    ),
    "hangman": GameDescriptor(
        game_id="hangman",
        name="Hangman",
        mechanics=("word", "guessing"),
        tags=("paper", "party"),
        average_duration=420,
        difficulty=1,
    ),
    "battleship": GameDescriptor(
        game_id="battleship",
        name="Battleship",
        mechanics=("deduction", "hidden-information"),
        tags=("board", "head-to-head"),
        average_duration=900,
        difficulty=2,
    ),
}


def get_default_game_catalogue() -> Dict[str, GameDescriptor]:
    """Return a copy of the curated game metadata catalogue."""

    return dict(_DEFAULT_GAME_CATALOGUE)


# Backwards compatibility helper for older documentation references.
get_default_game_catalog = get_default_game_catalogue
