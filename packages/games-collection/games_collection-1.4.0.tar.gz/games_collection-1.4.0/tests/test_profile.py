"""Tests for the player profile system."""

from __future__ import annotations

import pathlib
import tempfile
from datetime import date, datetime

import pytest

from common.achievements import Achievement, AchievementCategory
from common.profile import GameProfile, PlayerProfile, get_default_profile_dir, load_or_create_profile


class TestGameProfile:
    """Test the GameProfile dataclass."""

    def test_initialization(self):
        """Test creating a game profile."""
        profile = GameProfile(game_id="test_game")

        assert profile.game_id == "test_game"
        assert profile.games_played == 0
        assert profile.wins == 0
        assert profile.losses == 0
        assert profile.draws == 0
        assert profile.win_streak == 0
        assert profile.best_win_streak == 0
        assert profile.total_playtime == 0.0
        assert profile.last_played is None

    def test_record_win(self):
        """Test recording a win."""
        profile = GameProfile(game_id="test_game")
        profile.record_game("win", playtime=60.0)

        assert profile.games_played == 1
        assert profile.wins == 1
        assert profile.losses == 0
        assert profile.win_streak == 1
        assert profile.best_win_streak == 1
        assert profile.total_playtime == 60.0
        assert profile.last_played is not None

    def test_record_loss(self):
        """Test recording a loss."""
        profile = GameProfile(game_id="test_game")
        profile.record_game("win")
        profile.record_game("loss")

        assert profile.games_played == 2
        assert profile.wins == 1
        assert profile.losses == 1
        assert profile.win_streak == 0  # Reset

    def test_record_draw(self):
        """Test recording a draw."""
        profile = GameProfile(game_id="test_game")
        profile.record_game("win")
        profile.record_game("draw")

        assert profile.games_played == 2
        assert profile.wins == 1
        assert profile.draws == 1
        assert profile.win_streak == 1  # Continues

    def test_win_streak_tracking(self):
        """Test win streak tracking."""
        profile = GameProfile(game_id="test_game")

        profile.record_game("win")
        profile.record_game("win")
        profile.record_game("win")

        assert profile.win_streak == 3
        assert profile.best_win_streak == 3

        profile.record_game("loss")
        assert profile.win_streak == 0
        assert profile.best_win_streak == 3  # Preserved

    def test_win_rate(self):
        """Test win rate calculation."""
        profile = GameProfile(game_id="test_game")

        assert profile.win_rate() == 0.0

        profile.record_game("win")
        profile.record_game("win")
        profile.record_game("loss")

        assert profile.win_rate() == pytest.approx(66.67, rel=0.1)

    def test_average_playtime(self):
        """Test average playtime calculation."""
        profile = GameProfile(game_id="test_game")

        assert profile.average_playtime() == 0.0

        profile.record_game("win", playtime=60.0)
        profile.record_game("win", playtime=120.0)

        assert profile.average_playtime() == 90.0

    def test_to_dict_and_from_dict(self):
        """Test serialization."""
        profile = GameProfile(game_id="test_game")
        profile.record_game("win", playtime=60.0)
        profile.custom_stats = {"special": "data"}

        data = profile.to_dict()
        restored = GameProfile.from_dict(data)

        assert restored.game_id == profile.game_id
        assert restored.games_played == profile.games_played
        assert restored.wins == profile.wins
        assert restored.total_playtime == profile.total_playtime
        assert restored.custom_stats == profile.custom_stats


