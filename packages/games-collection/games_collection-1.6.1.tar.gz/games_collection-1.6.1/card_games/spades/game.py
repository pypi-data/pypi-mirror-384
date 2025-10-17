"""Spades game engine.

Spades is a trick-taking card game where spades are always trump. Players bid on
how many tricks they expect to win, and partnerships try to meet their combined bid.
Special bids include "nil" (zero tricks) for bonus points.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from card_games.common.cards import Card, Deck, Suit


@dataclass
class SpadesPlayer:
    """Represents a player in Spades."""

    name: str
    hand: list[Card] = field(default_factory=list)
    tricks_won: int = 0
    bid: Optional[int] = None
    score: int = 0
    is_ai: bool = False
    partner_index: Optional[int] = None
    blind_nil: bool = False

    def has_suit(self, suit: Suit) -> bool:
        """Check if player has any cards of the given suit."""
        return any(card.suit == suit for card in self.hand)


class SpadesGame:
    """Main engine for the Spades card game."""

    def __init__(self, players: list[SpadesPlayer], *, rng=None, target_score: int = 500):
        """Initialize a Spades game."""
        if len(players) != 4:
            raise ValueError("Spades requires exactly 4 players")
        self.players = players
        self.players[0].partner_index = 2
        self.players[2].partner_index = 0
        self.players[1].partner_index = 3
        self.players[3].partner_index = 1
        self.rng = rng
        self.deck = Deck()
        self.spades_broken = False
        self.current_trick: list[tuple[SpadesPlayer, Card]] = []
        self.trick_history: list[list[tuple[SpadesPlayer, Card]]] = []
        self.bidding_history: list[tuple[SpadesPlayer, int | str]] = []
        self.lead_suit: Optional[Suit] = None
        self.round_number = 0
        self.current_player_index: Optional[int] = None
        self.last_trick_winner_index: Optional[int] = None
        self.next_round_leader_index: Optional[int] = None
        self.team_scores = [0, 0]
        self.target_score = target_score
        self.bags = [0, 0]
        self.total_tricks_played = 0
        self._last_round_scores: Optional[dict[int, int]] = None

    def deal_cards(self) -> None:
        """Deal all 52 cards evenly to 4 players."""
        self.deck = Deck()
        if self.rng:
            self.deck.shuffle(rng=self.rng)
        else:
            self.deck.shuffle()
        for player in self.players:
            player.hand = []
            player.tricks_won = 0
            player.bid = None
            player.blind_nil = False
        for _ in range(13):
            for player in self.players:
                player.hand.append(self.deck.deal(1)[0])
        for player in self.players:
            player.hand.sort(key=lambda c: (c.suit.value, c.value))
        self.total_tricks_played = 0
        self.trick_history = []
        self.bidding_history = []
        self.current_trick = []
        self.lead_suit = None
        self.spades_broken = False
        self._last_round_scores = None

    def start_new_round(self) -> None:
        """Start a new round by dealing cards and setting the opening leader."""
        self.round_number += 1
        self.deal_cards()
        if self.next_round_leader_index is not None:
            self.current_player_index = self.next_round_leader_index
        else:
            self.current_player_index = self._find_two_of_clubs_holder()
        self.next_round_leader_index = None
        self.last_trick_winner_index = None

    def _find_two_of_clubs_holder(self) -> int:
        """Locate the player who holds the two of clubs."""
        target_card = Card("2", Suit.CLUBS)
        for idx, player in enumerate(self.players):
            if target_card in player.hand:
                return idx
        raise RuntimeError("Two of clubs not found after dealing")

    def register_bid(self, player: SpadesPlayer, bid: int, *, blind_nil: bool = False) -> None:
        """Register a player's bid for the round."""
        if bid < 0 or bid > 13:
            raise ValueError("Bid must be between 0 and 13")
        if player not in self.players:
            raise ValueError("Unknown player")
        player.bid = bid
        player.blind_nil = blind_nil and bid == 0
        description: int | str = bid
        if player.blind_nil:
            description = "blind nil"
        elif bid == 0:
            description = "nil"
        self.bidding_history.append((player, description))

    def is_valid_play(self, player: SpadesPlayer, card: Card) -> bool:
        """Check if a card play is valid."""
        if card not in player.hand:
            return False
        if self.current_player_index is not None and self.players[self.current_player_index] != player:
            return False
        if not self.current_trick:
            if self.total_tricks_played == 0 and self.round_number == 1:
                two_of_clubs = Card("2", Suit.CLUBS)
                if card != two_of_clubs:
                    return False
            if card.suit == Suit.SPADES:
                if self.spades_broken:
                    return True
                return all(c.suit == Suit.SPADES for c in player.hand)
            return True
        if self.lead_suit and player.has_suit(self.lead_suit):
            return card.suit == self.lead_suit
        return True

    def play_card(self, player: SpadesPlayer, card: Card) -> None:
        """Play a card to the current trick."""
        if not self.is_valid_play(player, card):
            raise ValueError("Invalid play")
        player.hand.remove(card)
        self.current_trick.append((player, card))
        if len(self.current_trick) == 1:
            self.lead_suit = card.suit
        if card.suit == Suit.SPADES:
            self.spades_broken = True
        if self.current_player_index is not None:
            self.current_player_index = (self.current_player_index + 1) % 4

    def complete_trick(self) -> SpadesPlayer:
        """Complete the current trick and determine winner."""
        if len(self.current_trick) != 4:
            raise RuntimeError("Trick is not complete")
        spades_played = [(p, c) for p, c in self.current_trick if c.suit == Suit.SPADES]
        if spades_played:
            winner, _ = max(spades_played, key=lambda x: x[1].value)
        else:
            lead_cards = [(p, c) for p, c in self.current_trick if c.suit == self.lead_suit]
            winner, _ = max(lead_cards, key=lambda x: x[1].value)
        winner.tricks_won += 1
        self.trick_history.append(list(self.current_trick))
        self.total_tricks_played += 1
        self.current_trick = []
        self.lead_suit = None
        self.last_trick_winner_index = self.players.index(winner)
        self.current_player_index = self.last_trick_winner_index
        if self.total_tricks_played == 13:
            self.next_round_leader_index = self.last_trick_winner_index
        return winner

    def calculate_round_score(self) -> dict[int, int]:
        """Calculate scores for the round."""
        if self._last_round_scores is not None:
            for player in self.players:
                team_index = self._team_index_for_player(player)
                player.score = self.team_scores[team_index]
            return dict(self._last_round_scores)

        scores: dict[int, int] = {0: 0, 1: 0}
        for partnership_idx in [0, 1]:
            if partnership_idx == 0:
                team = [self.players[0], self.players[2]]
            else:
                team = [self.players[1], self.players[3]]
            nil_bonuses = 0
            non_nil_bid = 0
            non_nil_tricks = 0
            for player in team:
                if player.bid == 0:
                    if player.tricks_won == 0:
                        if player.blind_nil:
                            nil_bonuses += 200
                        else:
                            nil_bonuses += 100
                    else:
                        if player.blind_nil:
                            nil_bonuses -= 200
                        else:
                            nil_bonuses -= 100
                else:
                    non_nil_bid += player.bid or 0
                    non_nil_tricks += player.tricks_won
            total_bid = non_nil_bid
            total_tricks = non_nil_tricks
            if total_tricks >= total_bid:
                scores[partnership_idx] = total_bid * 10
                overtricks = total_tricks - total_bid
                scores[partnership_idx] += overtricks
                self.bags[partnership_idx] += overtricks
                if self.bags[partnership_idx] >= 10:
                    scores[partnership_idx] -= 100
                    self.bags[partnership_idx] -= 10
            else:
                scores[partnership_idx] = -total_bid * 10
            scores[partnership_idx] += nil_bonuses
            self.team_scores[partnership_idx] += scores[partnership_idx]
        for player in self.players:
            team_index = self._team_index_for_player(player)
            player.score = self.team_scores[team_index]
        self._last_round_scores = dict(scores)
        return scores

    def get_valid_plays(self, player: SpadesPlayer) -> list[Card]:
        """Get all valid cards a player can play."""
        return [card for card in player.hand if self.is_valid_play(player, card)]

    def suggest_bid(self, player: SpadesPlayer) -> int:
        """AI logic to suggest a bid."""
        spade_cards = [c for c in player.hand if c.suit == Suit.SPADES]
        non_spade_high_cards = [c for c in player.hand if c.suit != Suit.SPADES and c.rank in {"A", "K", "Q"}]
        if not any(card.rank in {"A", "K", "Q", "J"} for card in player.hand) and len(spade_cards) <= 1:
            return 0

        bid = 0.0
        for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
            suit_cards = [c for c in player.hand if c.suit == suit]
            if not suit_cards:
                bid += 0.5
                continue
            high_cards = sum(1 for c in suit_cards if c.rank in ("A", "K", "Q"))
            if suit == Suit.SPADES:
                bid += high_cards
                if len(suit_cards) >= 5:
                    bid += 1.5
                elif len(suit_cards) >= 4:
                    bid += 1
                elif len(suit_cards) == 3:
                    bid += 0.5
                if any(c.rank == "A" for c in suit_cards):
                    bid += 0.5
            else:
                bid += high_cards * 0.75
                if len(suit_cards) <= 2 and high_cards:
                    bid += 0.25

        if len(non_spade_high_cards) <= 1 and len(spade_cards) >= 6:
            bid += 1

        return min(int(round(bid)), 13)

    def select_card_to_play(self, player: SpadesPlayer) -> Card:
        """AI logic to select a card to play."""
        valid_cards = self.get_valid_plays(player)
        if len(valid_cards) == 1:
            return valid_cards[0]
        if not self.current_trick:
            non_spades = [c for c in valid_cards if c.suit != Suit.SPADES]
            if non_spades:
                return min(non_spades, key=lambda c: c.value)
            return min(valid_cards, key=lambda c: c.value)
        lead_suit_cards = [c for c in valid_cards if c.suit == self.lead_suit]
        if lead_suit_cards:
            return max(lead_suit_cards, key=lambda c: c.value)
        non_spades = [c for c in valid_cards if c.suit != Suit.SPADES]
        if non_spades:
            return max(non_spades, key=lambda c: c.value)
        return min(valid_cards, key=lambda c: c.value)

    def is_game_over(self) -> bool:
        """Check whether a partnership has reached the target score."""
        return any(score >= self.target_score for score in self.team_scores)

    def get_winner(self) -> Optional[int]:
        """Return the winning partnership index if the game is over."""
        if not self.is_game_over():
            return None
        if self.team_scores[0] == self.team_scores[1]:
            return None
        return 0 if self.team_scores[0] > self.team_scores[1] else 1

    def _team_index_for_player(self, player: SpadesPlayer) -> int:
        """Determine the partnership index for a player."""
        player_index = self.players.index(player)
        return 0 if player_index in (0, 2) else 1
