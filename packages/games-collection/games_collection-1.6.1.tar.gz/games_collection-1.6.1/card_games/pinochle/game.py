"""Game engine for partnership double-deck Pinochle.

This module provides the core classes and logic for playing a game of
double-deck partnership Pinochle, including bidding, melding, and trick-taking.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from random import Random
from typing import Dict, Iterable, List, Optional, Tuple

from card_games.common.cards import Card, Deck, Suit, format_cards

# Constants for Pinochle card ranks, trick strength, and point values.
PINOCHLE_RANKS: Tuple[str, ...] = ("A", "T", "K", "Q", "J", "9")
TRICK_STRENGTH: Dict[str, int] = {"9": 0, "J": 1, "Q": 2, "K": 3, "T": 4, "A": 5}
CARD_POINT_VALUES: Dict[str, int] = {"A": 11, "T": 10, "K": 4, "Q": 3, "J": 2, "9": 0}

# Standard scores for different meld combinations.
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
    """A deck for Pinochle, containing two standard Pinochle decks (96 cards)."""

    def __post_init__(self) -> None:
        """Initialize the deck with two copies of each Pinochle card."""
        self.cards = []
        for _ in range(2):  # Two decks
            for suit in Suit:
                for rank in PINOCHLE_RANKS:
                    # Two copies of each card per rank and suit in a Pinochle deck.
                    self.cards.extend([Card(rank, suit), Card(rank, suit)])


@dataclass
class PinochlePlayer:
    """Represents a player in a game of Pinochle.

    Attributes:
        name: The player's name.
        hand: A list of cards in the player's hand.
        bid: The player's current bid.
        passed: True if the player has passed in the current bidding round.
        meld_points: Points scored from melds in the current round.
        trick_points: Points scored from tricks in the current round.
        team_index: The index of the team this player belongs to.
        is_ai: True if the player is controlled by an AI.
        total_score: The player's total score across all rounds.
    """

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
        """Reset the player's state for a new round."""
        self.hand.clear()
        self.bid = None
        self.passed = False
        self.meld_points = 0
        self.trick_points = 0

    def remove_card(self, card: Card) -> None:
        """Remove a specific card from the player's hand."""
        self.hand.remove(card)

    def has_suit(self, suit: Suit) -> bool:
        """Check if the player has any cards of a given suit."""
        return any(c.suit == suit for c in self.hand)


class BiddingPhase:
    """Manages the bidding phase of a Pinochle round."""

    def __init__(self, players: List[PinochlePlayer], dealer_index: int, *, min_bid: int = 250) -> None:
        """Initialize the bidding phase."""
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
        """Return True when only one player remains in the auction."""
        return sum(1 for p in self.players if not p.passed) <= 1 and self.high_bidder is not None

    def current_player(self) -> PinochlePlayer:
        """Return the player whose turn it is to bid."""
        return self.players[self.current_index]

    def advance(self) -> None:
        """Advance the turn to the next player."""
        self.current_index = (self.current_index + 1) % len(self.players)

    def place_bid(self, value: Optional[int]) -> None:
        """Register a bid or a pass for the current player."""
        player = self.current_player()
        if value is None:
            player.passed = True
            self.history.append((player.name, "pass"))
            self.passes_in_row += 1
        else:
            if value < self.min_bid:
                raise ValueError(f"The minimum bid is {self.min_bid}.")
            if self.high_bid is not None and value <= self.high_bid:
                raise ValueError("A new bid must exceed the current high bid.")
            player.bid = value
            self.high_bid = value
            self.high_bidder = player
            self.history.append((player.name, str(value)))
            self.passes_in_row = 0
        self.advance()


