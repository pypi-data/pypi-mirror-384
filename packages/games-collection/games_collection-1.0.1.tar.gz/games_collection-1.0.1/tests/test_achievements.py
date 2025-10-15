"""Tests for the achievement system."""

from __future__ import annotations

import pathlib
import tempfile
from datetime import datetime

import pytest

from common.achievements import (
    Achievement,
    AchievementCategory,
    AchievementManager,
    AchievementRarity,
    UnlockedAchievement,
    create_common_achievements,
)


class TestAchievement:
    """Test the Achievement dataclass."""

    def test_initialization(self):
        """Test creating an achievement."""
        ach = Achievement(
            id="test_ach",
            name="Test Achievement",
            description="A test achievement",
            category=AchievementCategory.GAMEPLAY,
            rarity=AchievementRarity.COMMON,
            points=10,
        )

        assert ach.id == "test_ach"
        assert ach.name == "Test Achievement"
        assert ach.description == "A test achievement"
        assert ach.category == AchievementCategory.GAMEPLAY
        assert ach.rarity == AchievementRarity.COMMON
        assert ach.points == 10
        assert ach.game is None
        assert ach.hidden is False

    def test_game_specific_achievement(self):
        """Test creating a game-specific achievement."""
        ach = Achievement(id="uno_win", name="Uno Champion", description="Win a game of Uno", category=AchievementCategory.GAMEPLAY, game="uno", points=15)

        assert ach.game == "uno"

    def test_negative_points_raises_error(self):
        """Test that negative points raise an error."""
        with pytest.raises(ValueError, match="Achievement points must be non-negative"):
            Achievement(id="bad", name="Bad", description="Bad points", category=AchievementCategory.GAMEPLAY, points=-10)


class TestUnlockedAchievement:
    """Test the UnlockedAchievement dataclass."""

    def test_create(self):
        """Test creating an unlocked achievement."""
        unlocked = UnlockedAchievement.create("test_ach")

        assert unlocked.achievement_id == "test_ach"
        assert unlocked.progress is None

        # Check timestamp is valid ISO format
        datetime.fromisoformat(unlocked.unlocked_at)

    def test_create_with_progress(self):
        """Test creating an unlocked achievement with progress."""
        progress = {"value": 10, "max": 100}
        unlocked = UnlockedAchievement.create("test_ach", progress)

        assert unlocked.achievement_id == "test_ach"
        assert unlocked.progress == progress


