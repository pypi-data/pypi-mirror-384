"""Unified player profile and progression system.

This module provides a centralized profile system for tracking player data,
statistics, and progression across all games.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from common.achievements import AchievementManager


@dataclass
class GameProfile:
    """Represents statistics for a specific game.

    Attributes:
        game_id: Unique identifier for the game.
        games_played: Total games played.
        wins: Number of wins.
        losses: Number of losses.
        draws: Number of draws.
        win_streak: Current win streak.
        best_win_streak: Best win streak achieved.
        total_playtime: Total playtime in seconds.
        last_played: ISO timestamp of last play.
        custom_stats: Game-specific statistics.
    """

    game_id: str
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    win_streak: int = 0
    best_win_streak: int = 0
    total_playtime: float = 0.0
    last_played: Optional[str] = None
    custom_stats: Dict = field(default_factory=dict)

    def record_game(self, result: str, playtime: Optional[float] = None) -> None:
        """Record a game result.

        Args:
            result: Game result ('win', 'loss', or 'draw').
            playtime: Optional playtime in seconds.
        """
        self.games_played += 1
        self.last_played = datetime.now().isoformat()

        if playtime is not None:
            self.total_playtime += playtime

        if result == "win":
            self.wins += 1
            self.win_streak += 1
            if self.win_streak > self.best_win_streak:
                self.best_win_streak = self.win_streak
        elif result == "loss":
            self.losses += 1
            self.win_streak = 0
        elif result == "draw":
            self.draws += 1
            # Win streak continues on draw

    def win_rate(self) -> float:
        """Calculate win rate as a percentage.

        Returns:
            Win rate (0-100).
        """
        total_decisive = self.wins + self.losses
        if total_decisive == 0:
            return 0.0
        return (self.wins / total_decisive) * 100

    def average_playtime(self) -> float:
        """Calculate average playtime per game.

        Returns:
            Average playtime in seconds.
        """
        if self.games_played == 0:
            return 0.0
        return self.total_playtime / self.games_played

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation.
        """
        return {
            "game_id": self.game_id,
            "games_played": self.games_played,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "win_streak": self.win_streak,
            "best_win_streak": self.best_win_streak,
            "total_playtime": self.total_playtime,
            "last_played": self.last_played,
            "custom_stats": self.custom_stats,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> GameProfile:
        """Create from dictionary.

        Args:
            data: Dictionary with profile data.

        Returns:
            GameProfile instance.
        """
        return cls(
            game_id=data["game_id"],
            games_played=data.get("games_played", 0),
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            draws=data.get("draws", 0),
            win_streak=data.get("win_streak", 0),
            best_win_streak=data.get("best_win_streak", 0),
            total_playtime=data.get("total_playtime", 0.0),
            last_played=data.get("last_played"),
            custom_stats=data.get("custom_stats", {}),
        )


@dataclass
class PlayerProfile:
    """Unified player profile across all games.

    Attributes:
        player_id: Unique player identifier.
        display_name: Player's display name.
        created_at: ISO timestamp of profile creation.
        last_active: ISO timestamp of last activity.
        game_profiles: Dictionary of game-specific profiles.
        achievement_manager: Achievement tracking manager.
        level: Player level based on total experience.
        experience: Total experience points.
        preferences: Player preferences (e.g., theme, difficulty).
    """

    player_id: str
    display_name: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    game_profiles: Dict[str, GameProfile] = field(default_factory=dict)
    achievement_manager: AchievementManager = field(default_factory=AchievementManager)
    level: int = 1
    experience: int = 0
    preferences: Dict = field(default_factory=dict)

    def get_game_profile(self, game_id: str) -> GameProfile:
        """Get or create a game-specific profile.

        Args:
            game_id: Unique identifier for the game.

        Returns:
            GameProfile for the specified game.
        """
        if game_id not in self.game_profiles:
            self.game_profiles[game_id] = GameProfile(game_id=game_id)
        return self.game_profiles[game_id]

    def record_game(self, game_id: str, result: str, playtime: Optional[float] = None, experience_gained: int = 0) -> None:
        """Record a game result and update profile.

        Args:
            game_id: Game identifier.
            result: Game result ('win', 'loss', or 'draw').
            playtime: Optional playtime in seconds.
            experience_gained: Experience points gained.
        """
        self.last_active = datetime.now().isoformat()

        profile = self.get_game_profile(game_id)
        profile.record_game(result, playtime)

        # Add experience
        if experience_gained > 0:
            self.add_experience(experience_gained)

    def add_experience(self, amount: int) -> bool:
        """Add experience points and check for level up.

        Args:
            amount: Amount of experience to add.

        Returns:
            True if player leveled up, False otherwise.
        """
        self.experience += amount
        new_level = self.calculate_level(self.experience)

        if new_level > self.level:
            self.level = new_level
            return True
        return False

    @staticmethod
    def calculate_level(experience: int) -> int:
        """Calculate player level from experience points.

        Uses a simple formula: level = floor(sqrt(experience / 100)) + 1

        Args:
            experience: Total experience points.

        Returns:
            Player level.
        """
        import math

        return int(math.sqrt(experience / 100)) + 1

    def experience_to_next_level(self) -> int:
        """Calculate experience needed for next level.

        Returns:
            Experience points needed to reach next level.
        """
        next_level = self.level + 1
        next_level_exp = (next_level - 1) ** 2 * 100
        return next_level_exp - self.experience

    def total_games_played(self) -> int:
        """Calculate total games played across all games.

        Returns:
            Total number of games played.
        """
        return sum(profile.games_played for profile in self.game_profiles.values())

    def total_wins(self) -> int:
        """Calculate total wins across all games.

        Returns:
            Total number of wins.
        """
        return sum(profile.wins for profile in self.game_profiles.values())

    def total_playtime(self) -> float:
        """Calculate total playtime across all games.

        Returns:
            Total playtime in seconds.
        """
        return sum(profile.total_playtime for profile in self.game_profiles.values())

    def overall_win_rate(self) -> float:
        """Calculate overall win rate across all games.

        Returns:
            Overall win rate (0-100).
        """
        total_wins = self.total_wins()
        total_games = sum(profile.wins + profile.losses for profile in self.game_profiles.values())

        if total_games == 0:
            return 0.0
        return (total_wins / total_games) * 100

    def favorite_game(self) -> Optional[str]:
        """Determine the player's favorite game based on playtime.

        Returns:
            Game ID of most played game, or None if no games played.
        """
        if not self.game_profiles:
            return None

        return max(self.game_profiles.items(), key=lambda x: x[1].games_played)[0]

    def save(self, filepath: pathlib.Path) -> None:
        """Save profile to a JSON file.

        Args:
            filepath: Path to the file where profile will be saved.
        """
        data = {
            "player_id": self.player_id,
            "display_name": self.display_name,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "level": self.level,
            "experience": self.experience,
            "preferences": self.preferences,
            "game_profiles": {gid: profile.to_dict() for gid, profile in self.game_profiles.items()},
        }

        # Save achievements separately or inline
        achievements_data = {
            "unlocked": {
                uid: {"achievement_id": u.achievement_id, "unlocked_at": u.unlocked_at, "progress": u.progress}
                for uid, u in self.achievement_manager.unlocked.items()
            },
            "progress": self.achievement_manager.progress,
        }
        data["achievements"] = achievements_data

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: pathlib.Path, player_id: str, display_name: str = "Player") -> PlayerProfile:
        """Load profile from a JSON file.

        Args:
            filepath: Path to the file to load profile from.
            player_id: Player identifier (used if file doesn't exist).
            display_name: Display name (used if file doesn't exist).

        Returns:
            PlayerProfile instance.
        """
        if not filepath.exists():
            return cls(player_id=player_id, display_name=display_name)

        with open(filepath) as f:
            data = json.load(f)

        profile = cls(
            player_id=data.get("player_id", player_id),
            display_name=data.get("display_name", display_name),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_active=data.get("last_active", datetime.now().isoformat()),
            level=data.get("level", 1),
            experience=data.get("experience", 0),
            preferences=data.get("preferences", {}),
        )

        # Load game profiles
        for gid, gdata in data.get("game_profiles", {}).items():
            profile.game_profiles[gid] = GameProfile.from_dict(gdata)

        # Load achievements
        achievements_data = data.get("achievements", {})
        if achievements_data:
            from common.achievements import UnlockedAchievement

            profile.achievement_manager.unlocked = {
                uid: UnlockedAchievement(achievement_id=u["achievement_id"], unlocked_at=u["unlocked_at"], progress=u.get("progress"))
                for uid, u in achievements_data.get("unlocked", {}).items()
            }
            profile.achievement_manager.progress = achievements_data.get("progress", {})

        return profile

    def summary(self) -> str:
        """Generate a profile summary.

        Returns:
            Formatted string with profile information.
        """
        lines = ["=" * 60]
        lines.append(f"PLAYER PROFILE: {self.display_name}")
        lines.append("=" * 60)
        lines.append(f"Level: {self.level} (XP: {self.experience})")
        lines.append(f"XP to Next Level: {self.experience_to_next_level()}")
        lines.append(f"Total Games: {self.total_games_played()}")
        lines.append(f"Total Wins: {self.total_wins()}")
        lines.append(f"Overall Win Rate: {self.overall_win_rate():.1f}%")

        if self.total_playtime() > 0:
            hours = self.total_playtime() / 3600
            lines.append(f"Total Playtime: {hours:.1f} hours")

        favorite = self.favorite_game()
        if favorite:
            lines.append(f"Favorite Game: {favorite}")

        lines.append(f"\nAchievements: {self.achievement_manager.get_unlocked_count()}/{self.achievement_manager.get_total_count()}")
        lines.append(f"Achievement Points: {self.achievement_manager.get_total_points()}")

        if self.game_profiles:
            lines.append("\nGame Statistics:")
            for game_id, profile in sorted(self.game_profiles.items(), key=lambda x: x[1].games_played, reverse=True)[:5]:
                lines.append(f"  {game_id}: {profile.wins}W/{profile.losses}L ({profile.win_rate():.1f}% win rate)")

        lines.append("=" * 60)
        return "\n".join(lines)


def get_default_profile_dir() -> pathlib.Path:
    """Get the default directory for storing player profiles.

    Returns:
        Path to the profiles directory.
    """
    import os

    # Use platform-appropriate directory
    if os.name == "nt":  # Windows
        base_dir = pathlib.Path(os.environ.get("APPDATA", "~/.games"))
    else:  # Unix-like
        base_dir = pathlib.Path.home() / ".games"

    return base_dir / "profiles"


def load_or_create_profile(player_id: str = "default", display_name: str = "Player") -> PlayerProfile:
    """Load an existing profile or create a new one.

    Args:
        player_id: Player identifier.
        display_name: Display name for new profiles.

    Returns:
        PlayerProfile instance.
    """
    profile_dir = get_default_profile_dir()
    profile_file = profile_dir / f"{player_id}.json"

    return PlayerProfile.load(profile_file, player_id, display_name)