class MeldPhase:
    """Calculates meld points for players' hands."""

    def __init__(self, trump: Suit) -> None:
        """Initialize the meld phase with the declared trump suit."""
        self.trump = trump

    def score_hand(self, hand: Iterable[Card]) -> Tuple[int, Dict[str, int]]:
        """Return the total meld score and a breakdown of melds for a hand."""
        counts = {s: Counter(c.rank for c in hand if c.suit == s) for s in Suit}
        score, breakdown = 0, defaultdict(int)

        # Score "arounds" (e.g., aces around, kings around).
        for rank, key in {"A": "aces", "K": "kings", "Q": "queens", "J": "jacks"}.items():
            if sets := min(counts[s][rank] for s in Suit):
                points = sets * MELD_SCORES[f"{key}_around"]
                breakdown[f"{key}_around"] += points
                score += points

        # Score Pinochles.
        if pinochles := min(counts[Suit.SPADES].get("Q", 0), counts[Suit.DIAMONDS].get("J", 0)):
            doubles = pinochles // 2
            singles = pinochles % 2
            if doubles > 0:
                breakdown["double_pinochle"] += doubles * MELD_SCORES["double_pinochle"]
                score += doubles * MELD_SCORES["double_pinochle"]
            if singles > 0:
                breakdown["pinochle"] += singles * MELD_SCORES["pinochle"]
                score += singles * MELD_SCORES["pinochle"]

        # Score runs, marriages, and dix.
        if self.trump:
            # Dix (9 of trump)
            dix_count = counts[self.trump].get("9", 0)
            if dix_count > 0:
                breakdown["dix"] += MELD_SCORES["dix"] * dix_count
                score += MELD_SCORES["dix"] * dix_count

            # Run (A, T, K, Q, J of trump)
            run_ranks = {"A", "T", "K", "Q", "J"}
            num_runs = min(counts[self.trump].get(r, 0) for r in run_ranks)

            if num_runs > 0:
                if num_runs >= 2:
                    breakdown["double_run"] += MELD_SCORES["double_run"]
                    score += MELD_SCORES["double_run"]
                else:
                    breakdown["run"] += MELD_SCORES["run"]
                    score += MELD_SCORES["run"]

            # Marriages (K, Q of same suit)
            for suit in Suit:
                marriages = min(counts[suit].get("K", 0), counts[suit].get("Q", 0))
                if marriages > 0:
                    is_trump_suit = suit == self.trump
                    # A run already includes the trump marriage. Avoid double-counting.
                    if is_trump_suit and num_runs > 0:
                        continue

                    key = "trump_marriage" if is_trump_suit else "offsuit_marriage"
                    breakdown[key] += marriages * MELD_SCORES[key]
                    score += marriages * MELD_SCORES[key]

        return score, dict(breakdown)


