"""Utilities for aggregating cross-game leaderboards and analytics snapshots."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional

from common.achievements_registry import get_achievement_registry
from common.analytics.game_stats import GameStatistics, PlayerStats
from common.profile import GameProfile, PlayerProfile


@dataclass(frozen=True)
class CrossGameLeaderboardEntry:
    """Summary row describing a player's progress across all games."""

    player_id: str
    display_name: str
    level: int
    experience: int
    total_games: int
    total_wins: int
    win_rate: float
    achievement_points: int
    achievements_unlocked: int
    favorite_game: Optional[str]
    daily_challenge_streak: int


class CrossGameLeaderboardService:
    """Build leaderboard and analytics data spanning every stored profile."""

    def __init__(self, profile_dir: pathlib.Path, *, active_profile: Optional[PlayerProfile] = None) -> None:
        self._profile_dir = profile_dir
        self._profiles: Dict[str, PlayerProfile] = {}
        if active_profile is not None:
            self._profiles[active_profile.player_id] = active_profile
        self._load_profiles_from_disk(active_profile)
        self._entries: Optional[List[CrossGameLeaderboardEntry]] = None
        self._analytics: Optional[Dict[str, GameStatistics]] = None

    def _load_profiles_from_disk(self, active_profile: Optional[PlayerProfile]) -> None:
        if not self._profile_dir.exists():
            return

        for path in sorted(self._profile_dir.glob("*.json")):
            player_id = path.stem
            if active_profile and player_id == active_profile.player_id:
                continue
            profile = PlayerProfile.load(path, player_id, player_id.title())
            registry = get_achievement_registry()
            registry.register_all(profile.achievement_manager)
            self._profiles[player_id] = profile

    def _build_entry(self, profile: PlayerProfile) -> CrossGameLeaderboardEntry:
        achievements = profile.achievement_manager
        return CrossGameLeaderboardEntry(
            player_id=profile.player_id,
            display_name=profile.display_name,
            level=profile.level,
            experience=profile.experience,
            total_games=profile.total_games_played(),
            total_wins=profile.total_wins(),
            win_rate=profile.overall_win_rate(),
            achievement_points=achievements.get_total_points(),
            achievements_unlocked=achievements.get_unlocked_count(),
            favorite_game=profile.favorite_game(),
            daily_challenge_streak=profile.daily_challenge_progress.current_streak,
        )

    def _ensure_entries(self) -> None:
        if self._entries is not None:
            return
        self._entries = [self._build_entry(profile) for profile in self._profiles.values()]

    def _player_stats_from_profile(self, profile: PlayerProfile, game_profile: GameProfile) -> PlayerStats:
        return PlayerStats(
            player_id=profile.player_id,
            total_games=game_profile.games_played,
            wins=game_profile.wins,
            losses=game_profile.losses,
            draws=game_profile.draws,
            current_win_streak=game_profile.win_streak,
            longest_win_streak=game_profile.best_win_streak,
            total_playtime=game_profile.total_playtime,
            first_played=game_profile.last_played,
            last_played=game_profile.last_played,
        )

    def _ensure_analytics(self) -> None:
        if self._analytics is not None:
            return

        analytics: Dict[str, GameStatistics] = {}
        for profile in self._profiles.values():
            for game_id, game_profile in profile.game_profiles.items():
                if game_profile.games_played == 0:
                    continue
                stats = analytics.setdefault(game_id, GameStatistics(game_name=game_id))
                stats.players[profile.player_id] = self._player_stats_from_profile(profile, game_profile)
        self._analytics = analytics

    def leaderboard(self, *, sort_by: str = "achievement_points", limit: int = 10) -> List[CrossGameLeaderboardEntry]:
        """Return a sorted list of leaderboard entries."""

        self._ensure_entries()
        entries = list(self._entries or [])
        if not entries:
            return []

        sorters: Dict[str, Callable[[CrossGameLeaderboardEntry], tuple]] = {
            "achievement_points": lambda entry: (
                entry.achievement_points,
                entry.total_wins,
                entry.win_rate,
                entry.experience,
            ),
            "wins": lambda entry: (entry.total_wins, entry.achievement_points, entry.win_rate, entry.experience),
            "xp": lambda entry: (entry.experience, entry.total_wins, entry.achievement_points),
            "streak": lambda entry: (
                entry.daily_challenge_streak,
                entry.total_wins,
                entry.achievement_points,
            ),
        }
        key = sorters.get(sort_by, sorters["achievement_points"])
        entries.sort(key=key, reverse=True)
        return entries[:limit]

    def analytics_snapshot(self) -> Dict[str, GameStatistics]:
        """Return aggregated analytics suitable for recommendations."""

        self._ensure_analytics()
        return dict(self._analytics or {})

    def profiles(self) -> Iterable[PlayerProfile]:
        """Return an iterable over the loaded profiles."""

        return self._profiles.values()
