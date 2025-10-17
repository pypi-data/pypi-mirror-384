"""Cribbage card game engine.

This module implements the classic two-player Cribbage card game, featuring:
- The Deal: Each player gets 6 cards, discards 2 to the crib
- The Play (Pegging): Players alternate playing cards, scoring for pairs, runs, and 15s
- The Show: Both hands and the crib are scored for combinations
- First to 121 points wins

Rules:
* Standard 52-card deck
* Cards score: Ace=1, 2-10=face value, J/Q/K=10
* During play, score for reaching 15 (2 points), pairs (2 points), runs (length points)
* Cannot exceed 31 during play
* The Show scores: 15s (2 each), pairs (2 each), runs (length), flush (4-5), nobs (1)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from random import Random
from typing import Any, Optional, Sequence

from card_games.common.cards import RANK_TO_VALUE, Card, Deck


class GamePhase(Enum):
    """Current phase of the Cribbage game."""

    DEAL = auto()
    DISCARD = auto()
    PLAY = auto()
    SHOW = auto()
    GAME_OVER = auto()


@dataclass
class CribbageGame:
    """Cribbage game engine.

    Attributes:
        player1_hand: Player 1's hand
        player2_hand: Player 2's hand
        crib: The crib (dealer's extra hand)
        starter: The starter card (cut card)
        player1_score: Player 1's score
        player2_score: Player 2's score
        dealer: Current dealer (1 or 2)
        phase: Current game phase
        play_sequence: Cards played during pegging phase
        play_count: Running count during pegging
        winner: Winner of the game (1 or 2), None if ongoing
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
        self.starter = None
        self.player1_score = 0
        self.player2_score = 0
        self.dealer = dealer
        self.phase = GamePhase.DEAL
        self.play_sequence = []
        self.play_count = 0
        self.current_player = 1
        self.winner = None
        self.deck = Deck()
        self.pegging_history = []
        self.passed_players = set()
        self.last_player_to_play = None
        self.sequence_id = 0
        self.rng = rng
        self.start_new_hand(dealer=dealer)

    def start_new_hand(self, *, dealer: Optional[int] = None, rng: Optional[Random] = None) -> None:
        """Deal new hands and reset per-hand state while keeping scores."""

        if dealer is not None:
            self.dealer = dealer

        self.deck = Deck()
        self.deck.shuffle(rng=rng or self.rng)

        self.player1_hand = self.deck.deal(6)
        self.player2_hand = self.deck.deal(6)
        self.crib = []
        self.starter = None
        self.play_sequence = []
        self.play_count = 0
        self.current_player = 2 if self.dealer == 1 else 1
        self.phase = GamePhase.DISCARD
        self.pegging_history = []
        self.passed_players = set()
        self.last_player_to_play = None
        self.sequence_id = 0

    @staticmethod
    def card_point_value(card: Card) -> int:
        """Return the pegging value of ``card`` (aces low, face cards ten)."""

        if card.rank in {"J", "Q", "K"}:
            return 10
        if card.rank == "A":
            return 1
        if card.rank == "T":
            return 10
        return int(card.rank)

    def discard_to_crib(self, player: int, cards: list[Card]) -> bool:
        """Discard exactly two cards to the crib for ``player``."""

        if self.phase != GamePhase.DISCARD or len(cards) != 2:
            return False

        hand = self._hand(player)
        if not all(card in hand for card in cards):
            return False

        for card in cards:
            hand.remove(card)
            self.crib.append(card)

        if len(self.crib) == 4:
            self._start_play()

        return True

    def _start_play(self) -> None:
        """Start the pegging phase by cutting a starter card."""

        if self.deck.cards:
            self.starter = self.deck.deal(1)[0]
            if self.starter.rank == "J":
                self._award_points(self.dealer, 2)
                self.pegging_history.append(
                    {
                        "type": "starter",
                        "player": self.dealer,
                        "card": self.starter,
                        "points": 2,
                        "events": ["His heels for 2"],
                        "sequence": self.sequence_id,
                    }
                )
        self.phase = GamePhase.PLAY
        self.play_sequence = []
        self.play_count = 0
        self.sequence_id = 0
        self.pegging_history = []
        self.passed_players = set()
        self.last_player_to_play = None
        self.current_player = 2 if self.dealer == 1 else 1

    def can_play_card(self, player: int, card: Card) -> bool:
        """Return ``True`` if ``player`` may legally play ``card``."""

        if self.phase != GamePhase.PLAY or player != self.current_player:
            return False

        hand = self._hand(player)
        if card not in hand:
            return False

        return self.card_point_value(card) + self.play_count <= 31

    def legal_plays(self, player: int) -> list[Card]:
        """Return all cards ``player`` may legally play at this moment."""

        if self.phase != GamePhase.PLAY:
            return []

        return [card for card in self._hand(player) if self.card_point_value(card) + self.play_count <= 31]

    def can_player_play(self, player: int) -> bool:
        """Return ``True`` if ``player`` has any legal pegging play."""

        return bool(self.legal_plays(player))

    def play_card(self, player: int, card: Card) -> dict[str, Any]:
        """Play ``card`` for ``player`` during pegging."""

        if not self.can_play_card(player, card):
            return {"success": False, "points": 0}

        hand = self._hand(player)
        hand.remove(card)

        self.play_sequence.append((player, card))
        self.play_count += self.card_point_value(card)

        sequence_cards = [c for _, c in self.play_sequence]
        points, events = self.pegging_points_for_sequence(sequence_cards, self.play_count)

        self._award_points(player, points)

        self.last_player_to_play = player
        count_after_play = self.play_count
        sequence_end = False
        end_reason = None

        self.pegging_history.append(
            {
                "type": "play",
                "player": player,
                "card": card,
                "count": count_after_play,
                "points": points,
                "events": events,
                "sequence": self.sequence_id,
            }
        )

        other = 2 if player == 1 else 1

        if count_after_play == 31:
            sequence_end = True
            end_reason = "31"
            self._reset_sequence()
            next_player = player if self._player_has_cards(player) else other
            self.current_player = next_player if next_player is not None else player
        else:
            self.current_player = other
            self.passed_players.discard(other)

        if not self.player1_hand and not self.player2_hand:
            self.phase = GamePhase.SHOW

        return {
            "success": True,
            "points": points,
            "events": events,
            "count": count_after_play,
            "sequence_end": sequence_end,
            "end_reason": end_reason,
            "game_over": self.phase == GamePhase.GAME_OVER,
        }

    def player_go(self, player: int) -> dict[str, Any]:
        """Handle a "go" declaration from ``player`` during pegging."""

        if self.phase != GamePhase.PLAY or player != self.current_player:
            return {"success": False, "reason": "not_turn"}

        if player in self.passed_players:
            return {"success": False, "reason": "already_passed"}

        if self.can_player_play(player):
            return {"success": False, "reason": "card_available"}

        self.passed_players.add(player)
        other = 2 if player == 1 else 1
        result: dict[str, Any] = {
            "success": True,
            "awarded": 0,
            "awarded_to": None,
            "sequence_end": False,
        }

        if self.can_player_play(other) and other not in self.passed_players:
            self.current_player = other
            result["next_player"] = other
            return result

        awarded_to = self.last_player_to_play
        events: list[str] = []
        if awarded_to and self.play_count not in (0, 31):
            self._award_points(awarded_to, 1)
            result["awarded"] = 1
            result["awarded_to"] = awarded_to
            events.append("Go for 1")

        self.pegging_history.append(
            {
                "type": "go",
                "player": player,
                "awarded_to": awarded_to,
                "points": result["awarded"],
                "events": events,
                "sequence": self.sequence_id,
            }
        )

        self._reset_sequence()
        result["sequence_end"] = True

        if awarded_to and self._player_has_cards(awarded_to):
            self.current_player = awarded_to
        elif self._player_has_cards(other):
            self.current_player = other
        elif self._player_has_cards(player):
            self.current_player = player
        else:
            self.current_player = None

        result["next_player"] = self.current_player

        if not self.player1_hand and not self.player2_hand:
            self.phase = GamePhase.SHOW

        return result

    def _reset_sequence(self) -> None:
        """Clear the active pegging sequence for a new count."""

        self.play_sequence = []
        self.play_count = 0
        self.passed_players = set()
        self.last_player_to_play = None
        self.sequence_id += 1

    def _award_points(self, player: int, points: int) -> None:
        """Award ``points`` to ``player`` and check for a win."""

        if points <= 0 or self.winner is not None:
            return

        if player == 1:
            self.player1_score += points
            if self.player1_score >= 121:
                self.winner = 1
        else:
            self.player2_score += points
            if self.player2_score >= 121:
                self.winner = 2

        if self.winner:
            self.phase = GamePhase.GAME_OVER

    def _player_has_cards(self, player: Optional[int]) -> bool:
        if player is None:
            return False
        return bool(self._hand(player))

    def _hand(self, player: int) -> list[Card]:
        return self.player1_hand if player == 1 else self.player2_hand

    def remaining_deck(self) -> list[Card]:
        """Return a copy of the undealt portion of the deck."""

        return list(self.deck.cards)

    @classmethod
    def pegging_points_for_sequence(cls, sequence: Sequence[Card], total: int) -> tuple[int, list[str]]:
        """Return points and descriptive events for a pegging sequence."""

        points = 0
        events: list[str] = []

        if total == 15:
            points += 2
            events.append("15 for 2")
        if total == 31:
            points += 2
            events.append("31 for 2")

        same_rank = cls._count_trailing_same_rank(sequence)
        if same_rank >= 2:
            pair_points = same_rank * (same_rank - 1)
            points += pair_points
            events.append(cls._pair_event_description(same_rank, pair_points))

        run_length = cls._trailing_run_length(sequence)
        if run_length >= 3:
            points += run_length
            events.append(f"Run of {run_length}")

        return points, events

    @staticmethod
    def _count_trailing_same_rank(sequence: Sequence[Card]) -> int:
        if not sequence:
            return 0

        last_rank = sequence[-1].rank
        count = 0
        for card in reversed(sequence):
            if card.rank == last_rank:
                count += 1
            else:
                break
        return count

    @staticmethod
    def _pair_event_description(count: int, points: int) -> str:
        if count == 2:
            return "Pair for 2"
        if count == 3:
            return "Three of a kind for 6"
        return "Four of a kind for 12"

    @staticmethod
    def _trailing_run_length(sequence: Sequence[Card]) -> int:
        for length in range(len(sequence), 2, -1):
            window = sequence[-length:]
            ranks = [card.rank for card in window]
            if len(set(ranks)) != length:
                continue
            values = sorted(RANK_TO_VALUE[rank] for rank in ranks)
            if all(values[i] + 1 == values[i + 1] for i in range(len(values) - 1)):
                return length
        return 0

    def score_hand(self, hand: list[Card], is_crib: bool = False, starter: Optional[Card] = None) -> int:
        """Score ``hand`` using ``starter`` if provided (else ``self.starter``)."""

        starter_card = starter or self.starter
        if not starter_card:
            return 0

        return self.score_hand_static(hand, starter_card, is_crib)

    @classmethod
    def score_hand_static(cls, hand: Sequence[Card], starter: Card, is_crib: bool = False) -> int:
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
        count = 0
        n = len(cards)
        for mask in range(1, 1 << n):
            total = 0
            for idx in range(n):
                if mask >> idx & 1:
                    total += CribbageGame.card_point_value(cards[idx])
            if total == 15:
                count += 1
        return count * 2

    @staticmethod
    def _score_pairs(cards: Sequence[Card]) -> int:
        points = 0
        for i in range(len(cards)):
            for j in range(i + 1, len(cards)):
                if cards[i].rank == cards[j].rank:
                    points += 2
        return points

    @staticmethod
    def _score_runs(cards: Sequence[Card]) -> int:
        from itertools import combinations

        best_length = 0
        count = 0
        for length in range(5, 2, -1):
            combos = [combo for combo in combinations(cards, length) if CribbageGame._is_run(combo)]
            if combos:
                best_length = length
                count = len(combos)
                break
        if best_length:
            return best_length * count
        return 0

    @staticmethod
    def _is_run(cards: Sequence[Card]) -> bool:
        ranks = [card.rank for card in cards]
        if len(set(ranks)) != len(cards):
            return False
        values = sorted(RANK_TO_VALUE[rank] for rank in ranks)
        return all(values[i] + 1 == values[i + 1] for i in range(len(values) - 1))

    @staticmethod
    def _score_flush(hand: Sequence[Card], starter: Card, is_crib: bool) -> int:
        if len(hand) < 4:
            return 0

        first_suit = hand[0].suit
        if any(card.suit != first_suit for card in hand):
            return 0

        if is_crib:
            return 5 if starter.suit == first_suit else 0

        return 5 if starter.suit == first_suit else 4

    @staticmethod
    def _score_nobs(hand: Sequence[Card], starter: Card) -> int:
        for card in hand:
            if card.rank == "J" and card.suit == starter.suit:
                return 1
        return 0

    def get_state_summary(self) -> dict[str, Any]:
        """Return a serialisable snapshot of the current game state."""

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
            "pegging_history": [
                {
                    "type": entry.get("type"),
                    "player": entry.get("player"),
                    "card": str(entry.get("card")) if entry.get("card") else None,
                    "count": entry.get("count"),
                    "points": entry.get("points", 0),
                    "events": entry.get("events", []),
                    "sequence": entry.get("sequence"),
                    "awarded_to": entry.get("awarded_to"),
                }
                for entry in self.pegging_history
            ],
        }
