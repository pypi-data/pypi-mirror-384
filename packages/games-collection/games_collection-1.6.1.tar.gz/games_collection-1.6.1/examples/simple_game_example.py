"""A simple game example demonstrating the use of core base classes.

This script illustrates how to structure a basic game by inheriting from the
`GameEngine` abstract base class. It also shows how to implement and integrate
different AI behaviors using the `RandomStrategy` and `HeuristicStrategy` classes.

The game implemented here is a classic Number Guessing Game, which provides a
clear and straightforward context for these architectural patterns.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import List, Optional

# Add the project's root directory to the Python path to allow for module imports.
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import GameEngine, GameState, HeuristicStrategy, RandomStrategy


class NumberGuessingGame(GameEngine[int, str]):
    """A simple number guessing game engine.

    This class implements the `GameEngine` interface for a game where the goal is
    to guess a secret number. It manages the game's state, rules, and player actions.

    Attributes:
        min_number (int): The lower bound of the guessing range.
        max_number (int): The upper bound of the guessing range.
        target (Optional[int]): The secret number to be guessed.
        guesses (List[int]): A list of numbers guessed so far.
        current_player_name (str): The name of the current player.
        state (GameState): The current state of the game (e.g., IN_PROGRESS, FINISHED).
        last_hint (Optional[str]): The hint provided after the last guess.
    """

    def __init__(self, min_number: int = 1, max_number: int = 100) -> None:
        """Initializes the Number Guessing Game.

        Args:
            min_number: The minimum number in the guessing range.
            max_number: The maximum number in the guessing range.
        """
        self.min_number = min_number
        self.max_number = max_number
        self.target: Optional[int] = None
        self.guesses: List[int] = []
        self.current_player_name = "Player"
        self.state = GameState.NOT_STARTED
        self.last_hint: Optional[str] = None

    def reset(self) -> None:
        """Resets the game to a new round."""
        self.target = random.randint(self.min_number, self.max_number)
        self.guesses = []
        self.state = GameState.IN_PROGRESS
        self.last_hint = None

    def is_game_over(self) -> bool:
        """Checks if the game has finished."""
        return self.state == GameState.FINISHED

    def get_current_player(self) -> str:
        """Returns the name of the current player."""
        return self.current_player_name

    def get_valid_moves(self) -> List[int]:
        """Returns a list of valid moves (numbers that haven't been guessed yet)."""
        if self.is_game_over():
            return []
        return [n for n in range(self.min_number, self.max_number + 1) if n not in self.guesses]

    def make_move(self, move: int) -> bool:
        """Processes a player's guess.

        Args:
            move: The number being guessed.

        Returns:
            True if the move was valid and processed, False otherwise.
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
        """Determines the winner, if any."""
        if self.is_game_over() and self.last_hint == "Correct!":
            return self.current_player_name
        return None

    def get_game_state(self) -> GameState:
        """Returns the current `GameState` enum."""
        return self.state

    def get_hint(self) -> str:
        """Provides a hint based on the last guess."""
        return self.last_hint or "Make your first guess!"

    def get_guess_count(self) -> int:
        """Returns the total number of guesses made."""
        return len(self.guesses)


def guess_heuristic(move: int, game: NumberGuessingGame) -> float:
    """A heuristic function for the AI to make intelligent guesses.

    This function implements a binary search-like strategy. It favors guesses
    that are in the middle of the remaining possible range, which it deduces
    from the hints provided by the game.

    Args:
        move: The potential guess to evaluate.
        game: The current game instance, used to access game state and hints.

    Returns:
        A score for the move. Higher scores are considered better. The score is
        the negative absolute difference from the midpoint, ensuring that moves
        closer to the middle get scores closer to zero (which is higher).
    """
    # On the first guess, aim for the absolute middle of the initial range.
    if not game.guesses:
        middle = (game.min_number + game.max_number) / 2
        return -abs(move - middle)

    # Determine the new search range based on previous hints.
    low = game.min_number
    high = game.max_number

    # Refine the search range using the hints from previous guesses.
    for i, g in enumerate(game.guesses):
        # This is a simplified logic. A more robust heuristic would track hints for each guess.
        # Here, we use the last hint to adjust the overall range.
        pass  # Simplified for demonstration.

    if game.last_hint == "Too low!":
        # If the last guess was too low, the new minimum is that guess.
        low = max([g for g in game.guesses if g < game.target] + [game.min_number])
    elif game.last_hint == "Too high!":
        # If the last guess was too high, the new maximum is that guess.
        high = min([g for g in game.guesses if g > game.target] + [game.max_number])

    # The ideal next guess is the middle of the refined range.
    middle = (low + high) / 2
    return -abs(move - middle)


def demo_human_play() -> None:
    """A simple command-line interface for a human player."""
    print("=" * 40)
    print("Number Guessing Game (Human Player)")
    print("=" * 40 + "\n")

    game = NumberGuessingGame(1, 100)
    game.reset()

    print(f"I'm thinking of a number between {game.min_number} and {game.max_number}.")
    print("Try to guess it!\n")

    while not game.is_game_over():
        try:
            guess_str = input(f"Guess #{game.get_guess_count() + 1}: ")
            guess = int(guess_str)
            if game.make_move(guess):
                print(f"  -> Hint: {game.get_hint()}\n")
            else:
                print("  Invalid guess! Please try a number you haven't guessed before.\n")
        except ValueError:
            print("  Please enter a valid integer.\n")

    print(f"🎉 Congratulations! You guessed the number in {game.get_guess_count()} guesses!")


def demo_ai_play() -> None:
    """Demonstrates different AI strategies playing the game."""
    print("\n" + "=" * 40)
    print("Number Guessing Game (AI Players)")
    print("=" * 40 + "\n")

    # A list of different AI strategies to demonstrate.
    strategies = [
        ("Random AI", RandomStrategy()),
        ("Smart AI (Heuristic)", HeuristicStrategy(heuristic_fn=guess_heuristic)),
    ]

    for name, strategy in strategies:
        game = NumberGuessingGame(1, 100)
        game.reset()

        print(f"--- {name} is playing ---")
        print(f"The secret number is: {game.target}")

        while not game.is_game_over():
            valid_moves = game.get_valid_moves()
            if not valid_moves:
                break  # Should not happen if logic is correct.

            # The AI strategy selects the best move from the available options.
            guess = strategy.select_move(valid_moves, game)
            game.make_move(guess)
            print(f"  Guess #{game.get_guess_count()}: {guess:<3} -> Hint: {game.get_hint()}")

        print(f"  Finished in {game.get_guess_count()} guesses!\n")


if __name__ == "__main__":
    print("This example demonstrates the GameEngine base class and AI strategies.\n")
    print("Choose a demonstration to run:")
    print("  1. Play the game yourself")
    print("  2. Watch the AI players")
    print("  3. Run both demonstrations")

    choice = input("\nYour choice (1-3): ").strip()

    if choice == "1":
        demo_human_play()
    elif choice == "2":
        demo_ai_play()
    elif choice == "3":
        demo_human_play()
        demo_ai_play()
    else:
        print("Invalid choice. Running the AI demonstration by default.")
        demo_ai_play()
