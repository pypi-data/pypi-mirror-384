"""Go Fish card game engine.

This module implements the classic card game Go Fish, where players try to
collect sets of four cards of the same rank by asking opponents for specific
cards.

Rules:
* 2-6 players (default 2)
* 5 cards dealt to each player (7 for 2 players)
* Players take turns asking opponents for cards of a specific rank
* If opponent has the rank, they must give all cards of that rank
* If opponent doesn't have it, they say "Go Fish!" and asking player draws
* When a player completes a set of 4, they lay it down and score 1 point
* Game ends when all sets are made; player with most sets wins
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from random import Random
from typing import Any, Dict, Optional

from card_games.common.cards import RANKS, Card, Deck, Suit
from common.architecture.events import EventBus, GameEventType, get_global_event_bus


class GameState(Enum):
    """Current state of the Go Fish game."""

    PLAYING = auto()
    GAME_OVER = auto()


@dataclass
class Player:
    """Represents a player in Go Fish.

    Attributes:
        name: Player's name
        hand: Cards in player's hand
        books: Number of complete sets (books) collected
    """

    name: str
    hand: list[Card] = field(default_factory=list)
    books: int = 0

    def has_rank(self, rank: str) -> bool:
        """Check if player has any cards of a given rank."""

        return any(card.rank == rank for card in self.hand)

    def get_cards_of_rank(self, rank: str) -> list[Card]:
        """Get all cards of a specific rank from hand."""

        return [card for card in self.hand if card.rank == rank]

    def remove_cards_of_rank(self, rank: str) -> list[Card]:
        """Remove and return all cards of a specific rank."""

        cards = self.get_cards_of_rank(rank)
        self.hand = [card for card in self.hand if card.rank != rank]
        return cards

    def check_for_books(self) -> int:
        """Check for and remove any complete sets of 4."""

        rank_counts: dict[str, int] = {}
        for card in self.hand:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1

        new_books = 0
        for rank, count in rank_counts.items():
            if count == 4:
                self.remove_cards_of_rank(rank)
                self.books += 1
                new_books += 1

        return new_books


@dataclass
class GoFishGame:
    """Go Fish game engine with event bus integration and persistence helpers."""

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
        if num_players < 2 or num_players > 6:
            raise ValueError("Go Fish requires 2-6 players")

        self._event_bus = event_bus
        self.players = []
        self.deck = Deck()
        self.current_player_idx = 0
        self.state = GameState.PLAYING
        self.last_action = ""

        if player_names is None:
            player_names = [f"Player {i + 1}" for i in range(num_players)]
        elif len(player_names) != num_players:
            raise ValueError(f"Expected {num_players} names, got {len(player_names)}")

        for name in player_names:
            self.players.append(Player(name=name))

        self.deck.shuffle(rng=rng)
        cards_per_player = 7 if num_players == 2 else 5

        for player in self.players:
            player.hand = self.deck.deal(cards_per_player)
            books = player.check_for_books()
            if books:
                self.emit_event(
                    GameEventType.SCORE_UPDATED,
                    {
                        "player": player.name,
                        "new_books": books,
                        "total_books": player.books,
                    },
                )

        self.emit_event(
            GameEventType.GAME_INITIALIZED,
            {
                "players": [player.name for player in self.players],
                "deck_size": len(self.deck.cards),
            },
        )
        self.emit_event(
            GameEventType.GAME_START,
            {
                "current_player": self.get_current_player().name,
                "total_players": len(self.players),
            },
        )

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Attach a specific :class:`EventBus` instance to the game."""

        self._event_bus = event_bus

    @property
    def event_bus(self) -> EventBus:
        """Return the active :class:`EventBus`, defaulting to the global bus."""

        bus = getattr(self, "_event_bus", None)
        if bus is None:
            bus = get_global_event_bus()
            self._event_bus = bus
        return bus

    def emit_event(self, event_type: GameEventType | str, data: Optional[Dict[str, Any]] = None) -> None:
        """Emit an event through the configured :class:`EventBus`."""

        name = event_type.value if isinstance(event_type, GameEventType) else event_type
        self.event_bus.emit(name, data=data or {}, source=self.__class__.__name__)

    def get_current_player(self) -> Player:
        """Get the player whose turn it is."""

        return self.players[self.current_player_idx]

    def get_player_by_name(self, name: str) -> Optional[Player]:
        """Get a player by name."""

        for player in self.players:
            if player.name == name:
                return player
        return None

    def ask_for_cards(self, target_player_name: str, rank: str) -> Dict[str, Any]:
        """Current player asks another player for cards of a specific rank."""

        if self.state == GameState.GAME_OVER:
            return {"success": False, "message": "Game is over"}

        current_player = self.get_current_player()
        target_player = self.get_player_by_name(target_player_name)

        if target_player is None:
            return {"success": False, "message": f"Player {target_player_name} not found"}

        if target_player == current_player:
            return {"success": False, "message": "Cannot ask yourself"}

        if rank not in RANKS:
            return {"success": False, "message": f"Invalid rank: {rank}"}

        if not current_player.has_rank(rank):
            return {"success": False, "message": f"You don't have any {rank}s to ask for"}

        cards_received = 0
        new_books = 0
        drew_card = False
        drawn_rank: Optional[str] = None
        lucky_draw = False
        extra_turn = False
        next_turn = current_player.name

        if target_player.has_rank(rank):
            cards = target_player.remove_cards_of_rank(rank)
            current_player.hand.extend(cards)
            cards_received = len(cards)
            new_books = current_player.check_for_books()
            extra_turn = True
            self.last_action = f"{current_player.name} got {cards_received} {rank}(s) from {target_player.name}"
            if new_books:
                self.last_action += f" and made {new_books} book(s)!"
        else:
            self.last_action = f"{current_player.name} asked {target_player.name} for {rank}s. Go Fish!"
            if self.deck.cards:
                drawn_cards = self.deck.deal(1)
                drawn_card = drawn_cards[0] if drawn_cards else None
                if drawn_card:
                    current_player.hand.append(drawn_card)
                    drew_card = True
                    drawn_rank = drawn_card.rank
                    self.last_action += f" Drew {drawn_card}"
                    if drawn_card.rank == rank:
                        lucky_draw = True
                        extra_turn = True
                        new_books = current_player.check_for_books()
                        if new_books:
                            self.last_action += f" Made {new_books} book(s)!"
                    else:
                        self._next_turn()
                        next_turn = self.get_current_player().name
            else:
                self._next_turn()
                next_turn = self.get_current_player().name

        result: Dict[str, Any] = {
            "success": True,
            "got_cards": cards_received > 0,
            "cards_received": cards_received,
            "new_books": new_books,
            "message": self.last_action,
            "next_turn": next_turn,
            "drew_card": drew_card,
            "drawn_rank": drawn_rank,
            "lucky_draw": lucky_draw,
            "extra_turn": extra_turn,
        }

        self._emit_action_event(
            acting_player=current_player,
            target_player=target_player,
            rank=rank,
            outcome=result,
        )

        if self._is_game_over():
            self.state = GameState.GAME_OVER
            winner = self._get_winner().name
            result["game_over"] = True
            result["winner"] = winner
            self.emit_event(
                GameEventType.GAME_OVER,
                {
                    "winner": winner,
                    "books": {player.name: player.books for player in self.players},
                },
            )
        else:
            self.emit_event(
                GameEventType.TURN_COMPLETE,
                {
                    "current_player": self.get_current_player().name,
                    "deck_size": len(self.deck.cards),
                    "books": {player.name: player.books for player in self.players},
                },
            )

        return result

    def _emit_action_event(
        self,
        *,
        acting_player: Player,
        target_player: Player,
        rank: str,
        outcome: Dict[str, Any],
    ) -> None:
        """Emit an action processed event summarizing the latest turn."""

        payload = {
            "acting_player": acting_player.name,
            "target_player": target_player.name,
            "rank": rank,
            "books": {player.name: player.books for player in self.players},
            "deck_size": len(self.deck.cards),
        }
        payload.update(outcome)
        self.emit_event(GameEventType.ACTION_PROCESSED, payload)

        new_books = outcome.get("new_books")
        if isinstance(new_books, int) and new_books > 0:
            self.emit_event(
                GameEventType.SCORE_UPDATED,
                {
                    "player": acting_player.name,
                    "new_books": new_books,
                    "total_books": acting_player.books,
                },
            )

    def _next_turn(self) -> None:
        """Move to the next player's turn."""

        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

    def _is_game_over(self) -> bool:
        """Check if the game is over."""

        total_books = sum(player.books for player in self.players)
        if total_books == 13:
            return True

        if not self.deck.cards and all(not player.hand for player in self.players):
            return True

        return False

    def _get_winner(self) -> Player:
        """Get the player with the most books."""

        return max(self.players, key=lambda p: p.books)

    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of the current game state."""

        return {
            "current_player": self.get_current_player().name,
            "deck_cards": len(self.deck.cards),
            "players": [{"name": p.name, "hand_size": len(p.hand), "books": p.books} for p in self.players],
            "state": self.state.name,
            "last_action": self.last_action,
        }

    def is_game_over(self) -> bool:
        """Check if the game is over."""

        return self.state == GameState.GAME_OVER

    def to_state(self) -> Dict[str, Any]:
        """Return a serializable representation of the current game state."""

        return {
            "players": [
                {
                    "name": player.name,
                    "hand": [self._card_to_dict(card) for card in player.hand],
                    "books": player.books,
                }
                for player in self.players
            ],
            "deck": [self._card_to_dict(card) for card in self.deck.cards],
            "current_player_idx": self.current_player_idx,
            "state": self.state.name,
            "last_action": self.last_action,
        }

    @classmethod
    def from_state(
        cls,
        state: Dict[str, Any],
        *,
        event_bus: Optional[EventBus] = None,
    ) -> "GoFishGame":
        """Restore a :class:`GoFishGame` from serialized state."""

        game: "GoFishGame" = cls.__new__(cls)
        game._event_bus = event_bus
        game.players = []

        for player_state in state.get("players", []):
            hand = [cls._card_from_dict(card_state) for card_state in player_state.get("hand", [])]
            game.players.append(
                Player(
                    name=player_state.get("name", "Player"),
                    hand=hand,
                    books=int(player_state.get("books", 0)),
                )
            )

        if not game.players:
            raise ValueError("Saved Go Fish state must include at least one player")

        game.deck = Deck(cards=[cls._card_from_dict(card_state) for card_state in state.get("deck", [])])
        game.current_player_idx = int(state.get("current_player_idx", 0)) % len(game.players)
        game.state = GameState[state.get("state", GameState.PLAYING.name)]
        game.last_action = state.get("last_action", "")

        game.emit_event(
            GameEventType.GAME_INITIALIZED,
            {
                "players": [player.name for player in game.players],
                "deck_size": len(game.deck.cards),
                "loaded": True,
            },
        )
        if game.state == GameState.GAME_OVER:
            winner = game._get_winner().name
            game.emit_event(
                GameEventType.GAME_OVER,
                {
                    "winner": winner,
                    "books": {player.name: player.books for player in game.players},
                    "loaded": True,
                },
            )
        else:
            game.emit_event(
                GameEventType.GAME_START,
                {
                    "current_player": game.get_current_player().name,
                    "loaded": True,
                },
            )

        return game

    @staticmethod
    def _card_to_dict(card: Card) -> Dict[str, str]:
        """Serialize a :class:`Card` to a dictionary."""

        return {"rank": card.rank, "suit": card.suit.value}

    @staticmethod
    def _card_from_dict(data: Dict[str, str]) -> Card:
        """Deserialize a :class:`Card` from a dictionary."""

        return Card(data["rank"], Suit(data["suit"]))
