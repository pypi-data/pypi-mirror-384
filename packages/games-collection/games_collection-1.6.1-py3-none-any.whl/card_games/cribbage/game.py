"""Cribbage card game engine.

This module implements the classic two-player Cribbage card game, featuring:
- The Deal: Each player gets 6 cards and discards 2 to the crib.
- The Play (Pegging): Players alternate playing cards, scoring for pairs, runs, and 15s.
- The Show: Both hands and the crib are scored for combinations.
- The first player to reach 121 points wins.

Core Rules:
- A standard 52-card deck is used.
- Card values for pegging: Ace=1, 2-10=face value, J/Q/K=10.
- Pegging scores: 15s (2 points), pairs (2 points), runs (1 point per card).
- The count during pegging cannot exceed 31.
- "The Show" scores: 15s (2 points), pairs (2 points), runs, flushes, and "nobs."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from random import Random
from typing import Any, Optional, Sequence

from card_games.common.cards import RANK_TO_VALUE, Card, Deck


class GamePhase(Enum):
    """Enumerates the different phases of a Cribbage game."""

    DEAL = auto()
    DISCARD = auto()
    PLAY = auto()
    SHOW = auto()
    GAME_OVER = auto()


@dataclass
class CribbageGame:
    """The main engine for the Cribbage game.

    This class manages the game state, including player hands, the crib, the
    starter card, scores, and the current phase of the game.

    Attributes:
        player1_hand: A list of cards in Player 1's hand.
        player2_hand: A list of cards in Player 2's hand.
        crib: The crib, which is an extra hand for the dealer.
        starter: The starter card, cut from the deck.
        player1_score: Player 1's current score.
        player2_score: Player 2's current score.
        dealer: The current dealer (1 or 2).
        phase: The current phase of the game (e.g., DEAL, PLAY, SHOW).
        play_sequence: A list of cards played during the pegging phase.
        play_count: The running count during the pegging phase.
        winner: The winner of the game (1 or 2), if any.
    """

    player1_hand: list[Card] = field(default_factory=list)
    player2_hand: list[Card] = field(default_factory=list)
    crib: list[Card] = field(default_factory=list)
    starter: Optional[Card] = None
    player1_score: int = 0
    player2_score: int = 0
    dealer: int = 1
    phase: GamePhase = GamePhase.DEAL
    play_sequence: list[tuple[int, Card]] = field(default_factory=list)
    play_count: int = 0
    current_player: int = 1
    winner: Optional[int] = None
    deck: Deck = field(default_factory=Deck)
    pegging_history: list[dict[str, Any]] = field(default_factory=list)
    passed_players: set[int] = field(default_factory=set)
    last_player_to_play: Optional[int] = None
    sequence_id: int = 0
    rng: Optional[Random] = None

    def __init__(self, dealer: int = 1, rng: Optional[Random] = None) -> None:
        """Initialize a new Cribbage game."""
        self.player1_hand = []
        self.player2_hand = []
        self.crib = []
        self.starter: Optional[Card] = None
        self.player1_score = 0
        self.player2_score = 0
        self.dealer = dealer
        self.phase = GamePhase.DEAL
        self.play_sequence: list[tuple[int, Card]] = []
        self.play_count = 0
        self.current_player = 1
        self.winner: Optional[int] = None
        self.deck = Deck()
        self.pegging_history: list[dict[str, Any]] = []
        self.passed_players: set[int] = set()
        self.last_player_to_play: Optional[int] = None
        self.sequence_id = 0
        self.rng = rng
        self.start_new_hand(dealer=dealer)

    def start_new_hand(self, *, dealer: Optional[int] = None, rng: Optional[Random] = None) -> None:
        """Deal new hands and reset the state for a new round."""
        if dealer is not None:
            self.dealer = dealer
        self.deck = Deck()
        self.deck.shuffle(rng=rng or self.rng)
        self.player1_hand = self.deck.deal(6)
        self.player2_hand = self.deck.deal(6)
        self.crib.clear()
        self.starter = None
        self.play_sequence.clear()
        self.play_count = 0
        self.current_player = 2 if self.dealer == 1 else 1
        self.phase = GamePhase.DISCARD
        self.pegging_history.clear()
        self.passed_players.clear()
        self.last_player_to_play = None
        self.sequence_id = 0

    @staticmethod
    def card_point_value(card: Card) -> int:
        """Return the pegging value of a card."""
        if card.rank in {"J", "Q", "K", "T"}:
            return 10
        if card.rank == "A":
            return 1
        return int(card.rank)

    def discard_to_crib(self, player: int, cards: list[Card]) -> bool:
        """Discard two cards from a player's hand to the crib."""
        if self.phase != GamePhase.DISCARD or len(cards) != 2:
            return False
        hand = self._hand(player)
        if not all(c in hand for c in cards):
            return False
        for card in cards:
            hand.remove(card)
            self.crib.append(card)
        if len(self.crib) == 4:
            self._start_play()
        return True

    def _start_play(self) -> None:
        """Start the pegging phase by cutting the starter card."""
        if self.deck.cards:
            self.starter = self.deck.deal(1)[0]
            if self.starter.rank == "J":
                self._award_points(self.dealer, 2, "His heels")
        self.phase = GamePhase.PLAY
        self.current_player = 2 if self.dealer == 1 else 1

    def can_play_card(self, player: int, card: Card) -> bool:
        """Check if a player can legally play a given card."""
        if self.phase != GamePhase.PLAY or player != self.current_player:
            return False
        if card not in self._hand(player):
            return False
        return self.card_point_value(card) + self.play_count <= 31

    def legal_plays(self, player: int) -> list[Card]:
        """Return a list of all legally playable cards for a player."""
        if self.phase != GamePhase.PLAY:
            return []
        return [c for c in self._hand(player) if self.can_play_card(player, c)]

    def can_player_play(self, player: int) -> bool:
        """Check if a player has any legal move."""
        return any(self.can_play_card(player, c) for c in self._hand(player))

    def play_card(self, player: int, card: Card) -> dict[str, Any]:
        """Play a card during the pegging phase."""
        if not self.can_play_card(player, card):
            return {"success": False, "message": "Invalid move"}

        self._hand(player).remove(card)
        self.play_sequence.append((player, card))
        self.play_count += self.card_point_value(card)

        points, events = self.pegging_points_for_sequence([c for _, c in self.play_sequence], self.play_count)
        self._award_points(player, points, ", ".join(events))

        self.last_player_to_play = player
        self.current_player = 2 if player == 1 else 1

        if self.play_count == 31:
            self._reset_sequence()

        if not self.player1_hand and not self.player2_hand:
            self.phase = GamePhase.SHOW

        return {"success": True, "points": points, "events": events, "game_over": self.winner is not None}

    def player_go(self, player: int) -> dict[str, Any]:
        """Handle a "go" from a player."""
        if self.phase != GamePhase.PLAY or player != self.current_player or self.can_player_play(player):
            return {"success": False, "message": "Cannot declare 'go'"}

        self.passed_players.add(player)
        other_player = 2 if player == 1 else 1

        if other_player not in self.passed_players:
            self.current_player = other_player
            return {"success": True, "message": f"{player} passes."}

        if self.last_player_to_play:
            self._award_points(self.last_player_to_play, 1, "Go")

        self._reset_sequence()
        self.current_player = self.last_player_to_play or other_player

        if not self.player1_hand and not self.player2_hand:
            self.phase = GamePhase.SHOW

        return {"success": True, "message": "Sequence reset."}

    def _reset_sequence(self) -> None:
        """Reset the pegging sequence for a new count."""
        self.play_sequence.clear()
        self.play_count = 0
        self.passed_players.clear()
        self.sequence_id += 1

    def _award_points(self, player: int, points: int, reason: str) -> None:
        """Award points to a player and check for a win."""
        if points <= 0 or self.winner is not None:
            return

        score_attr = "player1_score" if player == 1 else "player2_score"
        setattr(self, score_attr, getattr(self, score_attr) + points)

        self.pegging_history.append({"player": player, "points": points, "reason": reason})

        if getattr(self, score_attr) >= 121:
            self.winner = player
            self.phase = GamePhase.GAME_OVER

    def _hand(self, player: int) -> list[Card]:
        """Get the hand for a given player."""
        return self.player1_hand if player == 1 else self.player2_hand

    @staticmethod
    def pegging_points_for_sequence(sequence: list[Card], total: int) -> tuple[int, list[str]]:
        """Calculate pegging points for the current sequence."""
        points = 0
        events = []
        if total == 15:
            points += 2
            events.append("15")

        # Pairs, pairs royal, double pairs royal
        if len(sequence) >= 2 and sequence[-1].rank == sequence[-2].rank:
            points += 2
            events.append("Pair")
            if len(sequence) >= 3 and sequence[-1].rank == sequence[-3].rank:
                points += 4  # 6 total for pair royal
                events.append("Pair Royal")
                if len(sequence) >= 4 and sequence[-1].rank == sequence[-4].rank:
                    points += 6  # 12 total for double pair royal
                    events.append("Double Pair Royal")
        # Runs
        for run_len in range(len(sequence), 2, -1):
            sub_sequence = sequence[-run_len:]
            if CribbageGame._is_run(sub_sequence):
                points += run_len
                events.append(f"Run of {run_len}")
                break  # Score only the longest run
        return points, events

    def score_hand(self, hand: list[Card], is_crib: bool = False, starter: Optional[Card] = None) -> int:
        """Score a hand using the provided starter card."""
        starter_card = starter or self.starter
        if not starter_card:
            return 0
        return self.score_hand_static(hand, starter_card, is_crib)

    @classmethod
    def score_hand_static(cls, hand: Sequence[Card], starter: Card, is_crib: bool = False) -> int:
        """Calculate the score for a given hand and starter card."""
        all_cards = list(hand) + [starter]
        points = 0
        points += cls._score_fifteens(all_cards)
        points += cls._score_pairs(all_cards)
        points += cls._score_runs(all_cards)
        points += cls._score_flush(hand, starter, is_crib)
        points += cls._score_nobs(hand, starter)
        return points

    @staticmethod
    def _score_fifteens(cards: Sequence[Card]) -> int:
        """Calculate points for combinations that sum to 15."""
        from itertools import combinations

        points = 0
        for i in range(2, len(cards) + 1):
            for combo in combinations(cards, i):
                if sum(CribbageGame.card_point_value(c) for c in combo) == 15:
                    points += 2
        return points

    @staticmethod
    def _score_pairs(cards: Sequence[Card]) -> int:
        """Calculate points for pairs."""
        points = 0
        ranks = [c.rank for c in cards]
        counts = {rank: ranks.count(rank) for rank in set(ranks)}
        for count in counts.values():
            if count == 2:
                points += 2
            elif count == 3:
                points += 6
            elif count == 4:
                points += 12
        return points

    @staticmethod
    def _score_runs(cards: Sequence[Card]) -> int:
        """Calculate points for runs."""

        sorted_ranks = sorted(list({c.rank for c in cards}), key=lambda r: RANK_TO_VALUE[r])
        if len(sorted_ranks) < 3:
            return 0

        # Find the longest run
        longest_run = 0
        current_run = 1
        for i in range(1, len(sorted_ranks)):
            if RANK_TO_VALUE[sorted_ranks[i]] - RANK_TO_VALUE[sorted_ranks[i - 1]] == 1:
                current_run += 1
            else:
                longest_run = max(longest_run, current_run)
                current_run = 1
        longest_run = max(longest_run, current_run)

        if longest_run < 3:
            return 0

        # This is a simplified approach; a full implementation is more complex
        return longest_run

    @staticmethod
    def _is_run(cards: Sequence[Card]) -> bool:
        """Check if a sequence of cards forms a run."""
        ranks = {c.rank for c in cards}
        if len(ranks) != len(cards):
            return False
        values = sorted([RANK_TO_VALUE[r] for r in ranks])
        return all(values[i] + 1 == values[i + 1] for i in range(len(values) - 1))

    @staticmethod
    def _score_flush(hand: Sequence[Card], starter: Card, is_crib: bool) -> int:
        """Calculate points for a flush."""
        if len(hand) < 4:
            return 0
        first_suit = hand[0].suit
        if all(c.suit == first_suit for c in hand):
            if starter.suit == first_suit:
                return 5
            return 4 if not is_crib else 0
        return 0

    @staticmethod
    def _score_nobs(hand: Sequence[Card], starter: Card) -> int:
        """Calculate points for 'nobs' (Jack of the same suit as the starter)."""
        return 1 if any(c.rank == "J" and c.suit == starter.suit for c in hand) else 0

    def get_state_summary(self) -> dict[str, Any]:
        """Return a serializable snapshot of the current game state."""
        return {
            "player1_score": self.player1_score,
            "player2_score": self.player2_score,
            "dealer": self.dealer,
            "phase": self.phase.name,
            "play_count": self.play_count,
            "current_player": self.current_player,
            "player1_cards": len(self.player1_hand),
            "player2_cards": len(self.player2_hand),
            "crib_size": len(self.crib),
            "starter": str(self.starter) if self.starter else None,
            "winner": self.winner,
            "game_over": self.phase == GamePhase.GAME_OVER,
        }
