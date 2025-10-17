"""Euchre card game engine.

This module implements the classic four-player Euchre game, featuring trump-based
trick-taking and the "going alone" mechanic.

Key Rules:
- 24-card deck (9, 10, J, Q, K, A of each suit).
- Four players in two partnerships (North/South vs. East/West).
- A trump suit is selected after the deal.
- The Jack of the trump suit (Right Bower) is the highest trump.
- The Jack of the same-colored suit (Left Bower) is the second-highest trump.
- The first team to score 10 points wins.
- A player can "go alone," where their partner sits out the hand.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from random import Random
from typing import Optional

from card_games.common.cards import RANK_TO_VALUE, Card, Suit


class GamePhase(Enum):
    """Enumerates the different phases of a Euchre game."""

    DEAL = auto()
    BIDDING = auto()
    DEALER_DISCARD = auto()
    PLAY = auto()
    SCORE = auto()
    GAME_OVER = auto()


@dataclass
class EuchreGame:
    """The main engine for the Euchre game.

    This class manages the game state, including player hands, the trump suit,
    scoring, and the overall flow of the game from dealing to scoring.

    Attributes:
        hands: A list of four lists, each representing a player's hand.
        trump: The trump suit for the current hand.
        maker: The team that chose the trump suit (1 or 2).
        dealer: The index of the current dealer (0-3).
        current_trick: A list of cards in the current trick.
        tricks_won: A list tracking the number of tricks won by each team.
        team1_score: The score for Team 1 (players 0 and 2).
        team2_score: The score for Team 2 (players 1 and 3).
        phase: The current phase of the game.
        going_alone: True if a player is "going alone."
        winner: The winning team (1 or 2), if the game is over.
    """

    hands: list[list[Card]] = field(default_factory=lambda: [[], [], [], []])
    trump: Optional[Suit] = None
    maker: Optional[int] = None
    dealer: int = 0
    current_trick: list[tuple[int, Card]] = field(default_factory=list)
    tricks_won: list[int] = field(default_factory=lambda: [0, 0])
    team1_score: int = 0
    team2_score: int = 0
    phase: GamePhase = GamePhase.DEAL
    going_alone: bool = False
    alone_player: Optional[int] = None
    defending_alone_player: Optional[int] = None
    current_player: int = 0
    winner: Optional[int] = None
    kitty: list[Card] = field(default_factory=list)
    up_card: Optional[Card] = None
    sitting_out_players: set[int] = field(default_factory=set)
    _dealer_must_discard: bool = False

    def __init__(self, rng: Optional[Random] = None) -> None:
        """Initialize a new Euchre game.

        Args:
            rng: An optional `random.Random` instance for deterministic games.
        """
        self.hands = [[], [], [], []]
        self.trump: Optional[Suit] = None
        self.maker: Optional[int] = None
        self.dealer = 0
        self.current_trick: list[tuple[int, Card]] = []
        self.tricks_won = [0, 0]
        self.team1_score = 0
        self.team2_score = 0
        self.phase = GamePhase.DEAL
        self.going_alone = False
        self.alone_player: Optional[int] = None
        self.defending_alone_player: Optional[int] = None
        self.current_player = 0
        self.winner: Optional[int] = None
        self.kitty: list[Card] = []
        self.up_card: Optional[Card] = None
        self.sitting_out_players: set[int] = set()
        self._dealer_must_discard = False
        self._rng = rng or Random()
        self._deal_hands()

    def _create_euchre_deck(self) -> list[Card]:
        """Create a 24-card Euchre deck (9s through Aces)."""
        ranks = ["9", "T", "J", "Q", "K", "A"]
        return [Card(r, s) for s in Suit for r in ranks]

    def _deal_hands(self) -> None:
        """Deal 5 cards to each player and set up the kitty."""
        deck = self._create_euchre_deck()
        self._rng.shuffle(deck)

        for i in range(4):
            self.hands[i] = deck[i * 5 : (i + 1) * 5]

        self.kitty = deck[20:]
        self.up_card = self.kitty[0] if self.kitty else None

        self.phase = GamePhase.BIDDING
        self.current_player = (self.dealer + 1) % 4
        # Reset other round-specific state
        self.trump = None
        self.maker = None
        self.going_alone = False

    def select_trump(self, suit: Suit, player: int, go_alone: bool = False, require_dealer_pickup: bool = False) -> bool:
        """Select the trump suit for the hand."""
        if self.phase != GamePhase.BIDDING:
            return False

        self.trump = suit
        self.maker = 1 if player % 2 == 0 else 2
        self.going_alone = go_alone
        if go_alone:
            self.alone_player = player
            self.sitting_out_players.add((player + 2) % 4)

        if require_dealer_pickup:
            self.phase = GamePhase.DEALER_DISCARD
            self._dealer_must_discard = True
            self.current_player = self.dealer
        else:
            self.phase = GamePhase.PLAY
            self.current_player = (self.dealer + 1) % 4
            self._skip_sitting_out_players()
        return True

    def set_defending_alone(self, player: int) -> None:
        """Allow a defending player to go alone."""
        self.defending_alone_player = player
        self.sitting_out_players.add((player + 2) % 4)

    def dealer_pickup(self, discard_card: Card) -> bool:
        """Handle the dealer picking up the up-card and discarding one."""
        if self.phase != GamePhase.DEALER_DISCARD or not self.up_card:
            return False

        dealer_hand = self.hands[self.dealer]
        if discard_card not in dealer_hand:
            return False

        dealer_hand.append(self.up_card)
        dealer_hand.remove(discard_card)
        self.kitty[0] = discard_card  # The discarded card replaces the up-card in the kitty
        self.phase = GamePhase.PLAY
        self.current_player = (self.dealer + 1) % 4
        self._skip_sitting_out_players()
        return True

    def _active_player_count(self) -> int:
        """Return the number of players currently active in the hand."""
        return 4 - len(self.sitting_out_players)

    def redeal(self) -> None:
        """Redeal the cards if no trump is selected."""
        self._deal_hands()

    def play_card(self, player: int, card: Card) -> dict[str, any]:
        """Play a card from a player's hand."""
        if self.phase != GamePhase.PLAY or player != self.current_player:
            return {"success": False, "message": "Not your turn to play."}
        if card not in self.get_legal_cards(player):
            return {"success": False, "message": "Illegal card played."}

        self.hands[player].remove(card)
        self.current_trick.append((player, card))

        if len(self.current_trick) == self._active_player_count():
            winner = self._determine_trick_winner()
            self.tricks_won[winner % 2] += 1
            self.current_trick.clear()
            if not any(self.hands):
                self._score_hand()
                if self.team1_score >= 10 or self.team2_score >= 10:
                    self.phase = GamePhase.GAME_OVER
                    self.winner = 1 if self.team1_score >= 10 else 2
                else:
                    self.dealer = (self.dealer + 1) % 4
                    self._deal_hands()
            else:
                self.current_player = winner
        else:
            self.current_player = (self.current_player + 1) % 4

        self._skip_sitting_out_players()
        return {"success": True}

    def get_legal_cards(self, player: int) -> list[Card]:
        """Get the list of legally playable cards for a player."""
        if self.phase != GamePhase.PLAY or not self.current_trick:
            return self.hands[player]

        lead_suit = self._get_effective_suit(self.current_trick[0][1])
        can_follow_suit = any(self._get_effective_suit(c) == lead_suit for c in self.hands[player])

        if can_follow_suit:
            return [c for c in self.hands[player] if self._get_effective_suit(c) == lead_suit]
        return self.hands[player]

    def _determine_trick_winner(self) -> int:
        """Determine the winner of the completed trick."""
        if not self.current_trick:
            return 0

        lead_suit = self._get_effective_suit(self.current_trick[0][1])
        winning_card = self.current_trick[0][1]
        winner = self.current_trick[0][0]

        for player_idx, card in self.current_trick[1:]:
            if self._card_strength(card, lead_suit) > self._card_strength(winning_card, lead_suit):
                winning_card = card
                winner = player_idx
        return winner

    def _card_strength(self, card: Card, lead_suit: Suit) -> int:
        """Calculate the strength of a card for trick-taking."""
        is_trump = self._get_effective_suit(card) == self.trump
        base_value = RANK_TO_VALUE.get(card.rank, 0)

        if card.rank == "J" and self.trump:
            if card.suit == self.trump:
                return 30  # Right Bower
            if card.suit == self._get_same_color_suit(self.trump):
                return 29  # Left Bower

        return base_value + (13 if is_trump else 0)

    def _get_effective_suit(self, card: Card) -> Suit:
        """Get the effective suit of a card, considering bowers."""
        if card.rank == "J" and self.trump:
            if card.suit == self.trump or card.suit == self._get_same_color_suit(self.trump):
                return self.trump
        return card.suit

    def _get_same_color_suit(self, suit: Suit) -> Optional[Suit]:
        """Get the other suit of the same color."""
        return {Suit.CLUBS: Suit.SPADES, Suit.SPADES: Suit.CLUBS, Suit.HEARTS: Suit.DIAMONDS, Suit.DIAMONDS: Suit.HEARTS}.get(suit)

    def _score_hand(self) -> None:
        """Score the completed hand and update team scores."""
        if not self.maker:
            return

        making_team_tricks = self.tricks_won[self.maker - 1]
        points = 0
        if making_team_tricks >= 3:  # Makers made it
            if making_team_tricks == 5:  # March
                points = 4 if self.going_alone else 2
            else:
                points = 1
            if self.maker == 1:
                self.team1_score += points
            else:
                self.team2_score += points
        else:  # Euchred
            points = 4 if self.going_alone else 2
            if self.maker == 1:
                self.team2_score += points
            else:
                self.team1_score += points

        self.phase = GamePhase.SCORE

    def _skip_sitting_out_players(self) -> None:
        """Advance the turn to the next active player."""
        while self.current_player in self.sitting_out_players:
            self.current_player = (self.current_player + 1) % 4

    def get_state_summary(self) -> dict[str, any]:
        """Return a summary of the current game state."""
        return {
            "team1_score": self.team1_score,
            "team2_score": self.team2_score,
            "dealer": self.dealer,
            "phase": self.phase.name,
            "trump": self.trump.value if self.trump else None,
            "maker": self.maker,
            "tricks_won": self.tricks_won,
            "current_player": self.current_player,
            "going_alone": self.going_alone,
            "winner": self.winner,
        }
