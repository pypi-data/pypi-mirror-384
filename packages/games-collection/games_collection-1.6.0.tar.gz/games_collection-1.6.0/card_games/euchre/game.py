"""Euchre card game engine.

This module implements the classic four-player Euchre game with trump-based
trick-taking gameplay and the unique "going alone" mechanic.

Rules:
* 24-card deck (9, T, J, Q, K, A of each suit)
* Four players in two partnerships (1&3 vs 2&4)
* Trump suit selected after dealing
* Right bower (Jack of trump) is highest trump
* Left bower (Jack of same-color suit) is second highest trump
* First team to 10 points wins
* "Going alone" option for maker's partner to sit out
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from random import Random
from typing import Optional

from card_games.common.cards import Card, Suit


class GamePhase(Enum):
    """Current phase of the Euchre game."""

    DEAL = auto()
    BIDDING = auto()
    DEALER_DISCARD = auto()
    PLAY = auto()
    SCORE = auto()
    GAME_OVER = auto()


@dataclass
class EuchreGame:
    """Euchre game engine.

    Attributes:
        hands: Four player hands
        trump: Trump suit
        maker: Team that chose trump (1 or 2)
        dealer: Current dealer (0-3)
        current_trick: Cards in current trick
        tricks_won: Tricks won by each team
        team1_score: Team 1 score
        team2_score: Team 2 score
        phase: Current game phase
        going_alone: Whether someone is going alone
        winner: Winning team (1 or 2), None if ongoing
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
            rng: Optional Random instance for deterministic games
        """
        self.hands = [[], [], [], []]
        self.trump = None
        self.maker = None
        self.dealer = 0
        self.current_trick = []
        self.tricks_won = [0, 0]
        self.team1_score = 0
        self.team2_score = 0
        self.phase = GamePhase.DEAL
        self.going_alone = False
        self.alone_player = None
        self.defending_alone_player = None
        self.current_player = 0
        self.winner = None
        self.kitty = []
        self.up_card = None
        self.sitting_out_players = set()
        self._dealer_must_discard = False
        self._rng = rng or Random()
        self._deal_hands()

    def _create_euchre_deck(self) -> list[Card]:
        """Create a 24-card Euchre deck (9-A in each suit).

        Returns:
            List of cards
        """
        ranks = ["9", "T", "J", "Q", "K", "A"]
        suits = [Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES]
        return [Card(rank, suit) for suit in suits for rank in ranks]

    def _deal_hands(self) -> None:
        """Deal 5 cards to each player."""
        deck = self._create_euchre_deck()
        self._rng.shuffle(deck)

        for i in range(4):
            self.hands[i] = deck[i * 5 : (i + 1) * 5]

        self.kitty = deck[20:]
        self.up_card = self.kitty[0] if self.kitty else None

        self.phase = GamePhase.BIDDING
        self.trump = None
        self.maker = None
        self.going_alone = False
        self.alone_player = None
        self.defending_alone_player = None
        self.sitting_out_players = set()
        self.current_trick = []
        self.tricks_won = [0, 0]
        self.current_player = (self.dealer + 1) % 4
        self._dealer_must_discard = False

    def select_trump(self, suit: Suit, player: int, go_alone: bool = False, require_dealer_pickup: bool = False) -> bool:
        """Select the trump suit once bidding concludes.

        Args:
            suit: Trump suit to select.
            player: Player selecting trump.
            go_alone: Whether the selecting player goes alone.
            require_dealer_pickup: Whether the dealer must pick up the turned card.

        Returns:
            True if the selection was recorded, otherwise ``False``.

        Raises:
            None.
        """
        if self.phase not in {GamePhase.BIDDING, GamePhase.DEALER_DISCARD}:
            return False

        self.trump = suit
        # Determine maker team (players 0&2 are team 1, players 1&3 are team 2)
        self.maker = 1 if player in [0, 2] else 2
        self.going_alone = go_alone
        self.alone_player = player if go_alone else None
        self.sitting_out_players = set()
        if go_alone:
            partner = (player + 2) % 4
            self.sitting_out_players.add(partner)

        if require_dealer_pickup:
            self.phase = GamePhase.DEALER_DISCARD
            self._dealer_must_discard = True
            self.current_player = self.dealer
        else:
            self.phase = GamePhase.PLAY
            self._dealer_must_discard = False
            self.current_player = (self.dealer + 1) % 4
            self._skip_sitting_out_players()
        return True

    def set_defending_alone(self, player: int) -> None:
        """Set a defending player to go alone and sit their partner out.

        Args:
            player: Seat index of the defending player electing to play alone.

        Returns:
            None.

        Raises:
            None.
        """

        self.defending_alone_player = player
        partner = (player + 2) % 4
        self.sitting_out_players.add(partner)

    def dealer_pickup(self, discard_card: Card) -> bool:
        """Handle the dealer picking up the turned card and discarding one.

        Args:
            discard_card: Card the dealer wishes to discard after picking up.

        Returns:
            bool: ``True`` when the discard is accepted, ``False`` otherwise.

        Raises:
            None.
        """

        if self.phase != GamePhase.DEALER_DISCARD or not self._dealer_must_discard or self.up_card is None:
            return False

        augmented = list(self.hands[self.dealer])
        augmented.append(self.up_card)
        if discard_card not in augmented:
            return False

        self.hands[self.dealer].append(self.up_card)
        self.hands[self.dealer].remove(discard_card)
        self.kitty = [discard_card] + self.kitty[1:]
        self._dealer_must_discard = False
        self.phase = GamePhase.PLAY
        self.current_player = (self.dealer + 1) % 4
        self._skip_sitting_out_players()
        return True

    def redeal(self) -> None:
        """Redeal the cards if both bidding rounds pass.

        Returns:
            None.

        Raises:
            None.
        """

        self._deal_hands()

    def _get_card_power(self, card: Card) -> int:
        """Get the power ranking of a card.

        Args:
            card: Card to evaluate

        Returns:
            Power ranking (higher is better)
        """
        if not self.trump:
            rank_values = {"9": 0, "T": 1, "J": 2, "Q": 3, "K": 4, "A": 5}
            return rank_values.get(card.rank, 0)

        # Right bower (Jack of trump) is highest
        if card.rank == "J" and card.suit == self.trump:
            return 100

        # Left bower (Jack of same color) is second highest
        same_color_suit = self._get_same_color_suit(self.trump)
        if same_color_suit and card.rank == "J" and card.suit == same_color_suit:
            return 99

        # Trump cards
        if card.suit == self.trump:
            rank_values = {"9": 80, "T": 81, "Q": 82, "K": 83, "A": 84}
            return rank_values.get(card.rank, 80)

        # Non-trump cards
        rank_values = {"9": 0, "T": 1, "J": 2, "Q": 3, "K": 4, "A": 5}
        return rank_values.get(card.rank, 0)

    def _get_same_color_suit(self, suit: Suit) -> Optional[Suit]:
        """Get the same-color suit.

        Args:
            suit: Input suit

        Returns:
            Same-color suit
        """
        if suit == Suit.CLUBS:
            return Suit.SPADES
        elif suit == Suit.SPADES:
            return Suit.CLUBS
        elif suit == Suit.HEARTS:
            return Suit.DIAMONDS
        elif suit == Suit.DIAMONDS:
            return Suit.HEARTS
        return None

    def play_card(self, player: int, card: Card) -> dict[str, any]:
        """Play a card.

        Args:
            player: Player number (0-3)
            card: Card to play

        Returns:
            Result dictionary
        """
        if self.phase != GamePhase.PLAY:
            return {"success": False, "message": "Not in play phase"}

        if player != self.current_player:
            return {"success": False, "message": "Not your turn"}

        if card not in self.hands[player]:
            return {"success": False, "message": "Card not in hand"}

        if player in self.sitting_out_players:
            return {"success": False, "message": "Player is sitting out"}

        legal_cards = self.get_legal_cards(player)
        if card not in legal_cards:
            return {"success": False, "message": "Card cannot be played"}

        # Play the card
        self.hands[player].remove(card)
        self.current_trick.append((player, card))

        # Check if trick is complete
        if len(self.current_trick) >= self._active_player_count():
            winner = self._determine_trick_winner()
            team = 1 if winner in [0, 2] else 2
            self.tricks_won[team - 1] += 1
            self.current_trick = []

            # Check if hand is complete
            if self._hand_complete():
                self._score_hand()
                if self.team1_score >= 10 or self.team2_score >= 10:
                    self.phase = GamePhase.GAME_OVER
                    self.winner = 1 if self.team1_score >= 10 else 2
                else:
                    # Deal new hand
                    self.dealer = (self.dealer + 1) % 4
                    self._deal_hands()
            else:
                self.current_player = winner
                self._skip_sitting_out_players()
            return {"success": True, "trick_complete": True, "trick_winner": winner}
        else:
            self.current_player = (self.current_player + 1) % 4
            self._skip_sitting_out_players()

        return {"success": True, "trick_complete": False}

    def get_legal_cards(self, player: int) -> list[Card]:
        """Return the list of cards the given player may legally play.

        Args:
            player: Seat index of the player whose options are requested.

        Returns:
            list[Card]: List of legal cards available for play.

        Raises:
            None.
        """

        if self.phase != GamePhase.PLAY or player in self.sitting_out_players:
            return []

        hand = self.hands[player]
        if not self.current_trick:
            return list(hand)

        lead_suit = self._get_effective_suit(self.current_trick[0][1])
        matching_cards = [card for card in hand if self._get_effective_suit(card) == lead_suit]
        return matching_cards if matching_cards else list(hand)

    def _determine_trick_winner(self) -> int:
        """Determine the winner of the current trick.

        Returns:
            Player number who won
        """
        if not self.current_trick:
            return 0

        lead_suit = self._get_effective_suit(self.current_trick[0][1])

        best_player = self.current_trick[0][0]
        best_power = self._card_strength(self.current_trick[0][1], lead_suit)

        for player, card in self.current_trick[1:]:
            power = self._card_strength(card, lead_suit)
            if power > best_power:
                best_player = player
                best_power = power

        return best_player

    def _card_strength(self, card: Card, lead_suit: Suit) -> int:
        """Calculate a sortable strength value for a card within a trick.

        Args:
            card: Card being evaluated.
            lead_suit: Effective suit that was led.

        Returns:
            int: Relative strength value for comparison purposes.

        Raises:
            None.
        """

        if not self.trump:
            rank_values = {"9": 0, "T": 1, "J": 2, "Q": 3, "K": 4, "A": 5}
            return rank_values.get(card.rank, 0)

        effective_suit = self._get_effective_suit(card)
        rank_values = {"9": 0, "T": 1, "J": 2, "Q": 3, "K": 4, "A": 5}

        if card.rank == "J" and card.suit == self.trump:
            return 400

        same_color_suit = self._get_same_color_suit(self.trump)
        if card.rank == "J" and same_color_suit and card.suit == same_color_suit:
            return 399

        if effective_suit == self.trump:
            return 300 + rank_values.get(card.rank, 0)

        if effective_suit == lead_suit:
            return 200 + rank_values.get(card.rank, 0)

        return rank_values.get(card.rank, 0)

    def _score_hand(self) -> None:
        """Score the completed hand."""
        making_team = self.maker
        if making_team is None:
            return

        defending_team = 2 if making_team == 1 else 1
        making_tricks = self.tricks_won[making_team - 1]

        if making_tricks >= 3:
            # Makers won
            if making_tricks == 5:
                # March
                points = 4 if self.going_alone else 2
            else:
                # Made it
                points = 2 if self.going_alone else 1
            if making_team == 1:
                self.team1_score += points
            else:
                self.team2_score += points
        else:
            # Euchred - defenders get points (4 if setting a lone maker)
            points = 4 if self.going_alone else 2
            if defending_team == 1:
                self.team1_score += points
            else:
                self.team2_score += points

        self.tricks_won = [0, 0]
        self.phase = GamePhase.SCORE

    def _hand_complete(self) -> bool:
        """Check whether the active players have exhausted their hands.

        Returns:
            bool: ``True`` if all active players have no cards remaining.

        Raises:
            None.
        """

        for idx, hand in enumerate(self.hands):
            if idx in self.sitting_out_players:
                continue
            if hand:
                return False
        return True

    def _active_player_count(self) -> int:
        """Return the number of players participating in the current hand.

        Returns:
            int: Count of players not sitting out.

        Raises:
            None.
        """

        return 4 - len(self.sitting_out_players)

    def _skip_sitting_out_players(self) -> None:
        """Advance ``current_player`` until an active player is reached.

        Returns:
            None.

        Raises:
            None.
        """

        while self.current_player in self.sitting_out_players:
            self.current_player = (self.current_player + 1) % 4

    def _get_effective_suit(self, card: Card) -> Suit:
        """Return the effective suit for follow-suit purposes.

        Args:
            card: Card whose effective suit is required.

        Returns:
            Suit: The suit that card represents during play.

        Raises:
            None.
        """

        if self.trump and card.rank == "J":
            same_color = self._get_same_color_suit(self.trump)
            if card.suit == self.trump:
                return self.trump
            if same_color and card.suit == same_color:
                return self.trump
        return card.suit

    def get_state_summary(self) -> dict[str, any]:
        """Get game state summary.

        Returns:
            State dictionary
        """
        return {
            "team1_score": self.team1_score,
            "team2_score": self.team2_score,
            "dealer": self.dealer,
            "phase": self.phase.name,
            "trump": str(self.trump) if self.trump else None,
            "maker": self.maker,
            "tricks_won": self.tricks_won,
            "current_player": self.current_player,
            "going_alone": self.going_alone,
            "defending_alone_player": self.defending_alone_player,
            "winner": self.winner,
            "game_over": self.phase == GamePhase.GAME_OVER,
            "up_card": str(self.up_card) if self.up_card else None,
        }
