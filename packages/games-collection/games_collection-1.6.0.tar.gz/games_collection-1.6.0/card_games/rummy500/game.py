"""Rummy 500 card game engine.

This module implements Rummy 500, a variant of rummy with melding, laying off,
and negative scoring for cards remaining in hand.

Rules:
* Standard 52-card deck
* 2-4 players
* Goal: Be first to reach 500 points
* Score points for melds (sets and runs)
* Lose points for cards left in hand
* Can pick from discard pile and see all discarded cards
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from functools import lru_cache
from itertools import combinations
from random import Random
from typing import Iterable, Optional, Sequence, Tuple

from card_games.common.cards import RANK_TO_VALUE, Card, Deck


class GamePhase(Enum):
    """Current phase of Rummy 500."""

    DEAL = auto()
    DRAW = auto()
    MELD = auto()
    DISCARD = auto()
    GAME_OVER = auto()


def _sort_cards(cards: Iterable[Card]) -> list[Card]:
    """Return cards sorted by rank then suit for consistent presentation."""

    return sorted(cards, key=lambda c: (RANK_TO_VALUE[c.rank], c.suit.value))


@dataclass
class Meld:
    """Representation of a meld on the table."""

    owner: int
    cards: list[Card]
    kind: str
    contributions: dict[int, list[Card]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalise card ordering and contribution tracking."""

        self.cards = _sort_cards(self.cards)
        normalised: dict[int, list[Card]] = {}
        for player, contributed in self.contributions.items():
            normalised[player] = _sort_cards(contributed)
        if self.owner not in normalised:
            normalised[self.owner] = _sort_cards(self.cards)
        self.contributions = normalised

    def add_cards(self, player: int, cards: Sequence[Card]) -> None:
        """Track additional cards laid on the meld by *player*."""

        if not cards:
            return

        self.cards.extend(cards)
        self.cards = _sort_cards(self.cards)
        existing = self.contributions.get(player, [])
        updated = existing + list(cards)
        self.contributions[player] = _sort_cards(updated)


