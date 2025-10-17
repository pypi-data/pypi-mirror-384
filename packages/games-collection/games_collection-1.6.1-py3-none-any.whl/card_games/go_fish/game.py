"""Go Fish card game engine.

This module implements the classic card game Go Fish, where players try to
collect sets of four cards of the same rank ("books") by asking opponents for
specific cards.

Key Rules:
- 2-6 players.
- 5 cards are dealt to each player (7 if there are 2 players).
- Players take turns asking an opponent for cards of a specific rank.
- If the opponent has the requested rank, they must give all cards of that rank.
- If not, the asking player must "Go Fish" by drawing from the deck.
- When a player collects a set of 4, they lay it down as a "book" and score a point.
- The game ends when all 13 books have been made.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from random import Random
from typing import Any, Dict, Optional

from card_games.common.cards import RANKS, Card, Deck
from common.architecture.events import EventBus, GameEventType, get_global_event_bus


class GameState(Enum):
    """Enumerates the possible states of the Go Fish game."""

    PLAYING = auto()
    GAME_OVER = auto()


@dataclass
class Player:
    """Represents a player in a game of Go Fish.

    Attributes:
        name: The player's name.
        hand: A list of cards currently in the player's hand.
        books: The number of complete sets (books) the player has collected.
    """

    name: str
    hand: list[Card] = field(default_factory=list)
    books: int = 0

    def has_rank(self, rank: str) -> bool:
        """Check if the player has any cards of a given rank."""
        return any(card.rank == rank for card in self.hand)

    def get_cards_of_rank(self, rank: str) -> list[Card]:
        """Get all cards of a specific rank from the player's hand."""
        return [card for card in self.hand if card.rank == rank]

    def remove_cards_of_rank(self, rank: str) -> list[Card]:
        """Remove and return all cards of a specific rank from the hand."""
        cards_to_remove = self.get_cards_of_rank(rank)
        self.hand = [card for card in self.hand if card.rank != rank]
        return cards_to_remove

    def check_for_books(self) -> int:
        """Check for and remove any complete sets of 4 cards (books)."""
        rank_counts = {}
        for card in self.hand:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1

        books_made = 0
        for rank, count in rank_counts.items():
            if count == 4:
                self.remove_cards_of_rank(rank)
                self.books += 1
                books_made += 1
        return books_made


@dataclass
class GoFishGame:
    """The main engine for the Go Fish game.

    This class manages the game state, including players, the deck, and the
    overall flow of the game. It also integrates with an event bus to announce
    game events.

    Attributes:
        players: A list of players in the game.
        deck: The draw pile.
        current_player_idx: The index of the current player.
        state: The current state of the game (e.g., PLAYING, GAME_OVER).
        last_action: A string describing the last action taken.
    """

    players: list[Player] = field(default_factory=list)
    deck: Deck = field(default_factory=Deck)
    current_player_idx: int = 0
    state: GameState = GameState.PLAYING
    last_action: str = ""

    def __init__(
        self,
        num_players: int = 2,
        player_names: Optional[list[str]] = None,
        rng: Optional[Random] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """Initialize a new game of Go Fish."""
        if not (2 <= num_players <= 6):
            raise ValueError("Go Fish requires 2-6 players.")

        self._event_bus = event_bus or get_global_event_bus()
        player_names = player_names or [f"Player {i+1}" for i in range(num_players)]
        if len(player_names) != num_players:
            raise ValueError("Number of player names must match the number of players.")

        self.players = [Player(name=name) for name in player_names]
        self.deck = Deck()
        self.deck.shuffle(rng=rng)

        cards_per_player = 7 if num_players == 2 else 5
        for player in self.players:
            player.hand = self.deck.deal(cards_per_player)
            if books := player.check_for_books():
                self.emit_event(
                    GameEventType.SCORE_UPDATED,
                    {"player": player.name, "new_books": books, "total_books": player.books},
                )

        self.emit_event(GameEventType.GAME_INITIALIZED, {"players": player_names})
        self.emit_event(GameEventType.GAME_START, {"current_player": self.get_current_player().name})

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Attach a specific event bus to the game instance."""
        self._event_bus = event_bus

    @property
    def event_bus(self) -> EventBus:
        """Return the active event bus, defaulting to the global instance."""
        return self._event_bus

    def emit_event(self, event_type: GameEventType | str, data: Optional[Dict[str, Any]] = None) -> None:
        """Emit a game event through the configured event bus."""
        name = event_type.value if isinstance(event_type, GameEventType) else event_type
        self.event_bus.emit(name, data=data or {}, source=self.__class__.__name__)

    def get_current_player(self) -> Player:
        """Return the player whose turn it is."""
        return self.players[self.current_player_idx]

    def get_player_by_name(self, name: str) -> Optional[Player]:
        """Return a player instance by their name."""
        return next((p for p in self.players if p.name == name), None)

    def ask_for_cards(self, target_player_name: str, rank: str) -> Dict[str, Any]:
        """The current player asks another for cards of a specific rank."""
        if self.state == GameState.GAME_OVER:
            return {"success": False, "message": "The game is over."}

        current_player = self.get_current_player()
        target_player = self.get_player_by_name(target_player_name)

        if not target_player or target_player == current_player:
            return {"success": False, "message": "Invalid target player."}
        if rank not in RANKS:
            return {"success": False, "message": "Invalid rank."}
        if not current_player.has_rank(rank):
            return {"success": False, "message": "You must hold a card of the rank you ask for."}

        if target_player.has_rank(rank):
            cards = target_player.remove_cards_of_rank(rank)
            current_player.hand.extend(cards)
            new_books = current_player.check_for_books()
            self.last_action = f"{current_player.name} got {len(cards)} {rank}s from {target_player.name}."
            return {"success": True, "got_cards": True, "cards_received": len(cards), "new_books": new_books}

        self.last_action = f"{current_player.name} asked for {rank}s and was told to 'Go Fish!'"
        drew_card = None
        if self.deck.cards:
            drew_card = self.deck.deal(1)[0]
            current_player.hand.append(drew_card)
            if drew_card.rank == rank:
                self.last_action += f" They drew a {drew_card} and get another turn."
                return {"success": True, "got_cards": False, "drew_card": str(drew_card)}

        self._next_turn()
        return {"success": True, "got_cards": False, "drew_card": str(drew_card) if drew_card else None}

    def _next_turn(self) -> None:
        """Advance the turn to the next player."""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

    def _is_game_over(self) -> bool:
        """Check if the game has ended."""
        return sum(p.books for p in self.players) == 13 or (not self.deck.cards and not any(p.hand for p in self.players))

    def _get_winner(self) -> Player:
        """Determine the winner based on the number of books."""
        return max(self.players, key=lambda p: p.books)

    def get_state_summary(self) -> Dict[str, Any]:
        """Return a summary of the current game state."""
        return {
            "current_player": self.get_current_player().name,
            "deck_cards": len(self.deck.cards),
            "players": [{"name": p.name, "hand_size": len(p.hand), "books": p.books} for p in self.players],
            "state": self.state.name,
            "last_action": self.last_action,
        }

    def is_game_over(self) -> bool:
        """Check if the game is over."""
        if self.state == GameState.GAME_OVER:
            return True
        if self._is_game_over():
            self.state = GameState.GAME_OVER
            return True
        return False
