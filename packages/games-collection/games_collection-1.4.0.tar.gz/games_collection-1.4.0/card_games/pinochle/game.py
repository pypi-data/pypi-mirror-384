"""Game engine for partnership double-deck Pinochle."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from card_games.common.cards import Card, Deck, Suit, format_cards

PINOCHLE_RANKS: Tuple[str, ...] = ("A", "T", "K", "Q", "J", "9")
TRICK_STRENGTH: Dict[str, int] = {"9": 0, "J": 1, "Q": 2, "K": 3, "T": 4, "A": 5}
CARD_POINT_VALUES: Dict[str, int] = {"A": 11, "T": 10, "K": 4, "Q": 3, "J": 2, "9": 0}

MELD_SCORES: Dict[str, int] = {
    "run": 150,
    "double_run": 1500,
    "trump_marriage": 40,
    "offsuit_marriage": 20,
    "pinochle": 40,
    "double_pinochle": 300,
    "aces_around": 100,
    "kings_around": 80,
    "queens_around": 60,
    "jacks_around": 40,
    "dix": 10,
}


class DoubleDeckPinochleDeck(Deck):
    """Deck containing two standard Pinochle decks (96 cards)."""

    def __post_init__(self) -> None:
        self.cards = []
        for _ in range(2):
            for suit in Suit:
                for rank in PINOCHLE_RANKS:
                    # Each Pinochle deck has two copies of every rank per suit.
                    self.cards.append(Card(rank, suit))
                    self.cards.append(Card(rank, suit))


@dataclass
class PinochlePlayer:
    """Representation of a player participating in the game."""

    name: str
    hand: List[Card] = field(default_factory=list)
    bid: Optional[int] = None
    passed: bool = False
    meld_points: int = 0
    trick_points: int = 0
    team_index: int = 0
    is_ai: bool = False
    total_score: int = 0

    def reset_for_round(self) -> None:
        """Clear round-specific state."""
        self.hand = []
        self.bid = None
        self.passed = False
        self.meld_points = 0
        self.trick_points = 0

    def remove_card(self, card: Card) -> None:
        """Remove ``card`` from the player's hand."""
        self.hand.remove(card)

    def has_suit(self, suit: Suit) -> bool:
        """Return ``True`` if the player can follow ``suit``."""
        return any(card.suit == suit for card in self.hand)


class BiddingPhase:
    """Coordinator for the bidding phase of a Pinochle round."""

    def __init__(self, players: List[PinochlePlayer], dealer_index: int, *, min_bid: int = 250) -> None:
        self.players = players
        self.dealer_index = dealer_index
        self.min_bid = min_bid
        self.current_index = (dealer_index + 1) % len(players)
        self.high_bid: Optional[int] = None
        self.high_bidder: Optional[PinochlePlayer] = None
        self.history: List[Tuple[str, str]] = []
        self.passes_in_row = 0

    @property
    def finished(self) -> bool:
        """Return ``True`` when only one player remains in the auction."""
        active_players = sum(1 for player in self.players if not player.passed)
        return active_players <= 1 and self.high_bidder is not None

    def current_player(self) -> PinochlePlayer:
        return self.players[self.current_index]

    def advance(self) -> None:
        self.current_index = (self.current_index + 1) % len(self.players)

    def place_bid(self, value: Optional[int]) -> None:
        """Register a bid for the current player."""
        player = self.current_player()
        if value is None:
            player.passed = True
            self.history.append((player.name, "pass"))
            self.passes_in_row += 1
        else:
            if value < self.min_bid:
                raise ValueError(f"Minimum bid is {self.min_bid}")
            if self.high_bid is not None and value <= self.high_bid:
                raise ValueError("Bid must exceed current high bid")
            player.bid = value
            player.passed = False
            self.high_bid = value
            self.high_bidder = player
            self.history.append((player.name, str(value)))
            self.passes_in_row = 0
        self.advance()


