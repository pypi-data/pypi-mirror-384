"""General representations of playing cards shared across games.

This module provides fundamental data structures for representing playing cards,
suits, and decks. These components are designed to be reusable across various
card games. The module includes:

- ``Suit``: An ``Enum`` for the four card suits (Clubs, Diamonds, Hearts, Spades).
- ``RANKS``: A tuple defining the order of card ranks from '2' to 'A'.
- ``RANK_TO_VALUE``: A dictionary mapping each rank to a numerical value.
- ``Card``: A dataclass representing a single playing card with a rank and suit.
- ``Deck``: A class for a deck of cards, with methods for shuffling and dealing.
- ``parse_card``: A function to create a ``Card`` from a two-character string (e.g., "KH" for King of Hearts).
- ``format_cards``: A utility function to format a collection of cards into a readable string.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Iterator, Tuple


class Suit(str, Enum):
    """Enumeration of the four suits in a standard 52-card deck.

    Each suit is represented by a string corresponding to its symbol.
    - CLUBS: "♣"
    - DIAMONDS: "♦"
    - HEARTS: "♥"
    - SPADES: "♠"
    """

    CLUBS = "♣"
    DIAMONDS = "♦"
    HEARTS = "♥"
    SPADES = "♠"


# RANKS defines the order of card ranks from lowest to highest.
# 'T' is used for Ten.
RANKS: Tuple[str, ...] = (
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "T",  # Ten
    "J",  # Jack
    "Q",  # Queen
    "K",  # King
    "A",  # Ace
)

# RANK_TO_VALUE provides a mapping from a card's rank to its integer value,
# which is useful for comparing cards.
RANK_TO_VALUE = {rank: index for index, rank in enumerate(RANKS)}


@dataclass(frozen=True)
class Card:
    """Representation of a single playing card, identified by its rank and suit.

    This is a frozen dataclass, meaning ``Card`` objects are immutable. Once a
    card is created, its rank and suit cannot be changed.

    Attributes:
        rank (str): The card's rank (e.g., 'A', 'K', 'T', '2').
        suit (Suit): The card's suit (e.g., ``Suit.SPADES``).
    """

    rank: str
    suit: Suit

    def __post_init__(self) -> None:
        """Validate the card's rank after initialization."""
        if self.rank not in RANK_TO_VALUE:
            raise ValueError(f"Unsupported rank: {self.rank!r}")

    @property
    def value(self) -> int:
        """Integer value of the card used for comparisons.

        The value is determined by the card's rank, based on the ``RANK_TO_VALUE``
        mapping. This is useful for sorting and comparing cards.

        Returns:
            int: The integer value of the card's rank.
        """
        return RANK_TO_VALUE[self.rank]

    def __str__(self) -> str:  # pragma: no cover - trivial
        """Return a string representation of the card (e.g., "K♠")."""
        return f"{self.rank}{self.suit.value}"


@dataclass
class Deck:
    """A mutable deck of playing cards.

    A ``Deck`` is initialized with a standard 52-card set unless an existing
    list of cards is provided. It supports shuffling and dealing operations.

    Attributes:
        cards (list[Card]): The list of cards currently in the deck.
    """

    cards: list[Card] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize the deck with a standard 52-card set if it's empty."""
        if not self.cards:
            self.cards = [Card(rank, suit) for suit in Suit for rank in RANKS]

    def shuffle(self, *, rng=None) -> None:
        """Shuffle the deck in place.

        This method uses the Fisher-Yates shuffle algorithm provided by
        ``random.shuffle``. An optional random number generator can be
        provided for deterministic shuffling.

        Args:
            rng: An optional random number generator instance with a ``shuffle``
                 method. If ``None``, the default ``random`` module is used.
        """
        if rng is None:
            import random

            rng = random

        # ``random.shuffle`` implements Fisher-Yates, giving an unbiased shuffle.
        rng.shuffle(self.cards)

    def deal(self, count: int = 1) -> list[Card]:
        """Remove and return ``count`` cards from the top of the deck.

        Args:
            count (int): The number of cards to deal. Defaults to 1.

        Returns:
            list[Card]: A list of the dealt cards.

        Raises:
            ValueError: If ``count`` is negative or exceeds the number of
                        cards remaining in the deck.
        """
        if count < 0:
            raise ValueError("count must be positive")
        if count > len(self.cards):
            raise ValueError("Not enough cards remaining in the deck")

        # Slicing for performance and atomicity
        dealt, self.cards = self.cards[:count], self.cards[count:]
        return dealt

    def __iter__(self) -> Iterator[Card]:  # pragma: no cover - trivial
        """Return an iterator over the cards in the deck."""
        yield from self.cards


def parse_card(code: str) -> Card:
    """Parse a two-character card code (e.g., "AS" for Ace of Spades) into a Card object.

    The first character represents the rank, and the second represents the suit.
    Rank codes: 'A', 'K', 'Q', 'J', 'T' (or '1' for 10), '2'-'9'.
    Suit codes: 'S' (Spades), 'H' (Hearts), 'D' (Diamonds), 'C' (Clubs).
    The input is case-insensitive.

    Args:
        code (str): The two-character string representing the card.

    Returns:
        Card: The corresponding ``Card`` object.

    Raises:
        ValueError: If the card code is invalid (e.g., wrong length, unknown
                    rank or suit).
    """
    if len(code) != 2:
        raise ValueError(f"Invalid card code: {code!r}")

    rank_code, suit_code = code[0].upper(), code[1].upper()

    # Map suit characters to Suit enum members
    suit_map = {"S": Suit.SPADES, "H": Suit.HEARTS, "D": Suit.DIAMONDS, "C": Suit.CLUBS}
    if suit_code not in suit_map:
        raise ValueError(f"Unknown suit code: {suit_code!r}")

    # Map rank characters to standard rank strings
    if rank_code == "A":
        rank = "A"
    elif rank_code == "K":
        rank = "K"
    elif rank_code == "Q":
        rank = "Q"
    elif rank_code == "J":
        rank = "J"
    elif rank_code in {"T", "1"}:  # 'T' or '1' for Ten
        rank = "T"
    elif rank_code in {"2", "3", "4", "5", "6", "7", "8", "9"}:
        rank = rank_code
    else:
        raise ValueError(f"Unknown rank code: {rank_code!r}")

    return Card(rank, suit_map[suit_code])


def format_cards(cards: Iterable[Card]) -> str:
    """Return a nicely formatted string representation of multiple cards.

    This function takes an iterable of ``Card`` objects and joins them into a
    single space-separated string.

    Args:
        cards (Iterable[Card]): An iterable of ``Card`` objects.

    Returns:
        str: A space-separated string of card representations (e.g., "K♠ Q♥").
    """
    return " ".join(str(card) for card in cards)


__all__ = [
    "Card",
    "Deck",
    "Suit",
    "RANKS",
    "RANK_TO_VALUE",
    "format_cards",
    "parse_card",
]