class PinochleGame:
    """The main engine for orchestrating rounds of double-deck Pinochle."""

    def __init__(
        self,
        players: List[PinochlePlayer],
        *,
        min_bid: int = 250,
        target_score: int = 1500,
        rng: Optional[Random] = None,
    ) -> None:
        """Initialize a new Pinochle game."""
        if len(players) != 4:
            raise ValueError("Pinochle requires exactly four players.")
        self.players = players
        for i, p in enumerate(self.players):
            p.team_index = i % 2
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
        if self.rng:
            self.deck.shuffle(rng=self.rng)
        else:
            self.deck.shuffle()

        for p in self.players:
            p.reset_for_round()
            p.hand = self.deck.deal(24)
            p.hand.sort(key=lambda c: (c.suit.value, TRICK_STRENGTH[c.rank]), reverse=True)

        self.current_trick.clear()
        self.trick_history.clear()
        self.bidding_history.clear()
        self.meld_breakdowns.clear()
        self.trump = None
        self.lead_suit = None
        self.last_trick_winner = None
        self.current_player_index = None

    def start_bidding(self) -> None:
        """Start the bidding phase of the round."""
        self.bidding_phase = BiddingPhase(self.players, self.dealer_index, min_bid=self.min_bid)
        self.current_player_index = self.bidding_phase.current_index

    def place_bid(self, value: Optional[int]) -> None:
        """Place a bid for the current player."""
        if not self.bidding_phase:
            raise RuntimeError("Bidding has not started.")
        self.bidding_phase.place_bid(value)
        self.current_player_index = self.bidding_phase.current_index
        self.bidding_history = list(self.bidding_phase.history)
        if self.bidding_phase.finished:
            self.trump = None
            self.meld_phase = None

    def set_trump(self, suit: Suit) -> None:
        """Set the trump suit for the round."""
        if not self.bidding_phase or not self.bidding_phase.finished:
            raise RuntimeError("Trump can only be selected after bidding is complete.")
        if self.bidding_phase.high_bidder is None:
            raise RuntimeError("There is no winning bidder to set trump.")
        self.trump = suit
        self.meld_phase = MeldPhase(suit)
        self.current_player_index = self.players.index(self.bidding_phase.high_bidder)

    def score_melds(self) -> None:
        """Calculate and store meld points for all players."""
        if not self.meld_phase:
            raise RuntimeError("Meld phase has not been initialized.")
        for player in self.players:
            score, breakdown = self.meld_phase.score_hand(player.hand)
            player.meld_points = score
            self.meld_breakdowns[player.name] = breakdown

    def is_valid_play(self, player: PinochlePlayer, card: Card) -> bool:
        """Check if a card is a valid play for the current player."""
        if self.current_player_index is None or self.players[self.current_player_index] is not player:
            return False
        if card not in player.hand:
            return False
        if not self.current_trick or not self.lead_suit:
            return True
        if player.has_suit(self.lead_suit):
            return card.suit == self.lead_suit
        return True

    def play_card(self, card: Card) -> None:
        """Play a card into the current trick."""
        if self.current_player_index is None:
            raise RuntimeError("The round has not started.")
        player = self.players[self.current_player_index]
        if not self.is_valid_play(player, card):
            raise ValueError("This is an illegal play.")
        player.remove_card(card)
        self.current_trick.append((player, card))
        if len(self.current_trick) == 1:
            self.lead_suit = card.suit
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def _card_strength(self, card: Card) -> int:
        """Calculate the strength of a card for trick-taking purposes."""
        trump_bonus = 100 if self.trump and card.suit == self.trump else 0
        lead_bonus = 10 if self.lead_suit and card.suit == self.lead_suit else 0
        return trump_bonus + lead_bonus + TRICK_STRENGTH.get(card.rank, 0)

    def complete_trick(self) -> PinochlePlayer:
        """Complete the current trick, determine the winner, and award points."""
        if len(self.current_trick) != len(self.players):
            raise RuntimeError("The trick is not yet complete.")

        winner, _ = max(self.current_trick, key=lambda item: self._card_strength(item[1]))
        trick_points = sum(CARD_POINT_VALUES[c.rank] for _, c in self.current_trick)
        winner.trick_points += trick_points

        self.trick_history.append(list(self.current_trick))
        self.current_trick.clear()
        self.current_player_index = self.players.index(winner)
        self.lead_suit = None
        self.last_trick_winner = winner
        return winner

    def score_tricks(self) -> None:
        """Award a bonus for winning the last trick of the round."""
        if self.last_trick_winner:
            self.last_trick_winner.trick_points += 10

    def partnership_totals(self) -> Dict[int, Dict[str, int]]:
        """Calculate the total meld and trick points for each partnership."""
        totals: Dict[int, Dict[str, int]] = {0: defaultdict(int), 1: defaultdict(int)}
        for p in self.players:
            totals[p.team_index]["meld"] += p.meld_points
            totals[p.team_index]["tricks"] += p.trick_points
        for team_scores in totals.values():
            team_scores["total"] = team_scores["meld"] + team_scores["tricks"]
        return totals

    def resolve_round(self) -> Dict[int, Dict[str, int]]:
        """Resolve the scores for the round and update the total partnership scores."""
        if not self.bidding_phase or not self.bidding_phase.finished or not self.trump:
            raise RuntimeError("The round is not ready to be resolved.")

        self.score_tricks()
        totals = self.partnership_totals()
        bidding_team = self.bidding_phase.high_bidder.team_index if self.bidding_phase.high_bidder else 0
        bid_value = self.bidding_phase.high_bid or self.min_bid

        for team_index, team_scores in totals.items():
            if team_index == bidding_team:
                if team_scores["total"] >= bid_value:
                    self.partnership_scores[team_index] += team_scores["total"]
                else:
                    self.partnership_scores[team_index] -= bid_value
            else:
                self.partnership_scores[team_index] += team_scores["total"]

        for p in self.players:
            p.total_score = self.partnership_scores[p.team_index]

        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        return totals

    def format_trick(self, trick: Iterable[Tuple[PinochlePlayer, Card]]) -> str:
        """Return a human-readable representation of a trick."""
        return ", ".join(f"{p.name}: {format_cards([c])}" for p, c in trick)


__all__ = [
    "BiddingPhase",
    "MeldPhase",
    "PinochleGame",
    "PinochlePlayer",
    "MELD_SCORES",
]
