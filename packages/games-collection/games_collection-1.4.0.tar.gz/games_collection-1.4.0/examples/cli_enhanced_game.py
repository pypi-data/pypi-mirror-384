"""Example game using CLI utilities - Number Guessing Game with Enhanced CLI.

This example demonstrates practical usage of all CLI enhancement features
in a simple number guessing game.
"""

from __future__ import annotations

import random
import time

from common.cli_utils import THEMES, ASCIIArt, Color, CommandHistory, InteractiveMenu, ProgressBar, RichText, Spinner


class NumberGuessingGame:
    """Number guessing game with enhanced CLI."""

    def __init__(self, min_number: int = 1, max_number: int = 100):
        """Initialize the game.

        Args:
            min_number: Minimum number in range.
            max_number: Maximum number in range.
        """
        self.min_number = min_number
        self.max_number = max_number
        self.secret_number = 0
        self.attempts = 0
        self.max_attempts = 10
        self.history = CommandHistory()
        self.theme = THEMES["ocean"]
        self.score = 0

    def show_welcome(self) -> None:
        """Display welcome screen with ASCII art."""
        print(ASCIIArt.banner("NUMBER GUESSING GAME", self.theme.primary, width=60))
        print()
        print(RichText.info("Guess the secret number to win!"))
        print(RichText.info(f"Range: {self.min_number} to {self.max_number}"))
        print(RichText.info(f"Attempts: {self.max_attempts}"))
        print()

    def show_loading(self) -> None:
        """Show loading animation."""
        print(RichText.header("Preparing game...", level=2, theme=self.theme))
        print()

        # Spinner for initialization
        spinner = Spinner(message="Generating secret number", theme=self.theme)
        spinner.start()
        for _ in range(5):
            time.sleep(0.1)
            spinner.tick()
        spinner.stop()

        # Progress bar for game setup
        print("Loading game assets:")
        bar = ProgressBar(total=20, width=40, theme=self.theme)
        for i in range(21):
            bar.update(i)
            time.sleep(0.02)
        print()

    def show_main_menu(self) -> int:
        """Display main menu and get selection.

        Returns:
            Selected menu option index.
        """
        options = [
            "Start New Game",
            "Change Difficulty",
            "View High Score",
            "How to Play",
            "Quit",
        ]

        menu = InteractiveMenu("Main Menu", options, theme=self.theme)
        return menu.display()

    def show_difficulty_menu(self) -> None:
        """Show difficulty selection menu."""
        print(RichText.header("Select Difficulty", level=2, theme=self.theme))
        print()

        options = [
            "Easy (1-50, 15 attempts)",
            "Medium (1-100, 10 attempts)",
            "Hard (1-200, 7 attempts)",
            "Expert (1-500, 5 attempts)",
        ]

        menu = InteractiveMenu("Difficulty", options, theme=self.theme)
        choice = menu.display()

        difficulty_settings = {
            0: (1, 50, 15),
            1: (1, 100, 10),
            2: (1, 200, 7),
            3: (1, 500, 5),
        }

        self.min_number, self.max_number, self.max_attempts = difficulty_settings[choice]
        print(RichText.success(f"Difficulty set to: {options[choice]}"))
        print()
        time.sleep(1)

    def show_how_to_play(self) -> None:
        """Show game instructions."""
        instructions = """How to Play:
1. The game picks a secret number
2. You have limited attempts to guess it
3. After each guess, you get a hint
4. Guess correctly to win!

Commands:
  - Enter a number to guess
  - Type 'hint' for a hint (-1 attempt)
  - Type 'quit' to exit
  - Type 'stats' to see your progress"""

        print()
        print(ASCIIArt.box(instructions, self.theme.info, padding=2))
        print()
        input(RichText.info("Press Enter to continue..."))

    def start_new_game(self) -> None:
        """Start a new game."""
        self.secret_number = random.randint(self.min_number, self.max_number)
        self.attempts = 0
        print()
        print(RichText.header("New Game Started!", level=1, theme=self.theme))
        print(RichText.info(f"I'm thinking of a number between {self.min_number} and {self.max_number}"))
        print(RichText.info(f"You have {self.max_attempts} attempts to guess it!"))
        print()

        self.play_game()

    def play_game(self) -> None:
        """Main game loop."""
        commands = ["hint", "quit", "stats"] + [str(i) for i in range(self.min_number, min(self.max_number + 1, 100))]

        while self.attempts < self.max_attempts:
            remaining = self.max_attempts - self.attempts

            # Show status
            print(f"{RichText.colorize('Attempts remaining:', self.theme.text)} " f"{RichText.highlight(str(remaining), self.theme)}")

            # Get user input
            try:
                guess_input = input(f"{self.theme.accent}Your guess: {Color.RESET}").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print()
                print(RichText.warning("Game interrupted!"))
                return

            # Add to history
            self.history.add(guess_input)

            # Handle special commands
            if guess_input == "quit":
                print(RichText.warning("Thanks for playing!"))
                return
            elif guess_input == "stats":
                self.show_stats()
                continue
            elif guess_input == "hint":
                self.give_hint()
                self.attempts += 1
                continue

            # Try autocomplete
            autocomplete = self.history.autocomplete(guess_input, commands)
            if autocomplete and autocomplete != guess_input:
                print(RichText.info(f"Autocomplete suggestion: {autocomplete}"))

            # Validate and process guess
            try:
                guess = int(guess_input)
            except ValueError:
                print(RichText.error("Please enter a valid number!"))
                continue

            self.attempts += 1

            # Check guess
            if guess == self.secret_number:
                self.win_game()
                return
            elif guess < self.secret_number:
                print(RichText.warning("Too low! Try a higher number."))
            else:
                print(RichText.warning("Too high! Try a lower number."))

            print()

        # Out of attempts
        self.lose_game()

    def give_hint(self) -> None:
        """Give a hint to the player."""
        range_size = self.max_number - self.min_number
        hint_range = range_size // 4

        if self.secret_number <= self.min_number + hint_range:
            hint = f"The number is in the lower quarter ({self.min_number}-{self.min_number + hint_range})"
        elif self.secret_number <= self.min_number + 2 * hint_range:
            hint = f"The number is in the second quarter ({self.min_number + hint_range + 1}-{self.min_number + 2 * hint_range})"
        elif self.secret_number <= self.min_number + 3 * hint_range:
            hint = f"The number is in the third quarter ({self.min_number + 2 * hint_range + 1}-{self.min_number + 3 * hint_range})"
        else:
            hint = f"The number is in the upper quarter ({self.min_number + 3 * hint_range + 1}-{self.max_number})"

        print(RichText.info(f"Hint: {hint}"))

    def show_stats(self) -> None:
        """Show current game statistics."""
        stats = f"""Game Statistics:
  Attempts used: {self.attempts}/{self.max_attempts}
  Range: {self.min_number}-{self.max_number}
  Current score: {self.score}"""

        print()
        print(ASCIIArt.box(stats, self.theme.info, padding=1))
        print()

    def win_game(self) -> None:
        """Handle winning the game."""
        print()
        print(ASCIIArt.victory(self.theme.success))
        print()

        # Calculate score
        score = max(0, (self.max_attempts - self.attempts) * 10)
        self.score += score

        print(RichText.success(f"Congratulations! You guessed it in {self.attempts} attempts!"))
        print(RichText.success(f"Score earned: {score} points"))
        print(RichText.info(f"Total score: {self.score}"))
        print()

        time.sleep(2)

    def lose_game(self) -> None:
        """Handle losing the game."""
        print()
        print(ASCIIArt.defeat(self.theme.error))
        print()
        print(RichText.error(f"Game Over! The secret number was {self.secret_number}"))
        print(RichText.info("Better luck next time!"))
        print()
        time.sleep(2)

    def run(self) -> None:
        """Run the game main loop."""
        self.show_welcome()
        self.show_loading()

        while True:
            choice = self.show_main_menu()

            if choice == 0:  # Start New Game
                self.start_new_game()
            elif choice == 1:  # Change Difficulty
                self.show_difficulty_menu()
            elif choice == 2:  # View High Score
                print()
                print(RichText.highlight(f"High Score: {self.score} points", self.theme))
                print()
                input(RichText.info("Press Enter to continue..."))
            elif choice == 3:  # How to Play
                self.show_how_to_play()
            elif choice == 4:  # Quit
                print()
                print(ASCIIArt.banner("Thanks for Playing!", self.theme.success, width=60))
                print(RichText.success(f"Final Score: {self.score} points"))
                break


def main() -> None:
    """Run the enhanced CLI game."""
    try:
        game = NumberGuessingGame()
        game.run()
    except KeyboardInterrupt:
        print()
        print(RichText.warning("Game interrupted by user."))
    except Exception as e:
        print()
        print(RichText.error(f"An error occurred: {e}"))


if __name__ == "__main__":
    main()