@dataclass
class Rummy500Game:
    """Rummy 500 game engine.

    Attributes:
        hands: Player hands
        melds: Melds laid down by each player
        discard_pile: Discard pile (visible)
        deck: Draw deck
        scores: Player scores
        current_player: Current player
        phase: Current game phase
        winner: Winner (player index), None if ongoing
    """

    hands: list[list[Card]] = field(default_factory=list)
    melds: list[Meld] = field(default_factory=list)
    discard_pile: list[Card] = field(default_factory=list)
    deck: Deck = field(default_factory=Deck)
    scores: list[int] = field(default_factory=list)
    current_player: int = 0
    phase: GamePhase = GamePhase.DEAL
    winner: Optional[int] = None
    num_players: int = 2

    def __init__(self, num_players: int = 2, rng: Optional[Random] = None) -> None:
        """Initialize Rummy 500 game.

        Args:
            num_players: Number of players (2-4)
            rng: Optional Random instance
        """
        self.num_players = max(2, min(4, num_players))
        self.hands = [[] for _ in range(self.num_players)]
        self.melds = []
        self.discard_pile = []
        self.deck = Deck()
        self.scores = [0] * self.num_players
        self.current_player = 0
        self.phase = GamePhase.DEAL
        self.winner = None
        self._rng = rng

        if rng:
            self.deck.shuffle(rng=rng)
        else:
            self.deck.shuffle()

        self._deal_hands()

    def _deal_hands(self) -> None:
        """Deal initial hands."""
        cards_per_player = 7 if self.num_players == 2 else 7
        for i in range(self.num_players):
            self.hands[i] = self.deck.deal(cards_per_player)

        # Start discard pile
        if len(self.deck.cards) > 0:
            self.discard_pile.append(self.deck.deal()[0])

        self.phase = GamePhase.DRAW

    def _card_value(self, card: Card) -> int:
        """Get point value of a card.

        Args:
            card: Card to evaluate

        Returns:
            Point value
        """
        if card.rank == "A":
            return 15
        elif card.rank in ["J", "Q", "K"]:
            return 10
        elif card.rank == "T":
            return 10
        else:
            return int(card.rank)

    def draw_card(self, from_discard: bool = False, take_count: int = 1) -> bool:
        """Draw a card.

        Args:
            from_discard: Whether to draw from discard pile
            take_count: Number of cards to take from discard

        Returns:
            True if successful
        """
        if self.phase != GamePhase.DRAW:
            return False

        if from_discard:
            if take_count <= 0:
                return False
            if len(self.discard_pile) >= take_count:
                # Take cards from discard pile
                for _ in range(take_count):
                    card = self.discard_pile.pop()
                    self.hands[self.current_player].append(card)
            else:
                return False
        else:
            # Draw from deck
            if len(self.deck.cards) > 0:
                card = self.deck.deal()[0]
                self.hands[self.current_player].append(card)
            else:
                # Reshuffle discard pile if deck empty
                if len(self.discard_pile) > 1:
                    top_discard = self.discard_pile.pop()
                    self.deck.cards = self.discard_pile[:]
                    self.deck.shuffle()
                    self.discard_pile = [top_discard]
                    card = self.deck.deal()[0]
                    self.hands[self.current_player].append(card)
                else:
                    return False

        self.phase = GamePhase.MELD
        return True

    def _identify_meld_type(self, cards: Sequence[Card]) -> str:
        """Identify whether *cards* form a set or run."""

        if len(cards) < 3:
            raise ValueError("Melds require at least three cards")

        if all(c.rank == cards[0].rank for c in cards):
            return "set"

        if all(c.suit == cards[0].suit for c in cards):
            values = sorted(RANK_TO_VALUE[c.rank] for c in cards)
            if all(values[i] + 1 == values[i + 1] for i in range(len(values) - 1)):
                return "run"

        raise ValueError("Cards do not form a valid meld")

    def is_valid_meld(self, cards: list[Card]) -> bool:
        """Check if cards form a valid meld.

        Args:
            cards: Cards to check

        Returns:
            True if valid meld
        """
        if len(cards) < 3:
            return False

        # Check for set (same rank)
        if all(c.rank == cards[0].rank for c in cards):
            return True

        # Check for run (consecutive ranks, same suit)
        if all(c.suit == cards[0].suit for c in cards):
            values = sorted([RANK_TO_VALUE[c.rank] for c in cards])
            return all(values[i] + 1 == values[i + 1] for i in range(len(values) - 1))

        return False

    def lay_meld(self, player: int, cards: list[Card]) -> bool:
        """Lay down a meld.

        Args:
            player: Player laying meld
            cards: Cards in the meld

        Returns:
            True if successful
        """
        if not self.is_valid_meld(cards):
            return False

        if not all(c in self.hands[player] for c in cards):
            return False

        # Remove from hand and add to melds
        for card in cards:
            self.hands[player].remove(card)

        kind = self._identify_meld_type(cards)
        meld = Meld(owner=player, cards=list(cards), kind=kind, contributions={player: list(cards)})
        self.melds.append(meld)
        return True

    def _canonical_cards(self, cards: Iterable[Card]) -> Tuple[Card, ...]:
        """Return a tuple of cards with deterministic ordering."""

        return tuple(_sort_cards(cards))

    def _valid_meld_combinations(self, cards: Sequence[Card]) -> list[Tuple[Card, ...]]:
        """Return all unique valid melds that can be made from *cards*."""

        unique: set[Tuple[Card, ...]] = set()
        for size in range(3, len(cards) + 1):
            for combo in combinations(cards, size):
                combo_list = list(combo)
                if self.is_valid_meld(combo_list):
                    unique.add(self._canonical_cards(combo_list))

        return sorted(
            unique,
            key=lambda meld: (
                len(meld),
                tuple(RANK_TO_VALUE[c.rank] for c in meld),
                tuple(c.suit.value for c in meld),
            ),
        )

    def _analyse_cards(self, cards: Sequence[Card]) -> tuple[list[list[Card]], list[Card], int, int]:
        """Return optimal meld arrangement for *cards*.

        Returns:
            A tuple ``(melds, deadwood, meld_points, deadwood_points)`` where
            ``melds`` is a list of card lists representing the best melds,
            ``deadwood`` are leftover cards, and the point totals summarise
            positive meld points and deadwood penalties respectively.
        """

        canonical_start = self._canonical_cards(cards)

        @lru_cache(maxsize=None)
        def best_plan(card_tuple: Tuple[Card, ...]) -> tuple[
            Tuple[Tuple[Card, ...], ...],
            Tuple[Card, ...],
            int,
            int,
        ]:
            cards_list = list(card_tuple)
            deadwood_points = sum(self._card_value(card) for card in cards_list)
            best_melds: Tuple[Tuple[Card, ...], ...] = tuple()
            best_deadwood: Tuple[Card, ...] = card_tuple
            best_meld_points = 0
            best_deadwood_points = deadwood_points
            best_net = -deadwood_points

            for meld in self._valid_meld_combinations(cards_list):
                remaining = list(card_tuple)
                for card in meld:
                    remaining.remove(card)
                remaining_tuple = self._canonical_cards(remaining)
                sub_melds, sub_deadwood, sub_meld_points, sub_deadwood_points = best_plan(remaining_tuple)

                meld_points = sum(self._card_value(card) for card in meld)
                total_meld_points = sub_meld_points + meld_points
                total_deadwood_points = sub_deadwood_points
                net = total_meld_points - total_deadwood_points

                if net > best_net or (
                    net == best_net
                    and (
                        total_deadwood_points < best_deadwood_points or (total_deadwood_points == best_deadwood_points and total_meld_points > best_meld_points)
                    )
                ):
                    best_net = net
                    best_meld_points = total_meld_points
                    best_deadwood_points = total_deadwood_points
                    best_melds = sub_melds + (meld,)
                    best_deadwood = sub_deadwood

            return best_melds, best_deadwood, best_meld_points, best_deadwood_points

        melds, deadwood, meld_points, deadwood_points = best_plan(canonical_start)
        return [list(meld) for meld in melds], list(deadwood), meld_points, deadwood_points

    def available_melds(self, player: int) -> list[list[Card]]:
        """Return all melds available in the current player's hand."""

        return [list(meld) for meld in self._valid_meld_combinations(self.hands[player])]

    def get_deadwood_summary(self, player: int) -> dict[str, object]:
        """Return the optimal meld/deadwood breakdown for *player*."""

        melds, deadwood, meld_points, deadwood_points = self._analyse_cards(self.hands[player])
        return {
            "melds": melds,
            "deadwood": deadwood,
            "meld_points": meld_points,
            "deadwood_points": deadwood_points,
            "net_points": meld_points - deadwood_points,
        }

    def summarize_cards(self, cards: Sequence[Card]) -> dict[str, object]:
        """Return meld/deadwood summary for an arbitrary card collection."""

        melds, deadwood, meld_points, deadwood_points = self._analyse_cards(cards)
        return {
            "melds": melds,
            "deadwood": deadwood,
            "meld_points": meld_points,
            "deadwood_points": deadwood_points,
            "net_points": meld_points - deadwood_points,
        }

    def preview_after_cards(self, player: int, cards_to_remove: Sequence[Card]) -> dict[str, object]:
        """Preview hand summary after removing the given cards."""

        remaining = list(self.hands[player])
        for card in cards_to_remove:
            if card not in remaining:
                raise ValueError("Card not present in hand for preview")
            remaining.remove(card)

        remaining_cards = self._canonical_cards(remaining)
        melds, deadwood, meld_points, deadwood_points = self._analyse_cards(remaining_cards)
        return {
            "melds": melds,
            "deadwood": deadwood,
            "meld_points": meld_points,
            "deadwood_points": deadwood_points,
            "net_points": meld_points - deadwood_points,
            "remaining": list(remaining_cards),
        }

    def get_layoff_options(self, player: int) -> list[dict[str, object]]:
        """Return layoff opportunities available to *player*."""

        options: list[dict[str, object]] = []
        hand = self.hands[player]
        for index, meld in enumerate(self.melds):
            usable = []
            for card in hand:
                if card in usable:
                    continue
                if self.can_lay_off(index, [card]):
                    usable.append(card)
            if usable:
                options.append(
                    {
                        "meld_index": index,
                        "owner": meld.owner,
                        "cards": _sort_cards(usable),
                    }
                )
        return options

    def can_lay_off(self, meld_index: int, cards: list[Card]) -> bool:
        """Return True if *cards* can be added to the meld at *meld_index*."""

        if meld_index < 0 or meld_index >= len(self.melds):
            return False

        meld = self.melds[meld_index]
        if not cards:
            return False

        candidate = meld.cards + list(cards)
        return self.is_valid_meld(candidate)

    def lay_off(self, player: int, meld_index: int, cards: list[Card]) -> bool:
        """Lay off *cards* from *player* onto the meld indexed by *meld_index*."""

        if self.phase != GamePhase.MELD:
            return False

        if not cards or not all(card in self.hands[player] for card in cards):
            return False

        if not self.can_lay_off(meld_index, cards):
            return False

        meld = self.melds[meld_index]
        for card in cards:
            self.hands[player].remove(card)
        meld.add_cards(player, cards)
        return True

    def end_round_due_to_empty_stock(self) -> None:
        """End the round when no cards can be drawn from the stock or discard piles.

        Returns:
            None
        """

        if self.phase == GamePhase.GAME_OVER:
            return

        self._score_round()
        if any(score >= 500 for score in self.scores):
            self.phase = GamePhase.GAME_OVER
            self.winner = self.scores.index(max(self.scores))
            return

        scores_snapshot = self.scores[:]
        rng = getattr(self, "_rng", None)
        self.__init__(self.num_players, rng=rng)
        self.scores = scores_snapshot

    def go_out(self, player: int) -> bool:
        """End the round if *player* has emptied their hand during the meld phase."""

        if player != self.current_player or self.phase != GamePhase.MELD:
            return False

        if self.hands[player]:
            return False

        self._score_round()
        if any(s >= 500 for s in self.scores):
            self.phase = GamePhase.GAME_OVER
            self.winner = self.scores.index(max(self.scores))
        else:
            scores_snapshot = self.scores[:]
            rng = getattr(self, "_rng", None)
            self.__init__(self.num_players, rng=rng)
            self.scores = scores_snapshot
        return True

    def discard(self, player: int, card: Card) -> bool:
        """Discard a card.

        Args:
            player: Player discarding
            card: Card to discard

        Returns:
            True if successful
        """
        if card not in self.hands[player]:
            return False

        self.hands[player].remove(card)
        self.discard_pile.append(card)

        # Check if hand is empty (going out)
        if not self.hands[player]:
            self._score_round()
            if any(s >= 500 for s in self.scores):
                self.phase = GamePhase.GAME_OVER
                self.winner = self.scores.index(max(self.scores))
            else:
                # Start new round while preserving scores
                scores_snapshot = self.scores[:]
                rng = getattr(self, "_rng", None)
                self.__init__(self.num_players, rng=rng)
                self.scores = scores_snapshot
        else:
            # Next player
            self.current_player = (self.current_player + 1) % self.num_players
            self.phase = GamePhase.DRAW

        return True

    def _score_round(self) -> None:
        """Score the round when someone goes out."""

        meld_points = [0] * self.num_players
        for meld in self.melds:
            for player, cards in meld.contributions.items():
                meld_points[player] += sum(self._card_value(card) for card in cards)

        for i in range(self.num_players):
            penalty = sum(self._card_value(card) for card in self.hands[i])
            self.scores[i] += meld_points[i] - penalty

    def get_state_summary(self) -> dict[str, object]:
        """Get game state summary.

        Returns:
            State dictionary
        """
        return {
            "scores": self.scores,
            "current_player": self.current_player,
            "phase": self.phase.name,
            "hand_sizes": [len(h) for h in self.hands],
            "discard_top": str(self.discard_pile[-1]) if self.discard_pile else None,
            "deck_size": len(self.deck.cards),
            "winner": self.winner,
            "game_over": self.phase == GamePhase.GAME_OVER,
            "melds": [
                {
                    "owner": meld.owner,
                    "cards": [str(card) for card in meld.cards],
                    "contributors": {player: [str(card) for card in cards] for player, cards in meld.contributions.items()},
                }
                for meld in self.melds
            ],
        }
