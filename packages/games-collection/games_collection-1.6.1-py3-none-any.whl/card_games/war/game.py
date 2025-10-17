"""War card game engine.

This module implements the classic card game War, where two players each have
half the deck and simultaneously reveal cards. The player with the higher card
wins both cards. When cards are equal, a "war" occurs where players place
additional cards face down and then reveal another card.

Rules:
* Standard 52-card deck divided equally between 2 players
* Each round, both players reveal their top card
* Higher card wins both cards (Ace is highest)
* On a tie, players enter "war": place 3 cards face down, then 1 face up
* Winner of war takes all cards in play
* Game ends when one player has all cards or cannot participate in a war
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from random import Random
from typing import Any, Optional

from card_games.common.cards import Card, Deck


class GameState(Enum):
    """Current state of the War game."""

    PLAYING = auto()
    WAR = auto()
    GAME_OVER = auto()


@dataclass
class WarGame:
    """War game engine.

    Attributes:
        player1_deck: Player 1's deck of cards
        player2_deck: Player 2's deck of cards
        pile: Current pile of cards in play
        state: Current game state
        rounds_played: Total number of rounds played
        wars_fought: Number of wars that occurred
        winner: Winner of the game (1 or 2), None if game ongoing
    """

    player1_deck: list[Card] = field(default_factory=list)
    player2_deck: list[Card] = field(default_factory=list)
    pile: list[Card] = field(default_factory=list)
    state: GameState = GameState.PLAYING
    rounds_played: int = 0
    wars_fought: int = 0
    winner: Optional[int] = None

    def __init__(self, rng: Optional[Random] = None) -> None:
        """Initialize a new War game.

        Args:
            rng: Optional Random instance for deterministic games
        """
        self.player1_deck = []
        self.player2_deck = []
        self.pile = []
        self.state = GameState.PLAYING
        self.rounds_played = 0
        self.wars_fought = 0
        self.winner = None

        # Create and shuffle deck
        deck = Deck()
        deck.shuffle(rng=rng)

        # Deal cards equally
        cards = deck.cards
        self.player1_deck = cards[::2]  # Every other card
        self.player2_deck = cards[1::2]  # Remaining cards

    def get_deck_sizes(self) -> tuple[int, int]:
        """Get the current deck sizes for both players.

        Returns:
            Tuple of (player1_size, player2_size)
        """
        return len(self.player1_deck), len(self.player2_deck)

    def play_round(self) -> dict[str, any]:
        """Play one round of War.

        Returns:
            Dictionary with round results including:
            - round_type: "normal" or "war"
            - player1_card: Card played by player 1
            - player2_card: Card played by player 2
            - winner: Winner of the round (1 or 2)
            - cards_won: Number of cards won
            - game_over: Whether the game ended
        """
        if self.state == GameState.GAME_OVER:
            return {"game_over": True, "winner": self.winner}

        # Check if either player has no cards
        if not self.player1_deck:
            self.state = GameState.GAME_OVER
            self.winner = 2
            return {"game_over": True, "winner": 2}
        if not self.player2_deck:
            self.state = GameState.GAME_OVER
            self.winner = 1
            return {"game_over": True, "winner": 1}

        self.rounds_played += 1

        # Draw cards from each player
        card1 = self.player1_deck.pop(0)
        card2 = self.player2_deck.pop(0)
        self.pile.extend([card1, card2])

        result = {
            "round_type": "normal",
            "player1_card": card1,
            "player2_card": card2,
            "game_over": False,
        }

        # Compare cards
        if card1.value > card2.value:
            # Player 1 wins
            self.player1_deck.extend(self.pile)
            result["winner"] = 1
            result["cards_won"] = len(self.pile)
            self.pile = []
        elif card2.value > card1.value:
            # Player 2 wins
            self.player2_deck.extend(self.pile)
            result["winner"] = 2
            result["cards_won"] = len(self.pile)
            self.pile = []
        else:
            # War!
            result["round_type"] = "war"
            war_result = self._handle_war()
            result.update(war_result)

        # Check for game over
        if not self.player1_deck:
            self.state = GameState.GAME_OVER
            self.winner = 2
            result["game_over"] = True
            result["final_winner"] = 2
        elif not self.player2_deck:
            self.state = GameState.GAME_OVER
            self.winner = 1
            result["game_over"] = True
            result["final_winner"] = 1

        return result

    def _handle_war(self) -> dict[str, any]:
        """Handle a war situation (tied cards).

        Returns:
            Dictionary with war results
        """
        self.wars_fought += 1

        # Each player places 3 cards face down, then 1 face up
        # If a player doesn't have enough cards, they lose
        war_cards_needed = 4  # 3 face down + 1 face up

        if len(self.player1_deck) < war_cards_needed:
            # Player 1 doesn't have enough cards
            self.player2_deck.extend(self.pile)
            cards_won = len(self.pile)
            self.pile = []
            return {"winner": 2, "cards_won": cards_won, "reason": "insufficient_cards"}

        if len(self.player2_deck) < war_cards_needed:
            # Player 2 doesn't have enough cards
            self.player1_deck.extend(self.pile)
            cards_won = len(self.pile)
            self.pile = []
            return {"winner": 1, "cards_won": cards_won, "reason": "insufficient_cards"}

        # Both players have enough cards - conduct war
        # Place 3 cards face down
        for _ in range(3):
            self.pile.append(self.player1_deck.pop(0))
            self.pile.append(self.player2_deck.pop(0))

        # Draw face up cards
        card1 = self.player1_deck.pop(0)
        card2 = self.player2_deck.pop(0)
        self.pile.extend([card1, card2])

        war_result = {
            "war_card1": card1,
            "war_card2": card2,
        }

        # Compare war cards
        if card1.value > card2.value:
            self.player1_deck.extend(self.pile)
            war_result["winner"] = 1
            war_result["cards_won"] = len(self.pile)
            self.pile = []
        elif card2.value > card1.value:
            self.player2_deck.extend(self.pile)
            war_result["winner"] = 2
            war_result["cards_won"] = len(self.pile)
            self.pile = []
        else:
            # Another war! Recursively handle it
            nested_war = self._handle_war()
            war_result.update(nested_war)
            war_result["nested_war"] = True

        return war_result

    def get_state_summary(self) -> dict[str, any]:
        """Get a summary of the current game state.

        Returns:
            Dictionary with game statistics
        """
        return {
            "player1_cards": len(self.player1_deck),
            "player2_cards": len(self.player2_deck),
            "pile_cards": len(self.pile),
            "rounds_played": self.rounds_played,
            "wars_fought": self.wars_fought,
            "state": self.state.name,
            "winner": self.winner,
        }

    def is_game_over(self) -> bool:
        """Check if the game is over.

        Returns:
            True if game is over, False otherwise
        """
        return self.state == GameState.GAME_OVER

    def to_dict(self) -> dict[str, Any]:
        """Serialize game state to a dictionary.

        Returns:
            Dictionary representation of the game state
        """
        return {
            "player1_deck": [{"rank": c.rank, "suit": c.suit.value} for c in self.player1_deck],
            "player2_deck": [{"rank": c.rank, "suit": c.suit.value} for c in self.player2_deck],
            "pile": [{"rank": c.rank, "suit": c.suit.value} for c in self.pile],
            "state": self.state.name,
            "rounds_played": self.rounds_played,
            "wars_fought": self.wars_fought,
            "winner": self.winner,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WarGame:
        """Deserialize game state from a dictionary.

        Args:
            data: Dictionary containing game state

        Returns:
            Restored WarGame instance
        """
        from card_games.common.cards import Suit

        game = cls.__new__(cls)
        game.player1_deck = [Card(rank=c["rank"], suit=Suit(c["suit"])) for c in data["player1_deck"]]
        game.player2_deck = [Card(rank=c["rank"], suit=Suit(c["suit"])) for c in data["player2_deck"]]
        game.pile = [Card(rank=c["rank"], suit=Suit(c["suit"])) for c in data["pile"]]
        game.state = GameState[data["state"]]
        game.rounds_played = data["rounds_played"]
        game.wars_fought = data["wars_fought"]
        game.winner = data.get("winner")
        return game
