"""Core Canasta engine with deck, meld, and scoring management.

This module provides the core classes and logic for playing Canasta, including
the game engine, player and team management, and rule validation for melds.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from random import Random
from typing import Iterable, Optional, Sequence, Union

from card_games.common.cards import RANK_TO_VALUE, Card, Deck, Suit


class MeldError(Exception):
    """Custom exception raised when an invalid meld is attempted."""


@dataclass(frozen=True)
class JokerCard:
    """A representation of a joker, used as a wild card in Canasta.

    Attributes:
        label: The string representation of the joker (default: "🃏").
    """

    label: str = "🃏"

    @property
    def rank(self) -> str:
        """Return the pseudo-rank "JOKER" for sorting and comparison."""
        return "JOKER"

    @property
    def suit(self) -> str:
        """Return the pseudo-suit "wild" for compatibility."""
        return "wild"

    @property
    def value(self) -> int:
        """Return the joker's ordering value, higher than any standard card."""
        return len(RANK_TO_VALUE) + 1

    def __str__(self) -> str:  # pragma: no cover - trivial
        """Return the emoji label for display."""
        return self.label


CanastaCard = Union[Card, JokerCard]


@dataclass
class Meld:
    """Represents a meld of same-ranked cards.

    Attributes:
        cards: The list of cards in the meld.
        rank: The rank of the natural cards in the meld.
        natural_count: The number of natural cards.
        wild_count: The number of wild cards.
    """

    cards: list[CanastaCard]
    rank: str
    natural_count: int
    wild_count: int

    def __post_init__(self) -> None:
        """Sort cards for a consistent and stable ordering."""
        self.cards.sort(key=_card_sort_key)

    @property
    def is_canasta(self) -> bool:
        """Return True if the meld qualifies as a canasta (7+ cards)."""
        return len(self.cards) >= 7

    @property
    def is_natural(self) -> bool:
        """Return True if the meld contains no wild cards."""
        return self.wild_count == 0

    def point_value(self) -> int:
        """Return the total point value of the meld, including canasta bonuses."""
        base = sum(card_point_value(card) for card in self.cards)
        if self.is_canasta:
            base += 500 if self.is_natural else 300
        return base


@dataclass(frozen=True)
class MeldValidation:
    """Represents the outcome of validating a potential meld.

    Attributes:
        is_valid: True if the meld is valid according to Canasta rules.
        message: A descriptive message explaining the validation result.
        meld: The resulting ``Meld`` object if validation is successful.
    """

    is_valid: bool
    message: str
    meld: Optional[Meld] = None


@dataclass
class CanastaPlayer:
    """Represents a single participant in a Canasta game.

    Attributes:
        name: The player's name.
        team_index: The index of the team this player belongs to.
        is_ai: True if this player is controlled by an AI.
        hand: The list of cards currently held by the player.
    """

    name: str
    team_index: int
    is_ai: bool = False
    hand: list[CanastaCard] = field(default_factory=list)

    def remove_cards(self, cards: Iterable[CanastaCard]) -> None:
        """Remove a collection of cards from the player's hand."""
        for card in cards:
            self.hand.remove(card)


@dataclass
class CanastaTeam:
    """Represents a partnership of players who share melds and a score.

    Attributes:
        name: The name of the team.
        players: A list of ``CanastaPlayer`` objects on this team.
        score: The team's total score across all rounds.
        melds: A list of melds the team has laid down in the current round.
        requirement_met: True if the team has met the initial meld requirement.
    """

    name: str
    players: list[CanastaPlayer]
    score: int = 0
    melds: list[Meld] = field(default_factory=list)
    requirement_met: bool = False

    def reset_for_round(self) -> None:
        """Clear round-specific data while preserving the overall score."""
        self.melds.clear()
        self.requirement_met = False


class DrawSource(Enum):
    """Enumerates the locations a player can draw a card from."""

    STOCK = "stock"
    DISCARD = "discard"


