"""Game statistics tracking module.

This module provides comprehensive game statistics tracking including wins,
losses, streaks, and various metrics for both individual players and overall games.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class PlayerStats:
    """Statistics for an individual player.

    Tracks wins, losses, draws, streaks, and other player-specific metrics.
    """

    player_id: str
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    current_win_streak: int = 0
    longest_win_streak: int = 0
    current_loss_streak: int = 0
    longest_loss_streak: int = 0
    total_playtime: float = 0.0
    first_played: Optional[str] = None
    last_played: Optional[str] = None

    def win_rate(self) -> float:
        """Calculate win rate as a percentage.

        Returns:
            Win rate percentage (0-100).
        """
        if self.total_games == 0:
            return 0.0
        return (self.wins / self.total_games) * 100

    def loss_rate(self) -> float:
        """Calculate loss rate as a percentage.

        Returns:
            Loss rate percentage (0-100).
        """
        if self.total_games == 0:
            return 0.0
        return (self.losses / self.total_games) * 100

    def draw_rate(self) -> float:
        """Calculate draw rate as a percentage.

        Returns:
            Draw rate percentage (0-100).
        """
        if self.total_games == 0:
            return 0.0
        return (self.draws / self.total_games) * 100

    def average_game_duration(self) -> float:
        """Calculate average game duration in seconds.

        Returns:
            Average game duration.
        """
        if self.total_games == 0:
            return 0.0
        return self.total_playtime / self.total_games

    def record_game(self, result: str, duration: float) -> None:
        """Record a game result.

        Args:
            result: 'win', 'loss', or 'draw'
            duration: Game duration in seconds
        """
        self.total_games += 1
        self.total_playtime += duration

        now = datetime.now().isoformat()
        if self.first_played is None:
            self.first_played = now
        self.last_played = now

        if result == "win":
            self.wins += 1
            self.current_win_streak += 1
            self.current_loss_streak = 0
            if self.current_win_streak > self.longest_win_streak:
                self.longest_win_streak = self.current_win_streak
        elif result == "loss":
            self.losses += 1
            self.current_loss_streak += 1
            self.current_win_streak = 0
            if self.current_loss_streak > self.longest_loss_streak:
                self.longest_loss_streak = self.current_loss_streak
        elif result == "draw":
            self.draws += 1
            self.current_win_streak = 0
            self.current_loss_streak = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of player stats.
        """
        return {
            "player_id": self.player_id,
            "total_games": self.total_games,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "current_win_streak": self.current_win_streak,
            "longest_win_streak": self.longest_win_streak,
            "current_loss_streak": self.current_loss_streak,
            "longest_loss_streak": self.longest_loss_streak,
            "total_playtime": self.total_playtime,
            "first_played": self.first_played,
            "last_played": self.last_played,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> PlayerStats:
        """Create instance from dictionary.

        Args:
            data: Dictionary containing player stats data.

        Returns:
            PlayerStats instance.
        """
        return cls(**data)


@dataclass
class GameStatistics:
    """Comprehensive game statistics tracker.

    Tracks statistics for all players and provides aggregated metrics.
    """

    game_name: str
    players: Dict[str, PlayerStats] = field(default_factory=dict)
    game_history: List[Dict] = field(default_factory=list)

    def get_or_create_player(self, player_id: str) -> PlayerStats:
        """Get existing player stats or create new one.

        Args:
            player_id: Unique player identifier.

        Returns:
            PlayerStats for the player.
        """
        if player_id not in self.players:
            self.players[player_id] = PlayerStats(player_id=player_id)
        return self.players[player_id]

    def record_game(
        self,
        winner: Optional[str],
        players: List[str],
        duration: float,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Record a completed game.

        Args:
            winner: Player ID of winner, or None for draw.
            players: List of all player IDs in the game.
            duration: Game duration in seconds.
            metadata: Optional additional game metadata.
        """
        # Record in history
        game_record = {
            "timestamp": datetime.now().isoformat(),
            "winner": winner,
            "players": players,
            "duration": duration,
            "metadata": metadata or {},
        }
        self.game_history.append(game_record)

        # Update player stats
        for player_id in players:
            player_stats = self.get_or_create_player(player_id)
            if winner is None:
                player_stats.record_game("draw", duration)
            elif player_id == winner:
                player_stats.record_game("win", duration)
            else:
                player_stats.record_game("loss", duration)

    def get_leaderboard(self, sort_by: str = "win_rate") -> List[PlayerStats]:
        """Get leaderboard sorted by specified metric.

        Args:
            sort_by: Metric to sort by ('win_rate', 'wins', 'total_games').

        Returns:
            Sorted list of PlayerStats.
        """
        players_list = list(self.players.values())

        if sort_by == "win_rate":
            return sorted(players_list, key=lambda p: p.win_rate(), reverse=True)
        elif sort_by == "wins":
            return sorted(players_list, key=lambda p: p.wins, reverse=True)
        elif sort_by == "total_games":
            return sorted(players_list, key=lambda p: p.total_games, reverse=True)
        else:
            return players_list

    def get_summary(self) -> str:
        """Generate a summary of all statistics.

        Returns:
            Formatted summary string.
        """
        total_games = len(self.game_history)
        total_players = len(self.players)

        lines = [
            f"=== {self.game_name} Statistics ===",
            f"Total Games: {total_games}",
            f"Total Players: {total_players}",
            "",
        ]

        if self.players:
            lines.append("Top Players (by win rate):")
            for i, player in enumerate(self.get_leaderboard("win_rate")[:5], 1):
                lines.append(f"  {i}. {player.player_id}: " f"{player.wins}W-{player.losses}L-{player.draws}D " f"({player.win_rate():.1f}% win rate)")

        return "\n".join(lines)

    def save(self, filepath: pathlib.Path) -> None:
        """Save statistics to JSON file.

        Args:
            filepath: Path to save file.
        """
        data = {
            "game_name": self.game_name,
            "players": {pid: p.to_dict() for pid, p in self.players.items()},
            "game_history": self.game_history,
        }
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: pathlib.Path) -> GameStatistics:
        """Load statistics from JSON file.

        Args:
            filepath: Path to load from.

        Returns:
            GameStatistics instance.
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Statistics file not found: {filepath}")

        with open(filepath) as f:
            data = json.load(f)

        stats = cls(game_name=data["game_name"])
        stats.players = {pid: PlayerStats.from_dict(pdata) for pid, pdata in data.get("players", {}).items()}
        stats.game_history = data.get("game_history", [])
        return stats
