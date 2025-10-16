"""Simple game example demonstrating the use of base classes.

This example shows how to create a simple number guessing game using
the GameEngine base class and AI strategies.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import GameEngine, GameState, HeuristicStrategy, RandomStrategy


class NumberGuessingGame(GameEngine[int, str]):
    """A simple number guessing game.

    The computer picks a number between 1 and 100, and the player tries to guess it.
    After each guess, hints are provided (too high, too low).
    """

    def __init__(self, min_number: int = 1, max_number: int = 100) -> None:
        """Initialize the game.

        Args:
            min_number: Minimum number in range.
            max_number: Maximum number in range.
        """
        self.min_number = min_number
        self.max_number = max_number
        self.target: Optional[int] = None
        self.guesses: List[int] = []
        self.current_player_name = "Player"
        self.state = GameState.NOT_STARTED
        self.last_hint: Optional[str] = None

    def reset(self) -> None:
        """Reset the game."""
        self.target = random.randint(self.min_number, self.max_number)
        self.guesses = []
        self.state = GameState.IN_PROGRESS
        self.last_hint = None

    def is_game_over(self) -> bool:
        """Check if game is over."""
        return self.state == GameState.FINISHED

    def get_current_player(self) -> str:
        """Get current player."""
        return self.current_player_name

    def get_valid_moves(self) -> List[int]:
        """Get valid moves (all unguessed numbers in range)."""
        if self.is_game_over():
            return []
        # Return all numbers that haven't been guessed
        return [n for n in range(self.min_number, self.max_number + 1) if n not in self.guesses]

    def make_move(self, move: int) -> bool:
        """Make a guess.

        Args:
            move: The number to guess.

        Returns:
            True if the move was valid, False otherwise.
        """
        if move not in self.get_valid_moves():
            return False

        self.guesses.append(move)

        if move == self.target:
            self.state = GameState.FINISHED
            self.last_hint = "Correct!"
        elif move < self.target:
            self.last_hint = "Too low!"
        else:
            self.last_hint = "Too high!"

        return True

    def get_winner(self) -> Optional[str]:
        """Get winner."""
        if self.is_game_over() and self.last_hint == "Correct!":
            return self.current_player_name
        return None

    def get_game_state(self) -> GameState:
        """Get game state."""
        return self.state

    def get_hint(self) -> str:
        """Get the last hint."""
        return self.last_hint or "Make your first guess!"

    def get_guess_count(self) -> int:
        """Get number of guesses made."""
        return len(self.guesses)


def guess_heuristic(move: int, game: NumberGuessingGame) -> float:
    """Heuristic for AI guessing.

    Uses binary search strategy - prefers middle values based on previous hints.

    Args:
        move: The number to evaluate.
        game: The current game state.

    Returns:
        Score for the move (higher is better).
    """
    if not game.guesses:
        # First guess - prefer middle
        middle = (game.min_number + game.max_number) / 2
        return -abs(move - middle)

    # Binary search: prefer middle of remaining range
    # Estimate range based on hints (in real game, we don't know target)
    # This is a simplified heuristic
    if game.last_hint == "Too low!":
        low = max(game.guesses)
        high = game.max_number
    elif game.last_hint == "Too high!":
        low = game.min_number
        high = min(game.guesses)
    else:
        low = game.min_number
        high = game.max_number

    middle = (low + high) / 2
    return -abs(move - middle)


def demo_human_play() -> None:
    """Demo: Human playing the game."""
    print("=== Number Guessing Game (Human) ===\n")

    game = NumberGuessingGame(1, 100)
    game.reset()

    print(f"I'm thinking of a number between {game.min_number} and {game.max_number}.")
    print("Try to guess it!\n")

    while not game.is_game_over():
        try:
            guess = int(input(f"Guess #{game.get_guess_count() + 1}: "))
            if game.make_move(guess):
                print(f"  {game.get_hint()}\n")
            else:
                print(f"  Invalid guess! Try a number between {game.min_number} and {game.max_number}.\n")
        except ValueError:
            print("  Please enter a valid number.\n")

    print(f"🎉 Congratulations! You guessed it in {game.get_guess_count()} guesses!")


def demo_ai_play() -> None:
    """Demo: AI playing the game."""
    print("\n=== Number Guessing Game (AI) ===\n")

    # Try different AI strategies
    strategies = [
        ("Random AI", RandomStrategy()),
        ("Smart AI", HeuristicStrategy(heuristic_fn=guess_heuristic)),
    ]

    for name, strategy in strategies:
        game = NumberGuessingGame(1, 100)
        game.reset()

        print(f"{name} is playing...")
        print(f"Target number: {game.target}")

        while not game.is_game_over():
            valid_moves = game.get_valid_moves()
            if not valid_moves:
                break

            guess = strategy.select_move(valid_moves, game)
            game.make_move(guess)
            print(f"  Guess #{game.get_guess_count()}: {guess} - {game.get_hint()}")

        print(f"  Finished in {game.get_guess_count()} guesses!\n")


if __name__ == "__main__":
    print("This example demonstrates the GameEngine base class and AI strategies.\n")
    print("Choose a demo:")
    print("1. Play the game yourself")
    print("2. Watch AI play")
    print("3. Both")

    choice = input("\nYour choice (1-3): ").strip()

    if choice == "1":
        demo_human_play()
    elif choice == "2":
        demo_ai_play()
    elif choice == "3":
        demo_human_play()
        demo_ai_play()
    else:
        print("Invalid choice. Running AI demo...")
        demo_ai_play()