class MeldPhase:
    """Calculate meld points for players."""

    def __init__(self, trump: Suit) -> None:
        self.trump = trump

    def score_hand(self, hand: Iterable[Card]) -> Tuple[int, Dict[str, int]]:
        """Return meld score and a breakdown for ``hand``."""
        counts: Dict[Suit, Counter[str]] = {suit: Counter() for suit in Suit}
        for card in hand:
            counts[card.suit][card.rank] += 1

        breakdown: Dict[str, int] = defaultdict(int)
        score = 0

        # Arounds (aces, kings, queens, jacks)
        around_ranks = {
            "A": "aces_around",
            "K": "kings_around",
            "Q": "queens_around",
            "J": "jacks_around",
        }
        for rank, key in around_ranks.items():
            sets = min(counts[suit][rank] for suit in Suit)
            if sets:
                points = sets * MELD_SCORES[key]
                breakdown[key] += points
                score += points

        # Pinochle (Q♠ J♦)
        pinochle_pairs = min(counts[Suit.SPADES]["Q"], counts[Suit.DIAMONDS]["J"])
        if pinochle_pairs >= 2:
            breakdown["double_pinochle"] += MELD_SCORES["double_pinochle"]
            score += MELD_SCORES["double_pinochle"]
            pinochle_pairs -= 2
        if pinochle_pairs > 0:
            points = pinochle_pairs * MELD_SCORES["pinochle"]
            breakdown["pinochle"] += points
            score += points

        mutable_counts: Dict[Suit, Counter[str]] = {suit: Counter(counter) for suit, counter in counts.items()}

        # Runs in trump
        run_ranks = ("A", "T", "K", "Q", "J")
        run_count = min(mutable_counts[self.trump][rank] for rank in run_ranks)
        while run_count >= 2:
            breakdown["double_run"] += MELD_SCORES["double_run"]
            score += MELD_SCORES["double_run"]
            for rank in run_ranks:
                mutable_counts[self.trump][rank] -= 2
            run_count -= 2
        if run_count == 1:
            breakdown["run"] += MELD_SCORES["run"]
            score += MELD_SCORES["run"]
            for rank in run_ranks:
                mutable_counts[self.trump][rank] -= 1

        # Marriages
        for suit in Suit:
            marriage_count = min(mutable_counts[suit]["K"], mutable_counts[suit]["Q"])
            if marriage_count:
                key = "trump_marriage" if suit == self.trump else "offsuit_marriage"
                points = marriage_count * MELD_SCORES[key]
                breakdown[key] += points
                score += points
                mutable_counts[suit]["K"] -= marriage_count
                mutable_counts[suit]["Q"] -= marriage_count

        # Dix (9 of trump)
        dix_count = mutable_counts[self.trump]["9"]
        if dix_count:
            points = dix_count * MELD_SCORES["dix"]
            breakdown["dix"] += points
            score += points

        return score, dict(breakdown)


