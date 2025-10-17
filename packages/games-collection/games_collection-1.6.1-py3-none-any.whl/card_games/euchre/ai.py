"""Basic AI heuristics for Euchre CLI opponents.

This module provides a simple AI for making decisions in the game of Euchre,
including ordering up, choosing trump, and selecting cards to play.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from card_games.common.cards import Card, Suit

RANK_VALUE = {"9": 0, "T": 1, "J": 2, "Q": 3, "K": 4, "A": 5}


@dataclass
class TrickMemory:
    """Tracks cards played across tricks for simple card counting."""

    played_cards: list[Card] = field(default_factory=list)

    def record(self, card: Card) -> None:
        """Record a card that has been played."""
        self.played_cards.append(card)

    def reset(self) -> None:
        """Clear all remembered cards for a new hand."""
        self.played_cards.clear()


class BasicEuchreAI:
    """A lightweight Euchre AI with simple heuristics."""

    def __init__(self) -> None:
        """Initialize the AI and its memory."""
        self.memory = TrickMemory()

    def reset_for_new_hand(self) -> None:
        """Reset the AI's internal memory for a new hand."""
        self.memory.reset()

    def record_card(self, card: Card) -> None:
        """Record a played card in the AI's memory."""
        self.memory.record(card)

    def evaluate_hand_strength(self, hand: Iterable[Card], trump: Optional[Suit], up_card: Optional[Card] = None) -> float:
        """Heuristically score a hand to guide bidding decisions."""
        score = 0.0
        for card in hand:
            base = 1.0 + RANK_VALUE.get(card.rank, 0)
            if trump:
                if card.suit == trump:
                    base += 3.0
                if card.rank == "J":
                    if card.suit == trump:  # Right Bower
                        base += 6.0
                    elif card.suit == _same_color_suit(trump):  # Left Bower
                        base += 5.0
            score += base
        if up_card and trump and up_card.suit == trump:
            score += 2.5
        return score

    def should_order_up(self, hand: list[Card], up_card: Card, dealer: int, player: int) -> bool:
        """Decide whether to order the dealer to pick up the up-card."""
        strength = self.evaluate_hand_strength(hand, up_card.suit, up_card)
        return strength >= (16.0 if player == dealer else 14.0)

    def choose_trump(self, hand: list[Card], forbidden_suit: Suit) -> Optional[Suit]:
        """Choose a trump suit, avoiding the one that was turned down."""
        best_suit: Optional[Suit] = None
        best_score = 0.0
        for suit in Suit:
            if suit != forbidden_suit:
                score = self.evaluate_hand_strength(hand, suit)
                if score > best_score:
                    best_score = score
                    best_suit = suit
        return best_suit if best_score >= 13.0 else None

    def choose_discard(self, hand: list[Card], pickup_card: Card, trump: Suit) -> Card:
        """Select a card to discard after the dealer picks up the up-card."""
        full_hand = hand + [pickup_card]
        return min(full_hand, key=lambda c: self._card_priority(c, trump))

    def choose_card(self, hand: list[Card], lead_card: Optional[Card], trump: Suit) -> Card:
        """Select a card to play, prioritizing high-value cards."""
        if not lead_card:
            return max(hand, key=lambda c: self._lead_priority(c, trump))

        lead_suit = effective_suit(lead_card, trump)
        legal_cards = [c for c in hand if effective_suit(c, trump) == lead_suit] or hand
        return max(legal_cards, key=lambda c: self._lead_priority(c, trump))

    def _card_priority(self, card: Card, trump: Suit) -> float:
        """Return a discard priority (lower is worse), respecting bowers."""
        if card.rank == "J":
            if card.suit == trump:
                return 100.0
            if card.suit == _same_color_suit(trump):
                return 99.0
        return float(RANK_VALUE.get(card.rank, 0) + (50 if card.suit == trump else 0))

    def _lead_priority(self, card: Card, trump: Suit) -> float:
        """Return a priority score for leading or following in a trick."""
        eff_suit = effective_suit(card, trump)
        base = RANK_VALUE.get(card.rank, 0)
        if card.rank == "J":
            if card.suit == trump:
                return 200.0
            if card.suit == _same_color_suit(trump):
                return 199.0
        if eff_suit == trump:
            return 150.0 + base
        return 80.0 + base if eff_suit == card.suit else base


def effective_suit(card: Card, trump: Suit) -> Suit:
    """Return the effective suit of a card, accounting for bowers."""
    if card.rank == "J":
        if card.suit == trump or card.suit == _same_color_suit(trump):
            return trump
    return card.suit


def _same_color_suit(suit: Optional[Suit]) -> Optional[Suit]:
    """Return the other suit of the same color."""
    return {Suit.CLUBS: Suit.SPADES, Suit.SPADES: Suit.CLUBS, Suit.HEARTS: Suit.DIAMONDS, Suit.DIAMONDS: Suit.HEARTS}.get(suit)
