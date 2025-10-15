"""Comprehensive Gin Rummy engine with realistic round handling and scoring.

This implementation models the complete flow of a two-player Gin Rummy match.
It captures authentic rules including the opening upcard offer, meld detection,
layoff processing, gin/big-gin bonuses, undercuts, and persistent round logs.
Each function includes precise type hints and documentation to promote clarity
and testability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Sequence

from card_games.common.cards import Card, Deck


class MeldType(Enum):
    """Type of meld in Gin Rummy."""

    SET = auto()
    RUN = auto()


class KnockType(Enum):
    """Ways a round of Gin Rummy can conclude."""

    GIN = auto()
    BIG_GIN = auto()
    KNOCK = auto()
    UNDERCUT = auto()


@dataclass(frozen=True)
class Meld:
    """Represents a meld (set or run) in Gin Rummy."""

    meld_type: MeldType
    cards: tuple[Card, ...]


@dataclass(frozen=True)
class HandAnalysis:
    """Optimal meld grouping and deadwood results for a hand."""

    melds: tuple[Meld, ...]
    deadwood_cards: tuple[Card, ...]
    deadwood_total: int


@dataclass(frozen=True)
class RoundSummary:
    """Summary of a completed round with scoring details."""

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
    """Represents a player in Gin Rummy."""

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
    """Main engine for Gin Rummy with realistic rule enforcement."""

    def __init__(self, players: list[GinRummyPlayer], *, rng=None) -> None:
        """Initialize a Gin Rummy game."""

        if len(players) != 2:
            raise ValueError("Gin Rummy requires exactly 2 players")
        self.players = players
        self.rng = rng
        self.deck = Deck()
        self.discard_pile: list[Card] = []
        self.dealer_idx = len(players) - 1
        self.current_player_idx = 0
        self.round_history: list[RoundSummary] = []
        self.turn_log: list[str] = []
        self.initial_offer_order: list[int] = []
        self.initial_offer_position = 0
        self.initial_upcard_phase = False
        self.current_turn_draw: Card | None = None
        self.current_turn_source: str | None = None
        self.last_discarded_card: Card | None = None
        self.last_discarder_idx: int | None = None
        self.blocked_discard_card = None

    def _shuffle_deck(self) -> None:
        """Shuffle the deck respecting deterministic RNG if provided."""

        if self.rng is not None:
            self.deck.shuffle(rng=self.rng)
        else:
            self.deck.shuffle()

    def deal_cards(self) -> None:
        """Deal a fresh round and prepare the opening upcard offer."""

        self.dealer_idx = (self.dealer_idx + 1) % len(self.players)
        self.deck = Deck()
        self._shuffle_deck()

        for player in self.players:
            player.hand.clear()

        for _ in range(10):
            for offset in range(len(self.players)):
                target = (self.dealer_idx + 1 + offset) % len(self.players)
                self.players[target].hand.append(self.deck.deal(1)[0])

        self.discard_pile = [self.deck.deal(1)[0]]
        for player in self.players:
            player.hand.sort(key=lambda c: (c.suit.value, c.value))

        self.turn_log = []
        self.initial_offer_order = [
            (self.dealer_idx + 1) % len(self.players),
            self.dealer_idx,
        ]
        self.initial_offer_position = 0
        self.initial_upcard_phase = True
        self.current_player_idx = self.initial_offer_order[0]
        self.current_turn_draw = None
        self.current_turn_source = None
        self.last_discarded_card = None
        self.last_discarder_idx = None
        self.blocked_discard_card = None

    def can_take_initial_upcard(self, player_idx: int) -> bool:
        """Return True if ``player_idx`` is entitled to the face-up upcard."""

        if not self.initial_upcard_phase:
            return False
        if self.initial_offer_position >= len(self.initial_offer_order):
            return False
        return self.initial_offer_order[self.initial_offer_position] == player_idx

    def take_initial_upcard(self, player_idx: int) -> Card:
        """Allow ``player_idx`` to accept the face-up upcard."""

        if not self.can_take_initial_upcard(player_idx):
            raise RuntimeError("Player cannot take the initial upcard at this time")
        card = self.draw_from_discard()
        self.players[player_idx].hand.append(card)
        self.players[player_idx].hand.sort(key=lambda c: (c.suit.value, c.value))
        self.initial_upcard_phase = False
        self.current_player_idx = player_idx
        self.current_turn_draw = card
        self.current_turn_source = "discard"
        self.blocked_discard_card = None
        self.turn_log.append(f"{self.players[player_idx].name} accepts the upcard {card}")
        return card

    def pass_initial_upcard(self, player_idx: int) -> None:
        """Record that ``player_idx`` declines the opening upcard."""

        if not self.can_take_initial_upcard(player_idx):
            raise RuntimeError("Player cannot decline the upcard right now")
        self.turn_log.append(f"{self.players[player_idx].name} passes on the upcard")
        self.initial_offer_position += 1
        if self.initial_offer_position >= len(self.initial_offer_order):
            self.initial_upcard_phase = False
            self.current_player_idx = self.initial_offer_order[0]
            self.blocked_discard_card = self.discard_pile[-1]
        else:
            self.current_player_idx = self.initial_offer_order[self.initial_offer_position]

    def _reshuffle_from_discard(self) -> None:
        """Recycle the discard pile (minus top card) back into the stock."""

        if len(self.discard_pile) <= 1:
            raise RuntimeError("Cannot reshuffle with fewer than two cards in the discard pile")
        top_card = self.discard_pile.pop()
        self.deck.cards = list(self.discard_pile)
        self.discard_pile = [top_card]
        self._shuffle_deck()

    def draw_from_stock(self) -> Card:
        """Draw a card from stock, reshuffling if necessary."""

        if not self.deck.cards:
            self._reshuffle_from_discard()
        card = self.deck.deal(1)[0]
        self.current_turn_draw = card
        self.current_turn_source = "stock"
        self.blocked_discard_card = None
        self.turn_log.append(f"{self.players[self.current_player_idx].name} draws from stock")
        return card

    def can_draw_from_discard(self, player_idx: int) -> bool:
        """Return whether ``player_idx`` may draw the top discard."""

        if not self.discard_pile:
            return False
        if self.initial_upcard_phase:
            return self.can_take_initial_upcard(player_idx)
        if self.blocked_discard_card is not None and self.discard_pile[-1] == self.blocked_discard_card:
            return False
        if self.last_discarder_idx == player_idx and self.discard_pile[-1] == self.last_discarded_card:
            return False
        return True

    def draw_from_discard(self) -> Card:
        """Draw the top card from the discard pile."""

        if not self.discard_pile:
            raise RuntimeError("Discard pile is empty")
        if self.blocked_discard_card is not None and self.discard_pile[-1] == self.blocked_discard_card:
            raise RuntimeError("The passed opening upcard cannot be drawn yet")
        card = self.discard_pile.pop()
        self.current_turn_draw = card
        self.current_turn_source = "discard"
        self.blocked_discard_card = None
        self.turn_log.append(f"{self.players[self.current_player_idx].name} draws {card} from discard")
        return card

    def discard(self, player_idx: int, card: Card) -> None:
        """Discard ``card`` from the player's hand, enforcing discard rules."""

        if card not in self.players[player_idx].hand:
            raise ValueError("Card not in player's hand")
        if self.current_turn_source == "discard" and self.current_turn_draw == card:
            raise ValueError("Cannot discard the card just drawn from the discard pile")
        self.players[player_idx].hand.remove(card)
        self.discard_pile.append(card)
        self.last_discarded_card = card
        self.last_discarder_idx = player_idx
        self.blocked_discard_card = None
        self.turn_log.append(f"{self.players[player_idx].name} discards {card}")
        self.current_turn_draw = None
        self.current_turn_source = None
        self.current_player_idx = (player_idx + 1) % len(self.players)

    def analyze_hand(self, cards: Sequence[Card]) -> HandAnalysis:
        """Return the optimal meld/deadwood analysis for ``cards``."""

        return _best_meld_plan(cards)

    def find_melds(self, cards: Sequence[Card]) -> list[Meld]:
        """Return all unique melds that can be formed from ``cards``."""

        seen: set[tuple] = set()
        melds: list[Meld] = []
        for meld in _generate_melds(cards):
            signature = (
                meld.meld_type,
                tuple((card.rank, card.suit.value) for card in meld.cards),
            )
            if signature not in seen:
                seen.add(signature)
                melds.append(meld)
        return melds

    def calculate_deadwood(self, player: GinRummyPlayer) -> int:
        """Calculate deadwood points for ``player``."""

        return self.analyze_hand(player.hand).deadwood_total

    def can_knock(self, player: GinRummyPlayer) -> bool:
        """Check if ``player`` can knock (deadwood <= 10)."""

        return self.calculate_deadwood(player) <= 10

    def has_gin(self, player: GinRummyPlayer) -> bool:
        """Check if ``player`` has gin (no deadwood)."""

        return self.calculate_deadwood(player) == 0

    def _score_round(self, knocker: GinRummyPlayer, opponent: GinRummyPlayer) -> RoundSummary:
        """Compute round scoring data without mutating player scores."""

        knocker_analysis = self.analyze_hand(knocker.hand)
        opponent_analysis = self.analyze_hand(opponent.hand)

        knocker_deadwood = knocker_analysis.deadwood_total
        opponent_initial_deadwood = opponent_analysis.deadwood_total

        layoff_cards: tuple[Card, ...]
        opponent_deadwood_cards: tuple[Card, ...]
        knock_type: KnockType

        if knocker_deadwood == 0:
            knock_type = KnockType.BIG_GIN if len(knocker.hand) == 11 else KnockType.GIN
            opponent_deadwood_cards = opponent_analysis.deadwood_cards
            layoff_cards = tuple()
            opponent_deadwood = sum(_deadwood_value(card) for card in opponent_deadwood_cards)
        else:
            remaining, layoff = _apply_layoffs(opponent_analysis.deadwood_cards, knocker_analysis.melds)
            opponent_deadwood = sum(_deadwood_value(card) for card in remaining)
            layoff_cards = layoff
            opponent_deadwood_cards = remaining
            if opponent_deadwood <= knocker_deadwood:
                knock_type = KnockType.UNDERCUT
            else:
                knock_type = KnockType.KNOCK

        points = {knocker.name: 0, opponent.name: 0}
        if knock_type == KnockType.GIN:
            points[knocker.name] = opponent_deadwood + 25
        elif knock_type == KnockType.BIG_GIN:
            points[knocker.name] = opponent_deadwood + 31
        elif knock_type == KnockType.UNDERCUT:
            points[opponent.name] = (knocker_deadwood - opponent_deadwood) + 25
        else:
            points[knocker.name] = opponent_deadwood - knocker_deadwood

        summary = RoundSummary(
            dealer=self.players[self.dealer_idx].name,
            knocker=knocker.name,
            opponent=opponent.name,
            knock_type=knock_type,
            knocker_deadwood=knocker_deadwood,
            opponent_deadwood=opponent_deadwood,
            opponent_initial_deadwood=opponent_initial_deadwood,
            melds_shown=knocker_analysis.melds,
            layoff_cards=layoff_cards,
            points_awarded=points,
        )
        return summary

    def calculate_round_summary(self, knocker: GinRummyPlayer, opponent: GinRummyPlayer) -> RoundSummary:
        """Return a :class:`RoundSummary` for the finished round."""

        summary = self._score_round(knocker, opponent)
        self.round_history.append(summary)
        return summary

    def calculate_round_score(self, knocker: GinRummyPlayer, opponent: GinRummyPlayer) -> RoundSummary:
        """Calculate scores for the round and record the summary."""

        return self.calculate_round_summary(knocker, opponent)

    def record_points(self, summary: RoundSummary) -> None:
        """Apply ``summary`` scores to the running totals."""

        for player in self.players:
            player.score += summary.points_awarded.get(player.name, 0)

    def is_game_over(self, target_score: int = 100) -> bool:
        """Check if game is over."""

        return any(player.score >= target_score for player in self.players)

    def get_winner(self) -> GinRummyPlayer:
        """Get the winner."""

        return max(self.players, key=lambda p: p.score)

    def should_draw_discard(self, player: GinRummyPlayer, top_card: Card) -> bool:
        """Heuristic for whether the AI should draw the top discard card."""

        current = self.analyze_hand(player.hand)
        improved = self.analyze_hand(list(player.hand) + [top_card])
        if improved.deadwood_total < current.deadwood_total:
            return True
        ranks_in_hand = {card.rank for card in player.hand}
        if top_card.rank in ranks_in_hand:
            return True
        suit_neighbors = {card.value for card in player.hand if card.suit == top_card.suit}
        return (top_card.value - 1 in suit_neighbors) or (top_card.value + 1 in suit_neighbors)

    def suggest_discard(self, player: GinRummyPlayer) -> Card:
        """AI logic to suggest a card to discard."""

        analysis = self.analyze_hand(player.hand)
        if analysis.deadwood_cards:

            def priority(card: Card) -> tuple[int, int, int]:
                value = _deadwood_value(card)
                same_rank = sum(1 for c in player.hand if c.rank == card.rank)
                suit_neighbors = sum(1 for c in player.hand if c.suit == card.suit and abs(c.value - card.value) == 1)
                return (value, -same_rank, -suit_neighbors)

            return max(analysis.deadwood_cards, key=priority)

        return min(player.hand, key=lambda c: (c.suit.value, c.value))
