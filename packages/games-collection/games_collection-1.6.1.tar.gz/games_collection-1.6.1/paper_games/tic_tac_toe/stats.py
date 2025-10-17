"""Game statistics tracking and persistence for Tic-Tac-Toe.

This module provides the `GameStats` class, which is responsible for tracking,
calculating, and persisting game statistics. It can record the outcome of
each game, calculate win rates, and break down stats by board size.

The statistics are saved to and loaded from a JSON file, allowing for
persistent tracking of a player's performance over multiple sessions.

Classes:
    GameStats: A dataclass for managing Tic-Tac-Toe game statistics.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class GameStats:
    """Tracks and manages statistics for Tic-Tac-Toe games.

    This class provides methods to record game outcomes, calculate performance
    metrics like win rate, and generate a summary of the statistics. It also
    handles the serialization and deserialization of stats to a JSON file.

    Attributes:
        human_wins (int): The total number of wins for the human player.
        computer_wins (int): The total number of wins for the computer.
        draws (int): The total number of drawn games.
        games_played (int): The total number of games played.
        stats_by_board_size (Dict[str, Dict[str, int]]): A nested dictionary
            that tracks wins, losses, and draws for each board size.
    """

    human_wins: int = 0
    computer_wins: int = 0
    draws: int = 0
    games_played: int = 0
    stats_by_board_size: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def record_game(self, winner: Optional[str], human_symbol: str, computer_symbol: str, board_size: int = 3) -> None:
        """Records the outcome of a single game and updates the statistics.

        This method increments the total games played and updates the win, loss,
        or draw counts for both the overall stats and the stats specific to the
        board size.

        Args:
            winner (Optional[str]): The symbol of the winning player, or None for a draw.
            human_symbol (str): The symbol used by the human player.
            computer_symbol (str): The symbol used by the computer player.
            board_size (int): The size of the board used in the game (e.g., 3 for 3x3).
        """
        self.games_played += 1

        # Update the overall win/loss/draw counts.
        if winner == human_symbol:
            self.human_wins += 1
        elif winner == computer_symbol:
            self.computer_wins += 1
        else:
            self.draws += 1

        # Track statistics by board size for more detailed analysis.
        board_key = f"{board_size}x{board_size}"
        if board_key not in self.stats_by_board_size:
            # Initialize the stats for this board size if it's the first time.
            self.stats_by_board_size[board_key] = {
                "human_wins": 0,
                "computer_wins": 0,
                "draws": 0,
                "games": 0,
            }

        # Update the stats for the specific board size.
        self.stats_by_board_size[board_key]["games"] += 1
        if winner == human_symbol:
            self.stats_by_board_size[board_key]["human_wins"] += 1
        elif winner == computer_symbol:
            self.stats_by_board_size[board_key]["computer_wins"] += 1
        else:
            self.stats_by_board_size[board_key]["draws"] += 1

    def win_rate(self) -> float:
        """Calculates the human player's win rate as a percentage.

        Returns:
            float: The win rate, ranging from 0.0 to 1.0.
        """
        if self.games_played == 0:
            return 0.0
        return self.human_wins / self.games_played

    def summary(self) -> str:
        """Generates a human-readable summary of the game statistics.

        This method creates a formatted string that displays the total games played,
        win/loss/draw counts, win rate, and a breakdown of stats by board size.

        Returns:
            str: A formatted string containing the statistics summary.
        """
        lines = [
            "=== Tic-Tac-Toe Statistics ===",
            f"Total games played: {self.games_played}",
            f"Your wins: {self.human_wins}",
            f"Computer wins: {self.computer_wins}",
            f"Draws: {self.draws}",
        ]

        if self.games_played > 0:
            win_rate_percent = self.win_rate() * 100
            lines.append(f"Your win rate: {win_rate_percent:.1f}%")

        if self.stats_by_board_size:
            lines.append("\n--- By Board Size ---")
            for board_key in sorted(self.stats_by_board_size.keys()):
                stats = self.stats_by_board_size[board_key]
                lines.append(f"{board_key}: {stats['games']} games")
                lines.append(f"  Your wins: {stats['human_wins']}, Computer wins: {stats['computer_wins']}, Draws: {stats['draws']}")

        return "\n".join(lines)

    def save(self, filepath: pathlib.Path) -> None:
        """Saves the current statistics to a JSON file.

        This method serializes the `GameStats` object to a dictionary and writes
        it to the specified file, creating the parent directory if it doesn't exist.

        Args:
            filepath (pathlib.Path): The path to the file where the statistics will be saved.
        """
        data = {
            "human_wins": self.human_wins,
            "computer_wins": self.computer_wins,
            "draws": self.draws,
            "games_played": self.games_played,
            "stats_by_board_size": self.stats_by_board_size,
        }
        # Ensure the directory exists before writing the file.
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: pathlib.Path) -> GameStats:
        """Loads game statistics from a JSON file.

        If the specified file does not exist or contains invalid data, a new
        `GameStats` instance with default values is returned.

        Args:
            filepath (pathlib.Path): The path to the file from which to load the statistics.

        Returns:
            GameStats: An instance of `GameStats` with the loaded data, or a new
                       instance if the file cannot be loaded.
        """
        if not filepath.exists():
            return cls()

        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            # Create a new GameStats instance from the loaded data.
            return cls(
                human_wins=data.get("human_wins", 0),
                computer_wins=data.get("computer_wins", 0),
                draws=data.get("draws", 0),
                games_played=data.get("games_played", 0),
                stats_by_board_size=data.get("stats_by_board_size", {}),
            )
        except (json.JSONDecodeError, IOError):
            # If the file is corrupted or unreadable, return a fresh instance.
            return cls()