def _card_sort_key(card: CanastaCard) -> tuple[int, str]:
    """Return a consistent sorting key for mixed decks."""

    if isinstance(card, Card):
        return (RANK_TO_VALUE[card.rank], card.suit.value)
    return (len(RANK_TO_VALUE) + 1, "wild")


def card_point_value(card: CanastaCard) -> int:
    """Return the point value assigned for scoring."""

    if isinstance(card, JokerCard):
        return 50
    if not isinstance(card, Card):  # pragma: no cover - defensive
        raise TypeError("Unsupported card type")
    if card.rank == "2":
        return 20
    if card.rank == "A":
        return 20
    if card.rank in {"K", "Q", "J", "T", "9", "8"}:
        return 10
    if card.rank in {"7", "6", "5", "4"}:
        return 5
    return 5


def is_wild(card: CanastaCard) -> bool:
    """Return whether *card* is wild."""

    return isinstance(card, JokerCard) or (isinstance(card, Card) and card.rank == "2")


def _collect_naturals(cards: Iterable[CanastaCard]) -> list[Card]:
    """Return the natural cards from *cards*."""

    naturals: list[Card] = []
    for card in cards:
        if isinstance(card, Card) and not is_wild(card):
            naturals.append(card)
    return naturals


def _collect_wilds(cards: Iterable[CanastaCard]) -> list[CanastaCard]:
    """Return the wild cards from *cards*."""

    wilds: list[CanastaCard] = []
    for card in cards:
        if is_wild(card):
            wilds.append(card)
    return wilds


def _natural_rank(cards: Iterable[CanastaCard]) -> Optional[str]:
    """Return the rank shared by all natural cards, if any."""

    naturals = _collect_naturals(cards)
    if not naturals:
        return None
    ranks = {card.rank for card in naturals}
    if len(ranks) == 1:
        return ranks.pop()
    return None


def validate_meld(cards: Sequence[CanastaCard], *, existing: Optional[Meld] = None) -> MeldValidation:
    """Validate ``cards`` as a new or extended meld."""

    if not cards:
        return MeldValidation(False, "A meld must contain at least one card.")

    naturals = _collect_naturals(cards)
    wilds = _collect_wilds(cards)
    rank = existing.rank if existing else _natural_rank(cards)

    if rank is None:
        return MeldValidation(False, "Melds require at least two natural cards of the same rank.")

    combined_naturals = len(naturals) + (existing.natural_count if existing else 0)
    combined_wilds = len(wilds) + (existing.wild_count if existing else 0)

    if combined_naturals < 2 and existing is None:
        return MeldValidation(False, "A new meld must contain at least two natural cards.")

    total_cards = combined_naturals + combined_wilds
    if existing is None and total_cards < 3:
        return MeldValidation(False, "A new meld must contain at least three cards.")

    if combined_wilds > combined_naturals:
        return MeldValidation(False, "Wild cards may not outnumber natural cards in a meld.")

    if combined_wilds > 3:
        return MeldValidation(False, "A meld may contain at most three wild cards.")

    for card in naturals:
        if card.rank != rank:
            return MeldValidation(False, "All natural cards must share the meld rank.")

    meld_cards = list(cards)
    if existing:
        meld_cards = existing.cards + meld_cards

    meld = Meld(meld_cards, rank, combined_naturals, combined_wilds)
    return MeldValidation(True, "Valid meld.", meld)


def minimum_meld_points(score: int) -> int:
    """Return the minimum opening meld requirement for a team score."""

    if score < 1500:
        return 50
    if score < 3000:
        return 90
    if score < 5000:
        return 120
    return 150


def is_black_three(card: CanastaCard) -> bool:
    """Return whether *card* is a black three."""

    return isinstance(card, Card) and card.rank == "3" and card.suit in {Suit.CLUBS, Suit.SPADES}


