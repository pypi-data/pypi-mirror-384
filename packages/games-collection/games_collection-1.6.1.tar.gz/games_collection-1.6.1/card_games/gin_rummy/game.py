"""Comprehensive Gin Rummy engine with realistic round handling and scoring.

This module provides a complete implementation of the two-player Gin Rummy game,
capturing authentic rules such as the opening upcard offer, meld detection,
layoffs, and various scoring bonuses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from random import Random
from typing import Optional, Sequence

from card_games.common.cards import Card, Deck


class MeldType(Enum):
    """Enumerates the types of melds in Gin Rummy."""

    SET = auto()
    RUN = auto()


class KnockType(Enum):
    """Enumerates the ways a round of Gin Rummy can end."""

    GIN = auto()
    BIG_GIN = auto()
    KNOCK = auto()
    UNDERCUT = auto()


@dataclass(frozen=True)
class Meld:
    """Represents a meld (a set or a run) in Gin Rummy.

    Attributes:
        meld_type: The type of the meld (SET or RUN).
        cards: A tuple of cards that form the meld.
    """

    meld_type: MeldType
    cards: tuple[Card, ...]


@dataclass(frozen=True)
class HandAnalysis:
    """Represents the optimal meld grouping and deadwood for a hand.

    Attributes:
        melds: A tuple of the best melds found in the hand.
        deadwood_cards: A tuple of cards that are not part of any meld.
        deadwood_total: The total point value of the deadwood cards.
    """

    melds: tuple[Meld, ...]
    deadwood_cards: tuple[Card, ...]
    deadwood_total: int


@dataclass(frozen=True)
class RoundSummary:
    """A summary of a completed round with detailed scoring information.

    Attributes:
        dealer: The name of the dealer for the round.
        knocker: The name of the player who knocked.
        opponent: The name of the opponent.
        knock_type: The type of knock (e.g., GIN, KNOCK).
        knocker_deadwood: The deadwood total of the knocker.
        opponent_deadwood: The opponent's deadwood total after layoffs.
        opponent_initial_deadwood: The opponent's deadwood before layoffs.
        melds_shown: The melds shown by the knocker.
        layoff_cards: The cards laid off by the opponent.
        points_awarded: A dictionary of points awarded to each player.
    """

    dealer: str
    knocker: str
    opponent: str
    knock_type: KnockType
    knocker_deadwood: int
    opponent_deadwood: int
    opponent_initial_deadwood: int
    melds_shown: tuple[Meld, ...]
    layoff_cards: tuple[Card, ...]
    points_awarded: dict[str, int]


@dataclass
class GinRummyPlayer:
    """Represents a player in a game of Gin Rummy.

    Attributes:
        name: The player's name.
        hand: A list of cards in the player's hand.
        score: The player's total score across all rounds.
        is_ai: True if the player is controlled by an AI.
    """

    name: str
    hand: list[Card] = field(default_factory=list)
    score: int = 0
    is_ai: bool = False


def _deadwood_value(card: Card) -> int:
    """Return the deadwood point value of a card."""

    if card.rank == "A":
        return 1
    if card.rank in {"K", "Q", "J", "T"}:
        return 10
    return int(card.rank)


def _generate_set_melds(cards: Sequence[Card]) -> list[Meld]:
    """Generate all set melds (three or four of a kind)."""

    by_rank: dict[str, list[Card]] = {}
    for card in cards:
        by_rank.setdefault(card.rank, []).append(card)

    melds: list[Meld] = []
    for group in by_rank.values():
        if len(group) >= 3:
            meld_cards = tuple(sorted(group, key=lambda c: c.suit.value))
            melds.append(Meld(MeldType.SET, meld_cards))
    return melds


def _generate_run_melds(cards: Sequence[Card]) -> list[Meld]:
    """Generate all run melds (three or more consecutive cards of one suit)."""

    by_suit: dict[str, list[Card]] = {}
    for card in cards:
        by_suit.setdefault(card.suit.value, []).append(card)

    melds: list[Meld] = []
    for suit_cards in by_suit.values():
        suit_cards.sort(key=lambda c: c.value)
        run: list[Card] = []
        for card in suit_cards:
            if not run or card.value == run[-1].value + 1:
                run.append(card)
            elif card.value == run[-1].value:
                # Skip duplicate ranks within the same suit.
                continue
            else:
                if len(run) >= 3:
                    melds.extend(Meld(MeldType.RUN, tuple(run[i:j])) for i in range(0, len(run) - 2) for j in range(i + 3, len(run) + 1))
                run = [card]
        if len(run) >= 3:
            melds.extend(Meld(MeldType.RUN, tuple(run[i:j])) for i in range(0, len(run) - 2) for j in range(i + 3, len(run) + 1))
    return melds


def _generate_melds(cards: Sequence[Card]) -> list[Meld]:
    """Return all potential melds from the given cards."""

    return _generate_set_melds(cards) + _generate_run_melds(cards)


def _best_meld_plan(cards: Sequence[Card]) -> HandAnalysis:
    """Compute the meld grouping that minimizes deadwood for ``cards``."""

    candidates = _generate_melds(cards)
    ordered_cards = list(cards)
    best_deadwood = float("inf")
    best_melds: tuple[Meld, ...] = tuple()
    best_deadwood_cards: tuple[Card, ...] = tuple()

    def search(index: int, used: set[Card], chosen: list[Meld]) -> None:
        nonlocal best_deadwood, best_melds, best_deadwood_cards
        if index == len(candidates):
            deadwood_cards = tuple(card for card in ordered_cards if card not in used)
            deadwood = sum(_deadwood_value(card) for card in deadwood_cards)
            if deadwood < best_deadwood or (deadwood == best_deadwood and len(chosen) > len(best_melds)):
                best_deadwood = deadwood
                best_melds = tuple(chosen)
                best_deadwood_cards = deadwood_cards
            return

        search(index + 1, used, chosen)

        meld = candidates[index]
        if any(card in used for card in meld.cards):
            return

        for card in meld.cards:
            used.add(card)
        chosen.append(meld)
        search(index + 1, used, chosen)
        chosen.pop()
        for card in meld.cards:
            used.remove(card)

    search(0, set(), [])

    if best_deadwood == float("inf"):
        deadwood_cards = tuple(ordered_cards)
        return HandAnalysis(tuple(), deadwood_cards, sum(_deadwood_value(card) for card in deadwood_cards))

    return HandAnalysis(best_melds, best_deadwood_cards, int(best_deadwood))


def _can_layoff(card: Card, meld: Meld) -> bool:
    """Return whether ``card`` can be laid off on ``meld``."""

    if meld.meld_type == MeldType.SET:
        if len(meld.cards) >= 4:
            return False
        return card.rank == meld.cards[0].rank

    meld_values = [c.value for c in meld.cards]
    if card.suit != meld.cards[0].suit:
        return False
    if card.value == meld_values[0] - 1:
        return True
    return card.value == meld_values[-1] + 1


def _apply_layoffs(deadwood_cards: Sequence[Card], melds: Sequence[Meld]) -> tuple[tuple[Card, ...], tuple[Card, ...]]:
    """Lay off as many cards as possible on the knocker's melds."""

    remaining = list(deadwood_cards)
    layoff: list[Card] = []
    current_meld_cards: dict[Meld, list[Card]] = {meld: list(meld.cards) for meld in melds}

    for card in list(remaining):
        for meld in melds:
            current_meld = Meld(meld.meld_type, tuple(current_meld_cards[meld]))
            if _can_layoff(card, current_meld):
                layoff.append(card)
                remaining.remove(card)
                if meld.meld_type == MeldType.SET:
                    current_meld_cards[meld].append(card)
                else:
                    if card.value < current_meld_cards[meld][0].value:
                        current_meld_cards[meld].insert(0, card)
                    else:
                        current_meld_cards[meld].append(card)
                break

    return tuple(remaining), tuple(layoff)


