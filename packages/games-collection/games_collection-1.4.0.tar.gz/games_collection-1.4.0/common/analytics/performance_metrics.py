"""Performance metrics tracking module.

This module tracks game performance metrics including game time,
decision time, move analysis, and other performance-related data.
"""

from __future__ import annotations

import json
import pathlib
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class DecisionMetrics:
    """Metrics for decision-making in games.

    Tracks decision times, move quality, and other decision-related metrics.
    """

    player_id: str
    total_decisions: int = 0
    decision_times: List[float] = field(default_factory=list)
    move_qualities: List[float] = field(default_factory=list)

    def record_decision(self, decision_time: float, quality: Optional[float] = None) -> None:
        """Record a decision.

        Args:
            decision_time: Time taken to make decision in seconds.
            quality: Optional quality score (0-1, where 1 is optimal).
        """
        self.total_decisions += 1
        self.decision_times.append(decision_time)
        if quality is not None:
            self.move_qualities.append(quality)

    def average_decision_time(self) -> float:
        """Calculate average decision time.

        Returns:
            Average decision time in seconds.
        """
        if not self.decision_times:
            return 0.0
        return statistics.mean(self.decision_times)

    def median_decision_time(self) -> float:
        """Calculate median decision time.

        Returns:
            Median decision time in seconds.
        """
        if not self.decision_times:
            return 0.0
        return statistics.median(self.decision_times)

    def decision_time_std(self) -> float:
        """Calculate standard deviation of decision times.

        Returns:
            Standard deviation of decision times.
        """
        if len(self.decision_times) < 2:
            return 0.0
        return statistics.stdev(self.decision_times)

    def average_move_quality(self) -> float:
        """Calculate average move quality.

        Returns:
            Average move quality (0-1).
        """
        if not self.move_qualities:
            return 0.0
        return statistics.mean(self.move_qualities)

    def fastest_decision(self) -> float:
        """Get fastest decision time.

        Returns:
            Fastest decision time in seconds.
        """
        if not self.decision_times:
            return 0.0
        return min(self.decision_times)

    def slowest_decision(self) -> float:
        """Get slowest decision time.

        Returns:
            Slowest decision time in seconds.
        """
        if not self.decision_times:
            return 0.0
        return max(self.decision_times)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation.
        """
        return {
            "player_id": self.player_id,
            "total_decisions": self.total_decisions,
            "decision_times": self.decision_times,
            "move_qualities": self.move_qualities,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> DecisionMetrics:
        """Create instance from dictionary.

        Args:
            data: Dictionary containing metrics data.

        Returns:
            DecisionMetrics instance.
        """
        return cls(**data)


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics tracker.

    Tracks various performance metrics including game duration,
    decision times, and player efficiency.
    """

    game_name: str
    players: Dict[str, DecisionMetrics] = field(default_factory=dict)
    game_durations: List[float] = field(default_factory=list)
    game_timestamps: List[str] = field(default_factory=list)

    def get_or_create_player(self, player_id: str) -> DecisionMetrics:
        """Get existing player metrics or create new one.

        Args:
            player_id: Unique player identifier.

        Returns:
            DecisionMetrics for the player.
        """
        if player_id not in self.players:
            self.players[player_id] = DecisionMetrics(player_id=player_id)
        return self.players[player_id]

    def record_decision(
        self,
        player_id: str,
        decision_time: float,
        quality: Optional[float] = None,
    ) -> None:
        """Record a player decision.

        Args:
            player_id: Player making the decision.
            decision_time: Time taken in seconds.
            quality: Optional quality score (0-1).
        """
        player_metrics = self.get_or_create_player(player_id)
        player_metrics.record_decision(decision_time, quality)

    def record_game_duration(self, duration: float) -> None:
        """Record a game duration.

        Args:
            duration: Game duration in seconds.
        """
        self.game_durations.append(duration)
        self.game_timestamps.append(datetime.now().isoformat())

    def average_game_duration(self) -> float:
        """Calculate average game duration.

        Returns:
            Average game duration in seconds.
        """
        if not self.game_durations:
            return 0.0
        return statistics.mean(self.game_durations)

    def median_game_duration(self) -> float:
        """Calculate median game duration.

        Returns:
            Median game duration in seconds.
        """
        if not self.game_durations:
            return 0.0
        return statistics.median(self.game_durations)

    def shortest_game(self) -> float:
        """Get shortest game duration.

        Returns:
            Shortest game duration in seconds.
        """
        if not self.game_durations:
            return 0.0
        return min(self.game_durations)

    def longest_game(self) -> float:
        """Get longest game duration.

        Returns:
            Longest game duration in seconds.
        """
        if not self.game_durations:
            return 0.0
        return max(self.game_durations)

    def get_summary(self) -> str:
        """Generate performance summary.

        Returns:
            Formatted summary string.
        """
        lines = [
            f"=== {self.game_name} Performance Metrics ===",
            f"Total Games Tracked: {len(self.game_durations)}",
            "",
        ]

        if self.game_durations:
            lines.extend(
                [
                    "Game Durations:",
                    f"  Average: {self.average_game_duration():.2f}s",
                    f"  Median: {self.median_game_duration():.2f}s",
                    f"  Shortest: {self.shortest_game():.2f}s",
                    f"  Longest: {self.longest_game():.2f}s",
                    "",
                ]
            )

        if self.players:
            lines.append("Player Decision Times:")
            for player_id, metrics in self.players.items():
                lines.append(f"  {player_id}:")
                lines.append(f"    Total Decisions: {metrics.total_decisions}")
                lines.append(f"    Average Time: {metrics.average_decision_time():.2f}s")
                lines.append(f"    Median Time: {metrics.median_decision_time():.2f}s")
                if metrics.move_qualities:
                    lines.append(f"    Average Move Quality: {metrics.average_move_quality():.2%}")

        return "\n".join(lines)

    def save(self, filepath: pathlib.Path) -> None:
        """Save metrics to JSON file.

        Args:
            filepath: Path to save file.
        """
        data = {
            "game_name": self.game_name,
            "players": {pid: p.to_dict() for pid, p in self.players.items()},
            "game_durations": self.game_durations,
            "game_timestamps": self.game_timestamps,
        }
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: pathlib.Path) -> PerformanceMetrics:
        """Load metrics from JSON file.

        Args:
            filepath: Path to load from.

        Returns:
            PerformanceMetrics instance.
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Metrics file not found: {filepath}")

        with open(filepath) as f:
            data = json.load(f)

        metrics = cls(game_name=data["game_name"])
        metrics.players = {pid: DecisionMetrics.from_dict(pdata) for pid, pdata in data.get("players", {}).items()}
        metrics.game_durations = data.get("game_durations", [])
        metrics.game_timestamps = data.get("game_timestamps", [])
        return metrics
