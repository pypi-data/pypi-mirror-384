"""Core poker domain models and hand evaluation utilities.

This module provides a modern, well-tested, and friendly API for working with
standard playing cards in the context of poker. It exposes a lightweight object
model for hand rankings that can be reused by various front-ends, such as a
command-line interface or a graphical user interface. The implementation is
designed to be stateless, making it easy to test and integrate.

The main entry point is the :func:`best_hand` function, which takes an iterable
of cards and returns the strongest five-card hand that can be formed. The result
is a :class:`HandRank` instance, which can be compared using standard ordering
operators to determine the winning hand.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from itertools import combinations
from typing import Iterable, Sequence, Tuple

from ..common.cards import Card


class HandCategory(int, Enum):
    """Enumeration of poker hand categories, ordered from weakest to strongest.

    Each member represents a distinct type of poker hand, with an integer value
    that allows for direct comparison of hand strengths.
    """

    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8


@dataclass(order=True, frozen=True)
class HandRank:
    """A value object that encapsulates the strength of a five-card poker hand.

    This class provides a comprehensive representation of a hand's rank, including
    its category (e.g., Full House), a tie-breaker value, and the cards that
    form the hand. The `order=True` argument automatically generates comparison
    methods (__lt__, __le__, __gt__, __ge__), allowing instances to be sorted.

    Attributes:
        category (HandCategory): The category of the hand.
        tiebreaker (Tuple[int, ...]): A tuple of card values for tie-breaking.
        cards (Tuple[Card, ...]): The five cards that constitute the ranked hand.
    """

    category: HandCategory
    tiebreaker: Tuple[int, ...]
    cards: Tuple[Card, ...] = field(compare=False)

    def describe(self) -> str:
        """Return a human-friendly description of the ranked hand."""
        category_name = self.category.name.replace("_", " ").title()
        cards_str = " ".join(map(str, self.cards))
        return f"{category_name} ({cards_str})"


def best_hand(cards: Iterable[Card]) -> HandRank:
    """Return the best possible five-card hand from the provided cards.

    This function is essential for games like Texas Hold'em, where players choose
    the best five cards from a larger set (e.g., two hole cards and five community
    cards). It iterates through all 5-card combinations and returns the one with
    the highest rank.

    Args:
        cards: An iterable of cards (typically 5 to 7).

    Returns:
        The `HandRank` of the best five-card hand.
    """
    card_list = list(cards)
    if len(card_list) < 5:
        raise ValueError("At least five cards are required to evaluate a hand")

    # Generate all 5-card combinations and find the one with the maximum rank.
    return max(rank_five_card_hand(combo) for combo in combinations(card_list, 5))


def rank_five_card_hand(cards: Sequence[Card]) -> HandRank:
    """Evaluate a five-card poker hand and return its :class:`HandRank`.

    This function determines the rank of a given 5-card hand by checking for
    straights, flushes, pairs, etc., and constructs a `HandRank` object with the
    appropriate category and tie-breaker values.

    Args:
        cards: A sequence of exactly five cards.

    Returns:
        The rank of the five-card hand.
    """
    if len(cards) != 5:
        raise ValueError("Exactly five cards must be supplied")

    # Sort once so subsequent evaluations can assume descending value order.
    sorted_cards = tuple(sorted(cards, key=lambda card: card.value, reverse=True))
    values = tuple(card.value for card in sorted_cards)
    is_flush = len({card.suit for card in cards}) == 1

    unique_values = sorted(set(values), reverse=True)
    straight_values = _straight_values(values)
    is_straight = straight_values is not None

    # Count the occurrences of each card rank.
    counts = {value: values.count(value) for value in unique_values}
    sorted_counts = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)

    # --- Hand Rank Evaluation Logic ---
    if is_straight and is_flush:
        return HandRank(HandCategory.STRAIGHT_FLUSH, (straight_values,), sorted_cards)

    if sorted_counts[0][1] == 4:  # Four of a Kind
        kicker = max(v for v in values if v != sorted_counts[0][0])
        return HandRank(HandCategory.FOUR_OF_A_KIND, (sorted_counts[0][0], kicker), sorted_cards)

    if sorted_counts[0][1] == 3 and sorted_counts[1][1] == 2:  # Full House
        return HandRank(
            HandCategory.FULL_HOUSE,
            (sorted_counts[0][0], sorted_counts[1][0]),
            sorted_cards,
        )

    if is_flush:
        return HandRank(HandCategory.FLUSH, values, sorted_cards)

    if is_straight:
        return HandRank(HandCategory.STRAIGHT, (straight_values,), sorted_cards)

    if sorted_counts[0][1] == 3:  # Three of a Kind
        kickers = tuple(v for v in values if v != sorted_counts[0][0])
        return HandRank(HandCategory.THREE_OF_A_KIND, (sorted_counts[0][0],) + kickers, sorted_cards)

    if sorted_counts[0][1] == 2 and sorted_counts[1][1] == 2:  # Two Pair
        pair_values = (sorted_counts[0][0], sorted_counts[1][0])
        kicker = max(v for v in values if v not in pair_values)
        return HandRank(HandCategory.TWO_PAIR, pair_values + (kicker,), sorted_cards)

    if sorted_counts[0][1] == 2:  # One Pair
        pair_value = sorted_counts[0][0]
        kickers = tuple(v for v in values if v != pair_value)
        return HandRank(HandCategory.ONE_PAIR, (pair_value,) + kickers, sorted_cards)

    # If no other hand is made, it's a High Card hand.
    return HandRank(HandCategory.HIGH_CARD, values, sorted_cards)


def _straight_values(values: Tuple[int, ...]) -> int | None:
    """Return the highest card's value in a straight, or None if it's not a straight.

    This helper function checks for both standard straights and the "wheel"
    (A-2-3-4-5) straight.

    Args:
        values: A tuple of card values, sorted in descending order.

    Returns:
        The value of the highest card in the straight, or None. For a wheel,
        it returns 3 (the value of the 5), as the Ace is low.
    """
    unique_values = sorted(set(values), reverse=True)
    if len(unique_values) < 5:
        # A straight must have 5 unique card ranks.
        return None

    # Handle the "wheel" straight: A-2-3-4-5.
    if unique_values == [12, 3, 2, 1, 0]:  # A, 5, 4, 3, 2
        return 3  # The 5 is the high card in an A-5 straight.

    high, *rest = unique_values
    # Check if the ranks form a contiguous sequence.
    is_straight = all(high - i == val for i, val in enumerate(unique_values))

    return high if is_straight else None