class GinRummyGame:
    """The main engine for Gin Rummy, enforcing rules and managing game flow."""

    def __init__(self, players: list[GinRummyPlayer], *, rng: Optional[Random] = None) -> None:
        """Initialize a Gin Rummy game."""
        if len(players) != 2:
            raise ValueError("Gin Rummy requires exactly two players.")
        self.players = players
        self.rng = rng or Random()
        self.deck = Deck()
        self.discard_pile: list[Card] = []
        self.dealer_idx = -1  # Will be incremented to 0 on first deal
        self.current_player_idx = 0
        self.round_history: list[RoundSummary] = []
        self.initial_upcard_phase = False
        self.blocked_discard_card: Optional[Card] = None
        self.initial_offer_order: list[int] = []

    def _shuffle_deck(self) -> None:
        """Shuffle the deck using the configured RNG."""
        self.deck.shuffle(rng=self.rng)

    def deal_cards(self) -> None:
        """Deal a new round, preparing the deck and hands."""
        self.dealer_idx = (self.dealer_idx + 1) % len(self.players)
        self.deck = Deck()
        self._shuffle_deck()

        for player in self.players:
            player.hand = self.deck.deal(10)
            player.hand.sort(key=lambda c: (c.suit.value, c.value))

        self.discard_pile = self.deck.deal(1)
        self.initial_upcard_phase = True
        self.current_player_idx = (self.dealer_idx + 1) % 2
        self.initial_offer_order = [(self.dealer_idx + 1) % 2, self.dealer_idx]
        self.blocked_discard_card = None

    def _reshuffle_from_discard(self) -> None:
        """Reshuffle the discard pile into the stock, leaving the top card."""
        if len(self.discard_pile) > 1:
            top_card = self.discard_pile.pop()
            self.deck.cards.extend(self.discard_pile)
            self.discard_pile = [top_card]
            self._shuffle_deck()

    def can_take_initial_upcard(self, player_idx: int) -> bool:
        """Check if the player is eligible to take the initial up-card."""
        return self.initial_upcard_phase and player_idx == self.current_player_idx

    def take_initial_upcard(self) -> Card:
        """Allow the current player to take the initial up-card."""
        if not self.can_take_initial_upcard(self.current_player_idx):
            raise RuntimeError("Cannot take the initial up-card now.")

        card = self.discard_pile.pop()
        self.players[self.current_player_idx].hand.append(card)
        self.initial_upcard_phase = False
        return card

    def pass_initial_upcard(self) -> None:
        """Allow the current player to pass on the initial up-card."""
        if not self.can_take_initial_upcard(self.current_player_idx):
            raise RuntimeError("Cannot pass on the up-card now.")

        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        if self.current_player_idx == (self.dealer_idx + 1) % len(self.players):
            # Both players passed, the first player must draw from stock
            self.initial_upcard_phase = False
            self.blocked_discard_card = self.discard_pile[-1]

    def draw_from_stock(self) -> Card:
        """Draw a card from the stock pile."""
        if not self.deck.cards:
            self._reshuffle_from_discard()
        card = self.deck.deal(1)[0]
        self.players[self.current_player_idx].hand.append(card)
        self.blocked_discard_card = None  # Drawing from stock unblocks the discard
        return card

    def can_draw_from_discard(self) -> bool:
        """Check if the current player can draw from the discard pile."""
        return bool(self.discard_pile) and self.discard_pile[-1] != self.blocked_discard_card

    def draw_from_discard(self) -> Card:
        """Draw the top card from the discard pile."""
        if not self.can_draw_from_discard():
            raise RuntimeError("Cannot draw from the discard pile.")
        card = self.discard_pile.pop()
        self.players[self.current_player_idx].hand.append(card)
        return card

    def discard(self, card: Card) -> None:
        """Discard a card from the current player's hand."""
        player = self.players[self.current_player_idx]
        if card not in player.hand:
            raise ValueError("Card not in player's hand.")
        player.hand.remove(card)
        self.discard_pile.append(card)
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

    def knock(self) -> RoundSummary:
        """End the round by knocking."""
        knocker = self.players[self.current_player_idx]
        opponent = self.players[(self.current_player_idx + 1) % 2]

        analysis = self.analyze_hand(knocker.hand)
        if analysis.deadwood_total > 10:
            raise ValueError("Cannot knock with more than 10 deadwood.")

        summary = self._score_round(knocker, opponent)
        self.record_points(summary)
        return summary

    def analyze_hand(self, cards: Sequence[Card]) -> HandAnalysis:
        """Return the optimal meld and deadwood analysis for a hand."""
        return _best_meld_plan(cards)

    def calculate_round_score(self, knocker: GinRummyPlayer, opponent: GinRummyPlayer) -> RoundSummary:
        """Compute the scoring for a completed round."""
        knocker_analysis = self.analyze_hand(knocker.hand)
        opponent_analysis = self.analyze_hand(opponent.hand)

        knock_type = KnockType.KNOCK
        if knocker_analysis.deadwood_total == 0:
            knock_type = KnockType.BIG_GIN if len(knocker.hand) == 11 else KnockType.GIN

        remaining_deadwood, layoff_cards = _apply_layoffs(opponent_analysis.deadwood_cards, knocker_analysis.melds)
        opponent_deadwood = sum(_deadwood_value(c) for c in remaining_deadwood)
        points = 0
        knocker_wins = True

        if knock_type in {KnockType.GIN, KnockType.BIG_GIN}:
            points = 25 if knock_type == KnockType.GIN else 31
            points += opponent_deadwood
        elif opponent_deadwood <= knocker_analysis.deadwood_total:
            knock_type = KnockType.UNDERCUT
            knocker_wins = False
            points = 25 + (knocker_analysis.deadwood_total - opponent_deadwood)
        else:
            points = opponent_deadwood - knocker_analysis.deadwood_total

        points_awarded = {
            knocker.name: points if knocker_wins else 0,
            opponent.name: 0 if knocker_wins else points,
        }

        return RoundSummary(
            dealer=self.players[self.dealer_idx].name,
            knocker=knocker.name,
            opponent=opponent.name,
            knock_type=knock_type,
            knocker_deadwood=knocker_analysis.deadwood_total,
            opponent_deadwood=opponent_deadwood,
            opponent_initial_deadwood=opponent_analysis.deadwood_total,
            melds_shown=knocker_analysis.melds,
            layoff_cards=layoff_cards,
            points_awarded=points_awarded,
        )

    def record_points(self, summary: RoundSummary) -> None:
        """Apply the points from a round summary to the players' scores."""
        for p in self.players:
            p.score += summary.points_awarded.get(p.name, 0)

    def is_game_over(self, target_score: int = 100) -> bool:
        """Check if the game has reached the target score."""
        return any(p.score >= target_score for p in self.players)

    def get_winner(self) -> Optional[GinRummyPlayer]:
        """Return the winner of the game, if any."""
        return max(self.players, key=lambda p: p.score) if self.is_game_over() else None

    # ... (AI helper methods can be documented here)
