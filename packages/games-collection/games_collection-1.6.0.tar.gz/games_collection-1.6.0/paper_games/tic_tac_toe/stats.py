"""Game statistics tracking for tic-tac-toe.

This module provides functionality to track and persist game statistics
including wins, losses, draws, and other metrics.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class GameStats:
    """Track statistics for tic-tac-toe games."""

    human_wins: int = 0
    computer_wins: int = 0
    draws: int = 0
    games_played: int = 0
    stats_by_board_size: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def record_game(self, winner: Optional[str], human_symbol: str, computer_symbol: str, board_size: int = 3) -> None:
        """Record the outcome of a game.

        Args:
            winner: The symbol of the winner, or None for a draw.
            human_symbol: The symbol used by the human player.
            computer_symbol: The symbol used by the computer player.
            board_size: The size of the board used in the game.
        """
        self.games_played += 1

        if winner == human_symbol:
            self.human_wins += 1
        elif winner == computer_symbol:
            self.computer_wins += 1
        else:
            self.draws += 1

        # Track stats by board size
        board_key = f"{board_size}x{board_size}"
        if board_key not in self.stats_by_board_size:
            self.stats_by_board_size[board_key] = {
                "human_wins": 0,
                "computer_wins": 0,
                "draws": 0,
                "games": 0,
            }

        self.stats_by_board_size[board_key]["games"] += 1
        if winner == human_symbol:
            self.stats_by_board_size[board_key]["human_wins"] += 1
        elif winner == computer_symbol:
            self.stats_by_board_size[board_key]["computer_wins"] += 1
        else:
            self.stats_by_board_size[board_key]["draws"] += 1

    def win_rate(self) -> float:
        """Calculate the human player's win rate."""
        if self.games_played == 0:
            return 0.0
        return self.human_wins / self.games_played

    def summary(self) -> str:
        """Generate a summary of the statistics."""
        lines = [
            "=== Tic-Tac-Toe Statistics ===",
            f"Total games played: {self.games_played}",
            f"Your wins: {self.human_wins}",
            f"Computer wins: {self.computer_wins}",
            f"Draws: {self.draws}",
        ]

        if self.games_played > 0:
            win_rate = self.win_rate() * 100
            lines.append(f"Your win rate: {win_rate:.1f}%")

        if self.stats_by_board_size:
            lines.append("\n--- By Board Size ---")
            for board_key in sorted(self.stats_by_board_size.keys()):
                stats = self.stats_by_board_size[board_key]
                lines.append(f"{board_key}: {stats['games']} games")
                lines.append(f"  Your wins: {stats['human_wins']}, Computer wins: {stats['computer_wins']}, Draws: {stats['draws']}")

        return "\n".join(lines)

    def save(self, filepath: pathlib.Path) -> None:
        """Save statistics to a JSON file.

        Args:
            filepath: Path to the file where statistics will be saved.
        """
        data = {
            "human_wins": self.human_wins,
            "computer_wins": self.computer_wins,
            "draws": self.draws,
            "games_played": self.games_played,
            "stats_by_board_size": self.stats_by_board_size,
        }
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: pathlib.Path) -> GameStats:
        """Load statistics from a JSON file.

        Args:
            filepath: Path to the file to load statistics from.

        Returns:
            A GameStats instance with loaded data, or a new instance if the file doesn't exist.
        """
        if not filepath.exists():
            return cls()

        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            return cls(
                human_wins=data.get("human_wins", 0),
                computer_wins=data.get("computer_wins", 0),
                draws=data.get("draws", 0),
                games_played=data.get("games_played", 0),
                stats_by_board_size=data.get("stats_by_board_size", {}),
            )
        except (json.JSONDecodeError, IOError):
            return cls()