@dataclass
class CanastaDeck:
    """A deck for Canasta, typically composed of two standard decks plus jokers.

    Attributes:
        cards: A list of ``CanastaCard`` objects in the deck.
    """

    cards: list[CanastaCard] = field(default_factory=list)
    _preseeded: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        """Populate the deck if it wasn't pre-seeded with cards."""
        if self.cards:
            self._preseeded = True
            return
        base_deck = Deck()
        self.cards.extend(base_deck.cards * 2)
        self.cards.extend(JokerCard() for _ in range(4))
        self._preseeded = False

    def shuffle(self, *, rng: Optional[Random] = None) -> None:
        """Shuffle the deck in place."""
        (rng or random).shuffle(self.cards)

    def draw(self) -> CanastaCard:
        """Draw the top card from the deck."""
        if not self.cards:
            raise ValueError("The stock is empty.")
        return self.cards.pop(0)

    def draw_many(self, count: int) -> list[CanastaCard]:
        """Draw a specified number of cards from the deck."""
        if not (0 <= count <= len(self.cards)):
            raise ValueError("Invalid number of cards to draw.")
        drawn = self.cards[:count]
        self.cards = self.cards[count:]
        return drawn

    def remaining(self) -> int:
        """Return the number of cards remaining in the deck."""
        return len(self.cards)

    def copy(self) -> "CanastaDeck":
        """Return a shallow copy of the deck, preserving card order."""
        return CanastaDeck(cards=list(self.cards))