class TestAchievementManager:
    """Test the AchievementManager class."""

    def test_initialization(self):
        """Test creating an achievement manager."""
        manager = AchievementManager()

        assert len(manager.achievements) == 0
        assert len(manager.unlocked) == 0
        assert len(manager.progress) == 0

    def test_register_achievement(self):
        """Test registering an achievement."""
        manager = AchievementManager()
        ach = Achievement(id="test", name="Test", description="Test", category=AchievementCategory.GAMEPLAY)

        manager.register_achievement(ach)

        assert "test" in manager.achievements
        assert manager.achievements["test"] == ach

    def test_register_duplicate_raises_error(self):
        """Test that registering a duplicate achievement raises an error."""
        manager = AchievementManager()
        ach = Achievement(id="test", name="Test", description="Test", category=AchievementCategory.GAMEPLAY)

        manager.register_achievement(ach)

        with pytest.raises(ValueError, match="already registered"):
            manager.register_achievement(ach)

    def test_register_multiple_achievements(self):
        """Test registering multiple achievements."""
        manager = AchievementManager()
        achievements = [
            Achievement(id="test1", name="Test1", description="Test1", category=AchievementCategory.GAMEPLAY),
            Achievement(id="test2", name="Test2", description="Test2", category=AchievementCategory.MASTERY),
        ]

        manager.register_achievements(achievements)

        assert len(manager.achievements) == 2
        assert "test1" in manager.achievements
        assert "test2" in manager.achievements

    def test_unlock_achievement(self):
        """Test unlocking an achievement."""
        manager = AchievementManager()
        ach = Achievement(id="test", name="Test", description="Test", category=AchievementCategory.GAMEPLAY)
        manager.register_achievement(ach)

        result = manager.unlock_achievement("test")

        assert result is True
        assert manager.is_unlocked("test")
        assert "test" in manager.unlocked

    def test_unlock_already_unlocked(self):
        """Test unlocking an already unlocked achievement."""
        manager = AchievementManager()
        ach = Achievement(id="test", name="Test", description="Test", category=AchievementCategory.GAMEPLAY)
        manager.register_achievement(ach)

        manager.unlock_achievement("test")
        result = manager.unlock_achievement("test")

        assert result is False

    def test_unlock_unregistered_raises_error(self):
        """Test that unlocking an unregistered achievement raises an error."""
        manager = AchievementManager()

        with pytest.raises(ValueError, match="not registered"):
            manager.unlock_achievement("nonexistent")

    def test_check_achievements(self):
        """Test checking achievements with conditions."""
        manager = AchievementManager()

        ach1 = Achievement(
            id="win_1", name="First Win", description="Win once", category=AchievementCategory.GAMEPLAY, condition=lambda stats: stats.get("wins", 0) >= 1
        )

        ach2 = Achievement(
            id="win_10", name="Ten Wins", description="Win 10 times", category=AchievementCategory.MASTERY, condition=lambda stats: stats.get("wins", 0) >= 10
        )

        manager.register_achievements([ach1, ach2])

        # Check with 1 win
        stats = {"wins": 1}
        newly_unlocked = manager.check_achievements(stats)

        assert "win_1" in newly_unlocked
        assert "win_10" not in newly_unlocked
        assert manager.is_unlocked("win_1")
        assert not manager.is_unlocked("win_10")

        # Check with 10 wins
        stats = {"wins": 10}
        newly_unlocked = manager.check_achievements(stats)

        assert "win_1" not in newly_unlocked  # Already unlocked
        assert "win_10" in newly_unlocked
        assert manager.is_unlocked("win_10")

    def test_update_progress(self):
        """Test updating achievement progress."""
        manager = AchievementManager()
        ach = Achievement(id="test", name="Test", description="Test", category=AchievementCategory.GAMEPLAY)
        manager.register_achievement(ach)

        progress = {"current": 5, "target": 10}
        manager.update_progress("test", progress)

        assert manager.get_progress("test") == progress

    def test_get_progress_nonexistent(self):
        """Test getting progress for a nonexistent achievement."""
        manager = AchievementManager()

        assert manager.get_progress("nonexistent") is None

    def test_get_counts(self):
        """Test getting achievement counts."""
        manager = AchievementManager()
        ach1 = Achievement(id="test1", name="Test1", description="Test1", category=AchievementCategory.GAMEPLAY)
        ach2 = Achievement(id="test2", name="Test2", description="Test2", category=AchievementCategory.MASTERY)

        manager.register_achievements([ach1, ach2])
        manager.unlock_achievement("test1")

        assert manager.get_total_count() == 2
        assert manager.get_unlocked_count() == 1
        assert manager.get_completion_percentage() == 50.0

    def test_get_total_points(self):
        """Test calculating total points."""
        manager = AchievementManager()
        ach1 = Achievement(id="test1", name="Test1", description="Test1", category=AchievementCategory.GAMEPLAY, points=10)
        ach2 = Achievement(id="test2", name="Test2", description="Test2", category=AchievementCategory.MASTERY, points=20)

        manager.register_achievements([ach1, ach2])
        manager.unlock_achievement("test1")

        assert manager.get_total_points() == 10

        manager.unlock_achievement("test2")
        assert manager.get_total_points() == 30

    def test_get_by_category(self):
        """Test filtering achievements by category."""
        manager = AchievementManager()
        ach1 = Achievement(id="test1", name="Test1", description="Test1", category=AchievementCategory.GAMEPLAY)
        ach2 = Achievement(id="test2", name="Test2", description="Test2", category=AchievementCategory.MASTERY)
        ach3 = Achievement(id="test3", name="Test3", description="Test3", category=AchievementCategory.GAMEPLAY)

        manager.register_achievements([ach1, ach2, ach3])

        gameplay = manager.get_achievements_by_category(AchievementCategory.GAMEPLAY)
        mastery = manager.get_achievements_by_category(AchievementCategory.MASTERY)

        assert len(gameplay) == 2
        assert len(mastery) == 1

    def test_get_by_game(self):
        """Test filtering achievements by game."""
        manager = AchievementManager()
        ach1 = Achievement(id="test1", name="Test1", description="Test1", category=AchievementCategory.GAMEPLAY, game="uno")
        ach2 = Achievement(id="test2", name="Test2", description="Test2", category=AchievementCategory.MASTERY, game="poker")
        ach3 = Achievement(id="test3", name="Test3", description="Test3", category=AchievementCategory.GAMEPLAY, game=None)

        manager.register_achievements([ach1, ach2, ach3])

        uno_achs = manager.get_achievements_by_game("uno")
        cross_game = manager.get_achievements_by_game(None)

        assert len(uno_achs) == 1
        assert len(cross_game) == 1

    def test_save_and_load(self):
        """Test saving and loading achievement data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = pathlib.Path(tmpdir) / "achievements.json"

            manager = AchievementManager()
            ach1 = Achievement(id="test1", name="Test1", description="Test1", category=AchievementCategory.GAMEPLAY, points=10)
            ach2 = Achievement(id="test2", name="Test2", description="Test2", category=AchievementCategory.MASTERY, points=20)

            manager.register_achievements([ach1, ach2])
            manager.unlock_achievement("test1")
            manager.update_progress("test2", {"current": 5, "target": 10})

            manager.save(filepath)

            # Create new manager and load
            new_manager = AchievementManager()
            new_manager.register_achievements([ach1, ach2])
            new_manager.load(filepath)

            assert new_manager.is_unlocked("test1")
            assert not new_manager.is_unlocked("test2")
            assert new_manager.get_progress("test2") == {"current": 5, "target": 10}

    def test_summary(self):
        """Test generating a summary."""
        manager = AchievementManager()
        ach1 = Achievement(id="test1", name="Test1", description="Test1", category=AchievementCategory.GAMEPLAY, points=10)
        manager.register_achievement(ach1)
        manager.unlock_achievement("test1")

        summary = manager.summary()

        assert "ACHIEVEMENT PROGRESS" in summary
        assert "1/1" in summary
        assert "10" in summary  # Total points


class TestCommonAchievements:
    """Test the common achievements."""

    def test_create_common_achievements(self):
        """Test creating common achievements."""
        achievements = create_common_achievements()

        assert len(achievements) > 0
        assert all(isinstance(ach, Achievement) for ach in achievements)
        assert all(ach.game is None for ach in achievements)  # All should be cross-game

    def test_common_achievements_have_conditions(self):
        """Test that common achievements have conditions."""
        achievements = create_common_achievements()

        for ach in achievements:
            assert ach.condition is not None

    def test_common_achievements_work(self):
        """Test that common achievement conditions work."""
        manager = AchievementManager()
        achievements = create_common_achievements()
        manager.register_achievements(achievements)

        # Simulate first win
        stats = {"wins": 1, "games_played": 1, "win_streak": 1}
        unlocked = manager.check_achievements(stats)

        assert "first_win" in unlocked
        assert "games_played_10" not in unlocked
