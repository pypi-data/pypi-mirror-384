"""Core logic and CLI for Snakes and Ladders.

This module implements the classic board game where players race to reach
the finish by rolling dice, climbing ladders for shortcuts, and sliding
down snakes as setbacks.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional

from common.game_engine import GameEngine, GameState


@dataclass(frozen=True)
class SnakesAndLaddersMove:
    """Representation of a move in Snakes and Ladders."""

    dice_roll: int


class SnakesAndLaddersGame(GameEngine[SnakesAndLaddersMove, int]):
    """Snakes and Ladders game with configurable board size."""

    def __init__(
        self,
        num_players: int = 2,
        board_size: int = 100,
        snakes: Optional[Dict[int, int]] = None,
        ladders: Optional[Dict[int, int]] = None,
    ) -> None:
        """Initialize the game.

        Args:
            num_players: Number of players (2-4)
            board_size: Size of the board (default 100)
            snakes: Dictionary mapping head positions to tail positions
            ladders: Dictionary mapping bottom positions to top positions
        """
        if num_players < 2 or num_players > 4:
            raise ValueError("Number of players must be between 2 and 4")

        self.num_players = num_players
        self.board_size = board_size
        self._positions: List[int] = []
        self._current_player = 0
        self._winner: Optional[int] = None
        self._state = GameState.NOT_STARTED

        # Default snakes and ladders for a 100-square board
        self.snakes = snakes or {
            16: 6,
            47: 26,
            49: 11,
            56: 53,
            62: 19,
            64: 60,
            87: 24,
            93: 73,
            95: 75,
            98: 78,
        }
        self.ladders = ladders or {
            1: 38,
            4: 14,
            9: 31,
            21: 42,
            28: 84,
            36: 44,
            51: 67,
            71: 91,
            80: 100,
        }

        self.reset()

    def reset(self) -> None:
        """Reset the game to initial state."""
        self._positions = [0] * self.num_players
        self._current_player = 0
        self._winner = None
        self._state = GameState.IN_PROGRESS

    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        return self._state == GameState.FINISHED

    def get_current_player(self) -> int:
        """Get the current player (0-indexed)."""
        return self._current_player

    def get_valid_moves(self) -> List[SnakesAndLaddersMove]:
        """Get valid moves (dice rolls 1-6)."""
        if self.is_game_over():
            return []
        return [SnakesAndLaddersMove(dice_roll=i) for i in range(1, 7)]

    def make_move(self, move: SnakesAndLaddersMove) -> bool:
        """Execute a move (roll dice and move player).

        Args:
            move: The dice roll move

        Returns:
            True if move was valid and executed
        """
        if self.is_game_over():
            return False

        if move.dice_roll < 1 or move.dice_roll > 6:
            return False

        # Move the current player
        current_pos = self._positions[self._current_player]
        new_pos = current_pos + move.dice_roll

        # Can't go beyond the board
        if new_pos > self.board_size:
            # In some variants, must land exactly; here we just stay
            new_pos = current_pos
        else:
            # Check for snakes
            if new_pos in self.snakes:
                new_pos = self.snakes[new_pos]

            # Check for ladders
            if new_pos in self.ladders:
                new_pos = self.ladders[new_pos]

        self._positions[self._current_player] = new_pos

        # Check for winner
        if new_pos >= self.board_size:
            self._winner = self._current_player
            self._state = GameState.FINISHED
        else:
            # Next player's turn
            self._current_player = (self._current_player + 1) % self.num_players

        return True

    def get_winner(self) -> Optional[int]:
        """Get the winner if game is over."""
        return self._winner

    def get_game_state(self) -> GameState:
        """Get the current game state."""
        return self._state

    def get_state_representation(self) -> Dict[str, any]:
        """Get a representation of the game state."""
        return {
            "positions": tuple(self._positions),
            "current_player": self._current_player,
            "winner": self._winner,
        }

    def get_player_position(self, player: int) -> int:
        """Get the position of a specific player."""
        if player < 0 or player >= self.num_players:
            raise ValueError(f"Player must be between 0 and {self.num_players - 1}")
        return self._positions[player]


class SnakesAndLaddersCLI:
    """Command line interface for Snakes and Ladders."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.game: Optional[SnakesAndLaddersGame] = None

    def run(self) -> None:
        """Run the game loop."""
        print("Welcome to Snakes and Ladders!")
        print("=" * 50)

        # Get number of players
        while True:
            try:
                num_players = int(input("Enter number of players (2-4): "))
                if 2 <= num_players <= 4:
                    break
                print("Please enter a number between 2 and 4")
            except ValueError:
                print("Please enter a valid number")

        self.game = SnakesAndLaddersGame(num_players=num_players)

        print(f"\nStarting game with {num_players} players!")
        print(f"First to reach square {self.game.board_size} wins!")
        print("\nSnakes and Ladders on the board:")
        print("Ladders:", ", ".join(f"{k}→{v}" for k, v in sorted(self.game.ladders.items())))
        print("Snakes:", ", ".join(f"{k}→{v}" for k, v in sorted(self.game.snakes.items())))
        print()

        # Game loop
        while not self.game.is_game_over():
            current = self.game.get_current_player()
            current_pos = self.game.get_player_position(current)

            print(f"\n--- Player {current + 1}'s turn ---")
            print(f"Current position: {current_pos}")

            # Show all positions
            positions_str = " | ".join(f"P{i+1}: {self.game.get_player_position(i)}" for i in range(self.game.num_players))
            print(f"All positions: {positions_str}")

            input("\nPress Enter to roll the dice...")

            # Roll dice
            dice_roll = random.randint(1, 6)
            print(f"🎲 You rolled a {dice_roll}!")

            # Make move
            move = SnakesAndLaddersMove(dice_roll=dice_roll)
            self.game.make_move(move)

            new_pos = self.game.get_player_position(current)

            # Check for snake or ladder
            if new_pos != current_pos + dice_roll:
                if new_pos > current_pos + dice_roll:
                    print(f"🪜 Ladder! Climbed from {current_pos + dice_roll} to {new_pos}!")
                elif new_pos < current_pos + dice_roll:
                    print(f"🐍 Snake! Slid from {current_pos + dice_roll} to {new_pos}!")
            else:
                print(f"Moved to position {new_pos}")

        # Game over
        winner = self.game.get_winner()
        if winner is not None:
            print(f"\n{'=' * 50}")
            print(f"🎉 Player {winner + 1} wins! 🎉")
            print(f"{'=' * 50}")