class PinochleGame:
    """Engine orchestrating double-deck Pinochle rounds."""

    def __init__(
        self,
        players: List[PinochlePlayer],
        *,
        min_bid: int = 250,
        target_score: int = 1500,
        rng=None,
    ) -> None:
        if len(players) != 4:
            raise ValueError("Pinochle requires exactly four players")
        self.players = players
        for index, player in enumerate(self.players):
            player.team_index = 0 if index % 2 == 0 else 1
        self.min_bid = min_bid
        self.target_score = target_score
        self.rng = rng
        self.deck = DoubleDeckPinochleDeck()
        self.dealer_index = 0
        self.bidding_phase: Optional[BiddingPhase] = None
        self.meld_phase: Optional[MeldPhase] = None
        self.trump: Optional[Suit] = None
        self.current_trick: List[Tuple[PinochlePlayer, Card]] = []
        self.trick_history: List[List[Tuple[PinochlePlayer, Card]]] = []
        self.bidding_history: List[Tuple[str, str]] = []
        self.meld_breakdowns: Dict[str, Dict[str, int]] = {}
        self.partnership_scores = [0, 0]
        self.current_player_index: Optional[int] = None
        self.lead_suit: Optional[Suit] = None
        self.last_trick_winner: Optional[PinochlePlayer] = None

    def shuffle_and_deal(self) -> None:
        """Shuffle the deck and deal 24 cards to each player."""
        self.deck = DoubleDeckPinochleDeck()
        if self.rng is not None:
            self.deck.shuffle(rng=self.rng)
        else:
            self.deck.shuffle()
        for player in self.players:
            player.reset_for_round()
        for _ in range(24):
            for player in self.players:
                player.hand.extend(self.deck.deal(1))
        for player in self.players:
            player.hand.sort(key=lambda c: (c.suit.value, TRICK_STRENGTH[c.rank]), reverse=True)
        self.current_trick = []
        self.trick_history = []
        self.bidding_history = []
        self.meld_breakdowns = {}
        self.trump = None
        self.lead_suit = None
        self.last_trick_winner = None
        self.current_player_index = None

    def start_bidding(self) -> None:
        self.bidding_phase = BiddingPhase(self.players, self.dealer_index, min_bid=self.min_bid)
        self.current_player_index = self.bidding_phase.current_index

    def place_bid(self, value: Optional[int]) -> None:
        if not self.bidding_phase:
            raise RuntimeError("Bidding has not started")
        self.bidding_phase.place_bid(value)
        self.current_player_index = self.bidding_phase.current_index
        self.bidding_history = list(self.bidding_phase.history)
        if self.bidding_phase.finished:
            self.trump = None
            self.meld_phase = None

    def set_trump(self, suit: Suit) -> None:
        if not self.bidding_phase or not self.bidding_phase.finished:
            raise RuntimeError("Trump may only be selected after bidding")
        if self.bidding_phase.high_bidder is None:
            raise RuntimeError("No winning bidder")
        self.trump = suit
        self.meld_phase = MeldPhase(suit)
        self.current_player_index = self.players.index(self.bidding_phase.high_bidder)

    def score_melds(self) -> None:
        if not self.meld_phase:
            raise RuntimeError("Meld phase has not started")
        for player in self.players:
            score, breakdown = self.meld_phase.score_hand(player.hand)
            player.meld_points = score
            self.meld_breakdowns[player.name] = breakdown

    def is_valid_play(self, player: PinochlePlayer, card: Card) -> bool:
        if self.current_player_index is None:
            return False
        if self.players[self.current_player_index] is not player:
            return False
        if card not in player.hand:
            return False
        if not self.current_trick:
            return True
        lead_suit = self.lead_suit
        if lead_suit and player.has_suit(lead_suit):
            return card.suit == lead_suit
        return True

    def play_card(self, card: Card) -> None:
        if self.current_player_index is None:
            raise RuntimeError("Round has not started")
        player = self.players[self.current_player_index]
        if not self.is_valid_play(player, card):
            raise ValueError("Illegal play")
        player.remove_card(card)
        self.current_trick.append((player, card))
        if len(self.current_trick) == 1:
            self.lead_suit = card.suit
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def _card_strength(self, card: Card) -> int:
        lead_bonus = 10 if self.lead_suit and card.suit == self.lead_suit else 0
        trump_bonus = 100 if self.trump and card.suit == self.trump else 0
        return trump_bonus + lead_bonus + TRICK_STRENGTH[card.rank]

    def complete_trick(self) -> PinochlePlayer:
        if len(self.current_trick) != len(self.players):
            raise RuntimeError("Trick is not complete")
        ranked: List[Tuple[int, int, PinochlePlayer, Card]] = []
        for order, (player, card) in enumerate(self.current_trick):
            ranked.append((self._card_strength(card), -order, player, card))
        ranked.sort(reverse=True)
        _, _, winner, _ = ranked[0]
        trick_points = sum(CARD_POINT_VALUES[card.rank] for _, card in self.current_trick)
        winner.trick_points += trick_points
        self.trick_history.append(list(self.current_trick))
        self.current_trick = []
        self.current_player_index = self.players.index(winner)
        self.lead_suit = None
        self.last_trick_winner = winner
        return winner

    def score_tricks(self) -> None:
        if self.last_trick_winner:
            self.last_trick_winner.trick_points += 10  # last trick bonus

    def partnership_totals(self) -> Dict[int, Dict[str, int]]:
        totals: Dict[int, Dict[str, int]] = {0: {"meld": 0, "tricks": 0}, 1: {"meld": 0, "tricks": 0}}
        for player in self.players:
            totals[player.team_index]["meld"] += player.meld_points
            totals[player.team_index]["tricks"] += player.trick_points
        for team in totals.values():
            team["total"] = team["meld"] + team["tricks"]
        return totals

    def resolve_round(self) -> Dict[int, Dict[str, int]]:
        if not self.bidding_phase or not self.bidding_phase.finished:
            raise RuntimeError("Bidding is incomplete")
        if self.trump is None:
            raise RuntimeError("Trump suit not selected")
        self.score_tricks()
        totals = self.partnership_totals()
        bidding_team = self.bidding_phase.high_bidder.team_index if self.bidding_phase.high_bidder else 0
        bid_value = self.bidding_phase.high_bid if self.bidding_phase.high_bid else self.min_bid
        for team_index, team_scores in totals.items():
            if team_index == bidding_team:
                if team_scores["total"] >= bid_value:
                    self.partnership_scores[team_index] += team_scores["total"]
                else:
                    self.partnership_scores[team_index] -= bid_value
            else:
                self.partnership_scores[team_index] += team_scores["total"]
        for player in self.players:
            player.total_score = self.partnership_scores[player.team_index]
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        return totals

    def format_trick(self, trick: Iterable[Tuple[PinochlePlayer, Card]]) -> str:
        """Return a human readable representation of a trick."""
        parts = [f"{player.name}: {format_cards([card])}" for player, card in trick]
        return ", ".join(parts)


__all__ = [
    "BiddingPhase",
    "MeldPhase",
    "PinochleGame",
    "PinochlePlayer",
    "MELD_SCORES",
]
