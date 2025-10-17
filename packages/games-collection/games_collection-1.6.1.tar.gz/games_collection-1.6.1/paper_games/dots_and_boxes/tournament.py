"""Tournament mode for Dots and Boxes.

This module provides tournament functionality where multiple games are played
and statistics are tracked across the tournament.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Tuple

from .dots_and_boxes import DotsAndBoxes


@dataclass
class TournamentStats:
    """Statistics for a tournament."""

    total_games: int = 0
    human_wins: int = 0
    computer_wins: int = 0
    ties: int = 0
    total_human_score: int = 0
    total_computer_score: int = 0

    def record_game(self, human_score: int, computer_score: int) -> None:
        """Record the results of a game."""
        self.total_games += 1
        self.total_human_score += human_score
        self.total_computer_score += computer_score

        if human_score > computer_score:
            self.human_wins += 1
        elif computer_score > human_score:
            self.computer_wins += 1
        else:
            self.ties += 1

    def win_percentage(self) -> float:
        """Calculate the human player's win percentage."""
        if self.total_games == 0:
            return 0.0
        return (self.human_wins / self.total_games) * 100

    def avg_score_diff(self) -> float:
        """Calculate the average score difference (human - computer)."""
        if self.total_games == 0:
            return 0.0
        return (self.total_human_score - self.total_computer_score) / self.total_games

    def __str__(self) -> str:
        """Format tournament statistics as a string."""
        lines = [
            "=" * 50,
            "TOURNAMENT RESULTS",
            "=" * 50,
            f"Total Games: {self.total_games}",
            f"Human Wins: {self.human_wins}",
            f"Computer Wins: {self.computer_wins}",
            f"Ties: {self.ties}",
            f"Win Percentage: {self.win_percentage():.1f}%",
            f"Total Score - Human: {self.total_human_score}, Computer: {self.total_computer_score}",
            f"Average Score Difference: {self.avg_score_diff():.2f}",
            "=" * 50,
        ]
        return "\n".join(lines)


class Tournament:
    """Manages a tournament of multiple Dots and Boxes games."""

    def __init__(self, size: int = 2, num_games: int = 5, seed: int | None = None) -> None:
        """Initialize a tournament.

        Args:
            size: Board size for all games
            num_games: Number of games to play
            seed: Random seed for reproducibility
        """
        self.size = size
        self.num_games = num_games
        self.rng = random.Random(seed)
        self.stats = TournamentStats()

    def play_game(self, game_number: int, interactive: bool = True) -> Tuple[int, int]:
        """Play a single game in the tournament.

        Args:
            game_number: The game number (for display)
            interactive: If True, human plays; if False, simulates automatic play

        Returns:
            Tuple of (human_score, computer_score)
        """
        game = DotsAndBoxes(size=self.size, rng=self.rng)

        if interactive:
            print(f"\n{'=' * 50}")
            print(f"GAME {game_number + 1} of {self.num_games}")
            print(f"{'=' * 50}\n")

        player_turn = True

        while not game.is_finished():
            if interactive:
                print("\n" + game.render())
                print(f"Score - {game.human_name}: {game.scores[game.human_name]} | " f"{game.computer_name}: {game.scores[game.computer_name]}")

            if player_turn:
                if interactive:
                    move = input("Your move (orientation row col): ").strip().split()
                    if len(move) != 3:
                        print("Please enter orientation and coordinates like 'v 1 0'.")
                        continue
                    orientation, row_str, col_str = move
                    try:
                        row, col = int(row_str), int(col_str)
                        completed = game.claim_edge(orientation, row, col, player=game.human_name)
                    except (ValueError, KeyError) as exc:
                        print(exc)
                        continue
                else:
                    # Simulate human player with random moves for non-interactive mode
                    available = game.available_edges()
                    if available:
                        orientation, row, col = self.rng.choice(available)
                        completed = game.claim_edge(orientation, row, col, player=game.human_name)
                    else:
                        break

                if not completed:
                    player_turn = False
            else:
                moves = game.computer_turn()
                if interactive:
                    for (orientation, row, col), completed in moves:
                        message = f"Computer draws {orientation} {row} {col}"
                        if completed:
                            message += f" and completes {completed} box{'es' if completed > 1 else ''}!"
                        print(message)
                player_turn = True

        human_score = game.scores[game.human_name]
        computer_score = game.scores[game.computer_name]

        if interactive:
            print("\n" + game.render())
            print(f"\nGame {game_number + 1} Result:")
            print(f"You: {human_score}, Computer: {computer_score}")
            if human_score > computer_score:
                print("You win this game! 🎉")
            elif human_score < computer_score:
                print("Computer wins this game! 🤖")
            else:
                print("This game is a tie! 🤝")

        return human_score, computer_score

    def run(self, interactive: bool = True) -> TournamentStats:
        """Run the entire tournament.

        Args:
            interactive: If True, human plays each game; if False, runs automatically

        Returns:
            TournamentStats with the tournament results
        """
        print(f"\n{'=' * 50}")
        print(f"DOTS AND BOXES TOURNAMENT ({self.size}x{self.size})")
        print(f"Playing {self.num_games} games")
        print(f"{'=' * 50}\n")

        for i in range(self.num_games):
            human_score, computer_score = self.play_game(i, interactive=interactive)
            self.stats.record_game(human_score, computer_score)

            if interactive and i < self.num_games - 1:
                input("\nPress Enter to continue to the next game...")

        print(f"\n{self.stats}")
        return self.stats


def play_tournament(size: int = 2, num_games: int = 5, seed: int | None = None) -> None:
    """Play a tournament of Dots and Boxes games.

    Args:
        size: Board size
        num_games: Number of games to play
        seed: Random seed for reproducibility
    """
    tournament = Tournament(size=size, num_games=num_games, seed=seed)
    tournament.run(interactive=True)


if __name__ == "__main__":
    play_tournament(size=2, num_games=3)
