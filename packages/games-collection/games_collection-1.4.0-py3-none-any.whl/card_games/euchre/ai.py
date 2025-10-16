"""Basic AI heuristics for the Euchre CLI opponents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from card_games.common.cards import Card, Suit

RANK_VALUE = {"9": 0, "T": 1, "J": 2, "Q": 3, "K": 4, "A": 5}


@dataclass
class TrickMemory:
    """Track cards played across tricks for simple counting strategies."""

    played_cards: list[Card] = field(default_factory=list)

    def record(self, card: Card) -> None:
        """Record a card that has been played.

        Args:
            card: Card to record.

        Returns:
            None.

        Raises:
            None.
        """

        self.played_cards.append(card)

    def reset(self) -> None:
        """Clear remembered cards between hands.

        Returns:
            None.

        Raises:
            None.
        """

        self.played_cards.clear()


class BasicEuchreAI:
    """Very lightweight Euchre heuristics for the CLI opponents."""

    def __init__(self) -> None:
        self.memory = TrickMemory()

    def reset_for_new_hand(self) -> None:
        """Reset the internal trick memory for a new hand.

        Returns:
            None.

        Raises:
            None.
        """

        self.memory.reset()

    def record_card(self, card: Card) -> None:
        """Remember a card that has been played.

        Args:
            card: Card to record in memory.

        Returns:
            None.

        Raises:
            None.
        """

        self.memory.record(card)

    def evaluate_hand_strength(self, hand: Iterable[Card], trump: Optional[Suit], up_card: Optional[Card] = None) -> float:
        """Heuristically score a hand for ordering decisions.

        Args:
            hand: Cards to evaluate.
            trump: Candidate trump suit being considered.
            up_card: Optional turned card available for pickup.

        Returns:
            float: Strength estimate used for bidding heuristics.

        Raises:
            None.
        """

        score = 0.0
        for card in hand:
            base = 1.0 + RANK_VALUE.get(card.rank, 0)
            if trump and card.suit == trump:
                base += 3.0
            if trump and card.rank == "J" and card.suit == trump:
                base += 6.0
            same_color = _same_color_suit(trump) if trump else None
            if trump and card.rank == "J" and same_color and card.suit == same_color:
                base += 5.0
            score += base
        if up_card and trump and up_card.suit == trump:
            score += 2.5
        return score

    def should_order_up(self, hand: list[Card], up_card: Card, dealer: int, player: int) -> bool:
        """Decide whether to order up the turned card in the first round.

        Args:
            hand: Cards held by the player.
            up_card: The turned card being considered.
            dealer: Seat index of the dealer.
            player: Seat index of the evaluating player.

        Returns:
            bool: ``True`` when the AI elects to order up the card.

        Raises:
            None.
        """

        trump = up_card.suit
        strength = self.evaluate_hand_strength(hand, trump, up_card)
        threshold = 16.0 if player == dealer else 14.0
        return strength >= threshold

    def choose_trump(self, hand: list[Card], forbidden_suit: Suit) -> Optional[Suit]:
        """Choose a trump suit in the naming round, avoiding the forbidden suit.

        Args:
            hand: Cards held by the player.
            forbidden_suit: Suit that cannot be named (the turned suit).

        Returns:
            Optional[Suit]: Selected trump suit or ``None`` to pass.

        Raises:
            None.
        """

        best_suit: Optional[Suit] = None
        best_score = 0.0
        for suit in Suit:
            if suit == forbidden_suit:
                continue
            score = self.evaluate_hand_strength(hand, suit)
            if score > best_score:
                best_score = score
                best_suit = suit
        return best_suit if best_score >= 13.0 else None

    def choose_discard(self, hand: list[Card], pickup_card: Card, trump: Suit) -> Card:
        """Select a discard after the dealer picks up the turned card.

        Args:
            hand: Current cards held by the dealer.
            pickup_card: The turned card being added.
            trump: The elected trump suit.

        Returns:
            Card: The card that should be discarded.

        Raises:
            None.
        """

        augmented_hand = hand + [pickup_card]
        augmented_hand.sort(key=lambda c: self._card_priority(c, trump))
        return augmented_hand[0]

    def choose_card(self, hand: list[Card], lead_card: Optional[Card], trump: Suit) -> Card:
        """Select a card to play, prioritising bowers and trump appropriately.

        Args:
            hand: Cards currently held by the AI player.
            lead_card: Card that opened the trick, if any.
            trump: Trump suit for the hand.

        Returns:
            Card: The chosen card to play.

        Raises:
            None.
        """

        if lead_card is None:
            sorted_hand = sorted(hand, key=lambda c: self._lead_priority(c, trump), reverse=True)
            return sorted_hand[0]

        lead_suit = effective_suit(lead_card, trump)
        legal_cards = [card for card in hand if effective_suit(card, trump) == lead_suit]
        if not legal_cards:
            legal_cards = hand
        legal_cards.sort(key=lambda c: self._lead_priority(c, trump), reverse=True)
        return legal_cards[0]

    def _card_priority(self, card: Card, trump: Suit) -> float:
        """Return a discard priority (lower is worse) respecting bowers.

        Args:
            card: Card to evaluate for discard.
            trump: Active trump suit.

        Returns:
            float: Priority value used for sorting.

        Raises:
            None.
        """

        if card.rank == "J" and card.suit == trump:
            return 100.0
        same_color = _same_color_suit(trump)
        if card.rank == "J" and same_color and card.suit == same_color:
            return 99.0
        base = RANK_VALUE.get(card.rank, 0)
        if card.suit == trump:
            base += 50
        return float(base)

    def _lead_priority(self, card: Card, trump: Suit) -> float:
        """Return a priority score for leading or following to a trick.

        Args:
            card: Card being assessed.
            trump: Active trump suit.

        Returns:
            float: Priority score where higher values are preferred.

        Raises:
            None.
        """

        eff = effective_suit(card, trump)
        base = RANK_VALUE.get(card.rank, 0)
        if card.rank == "J" and card.suit == trump:
            return 200.0
        same_color = _same_color_suit(trump)
        if card.rank == "J" and same_color and card.suit == same_color:
            return 199.0
        if eff == trump:
            return 150.0 + base
        return 80.0 + base if eff == card.suit else base


def effective_suit(card: Card, trump: Suit) -> Suit:
    """Return the suit a card counts as when following lead.

    Args:
        card: Card whose effective suit is requested.
        trump: Active trump suit.

    Returns:
        Suit: Suit the card represents for following.

    Raises:
        None.
    """

    if card.rank == "J" and card.suit == trump:
        return trump
    same_color = _same_color_suit(trump)
    if card.rank == "J" and same_color and card.suit == same_color:
        return trump
    return card.suit


def _same_color_suit(suit: Optional[Suit]) -> Optional[Suit]:
    """Return the same-colour suit for evaluating the left bower.

    Args:
        suit: Suit whose same-colour counterpart is required.

    Returns:
        Optional[Suit]: Same-colour suit, if applicable.

    Raises:
        None.
    """

    if suit == Suit.CLUBS:
        return Suit.SPADES
    if suit == Suit.SPADES:
        return Suit.CLUBS
    if suit == Suit.HEARTS:
        return Suit.DIAMONDS
    if suit == Suit.DIAMONDS:
        return Suit.HEARTS
    return None