class CanastaGame:
    """The main controller for a game of Canasta.

    This class manages players, teams, the deck, and the overall flow of each
    round, enforcing the rules of the game.
    """

    def __init__(
        self,
        players: Optional[Sequence[CanastaPlayer]] = None,
        *,
        deck: Optional[CanastaDeck] = None,
        rng: Optional[Random] = None,
    ) -> None:
        """Initialize a new Canasta game."""
        self.players = self._initialize_players(players)
        self.teams = self._build_teams(self.players)
        self._custom_deck = deck.copy() if deck else None
        self.deck = self._custom_deck.copy() if self._custom_deck else CanastaDeck()
        self.discard_pile: list[CanastaCard] = []
        self.current_player_index = 0
        self.discard_frozen = False
        self.round_over = False
        self._rng = rng
        self.reset_round()

    def _initialize_players(self, players: Optional[Sequence[CanastaPlayer]]) -> list[CanastaPlayer]:
        """Ensure a standard four-player table if none is provided."""
        if players:
            return list(players)
        default_names = ["North", "East", "South", "West"]
        return [CanastaPlayer(name=name, team_index=i % 2) for i, name in enumerate(default_names)]

    def _build_teams(self, players: Sequence[CanastaPlayer]) -> list[CanastaTeam]:
        """Create partnership teams from the list of players."""
        team0 = [p for p in players if p.team_index == 0]
        team1 = [p for p in players if p.team_index == 1]
        return [
            CanastaTeam(name="Team North/South", players=team0),
            CanastaTeam(name="Team East/West", players=team1),
        ]

    def reset_round(self) -> None:
        """Reset the game state for a new round."""
        self.round_over = False
        for player in self.players:
            player.hand.clear()
        for team in self.teams:
            team.reset_for_round()

        self.deck = self._custom_deck.copy() if self._custom_deck else CanastaDeck()
        self.deck.shuffle(rng=self._rng)

        self._deal_hands()
        self.discard_pile = [self.deck.draw()]
        self.discard_frozen = is_wild(self.discard_pile[-1]) or is_black_three(self.discard_pile[-1])
        self.current_player_index = 0

    def _deal_hands(self) -> None:
        """Deal eleven cards to each player."""
        for player in self.players:
            player.hand.extend(self.deck.draw_many(11))

    def draw(self, player: CanastaPlayer, source: DrawSource = DrawSource.STOCK) -> CanastaCard:
        """Draw a card for a player from the specified source."""
        if self.round_over:
            raise RuntimeError("The round is over.")
        if source == DrawSource.STOCK:
            card = self.deck.draw()
            player.hand.append(card)
            return card

        if not self.discard_pile:
            raise RuntimeError("The discard pile is empty.")
        if not self.can_take_discard(player):
            raise RuntimeError("The player may not take the discard pile.")

        pile = list(self.discard_pile)
        self.discard_pile.clear()
        player.hand.extend(pile)
        self.discard_frozen = False
        return pile[-1]

    def can_take_discard(self, player: CanastaPlayer) -> bool:
        """Check if a player is legally allowed to take the discard pile."""
        if not self.discard_pile:
            return False
        if not self.discard_frozen:
            return True

        top_card = self.discard_pile[-1]
        if is_wild(top_card):
            return False

        rank = top_card.rank if isinstance(top_card, Card) else ""
        natural_matches = [card for card in player.hand if isinstance(card, Card) and not is_wild(card) and card.rank == rank]
        return len(natural_matches) >= 2

    def discard(self, player: CanastaPlayer, card: CanastaCard) -> None:
        """Discard a card from a player's hand."""
        if card not in player.hand:
            raise ValueError("Player does not hold that card.")
        player.hand.remove(card)
        self.discard_pile.append(card)
        if is_wild(card) or is_black_three(card):
            self.discard_frozen = True

    def add_meld(self, player: CanastaPlayer, cards: Sequence[CanastaCard], *, meld_index: Optional[int] = None) -> Meld:
        """Lay down cards as a new meld or extend an existing one."""
        team = self.teams[player.team_index]
        existing = team.melds[meld_index] if meld_index is not None else None

        validation = validate_meld(cards, existing=existing)
        if not validation.is_valid or not validation.meld:
            raise MeldError(validation.message)

        points = sum(card_point_value(card) for card in cards)
        if not team.requirement_met and not existing:
            required = minimum_meld_points(team.score)
            if points < required:
                raise MeldError(f"Opening meld requires {required} points; provided {points}.")
            team.requirement_met = True

        player.remove_cards(cards)
        if existing is None:
            team.melds.append(validation.meld)
        else:
            team.melds[meld_index] = validation.meld
        return validation.meld

    def calculate_team_meld_points(self, team_index: int) -> int:
        """Return the total meld score for a team."""
        return sum(meld.point_value() for meld in self.teams[team_index].melds)

    def calculate_team_deadwood(self, team_index: int) -> int:
        """Return the total deadwood (unmelded cards) value for a team."""
        return sum(card_point_value(card) for player in self.teams[team_index].players for card in player.hand)

    def can_go_out(self, team_index: int) -> bool:
        """Check if a team can legally go out."""
        team = self.teams[team_index]
        return any(meld.is_canasta for meld in team.melds) and all(not p.hand for p in team.players)

    def go_out(self, player: CanastaPlayer, *, concealed: bool = False) -> dict[int, int]:
        """End the round with a player going out."""
        if not self.can_go_out(player.team_index):
            raise RuntimeError("Cannot go out without a canasta and empty hands.")

        bonus = 200 if concealed else 100
        team_points = {i: self.calculate_team_meld_points(i) - self.calculate_team_deadwood(i) for i in range(len(self.teams))}
        team_points[player.team_index] += bonus

        for i, points in team_points.items():
            self.teams[i].score += points

        self.round_over = True
        return team_points

    def advance_turn(self) -> None:
        """Move play to the next player in sequence."""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)


__all__ = [
    "CanastaCard",
    "CanastaDeck",
    "CanastaGame",
    "CanastaPlayer",
    "CanastaTeam",
    "DrawSource",
    "JokerCard",
    "Meld",
    "MeldError",
    "MeldValidation",
    "is_black_three",
    "card_point_value",
    "is_wild",
    "minimum_meld_points",
    "validate_meld",
]
