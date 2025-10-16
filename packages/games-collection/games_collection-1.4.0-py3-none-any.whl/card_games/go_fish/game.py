"""Go Fish card game engine.

This module implements the classic card game Go Fish, where players try to
collect sets of four cards of the same rank by asking opponents for specific cards.

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
from typing import Optional

from card_games.common.cards import RANKS, Card, Deck


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
        """Check if player has any cards of a given rank.

        Args:
            rank: Card rank to check for

        Returns:
            True if player has at least one card of that rank
        """
        return any(card.rank == rank for card in self.hand)

    def get_cards_of_rank(self, rank: str) -> list[Card]:
        """Get all cards of a specific rank from hand.

        Args:
            rank: Card rank to get

        Returns:
            List of cards of that rank
        """
        return [card for card in self.hand if card.rank == rank]

    def remove_cards_of_rank(self, rank: str) -> list[Card]:
        """Remove and return all cards of a specific rank.

        Args:
            rank: Card rank to remove

        Returns:
            List of removed cards
        """
        cards = self.get_cards_of_rank(rank)
        self.hand = [card for card in self.hand if card.rank != rank]
        return cards

    def check_for_books(self) -> int:
        """Check for and remove any complete sets of 4.

        Returns:
            Number of new books formed
        """
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
    """Go Fish game engine.

    Attributes:
        players: List of players in the game
        deck: Remaining cards in the draw pile
        current_player_idx: Index of current player
        state: Current game state
        last_action: Description of last action taken
    """

    players: list[Player] = field(default_factory=list)
    deck: Deck = field(default_factory=Deck)
    current_player_idx: int = 0
    state: GameState = GameState.PLAYING
    last_action: str = ""

    def __init__(self, num_players: int = 2, player_names: Optional[list[str]] = None, rng: Optional[Random] = None) -> None:
        """Initialize a new Go Fish game.

        Args:
            num_players: Number of players (2-6)
            player_names: Optional list of player names
            rng: Optional Random instance for deterministic games

        Raises:
            ValueError: If num_players is not between 2 and 6
        """
        if num_players < 2 or num_players > 6:
            raise ValueError("Go Fish requires 2-6 players")

        self.players = []
        self.deck = Deck()
        self.current_player_idx = 0
        self.state = GameState.PLAYING
        self.last_action = ""

        # Create players
        if player_names is None:
            player_names = [f"Player {i + 1}" for i in range(num_players)]
        elif len(player_names) != num_players:
            raise ValueError(f"Expected {num_players} names, got {len(player_names)}")

        for name in player_names:
            self.players.append(Player(name=name))

        # Shuffle and deal
        self.deck.shuffle(rng=rng)
        cards_per_player = 7 if num_players == 2 else 5

        for player in self.players:
            player.hand = self.deck.deal(cards_per_player)
            # Check for initial books
            player.check_for_books()

    def get_current_player(self) -> Player:
        """Get the player whose turn it is.

        Returns:
            Current player
        """
        return self.players[self.current_player_idx]

    def get_player_by_name(self, name: str) -> Optional[Player]:
        """Get a player by name.

        Args:
            name: Player's name

        Returns:
            Player with that name, or None if not found
        """
        for player in self.players:
            if player.name == name:
                return player
        return None

    def ask_for_cards(self, target_player_name: str, rank: str) -> dict[str, any]:
        """Current player asks another player for cards of a specific rank.

        Args:
            target_player_name: Name of player to ask
            rank: Rank of cards to ask for

        Returns:
            Dictionary with action results
        """
        if self.state == GameState.GAME_OVER:
            return {"success": False, "message": "Game is over"}

        current_player = self.get_current_player()
        target_player = self.get_player_by_name(target_player_name)

        # Validation
        if target_player is None:
            return {"success": False, "message": f"Player {target_player_name} not found"}

        if target_player == current_player:
            return {"success": False, "message": "Cannot ask yourself"}

        if rank not in RANKS:
            return {"success": False, "message": f"Invalid rank: {rank}"}

        if not current_player.has_rank(rank):
            return {"success": False, "message": f"You don't have any {rank}s to ask for"}

        # Perform the ask
        if target_player.has_rank(rank):
            # Target has the cards - transfer them
            cards = target_player.remove_cards_of_rank(rank)
            current_player.hand.extend(cards)

            # Check for books
            new_books = current_player.check_for_books()

            self.last_action = f"{current_player.name} got {len(cards)} {rank}(s) from {target_player.name}"
            if new_books > 0:
                self.last_action += f" and made {new_books} book(s)!"

            # Current player gets another turn
            result = {
                "success": True,
                "got_cards": True,
                "cards_received": len(cards),
                "new_books": new_books,
                "message": self.last_action,
                "next_turn": current_player.name,
            }

        else:
            # Go fish!
            self.last_action = f"{current_player.name} asked {target_player.name} for {rank}s. Go Fish!"

            # Draw a card if deck has cards
            drawn_card = None
            if self.deck.cards:
                drawn_cards = self.deck.deal(1)
                drawn_card = drawn_cards[0] if drawn_cards else None
                if drawn_card:
                    current_player.hand.append(drawn_card)
                    self.last_action += f" Drew {drawn_card}"

                    # If drawn card matches what was asked for, player gets another turn
                    if drawn_card.rank == rank:
                        self.last_action += f" - Lucky! Drew the {rank} you asked for!"
                        new_books = current_player.check_for_books()
                        if new_books > 0:
                            self.last_action += f" Made {new_books} book(s)!"

                        result = {
                            "success": True,
                            "got_cards": False,
                            "drew_card": True,
                            "drawn_rank": drawn_card.rank,
                            "lucky_draw": True,
                            "new_books": new_books,
                            "message": self.last_action,
                            "next_turn": current_player.name,
                        }
                    else:
                        # Move to next player
                        self._next_turn()
                        result = {
                            "success": True,
                            "got_cards": False,
                            "drew_card": True,
                            "drawn_rank": drawn_card.rank if drawn_card else None,
                            "lucky_draw": False,
                            "new_books": 0,
                            "message": self.last_action,
                            "next_turn": self.get_current_player().name,
                        }
            else:
                # No cards to draw
                self._next_turn()
                result = {"success": True, "got_cards": False, "drew_card": False, "message": self.last_action, "next_turn": self.get_current_player().name}

        # Check for game over
        if self._is_game_over():
            self.state = GameState.GAME_OVER
            result["game_over"] = True
            result["winner"] = self._get_winner().name

        return result

    def _next_turn(self) -> None:
        """Move to the next player's turn."""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

    def _is_game_over(self) -> bool:
        """Check if the game is over.

        Returns:
            True if game is over (all books made or no moves possible)
        """
        # Game is over when all 13 books are made (13 ranks)
        total_books = sum(player.books for player in self.players)
        if total_books == 13:
            return True

        # Or when no player has cards and deck is empty
        if not self.deck.cards:
            if all(not player.hand for player in self.players):
                return True

        return False

    def _get_winner(self) -> Player:
        """Get the player with the most books.

        Returns:
            Winning player
        """
        return max(self.players, key=lambda p: p.books)

    def get_state_summary(self) -> dict[str, any]:
        """Get a summary of the current game state.

        Returns:
            Dictionary with game statistics
        """
        return {
            "current_player": self.get_current_player().name,
            "deck_cards": len(self.deck.cards),
            "players": [{"name": p.name, "hand_size": len(p.hand), "books": p.books} for p in self.players],
            "state": self.state.name,
            "last_action": self.last_action,
        }

    def is_game_over(self) -> bool:
        """Check if the game is over.

        Returns:
            True if game is over
        """
        return self.state == GameState.GAME_OVER
