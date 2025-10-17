"""Crazy Eights card game engine.

This module implements the classic Crazy Eights shedding game where players
try to discard all their cards by matching the rank or suit of the previous
card. Eights are wild and allow the player to declare a new suit.

Rules:
- 2-6 players, with 5 or 7 cards dealt to each.
- Players take turns playing a card that matches the active card's rank or suit.
- Eights are wild and can be played on any card.
- If unable to play, a player must draw cards until they can play or a limit is reached.
- The first player to discard all their cards wins the round.
- The winner scores points based on the cards remaining in opponents' hands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from random import Random
from typing import Optional

from card_games.common.cards import Card, Deck, Suit


class GameState(Enum):
    """Enumerates the possible states of the Crazy Eights game."""

    PLAYING = auto()
    GAME_OVER = auto()


@dataclass
class Player:
    """Represents a player in a game of Crazy Eights.

    Attributes:
        name: The player's name.
        hand: A list of cards currently in the player's hand.
        score: The player's total score across all rounds.
    """

    name: str
    hand: list[Card] = field(default_factory=list)
    score: int = 0

    def has_playable_card(self, active_suit: Suit, active_rank: str) -> bool:
        """Check if the player has any card that can be legally played.

        Args:
            active_suit: The current suit that must be matched.
            active_rank: The current rank that must be matched.

        Returns:
            True if the player has at least one playable card.
        """
        return any(self._is_card_playable(card, active_suit, active_rank) for card in self.hand)

    def get_playable_cards(self, active_suit: Suit, active_rank: str) -> list[Card]:
        """Get a list of all cards that the player can legally play.

        Args:
            active_suit: The current suit to match.
            active_rank: The current rank to match.

        Returns:
            A list of playable cards from the player's hand.
        """
        return [card for card in self.hand if self._is_card_playable(card, active_suit, active_rank)]

    def calculate_hand_value(self) -> int:
        """Calculate the total point value of the cards remaining in the hand.

        Returns:
            The total point value (eights are 50, face cards 10, others face value).
        """
        value = 0
        for card in self.hand:
            if card.rank == "8":
                value += 50
            elif card.rank in ("J", "Q", "K", "A"):
                value += 10
            else:
                value += int(card.rank) if card.rank.isdigit() else 10
        return value

    def _is_card_playable(self, card: Card, active_suit: Suit, active_rank: str) -> bool:
        """Check if a single card is playable."""
        return card.rank == "8" or card.suit == active_suit or card.rank == active_rank


@dataclass
class CrazyEightsGame:
    """The main engine for the Crazy Eights game.

    Attributes:
        players: A list of players in the game.
        deck: The draw pile.
        discard_pile: The pile of discarded cards.
        active_suit: The current suit that must be matched.
        active_rank: The current rank that must be matched.
        current_player_idx: The index of the current player in the `players` list.
        state: The current state of the game (e.g., PLAYING, GAME_OVER).
        draw_limit: The maximum number of cards a player can draw if they cannot play.
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
        """Initialize a new game of Crazy Eights.

        Args:
            num_players: The number of players (must be between 2 and 6).
            player_names: An optional list of names for the players.
            draw_limit: The maximum cards a player can draw if unable to play.
            rng: An optional `random.Random` instance for deterministic games.

        Raises:
            ValueError: If the number of players is not between 2 and 6.
        """
        if not (2 <= num_players <= 6):
            raise ValueError("Crazy Eights requires 2-6 players.")

        self.players = [Player(name=(player_names[i] if player_names else f"Player {i + 1}")) for i in range(num_players)]
        self.deck = Deck()
        self.discard_pile = []
        self.active_suit = None
        self.active_rank = ""
        self.current_player_idx = 0
        self.state = GameState.PLAYING
        self.draw_limit = draw_limit

        self.deck.shuffle(rng=rng)
        cards_to_deal = 5 if num_players == 2 else 7
        for player in self.players:
            player.hand = self.deck.deal(cards_to_deal)

        if self.deck.cards:
            first_card = self.deck.deal(1)[0]
            self.discard_pile.append(first_card)
            self.active_suit = first_card.suit
            self.active_rank = first_card.rank
            if first_card.rank == "8":
                self.active_suit = Suit.HEARTS  # Default suit for an opening 8

    def get_current_player(self) -> Player:
        """Return the player whose turn it is."""
        return self.players[self.current_player_idx]

    def get_top_card(self) -> Optional[Card]:
        """Return the top card of the discard pile."""
        return self.discard_pile[-1] if self.discard_pile else None

    def play_card(self, card: Card, new_suit: Optional[Suit] = None) -> dict[str, any]:
        """Play a card from the current player's hand.

        Args:
            card: The card to be played.
            new_suit: The new suit to declare if an eight is played.

        Returns:
            A dictionary containing the result of the action.
        """
        if self.state == GameState.GAME_OVER:
            return {"success": False, "message": "The game is over."}

        player = self.get_current_player()
        if card not in player.hand:
            return {"success": False, "message": "Card is not in the player's hand."}
        if not self._is_valid_play(card):
            return {"success": False, "message": "This card cannot be played."}

        player.hand.remove(card)
        self.discard_pile.append(card)

        if card.rank == "8":
            if not new_suit:
                return {"success": False, "message": "A new suit must be declared for an 8."}
            self.active_suit = new_suit
            message = f"{player.name} played {card} and changed the suit to {new_suit.value}."
        else:
            self.active_suit = card.suit
            message = f"{player.name} played {card}."

        self.active_rank = card.rank

        if not player.hand:
            self.state = GameState.GAME_OVER
            for p in self.players:
                if p != player:
                    player.score += p.calculate_hand_value()
            return {"success": True, "message": message, "game_over": True, "winner": player.name}

        self._next_turn()
        return {"success": True, "message": message}

    def draw_card(self) -> dict[str, any]:
        """Draw a card for the current player."""
        if self.state == GameState.GAME_OVER:
            return {"success": False, "message": "The game is over."}

        if not self.deck.cards:
            if len(self.discard_pile) > 1:
                top_card = self.discard_pile.pop()
                self.deck.cards = self.discard_pile
                self.discard_pile = [top_card]
                self.deck.shuffle()
            else:
                return {"success": False, "message": "No cards left to draw."}

        player = self.get_current_player()
        card = self.deck.deal(1)[0]
        player.hand.append(card)
        return {"success": True, "message": f"{player.name} drew a card.", "card": card}

    def pass_turn(self) -> dict[str, any]:
        """Pass the current player's turn."""
        if self.state == GameState.GAME_OVER:
            return {"success": False, "message": "The game is over."}

        player = self.get_current_player()
        self._next_turn()
        return {"success": True, "message": f"{player.name} passed."}

    def _is_valid_play(self, card: Card) -> bool:
        """Check if a card can be legally played on the discard pile."""
        return card.rank == "8" or card.suit == self.active_suit or card.rank == self.active_rank

    def _next_turn(self) -> None:
        """Move to the next player's turn."""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

    def get_state_summary(self) -> dict[str, any]:
        """Return a summary of the current game state."""
        return {
            "current_player": self.get_current_player().name,
            "active_suit": self.active_suit.value if self.active_suit else "None",
            "active_rank": self.active_rank,
            "top_card": str(self.get_top_card()) if self.get_top_card() else "None",
            "deck_cards": len(self.deck.cards),
            "players": [{"name": p.name, "hand_size": len(p.hand), "score": p.score} for p in self.players],
            "state": self.state.name,
        }

    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.state == GameState.GAME_OVER
