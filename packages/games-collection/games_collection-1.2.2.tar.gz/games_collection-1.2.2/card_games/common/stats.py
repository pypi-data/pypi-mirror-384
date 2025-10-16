"""Statistics tracking for card games.

This module provides a simplified interface to the common analytics system
specifically tailored for card games. It tracks wins, losses, game durations,
and card-specific metrics.
"""

from __future__ import annotations

import json
import pathlib
from typing import Optional

from common.analytics.game_stats import GameStatistics, PlayerStats


class CardGameStats:
    """Statistics tracker for card games.

    This class wraps the common GameStatsTracker to provide card game
    specific functionality and simplified interface.
    """

    def __init__(self, game_name: str, stats_dir: Optional[pathlib.Path] = None) -> None:
        """Initialize card game statistics tracker.

        Args:
            game_name: Name of the card game (e.g., "poker", "war", "go_fish")
            stats_dir: Optional directory for storing stats (defaults to ~/.game_stats)
        """
        self.game_name = game_name
        self.stats_dir = stats_dir or pathlib.Path.home() / ".game_stats"
        self.stats_dir.mkdir(parents=True, exist_ok=True)
        self.stats_file = self.stats_dir / f"{game_name}_stats.json"
        self.tracker = self._load_stats()

    def _load_stats(self) -> GameStatistics:
        """Load statistics from file.

        Returns:
            GameStatistics instance
        """
        if self.stats_file.exists():
            try:
                with open(self.stats_file, "r") as f:
                    data = json.load(f)
                    stats = GameStatistics(game_name=self.game_name)
                    stats.players = {pid: PlayerStats.from_dict(pdata) for pid, pdata in data.get("players", {}).items()}
                    stats.game_history = data.get("game_history", [])
                    return stats
            except Exception:
                pass
        return GameStatistics(game_name=self.game_name)

    def record_win(self, player_name: str, duration: float, score: Optional[int] = None) -> None:
        """Record a win for a player.

        Args:
            player_name: Name of the winning player
            duration: Game duration in seconds
            score: Optional final score
        """
        player_stats = self.tracker.get_or_create_player(player_name)
        player_stats.record_game("win", duration)

    def record_loss(self, player_name: str, duration: float, score: Optional[int] = None) -> None:
        """Record a loss for a player.

        Args:
            player_name: Name of the losing player
            duration: Game duration in seconds
            score: Optional final score
        """
        player_stats = self.tracker.get_or_create_player(player_name)
        player_stats.record_game("loss", duration)

    def record_draw(self, player_name: str, duration: float) -> None:
        """Record a draw for a player.

        Args:
            player_name: Name of the player
            duration: Game duration in seconds
        """
        player_stats = self.tracker.get_or_create_player(player_name)
        player_stats.record_game("draw", duration)

    def get_player_stats(self, player_name: str) -> dict[str, any]:
        """Get statistics for a specific player.

        Args:
            player_name: Name of the player

        Returns:
            Dictionary with player statistics including:
            - total_games: Total games played
            - wins: Number of wins
            - losses: Number of losses
            - draws: Number of draws
            - win_rate: Win rate percentage
            - current_streak: Current win/loss streak
            - longest_win_streak: Longest winning streak
            - average_duration: Average game duration
        """
        if player_name not in self.tracker.players:
            return {
                "total_games": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "win_rate": 0.0,
                "current_streak": 0,
                "longest_win_streak": 0,
                "average_duration": 0.0,
            }

        stats = self.tracker.players[player_name]
        return {
            "total_games": stats.total_games,
            "wins": stats.wins,
            "losses": stats.losses,
            "draws": stats.draws,
            "win_rate": stats.win_rate(),
            "current_streak": stats.current_win_streak,
            "longest_win_streak": stats.longest_win_streak,
            "average_duration": stats.average_game_duration(),
        }

    def get_leaderboard(self, limit: int = 10) -> list[dict[str, any]]:
        """Get top players by win rate.

        Args:
            limit: Maximum number of players to return

        Returns:
            List of player dictionaries sorted by wins, each containing:
            - player_name: Player's name
            - wins: Number of wins
            - total_games: Total games played
            - win_rate: Win rate percentage
        """
        leaderboard = [
            {
                "player_name": player_id,
                "wins": stats.wins,
                "total_games": stats.total_games,
                "win_rate": stats.win_rate(),
            }
            for player_id, stats in self.tracker.players.items()
            if stats.total_games > 0
        ]

        # Sort by wins (primary) and win rate (secondary)
        leaderboard.sort(key=lambda x: (x["wins"], x["win_rate"]), reverse=True)

        return leaderboard[:limit]

    def display_player_stats(self, player_name: str) -> None:
        """Display formatted statistics for a player.

        Args:
            player_name: Name of the player
        """
        stats = self.get_player_stats(player_name)

        print(f"\n{'=' * 60}")
        print(f"Statistics for {player_name} - {self.game_name.title()}")
        print(f"{'=' * 60}")
        print(f"Total Games:          {stats['total_games']}")
        print(f"Wins:                 {stats['wins']}")
        print(f"Losses:               {stats['losses']}")
        print(f"Draws:                {stats['draws']}")
        print(f"Win Rate:             {stats['win_rate']:.1f}%")
        print(f"Current Streak:       {stats['current_streak']}")
        print(f"Longest Win Streak:   {stats['longest_win_streak']}")
        print(f"Average Game Time:    {stats['average_duration']:.1f}s")
        print(f"{'=' * 60}\n")

    def display_leaderboard(self, limit: int = 10) -> None:
        """Display formatted leaderboard.

        Args:
            limit: Maximum number of players to show
        """
        leaderboard = self.get_leaderboard(limit)

        print(f"\n{'=' * 60}")
        print(f"Leaderboard - {self.game_name.title()}")
        print(f"{'=' * 60}")
        print(f"{'Rank':<6} {'Player':<20} {'Wins':<8} {'Games':<8} {'Win %':<8}")
        print(f"{'-' * 60}")

        for i, entry in enumerate(leaderboard, 1):
            print(f"{i:<6} {entry['player_name']:<20} {entry['wins']:<8} " f"{entry['total_games']:<8} {entry['win_rate']:<8.1f}")

        print(f"{'=' * 60}\n")

    def save(self) -> None:
        """Save statistics to disk."""
        data = {
            "game_name": self.tracker.game_name,
            "players": {pid: stats.to_dict() for pid, stats in self.tracker.players.items()},
            "game_history": self.tracker.game_history,
        }
        with open(self.stats_file, "w") as f:
            json.dump(data, f, indent=2)

    def clear_stats(self, player_name: Optional[str] = None) -> None:
        """Clear statistics.

        Args:
            player_name: If provided, clear only this player's stats.
                        If None, clear all stats for this game.
        """
        if player_name:
            # Remove specific player
            if player_name in self.tracker.players:
                del self.tracker.players[player_name]
                self.save()
        else:
            # Clear all stats
            self.tracker.players.clear()
            self.tracker.game_history.clear()
            self.save()