class TestPlayerProfile:
    """Test the PlayerProfile dataclass."""

    def test_initialization(self):
        """Test creating a player profile."""
        profile = PlayerProfile(player_id="test_player", display_name="Test Player")

        assert profile.player_id == "test_player"
        assert profile.display_name == "Test Player"
        assert profile.level == 1
        assert profile.experience == 0
        assert len(profile.game_profiles) == 0

        # Check timestamps are valid ISO format
        datetime.fromisoformat(profile.created_at)
        datetime.fromisoformat(profile.last_active)

    def test_get_game_profile(self):
        """Test getting or creating a game profile."""
        profile = PlayerProfile(player_id="test_player", display_name="Test Player")

        game_profile = profile.get_game_profile("uno")

        assert game_profile.game_id == "uno"
        assert "uno" in profile.game_profiles

        # Getting again should return same instance
        game_profile2 = profile.get_game_profile("uno")
        assert game_profile is game_profile2

    def test_record_game(self):
        """Test recording a game."""
        profile = PlayerProfile(player_id="test_player", display_name="Test Player")

        profile.record_game("uno", "win", playtime=120.0, experience_gained=50)

        game_profile = profile.get_game_profile("uno")
        assert game_profile.games_played == 1
        assert game_profile.wins == 1
        assert profile.experience == 50

    def test_add_experience_and_level_up(self):
        """Test adding experience and leveling up."""
        profile = PlayerProfile(player_id="test_player", display_name="Test Player")

        # Level 1 needs 100 XP to reach level 2
        leveled_up = profile.add_experience(50)
        assert not leveled_up
        assert profile.level == 1

        leveled_up = profile.add_experience(50)
        assert leveled_up
        assert profile.level == 2

    def test_calculate_level(self):
        """Test level calculation."""
        assert PlayerProfile.calculate_level(0) == 1
        assert PlayerProfile.calculate_level(100) == 2
        assert PlayerProfile.calculate_level(400) == 3
        assert PlayerProfile.calculate_level(900) == 4

    def test_experience_to_next_level(self):
        """Test calculating XP to next level."""
        profile = PlayerProfile(player_id="test_player", display_name="Test Player")

        assert profile.experience_to_next_level() == 100

        profile.add_experience(50)
        assert profile.experience_to_next_level() == 50

        profile.add_experience(50)
        assert profile.level == 2
        assert profile.experience_to_next_level() == 300  # Need 400 total for level 3

    def test_total_games_played(self):
        """Test calculating total games played."""
        profile = PlayerProfile(player_id="test_player", display_name="Test Player")

        profile.record_game("uno", "win")
        profile.record_game("poker", "loss")
        profile.record_game("uno", "win")

        assert profile.total_games_played() == 3

    def test_total_wins(self):
        """Test calculating total wins."""
        profile = PlayerProfile(player_id="test_player", display_name="Test Player")

        profile.record_game("uno", "win")
        profile.record_game("poker", "loss")
        profile.record_game("uno", "win")

        assert profile.total_wins() == 2

    def test_total_playtime(self):
        """Test calculating total playtime."""
        profile = PlayerProfile(player_id="test_player", display_name="Test Player")

        profile.record_game("uno", "win", playtime=60.0)
        profile.record_game("poker", "loss", playtime=120.0)

        assert profile.total_playtime() == 180.0

    def test_overall_win_rate(self):
        """Test calculating overall win rate."""
        profile = PlayerProfile(player_id="test_player", display_name="Test Player")

        assert profile.overall_win_rate() == 0.0

        profile.record_game("uno", "win")
        profile.record_game("poker", "win")
        profile.record_game("uno", "loss")

        assert profile.overall_win_rate() == pytest.approx(66.67, rel=0.1)

    def test_favorite_game(self):
        """Test determining favorite game."""
        profile = PlayerProfile(player_id="test_player", display_name="Test Player")

        assert profile.favorite_game() is None

        profile.record_game("uno", "win")
        profile.record_game("uno", "win")
        profile.record_game("poker", "win")

        assert profile.favorite_game() == "uno"

    def test_save_and_load(self):
        """Test saving and loading profile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = pathlib.Path(tmpdir) / "profile.json"

            # Create and save profile
            profile = PlayerProfile(player_id="test_player", display_name="Test Player")
            profile.record_game("uno", "win", playtime=60.0, experience_gained=50)
            profile.record_game("poker", "loss", playtime=120.0)
            profile.preferences = {"theme": "dark"}

            profile.save(filepath)

            # Load profile
            loaded = PlayerProfile.load(filepath, "test_player", "Test Player")

            assert loaded.player_id == profile.player_id
            assert loaded.display_name == profile.display_name
            assert loaded.level == profile.level
            assert loaded.experience == profile.experience
            assert loaded.preferences == profile.preferences
            assert len(loaded.game_profiles) == 2
            assert "uno" in loaded.game_profiles
            assert "poker" in loaded.game_profiles

    def test_load_nonexistent_creates_new(self):
        """Test loading a nonexistent profile creates a new one."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = pathlib.Path(tmpdir) / "nonexistent.json"

            profile = PlayerProfile.load(filepath, "new_player", "New Player")

            assert profile.player_id == "new_player"
            assert profile.display_name == "New Player"
            assert profile.level == 1
            assert profile.experience == 0

    def test_achievements_integration(self):
        """Test achievement integration with profile."""
        profile = PlayerProfile(player_id="test_player", display_name="Test Player")

        assert "first_win" in profile.achievement_manager.achievements

        unlocked = profile.record_game("uno", "win")

        assert "first_win" in unlocked
        assert profile.achievement_manager.is_unlocked("first_win")

    def test_save_and_load_with_achievements(self):
        """Test saving and loading profile with achievements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = pathlib.Path(tmpdir) / "profile.json"

            # Create profile with achievement
            profile = PlayerProfile(player_id="test_player", display_name="Test Player")
            ach = Achievement(id="test_ach", name="Test", description="Test", category=AchievementCategory.GAMEPLAY, points=10)
            profile.achievement_manager.register_achievement(ach)
            profile.achievement_manager.unlock_achievement("test_ach")

            profile.save(filepath)

            # Load profile
            loaded = PlayerProfile.load(filepath, "test_player", "Test Player")

            # Re-register achievement (not persisted, only unlocked status is)
            loaded.achievement_manager.register_achievement(ach)

            assert loaded.achievement_manager.is_unlocked("test_ach")

    def test_summary(self):
        """Test generating a profile summary."""
        profile = PlayerProfile(player_id="test_player", display_name="Test Player")
        profile.record_game("uno", "win", playtime=60.0, experience_gained=50)
        profile.record_game("poker", "loss", playtime=120.0)

        summary = profile.summary()

        assert "Test Player" in summary
        assert "Level: 1" in summary
        assert "Total Games: 2" in summary
        assert "uno" in summary.lower()

    def test_daily_challenge_progress(self):
        """Daily challenge tracking should update streaks and avoid duplicates."""

        profile = PlayerProfile(player_id="test_player", display_name="Test Player")

        unlocked_first = profile.record_daily_challenge("challenge1", date(2024, 1, 1))
        assert profile.daily_challenge_progress.total_completed == 1
        assert profile.daily_challenge_progress.current_streak == 1
        assert profile.daily_challenge_progress.best_streak == 1
        assert profile.daily_challenge_progress.is_completed(date(2024, 1, 1))
        assert "daily_challenge_first_completion" in unlocked_first

        unlocked_second = profile.record_daily_challenge("challenge2", date(2024, 1, 2))
        assert profile.daily_challenge_progress.total_completed == 2
        assert profile.daily_challenge_progress.current_streak == 2
        assert profile.daily_challenge_progress.best_streak == 2
        assert "daily_challenge_first_completion" not in unlocked_second

        repeat = profile.record_daily_challenge("challenge_duplicate", date(2024, 1, 2))
        assert repeat == []
        assert profile.daily_challenge_progress.total_completed == 2

        profile.record_daily_challenge("challenge3", date(2024, 1, 4))
        assert profile.daily_challenge_progress.current_streak == 1
        assert profile.daily_challenge_progress.best_streak == 2


class TestHelperFunctions:
    """Test helper functions."""

    def test_get_default_profile_dir(self):
        """Test getting the default profile directory."""
        profile_dir = get_default_profile_dir()

        assert isinstance(profile_dir, pathlib.Path)
        assert "profiles" in str(profile_dir)

    def test_load_or_create_profile(self):
        """Test loading or creating a profile."""
        profile = load_or_create_profile("test_player", "Test Player")

        assert isinstance(profile, PlayerProfile)
        assert profile.player_id == "test_player"
        assert profile.display_name == "Test Player"
