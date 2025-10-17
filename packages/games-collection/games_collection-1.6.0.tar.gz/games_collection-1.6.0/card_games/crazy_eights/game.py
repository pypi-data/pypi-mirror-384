"""Crazy Eights card game engine.

This module implements the classic Crazy Eights shedding game where players
try to discard all their cards by matching rank or suit. Eights are wild and
allow changing the active suit.

Rules:
* 2-6 players, 5-7 cards each (5 for 2 players, 7 for 3+)
* Players take turns playing cards that match the active card's rank or suit
* Eights are wild - player can declare any suit
* If unable to play, draw cards until able to play (or limit reached)
* First player to discard all cards wins
* Scoring: Winner gets points for cards left in opponents' hands
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from random import Random
from typing import Optional

from card_games.common.cards import Card, Deck, Suit


class GameState(Enum):
    """Current state of the Crazy Eights game."""

    PLAYING = auto()
    GAME_OVER = auto()


@dataclass
class Player:
    """Represents a player in Crazy Eights.

    Attributes:
        name: Player's name
        hand: Cards in player's hand
        score: Total score across rounds
    """

    name: str
    hand: list[Card] = field(default_factory=list)
    score: int = 0

    def has_playable_card(self, active_suit: Suit, active_rank: str) -> bool:
        """Check if player has a card they can play.

        Args:
            active_suit: Current active suit
            active_rank: Current active rank

        Returns:
            True if player has at least one playable card
        """
        return any(card.rank == "8" or card.suit == active_suit or card.rank == active_rank for card in self.hand)

    def get_playable_cards(self, active_suit: Suit, active_rank: str) -> list[Card]:
        """Get all cards the player can currently play.

        Args:
            active_suit: Current active suit
            active_rank: Current active rank

        Returns:
            List of playable cards
        """
        return [card for card in self.hand if card.rank == "8" or card.suit == active_suit or card.rank == active_rank]

    def calculate_hand_value(self) -> int:
        """Calculate point value of cards in hand.

        Returns:
            Total point value (eights=50, face cards=10, numbers=face value)
        """
        total = 0
        for card in self.hand:
            if card.rank == "8":
                total += 50
            elif card.rank in ("J", "Q", "K", "A"):
                total += 10
            else:
                total += int(card.rank) if card.rank.isdigit() else 10
        return total


@dataclass
class CrazyEightsGame:
    """Crazy Eights game engine.

    Attributes:
        players: List of players
        deck: Draw pile
        discard_pile: Discard pile
        active_suit: Current active suit for play
        active_rank: Current active rank
        current_player_idx: Index of current player
        state: Current game state
        draw_limit: Max cards to draw when unable to play (0 = unlimited)
    """

    players: list[Player] = field(default_factory=list)
    deck: Deck = field(default_factory=Deck)
    discard_pile: list[Card] = field(default_factory=list)
    active_suit: Optional[Suit] = None
    active_rank: str = ""
    current_player_idx: int = 0
    state: GameState = GameState.PLAYING
    draw_limit: int = 3

    def __init__(self, num_players: int = 2, player_names: Optional[list[str]] = None, draw_limit: int = 3, rng: Optional[Random] = None) -> None:
        """Initialize a new Crazy Eights game.

        Args:
            num_players: Number of players (2-6)
            player_names: Optional list of player names
            draw_limit: Max cards to draw when unable to play (0 = draw until can play)
            rng: Optional Random instance for deterministic games

        Raises:
            ValueError: If num_players is not between 2 and 6
        """
        if num_players < 2 or num_players > 6:
            raise ValueError("Crazy Eights requires 2-6 players")

        self.players = []
        self.deck = Deck()
        self.discard_pile = []
        self.active_suit = None
        self.active_rank = ""
        self.current_player_idx = 0
        self.state = GameState.PLAYING
        self.draw_limit = draw_limit

        # Create players
        if player_names is None:
            player_names = [f"Player {i + 1}" for i in range(num_players)]
        elif len(player_names) != num_players:
            raise ValueError(f"Expected {num_players} names, got {len(player_names)}")

        for name in player_names:
            self.players.append(Player(name=name))

        # Shuffle and deal
        self.deck.shuffle(rng=rng)
        cards_per_player = 5 if num_players == 2 else 7

        for player in self.players:
            player.hand = self.deck.deal(cards_per_player)

        # Flip first card
        if self.deck.cards:
            first_card = self.deck.deal(1)[0]
            self.discard_pile.append(first_card)
            self.active_suit = first_card.suit
            self.active_rank = first_card.rank

            # If first card is an 8, set random suit
            if first_card.rank == "8":
                self.active_suit = Suit.HEARTS  # Default to hearts

    def get_current_player(self) -> Player:
        """Get the player whose turn it is.

        Returns:
            Current player
        """
        return self.players[self.current_player_idx]

    def get_top_card(self) -> Optional[Card]:
        """Get the top card of the discard pile.

        Returns:
            Top card or None if pile is empty
        """
        return self.discard_pile[-1] if self.discard_pile else None

    def play_card(self, card: Card, new_suit: Optional[Suit] = None) -> dict[str, any]:
        """Current player plays a card.

        Args:
            card: Card to play
            new_suit: If playing an 8, the new suit to declare

        Returns:
            Dictionary with action results
        """
        if self.state == GameState.GAME_OVER:
            return {"success": False, "message": "Game is over"}

        current_player = self.get_current_player()

        # Validate card is in hand
        if card not in current_player.hand:
            return {"success": False, "message": "Card not in hand"}

        # Validate play is legal
        if not self._is_valid_play(card):
            return {"success": False, "message": f"Cannot play {card} on {self.active_suit.value} {self.active_rank}"}

        # Play the card
        current_player.hand.remove(card)
        self.discard_pile.append(card)

        # Handle eights
        if card.rank == "8":
            if new_suit is None:
                return {"success": False, "message": "Must declare a suit when playing an 8"}
            self.active_suit = new_suit
            self.active_rank = card.rank
            message = f"{current_player.name} played {card} and changed suit to {new_suit.value}"
        else:
            self.active_suit = card.suit
            self.active_rank = card.rank
            message = f"{current_player.name} played {card}"

        # Check for win
        if not current_player.hand:
            self.state = GameState.GAME_OVER
            # Calculate winner's score
            for player in self.players:
                if player != current_player:
                    current_player.score += player.calculate_hand_value()

            return {"success": True, "message": message, "game_over": True, "winner": current_player.name, "score": current_player.score}

        # Move to next player
        self._next_turn()

        return {"success": True, "message": message, "next_player": self.get_current_player().name}

    def draw_card(self) -> dict[str, any]:
        """Current player draws a card.

        Returns:
            Dictionary with draw results
        """
        if self.state == GameState.GAME_OVER:
            return {"success": False, "message": "Game is over"}

        current_player = self.get_current_player()

        if not self.deck.cards:
            # Reshuffle discard pile if deck is empty (keep top card)
            if len(self.discard_pile) > 1:
                top_card = self.discard_pile.pop()
                self.deck.cards = self.discard_pile
                self.discard_pile = [top_card]
                self.deck.shuffle()
            else:
                return {"success": False, "message": "No cards left to draw"}

        card = self.deck.deal(1)[0]
        current_player.hand.append(card)

        return {"success": True, "message": f"{current_player.name} drew a card", "card": card}

    def pass_turn(self) -> dict[str, any]:
        """Current player passes their turn (after drawing max cards).

        Returns:
            Dictionary with pass results
        """
        if self.state == GameState.GAME_OVER:
            return {"success": False, "message": "Game is over"}

        current_player = self.get_current_player()
        self._next_turn()

        return {"success": True, "message": f"{current_player.name} passed", "next_player": self.get_current_player().name}

    def _is_valid_play(self, card: Card) -> bool:
        """Check if a card can be legally played.

        Args:
            card: Card to check

        Returns:
            True if card can be played
        """
        # Eights are always playable
        if card.rank == "8":
            return True

        # Must match active suit or rank
        return card.suit == self.active_suit or card.rank == self.active_rank

    def _next_turn(self) -> None:
        """Move to the next player's turn."""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

    def get_state_summary(self) -> dict[str, any]:
        """Get a summary of the current game state.

        Returns:
            Dictionary with game statistics
        """
        return {
            "current_player": self.get_current_player().name,
            "active_suit": self.active_suit.value if self.active_suit else None,
            "active_rank": self.active_rank,
            "top_card": str(self.get_top_card()) if self.get_top_card() else None,
            "deck_cards": len(self.deck.cards),
            "players": [{"name": p.name, "hand_size": len(p.hand), "score": p.score} for p in self.players],
            "state": self.state.name,
        }

    def is_game_over(self) -> bool:
        """Check if the game is over.

        Returns:
            True if game is over
        """
        return self.state == GameState.GAME_OVER
