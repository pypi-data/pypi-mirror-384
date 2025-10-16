"""Core logic and CLI for Mastermind.

Code-breaking game where player guesses a secret code of colored pegs.
Feedback given as black pegs (correct color and position) and white pegs
(correct color, wrong position).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

from common.game_engine import GameEngine, GameState


@dataclass(frozen=True)
class MastermindMove:
    """Representation of a Mastermind guess."""

    guess: Tuple[int, ...]  # Tuple of color indices


class MastermindGame(GameEngine[MastermindMove, int]):
    """Mastermind code-breaking game."""

    COLORS = ["Red", "Blue", "Green", "Yellow", "Orange", "Purple"]

    def __init__(self, code_length: int = 4, max_guesses: int = 10, num_colors: int = 6) -> None:
        """Initialize Mastermind game.

        Args:
            code_length: Length of the secret code
            max_guesses: Maximum number of guesses allowed
            num_colors: Number of different colors available
        """
        if code_length < 2 or code_length > 8:
            raise ValueError("Code length must be between 2 and 8")
        if num_colors < 2 or num_colors > len(self.COLORS):
            raise ValueError(f"Number of colors must be between 2 and {len(self.COLORS)}")

        self.code_length = code_length
        self.max_guesses = max_guesses
        self.num_colors = num_colors
        self._secret_code: List[int] = []
        self._guesses: List[Tuple[int, ...]] = []
        self._feedback: List[Tuple[int, int]] = []  # (black pegs, white pegs)
        self._state = GameState.NOT_STARTED
        self.reset()

    def reset(self) -> None:
        """Reset the game to initial state."""
        self._secret_code = [random.randint(0, self.num_colors - 1) for _ in range(self.code_length)]
        self._guesses = []
        self._feedback = []
        self._state = GameState.IN_PROGRESS

    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        return self._state == GameState.FINISHED

    def get_current_player(self) -> int:
        """Get the current player (always 0 for single player)."""
        return 0

    def get_valid_moves(self) -> List[MastermindMove]:
        """Get valid moves (any valid color combination)."""
        if self.is_game_over():
            return []
        # Return empty list - too many possible combinations
        # Player must construct their own guess
        return []

    def make_move(self, move: MastermindMove) -> bool:
        """Execute a move (make a guess).

        Args:
            move: The guess to check

        Returns:
            True if move was valid and executed
        """
        if self.is_game_over():
            return False

        guess = move.guess
        if len(guess) != self.code_length:
            return False

        if any(color < 0 or color >= self.num_colors for color in guess):
            return False

        # Calculate feedback
        black_pegs, white_pegs = self._calculate_feedback(guess)
        self._guesses.append(guess)
        self._feedback.append((black_pegs, white_pegs))

        # Check win condition
        if black_pegs == self.code_length:
            self._state = GameState.FINISHED
        elif len(self._guesses) >= self.max_guesses:
            self._state = GameState.FINISHED

        return True

    def _calculate_feedback(self, guess: Tuple[int, ...]) -> Tuple[int, int]:
        """Calculate feedback for a guess.

        Args:
            guess: The guessed code

        Returns:
            Tuple of (black_pegs, white_pegs)
        """
        black_pegs = sum(1 for i in range(self.code_length) if guess[i] == self._secret_code[i])

        # Count remaining colors
        secret_remaining = list(self._secret_code)
        guess_remaining = list(guess)

        # Remove exact matches
        for i in range(self.code_length - 1, -1, -1):
            if guess[i] == self._secret_code[i]:
                secret_remaining.pop(i)
                guess_remaining.pop(i)

        # Count white pegs (correct color, wrong position)
        white_pegs = 0
        for color in guess_remaining:
            if color in secret_remaining:
                white_pegs += 1
                secret_remaining.remove(color)

        return black_pegs, white_pegs

    def get_winner(self) -> Optional[int]:
        """Get the winner if game is over."""
        if not self.is_game_over():
            return None
        # Win if last guess was correct
        if self._feedback and self._feedback[-1][0] == self.code_length:
            return 0
        return None  # Lost

    def get_game_state(self) -> GameState:
        """Get the current game state."""
        return self._state

    def get_state_representation(self) -> dict:
        """Get a representation of the game state."""
        return {
            "guesses": self._guesses.copy(),
            "feedback": self._feedback.copy(),
            "guesses_remaining": self.max_guesses - len(self._guesses),
        }

    def get_guesses(self) -> List[Tuple[int, ...]]:
        """Get all guesses made so far."""
        return self._guesses.copy()

    def get_feedback(self) -> List[Tuple[int, int]]:
        """Get feedback for all guesses."""
        return self._feedback.copy()

    def get_secret_code(self) -> List[int]:
        """Get the secret code (for debugging or after game ends)."""
        return self._secret_code.copy()


class MastermindCLI:
    """Command line interface for Mastermind."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.game: Optional[MastermindGame] = None

    def run(self) -> None:
        """Run the game loop."""
        print("Welcome to Mastermind!")
        print("=" * 60)

        # Get game settings
        while True:
            try:
                code_length = int(input("Enter code length (2-8, default 4): ") or "4")
                if 2 <= code_length <= 8:
                    break
                print("Please enter a number between 2 and 8")
            except ValueError:
                print("Please enter a valid number")

        self.game = MastermindGame(code_length=code_length)

        print(f"\nStarting game with {code_length}-color code!")
        print(f"Available colors: {', '.join(self.game.COLORS[:self.game.num_colors])}")
        print(f"You have {self.game.max_guesses} guesses.")
        print("\nFeedback:")
        print("  ⚫ Black peg = correct color and position")
        print("  ⚪ White peg = correct color, wrong position")
        print()

        # Game loop
        while not self.game.is_game_over():
            self._make_guess()
            self._show_history()

        # Game over
        if self.game.get_winner() is not None:
            print(f"\n{'=' * 60}")
            print("🎉 Congratulations! You cracked the code! 🎉")
            print(f"{'=' * 60}")
        else:
            secret = self.game.get_secret_code()
            secret_str = " ".join(self.game.COLORS[c] for c in secret)
            print(f"\n{'=' * 60}")
            print("Game Over! You ran out of guesses.")
            print(f"The secret code was: {secret_str}")
            print(f"{'=' * 60}")

    def _make_guess(self) -> None:
        """Make a single guess."""
        if self.game is None:
            return

        guesses_left = self.game.max_guesses - len(self.game.get_guesses())
        print(f"\n--- Guess {len(self.game.get_guesses()) + 1}/{self.game.max_guesses} ---")
        print(f"Guesses remaining: {guesses_left}")

        while True:
            guess_str = input(f"Enter your guess ({self.game.code_length} colors, e.g., 'red blue green yellow'): ")
            guess_parts = guess_str.lower().split()

            if len(guess_parts) != self.game.code_length:
                print(f"Please enter exactly {self.game.code_length} colors")
                continue

            # Convert color names to indices
            try:
                guess = []
                for part in guess_parts:
                    # Find matching color
                    for i, color in enumerate(self.game.COLORS[: self.game.num_colors]):
                        if color.lower().startswith(part):
                            guess.append(i)
                            break
                    else:
                        raise ValueError(f"Unknown color: {part}")

                move = MastermindMove(guess=tuple(guess))
                if self.game.make_move(move):
                    break
                else:
                    print("Invalid move, please try again")
            except ValueError as e:
                print(f"Error: {e}")

    def _show_history(self) -> None:
        """Show guess history with feedback."""
        if self.game is None:
            return

        print("\n--- Guess History ---")
        guesses = self.game.get_guesses()
        feedback = self.game.get_feedback()

        for i, (guess, (black, white)) in enumerate(zip(guesses, feedback), 1):
            guess_str = " ".join(self.game.COLORS[c][:3].upper() for c in guess)
            feedback_str = "⚫" * black + "⚪" * white
            print(f"{i:2d}. {guess_str:30s} | {feedback_str}")

        print()
