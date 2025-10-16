"""Utility for evaluating and describing poker hands from concise card codes.

This module provides a convenient command-line tool for quickly evaluating poker
hands. It uses a two-character code for each card (e.g., "AS" for Ace of Spades)
and prints a human-friendly description of the hand's rank.

Example Usage:
    python -m card_games.poker.poker_hand_evaluator AS KD QH JC TC
    # Output: Straight (A♠ K♦ Q♥ J♣ T♣)
"""

from __future__ import annotations

import sys
from typing import Iterable, Sequence

from ..common.cards import format_cards, parse_card
from .poker_core import HandRank, best_hand


def evaluate_hand(card_codes: Sequence[str]) -> HandRank:
    """Return a `HandRank` for the provided card codes.

    Args:
        card_codes: A sequence of two-character strings representing cards,
                    e.g., "AS" for Ace of Spades or "TD" for Ten of Diamonds.

    Returns:
        The `HandRank` of the best possible 5-card hand.
    """
    # Translate the compact CLI codes into ``Card`` objects before evaluation.
    cards = [parse_card(code) for code in card_codes]
    return best_hand(cards)


def describe_hand(card_codes: Sequence[str]) -> str:
    """Return a human-friendly description of the hand from card codes.

    Args:
        card_codes: A sequence of two-character card codes.

    Returns:
        A string describing the hand's rank and the cards it was formed from.
    """
    rank = evaluate_hand(card_codes)
    cards = [parse_card(code) for code in card_codes]
    return f"{rank.describe()} from {format_cards(cards)}"


def main(card_codes: Iterable[str]) -> None:  # pragma: no cover - convenience
    """Main function for the CLI tool. Evaluates and prints the hand rank.

    Args:
        card_codes: An iterable of card code strings from the command line.
    """
    try:
        rank = evaluate_hand(list(card_codes))
        print(rank.describe())
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - script entry point
    if len(sys.argv) <= 1:
        print(
            "Usage: python -m card_games.poker.poker_hand_evaluator <card> [<card> ...]",
            file=sys.stderr,
        )
        print(
            "Example: python -m card_games.poker.poker_hand_evaluator AS KD QH JC TC",
            file=sys.stderr,
        )
        sys.exit(1)

    main(sys.argv[1:])
