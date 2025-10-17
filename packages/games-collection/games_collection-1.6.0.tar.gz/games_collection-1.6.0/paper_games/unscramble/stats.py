"""Game statistics tracking for Unscramble.

This module provides functionality to track and persist game statistics
including wins, losses, streaks, and achievements.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GameStats:
    """Track statistics for Unscramble games."""

    total_words: int = 0
    words_solved: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    games_played: int = 0
    stats_by_difficulty: Dict[str, Dict[str, int]] = field(default_factory=dict)
    stats_by_theme: Dict[str, Dict[str, int]] = field(default_factory=dict)
    achievements: List[str] = field(default_factory=list)
    total_time_spent: float = 0.0
    fastest_solve: Optional[float] = None

    def record_word(self, solved: bool, difficulty: Optional[str] = None, theme: Optional[str] = None, time_taken: Optional[float] = None) -> None:
        """Record the outcome of a word.

        Args:
            solved: Whether the word was solved correctly.
            difficulty: The difficulty level of the word (easy/medium/hard).
            theme: The theme of the word if applicable.
            time_taken: Time taken to solve the word in seconds.
        """
        self.total_words += 1

        if solved:
            self.words_solved += 1
            self.current_streak += 1
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak

            # Track fastest solve
            if time_taken is not None:
                if self.fastest_solve is None or time_taken < self.fastest_solve:
                    self.fastest_solve = time_taken
        else:
            self.current_streak = 0

        # Track time
        if time_taken is not None:
            self.total_time_spent += time_taken

        # Track stats by difficulty
        if difficulty:
            if difficulty not in self.stats_by_difficulty:
                self.stats_by_difficulty[difficulty] = {
                    "total": 0,
                    "solved": 0,
                }
            self.stats_by_difficulty[difficulty]["total"] += 1
            if solved:
                self.stats_by_difficulty[difficulty]["solved"] += 1

        # Track stats by theme
        if theme:
            if theme not in self.stats_by_theme:
                self.stats_by_theme[theme] = {
                    "total": 0,
                    "solved": 0,
                }
            self.stats_by_theme[theme]["total"] += 1
            if solved:
                self.stats_by_theme[theme]["solved"] += 1

    def record_game(self) -> None:
        """Record that a game session was completed."""
        self.games_played += 1

    def check_achievements(self) -> List[str]:
        """Check for newly unlocked achievements.

        Returns:
            List of newly unlocked achievement names.
        """
        new_achievements = []

        achievement_defs = [
            ("First Solve", lambda: self.words_solved >= 1),
            ("Getting Started", lambda: self.words_solved >= 10),
            ("Word Master", lambda: self.words_solved >= 50),
            ("Unscramble Legend", lambda: self.words_solved >= 100),
            ("Streak Starter", lambda: self.longest_streak >= 3),
            ("On Fire", lambda: self.longest_streak >= 5),
            ("Unstoppable", lambda: self.longest_streak >= 10),
            ("Speed Demon", lambda: self.fastest_solve is not None and self.fastest_solve < 5.0),
            ("Lightning Fast", lambda: self.fastest_solve is not None and self.fastest_solve < 3.0),
            ("Marathon Player", lambda: self.games_played >= 10),
            ("Dedicated", lambda: self.games_played >= 25),
        ]

        for name, condition in achievement_defs:
            if name not in self.achievements and condition():
                new_achievements.append(name)
                self.achievements.append(name)

        return new_achievements

    def solve_rate(self) -> float:
        """Calculate the solve rate as a percentage."""
        if self.total_words == 0:
            return 0.0
        return (self.words_solved / self.total_words) * 100

    def average_solve_time(self) -> float:
        """Calculate the average time to solve a word."""
        if self.words_solved == 0:
            return 0.0
        return self.total_time_spent / self.words_solved

    def summary(self) -> str:
        """Generate a summary of the statistics."""
        lines = ["=" * 60]
        lines.append("UNSCRAMBLE STATISTICS")
        lines.append("=" * 60)
        lines.append(f"Games Played: {self.games_played}")
        lines.append(f"Total Words: {self.total_words}")
        lines.append(f"Words Solved: {self.words_solved}")
        lines.append(f"Solve Rate: {self.solve_rate():.1f}%")
        lines.append(f"Current Streak: {self.current_streak}")
        lines.append(f"Longest Streak: {self.longest_streak}")

        if self.fastest_solve is not None:
            lines.append(f"Fastest Solve: {self.fastest_solve:.2f}s")

        if self.words_solved > 0:
            lines.append(f"Average Time: {self.average_solve_time():.2f}s")

        if self.stats_by_difficulty:
            lines.append("\nBy Difficulty:")
            for diff in ["easy", "medium", "hard"]:
                if diff in self.stats_by_difficulty:
                    stats = self.stats_by_difficulty[diff]
                    rate = (stats["solved"] / stats["total"] * 100) if stats["total"] > 0 else 0
                    lines.append(f"  {diff.capitalize()}: {stats['solved']}/{stats['total']} ({rate:.1f}%)")

        if self.stats_by_theme:
            lines.append("\nBy Theme:")
            for theme, stats in sorted(self.stats_by_theme.items()):
                rate = (stats["solved"] / stats["total"] * 100) if stats["total"] > 0 else 0
                lines.append(f"  {theme.capitalize()}: {stats['solved']}/{stats['total']} ({rate:.1f}%)")

        if self.achievements:
            lines.append(f"\nAchievements Unlocked: {len(self.achievements)}")
            for achievement in self.achievements[-5:]:  # Show last 5
                lines.append(f"  🏆 {achievement}")
            if len(self.achievements) > 5:
                lines.append(f"  ... and {len(self.achievements) - 5} more")

        lines.append("=" * 60)
        return "\n".join(lines)

    def save(self, filepath: pathlib.Path) -> None:
        """Save statistics to a JSON file.

        Args:
            filepath: Path to the file where statistics will be saved.
        """
        data = {
            "total_words": self.total_words,
            "words_solved": self.words_solved,
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "games_played": self.games_played,
            "stats_by_difficulty": self.stats_by_difficulty,
            "stats_by_theme": self.stats_by_theme,
            "achievements": self.achievements,
            "total_time_spent": self.total_time_spent,
            "fastest_solve": self.fastest_solve,
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
            GameStats instance with loaded data.
        """
        if not filepath.exists():
            return cls()

        with open(filepath) as f:
            data = json.load(f)

        return cls(
            total_words=data.get("total_words", 0),
            words_solved=data.get("words_solved", 0),
            current_streak=data.get("current_streak", 0),
            longest_streak=data.get("longest_streak", 0),
            games_played=data.get("games_played", 0),
            stats_by_difficulty=data.get("stats_by_difficulty", {}),
            stats_by_theme=data.get("stats_by_theme", {}),
            achievements=data.get("achievements", []),
            total_time_spent=data.get("total_time_spent", 0.0),
            fastest_solve=data.get("fastest_solve"),
        )
