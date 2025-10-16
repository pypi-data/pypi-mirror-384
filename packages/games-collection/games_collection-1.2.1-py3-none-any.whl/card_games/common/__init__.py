"""Shared building blocks for card-based games."""

# Provide convenient access to the core card primitives for consumers of the
# ``card_games.common`` package.
from .cards import Card, Deck, Suit, format_cards, parse_card

__all__ = ["Card", "Deck", "Suit", "format_cards", "parse_card"]
