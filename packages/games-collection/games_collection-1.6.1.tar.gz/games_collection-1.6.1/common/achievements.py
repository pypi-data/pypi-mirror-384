"""Cross-game achievement system for tracking player accomplishments.

This module provides a unified achievement framework that can be used across all
games in the repository. It includes achievement definitions, tracking, and
persistence.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional


class AchievementCategory(Enum):
    """Categories for organizing achievements."""

    GAMEPLAY = "gameplay"
    MASTERY = "mastery"
    PROGRESSION = "progression"
    SOCIAL = "social"
    SPECIAL = "special"


class AchievementRarity(Enum):
    """Rarity levels for achievements."""

    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass
class Achievement:
    """Represents a single achievement.

    Attributes:
        id: Unique identifier for the achievement.
        name: Display name of the achievement.
        description: Description of how to unlock the achievement.
        category: Category the achievement belongs to.
        rarity: Rarity level of the achievement.
        game: Optional game-specific achievement (None for cross-game).
        points: Point value of the achievement.
        hidden: Whether the achievement is hidden until unlocked.
        condition: Optional callable to check if achievement is unlocked.
    """

    id: str
    name: str
    description: str
    category: AchievementCategory
    rarity: AchievementRarity = AchievementRarity.COMMON
    game: Optional[str] = None
    points: int = 10
    hidden: bool = False
    condition: Optional[Callable[[Dict], bool]] = None

    def __post_init__(self) -> None:
        """Validate achievement data."""
        if self.points < 0:
            raise ValueError("Achievement points must be non-negative")


@dataclass
class UnlockedAchievement:
    """Represents an unlocked achievement with timestamp.

    Attributes:
        achievement_id: ID of the unlocked achievement.
        unlocked_at: Timestamp when achievement was unlocked.
        progress: Optional progress value (e.g., for incremental achievements).
    """

    achievement_id: str
    unlocked_at: str  # ISO format timestamp
    progress: Optional[Dict] = None

    @classmethod
    def create(cls, achievement_id: str, progress: Optional[Dict] = None) -> UnlockedAchievement:
        """Create a new unlocked achievement with current timestamp.

        Args:
            achievement_id: ID of the achievement being unlocked.
            progress: Optional progress data.

        Returns:
            New UnlockedAchievement instance.
        """
        return cls(achievement_id=achievement_id, unlocked_at=datetime.now().isoformat(), progress=progress)


class AchievementManager:
    """Manages achievement definitions, tracking, and persistence.

    This class provides methods to:
    - Register achievement definitions
    - Check and unlock achievements
    - Track progress towards achievements
    - Save and load achievement data
    """

    def __init__(self) -> None:
        """Initialize the achievement manager."""
        self.achievements: Dict[str, Achievement] = {}
        self.unlocked: Dict[str, UnlockedAchievement] = {}
        self.progress: Dict[str, Dict] = {}

    def register_achievement(self, achievement: Achievement) -> None:
        """Register a new achievement.

        Args:
            achievement: Achievement to register.

        Raises:
            ValueError: If achievement with same ID already exists.
        """
        if achievement.id in self.achievements:
            raise ValueError(f"Achievement with ID '{achievement.id}' already registered")
        self.achievements[achievement.id] = achievement

    def register_achievements(self, achievements: List[Achievement]) -> None:
        """Register multiple achievements.

        Args:
            achievements: List of achievements to register.
        """
        for achievement in achievements:
            self.register_achievement(achievement)

    def is_unlocked(self, achievement_id: str) -> bool:
        """Check if an achievement is unlocked.

        Args:
            achievement_id: ID of the achievement to check.

        Returns:
            True if unlocked, False otherwise.
        """
        return achievement_id in self.unlocked

    def unlock_achievement(self, achievement_id: str, progress: Optional[Dict] = None) -> bool:
        """Unlock an achievement.

        Args:
            achievement_id: ID of the achievement to unlock.
            progress: Optional progress data.

        Returns:
            True if newly unlocked, False if already unlocked.

        Raises:
            ValueError: If achievement ID is not registered.
        """
        if achievement_id not in self.achievements:
            raise ValueError(f"Achievement ID '{achievement_id}' not registered")

        if self.is_unlocked(achievement_id):
            return False

        self.unlocked[achievement_id] = UnlockedAchievement.create(achievement_id, progress)
        return True

    def check_achievements(self, stats: Dict) -> List[str]:
        """Check all achievements and unlock any that meet their conditions.

        Args:
            stats: Dictionary of statistics to check against conditions.

        Returns:
            List of newly unlocked achievement IDs.
        """
        newly_unlocked = []

        for achievement_id, achievement in self.achievements.items():
            if self.is_unlocked(achievement_id):
                continue

            if achievement.condition and achievement.condition(stats):
                if self.unlock_achievement(achievement_id):
                    newly_unlocked.append(achievement_id)

        return newly_unlocked

    def update_progress(self, achievement_id: str, progress_data: Dict) -> None:
        """Update progress for an achievement.

        Args:
            achievement_id: ID of the achievement.
            progress_data: Progress data to store.

        Raises:
            ValueError: If achievement ID is not registered.
        """
        if achievement_id not in self.achievements:
            raise ValueError(f"Achievement ID '{achievement_id}' not registered")

        self.progress[achievement_id] = progress_data

    def get_progress(self, achievement_id: str) -> Optional[Dict]:
        """Get progress data for an achievement.

        Args:
            achievement_id: ID of the achievement.

        Returns:
            Progress data if available, None otherwise.
        """
        return self.progress.get(achievement_id)

    def get_unlocked_count(self) -> int:
        """Get the count of unlocked achievements.

        Returns:
            Number of unlocked achievements.
        """
        return len(self.unlocked)

    def get_total_count(self) -> int:
        """Get the total count of registered achievements.

        Returns:
            Total number of registered achievements.
        """
        return len(self.achievements)

    def get_completion_percentage(self) -> float:
        """Calculate achievement completion percentage.

        Returns:
            Completion percentage (0-100).
        """
        total = self.get_total_count()
        if total == 0:
            return 0.0
        return (self.get_unlocked_count() / total) * 100

    def get_total_points(self) -> int:
        """Calculate total points earned from unlocked achievements.

        Returns:
            Total achievement points.
        """
        total_points = 0
        for unlocked in self.unlocked.values():
            if unlocked.achievement_id in self.achievements:
                total_points += self.achievements[unlocked.achievement_id].points
        return total_points

    def get_achievements_by_category(self, category: AchievementCategory) -> List[Achievement]:
        """Get all achievements in a specific category.

        Args:
            category: Category to filter by.

        Returns:
            List of achievements in the category.
        """
        return [ach for ach in self.achievements.values() if ach.category == category]

    def get_achievements_by_game(self, game: Optional[str]) -> List[Achievement]:
        """Get all achievements for a specific game.

        Args:
            game: Game name to filter by, or None for cross-game achievements.

        Returns:
            List of achievements for the game.
        """
        return [ach for ach in self.achievements.values() if ach.game == game]

    def get_unlocked_achievements(self) -> List[Achievement]:
        """Get all unlocked achievements.

        Returns:
            List of unlocked Achievement objects.
        """
        return [self.achievements[uid] for uid in self.unlocked.keys() if uid in self.achievements]

    def save(self, filepath: pathlib.Path) -> None:
        """Save achievement data to a JSON file.

        Args:
            filepath: Path to the file where data will be saved.
        """
        data = {
            "unlocked": {uid: {"achievement_id": u.achievement_id, "unlocked_at": u.unlocked_at, "progress": u.progress} for uid, u in self.unlocked.items()},
            "progress": self.progress,
        }
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: pathlib.Path) -> None:
        """Load achievement data from a JSON file.

        Args:
            filepath: Path to the file to load data from.
        """
        if not filepath.exists():
            return

        with open(filepath) as f:
            data = json.load(f)

        self.unlocked = {
            uid: UnlockedAchievement(achievement_id=u["achievement_id"], unlocked_at=u["unlocked_at"], progress=u.get("progress"))
            for uid, u in data.get("unlocked", {}).items()
        }
        self.progress = data.get("progress", {})

    def summary(self) -> str:
        """Generate a summary of achievement progress.

        Returns:
            Formatted string with achievement statistics.
        """
        lines = ["=" * 60]
        lines.append("ACHIEVEMENT PROGRESS")
        lines.append("=" * 60)
        lines.append(f"Unlocked: {self.get_unlocked_count()}/{self.get_total_count()} ({self.get_completion_percentage():.1f}%)")
        lines.append(f"Total Points: {self.get_total_points()}")
        lines.append("")

        # Show by category
        for category in AchievementCategory:
            cat_achievements = self.get_achievements_by_category(category)
            if not cat_achievements:
                continue

            unlocked_in_cat = sum(1 for ach in cat_achievements if self.is_unlocked(ach.id))
            lines.append(f"{category.value.capitalize()}: {unlocked_in_cat}/{len(cat_achievements)}")

        if self.unlocked:
            lines.append("")
            lines.append("Recent Achievements:")
            # Show last 5 unlocked achievements
            sorted_unlocked = sorted(self.unlocked.values(), key=lambda x: x.unlocked_at, reverse=True)[:5]
            for unlocked in sorted_unlocked:
                if unlocked.achievement_id in self.achievements:
                    ach = self.achievements[unlocked.achievement_id]
                    lines.append(f"  🏆 {ach.name} ({ach.points} points)")

        lines.append("=" * 60)
        return "\n".join(lines)


def create_common_achievements() -> List[Achievement]:
    """Create a set of common cross-game achievements.

    Returns:
        List of Achievement objects for common accomplishments.
    """
    return [
        Achievement(
            id="first_win",
            name="First Victory",
            description="Win your first game",
            category=AchievementCategory.PROGRESSION,
            rarity=AchievementRarity.COMMON,
            points=10,
            condition=lambda stats: stats.get("wins", 0) >= 1,
        ),
        Achievement(
            id="winning_streak_3",
            name="On a Roll",
            description="Win 3 games in a row",
            category=AchievementCategory.MASTERY,
            rarity=AchievementRarity.UNCOMMON,
            points=20,
            condition=lambda stats: stats.get("win_streak", 0) >= 3,
        ),
        Achievement(
            id="winning_streak_5",
            name="Unstoppable",
            description="Win 5 games in a row",
            category=AchievementCategory.MASTERY,
            rarity=AchievementRarity.RARE,
            points=50,
            condition=lambda stats: stats.get("win_streak", 0) >= 5,
        ),
        Achievement(
            id="games_played_10",
            name="Getting Started",
            description="Play 10 games",
            category=AchievementCategory.PROGRESSION,
            rarity=AchievementRarity.COMMON,
            points=15,
            condition=lambda stats: stats.get("games_played", 0) >= 10,
        ),
        Achievement(
            id="games_played_50",
            name="Dedicated Player",
            description="Play 50 games",
            category=AchievementCategory.PROGRESSION,
            rarity=AchievementRarity.UNCOMMON,
            points=30,
            condition=lambda stats: stats.get("games_played", 0) >= 50,
        ),
        Achievement(
            id="games_played_100",
            name="Veteran",
            description="Play 100 games",
            category=AchievementCategory.PROGRESSION,
            rarity=AchievementRarity.RARE,
            points=75,
            condition=lambda stats: stats.get("games_played", 0) >= 100,
        ),
        Achievement(
            id="perfect_game",
            name="Perfection",
            description="Win a game without losing a single round",
            category=AchievementCategory.SPECIAL,
            rarity=AchievementRarity.EPIC,
            points=100,
            hidden=True,
            condition=lambda stats: stats.get("perfect_games", 0) >= 1,
        ),
    ]
