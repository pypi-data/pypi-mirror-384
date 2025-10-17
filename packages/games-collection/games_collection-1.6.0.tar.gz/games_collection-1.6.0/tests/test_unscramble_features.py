"""Tests for new Unscramble features: difficulty, themes, stats, and timed mode."""

import tempfile
from pathlib import Path

import pytest

from paper_games.unscramble import GameStats, UnscrambleGame, list_themes, load_themed_words, load_unscramble_words, load_words_by_difficulty


def test_load_unscramble_words():
    """Test loading default unscramble words."""
    words = load_unscramble_words()
    assert len(words) > 0
    assert all(isinstance(w, str) for w in words)
    assert all(w.islower() for w in words)


def test_load_words_by_difficulty_easy():
    """Test loading easy difficulty words."""
    words = load_words_by_difficulty("easy")
    assert len(words) > 0
    # Easy words should be 6+ letters
    assert all(len(w) >= 6 for w in words)


def test_load_words_by_difficulty_medium():
    """Test loading medium difficulty words."""
    words = load_words_by_difficulty("medium")
    assert len(words) > 0
    # Medium words should be 4-5 letters
    assert all(4 <= len(w) <= 5 for w in words)


def test_load_words_by_difficulty_hard():
    """Test loading hard difficulty words."""
    words = load_words_by_difficulty("hard")
    assert len(words) > 0
    # Hard words should be 3 letters
    assert all(len(w) == 3 for w in words)


def test_load_words_by_difficulty_all():
    """Test loading all difficulty words."""
    words = load_words_by_difficulty("all")
    assert len(words) > 0


def test_load_words_by_difficulty_invalid():
    """Test that invalid difficulty raises an error."""
    with pytest.raises(ValueError, match="Invalid difficulty"):
        load_words_by_difficulty("super_hard")


def test_load_themed_words_all():
    """Test loading all themed word lists."""
    themes = load_themed_words()
    assert isinstance(themes, dict)
    assert len(themes) > 0
    # Check we have expected themes
    assert "technical" in themes
    assert "literature" in themes
    assert all(isinstance(words, list) for words in themes.values())


def test_load_themed_words_specific():
    """Test loading specific theme."""
    technical_words = load_themed_words("technical")
    assert isinstance(technical_words, list)
    assert len(technical_words) > 0
    assert all(isinstance(w, str) for w in technical_words)


def test_load_themed_words_invalid():
    """Test that invalid theme raises an error."""
    with pytest.raises(ValueError, match="not found"):
        load_themed_words("nonexistent_theme")


def test_list_themes():
    """Test listing available themes."""
    themes_str = list_themes()
    assert isinstance(themes_str, str)
    assert "Available themes:" in themes_str
    assert "technical" in themes_str.lower()


def test_unscramble_game_basic():
    """Test basic game functionality."""
    game = UnscrambleGame(words=["hello", "world"])
    scrambled = game.new_round()
    assert len(scrambled) > 0
    assert game.secret_word in ["hello", "world"]


def test_unscramble_game_with_difficulty():
    """Test game with difficulty setting."""
    easy_words = load_words_by_difficulty("easy")
    game = UnscrambleGame(words=easy_words, difficulty="easy")
    game.new_round()
    assert game.secret_word in easy_words
    assert len(game.secret_word) >= 6


def test_unscramble_game_with_theme():
    """Test game with theme setting."""
    technical_words = load_themed_words("technical")
    game = UnscrambleGame(words=technical_words, theme="technical")
    game.new_round()
    assert game.secret_word in technical_words


def test_unscramble_game_scrambling():
    """Test that words are properly scrambled."""
    game = UnscrambleGame(words=["testing"])
    scrambled = game.new_round()
    # Scrambled should have same letters
    assert sorted(scrambled) == sorted("testing")
    # Should be different from original (with high probability)
    assert scrambled != "testing"


def test_unscramble_game_guess_correct():
    """Test correct guess."""
    game = UnscrambleGame(words=["hello"])
    game.new_round()
    assert game.guess("hello") is True
    assert game.guess("HELLO") is True  # Case insensitive
    assert game.guess(" hello ") is True  # Strips whitespace


def test_unscramble_game_guess_incorrect():
    """Test incorrect guess."""
    game = UnscrambleGame(words=["hello"])
    game.new_round()
    assert game.guess("world") is False


def test_game_stats_initialization():
    """Test GameStats initialization."""
    stats = GameStats()
    assert stats.total_words == 0
    assert stats.words_solved == 0
    assert stats.current_streak == 0
    assert stats.longest_streak == 0
    assert stats.games_played == 0


def test_game_stats_record_word_solved():
    """Test recording a solved word."""
    stats = GameStats()
    stats.record_word(solved=True, difficulty="easy")
    assert stats.total_words == 1
    assert stats.words_solved == 1
    assert stats.current_streak == 1
    assert stats.longest_streak == 1


def test_game_stats_record_word_failed():
    """Test recording a failed word."""
    stats = GameStats()
    stats.record_word(solved=False, difficulty="easy")
    assert stats.total_words == 1
    assert stats.words_solved == 0
    assert stats.current_streak == 0
    assert stats.longest_streak == 0


def test_game_stats_streak_tracking():
    """Test streak tracking."""
    stats = GameStats()
    # Build a streak
    stats.record_word(solved=True)
    stats.record_word(solved=True)
    stats.record_word(solved=True)
    assert stats.current_streak == 3
    assert stats.longest_streak == 3

    # Break the streak
    stats.record_word(solved=False)
    assert stats.current_streak == 0
    assert stats.longest_streak == 3  # Longest should remain

    # Start new streak
    stats.record_word(solved=True)
    stats.record_word(solved=True)
    assert stats.current_streak == 2
    assert stats.longest_streak == 3  # Still the longest


def test_game_stats_by_difficulty():
    """Test tracking stats by difficulty."""
    stats = GameStats()
    stats.record_word(solved=True, difficulty="easy")
    stats.record_word(solved=True, difficulty="easy")
    stats.record_word(solved=False, difficulty="easy")
    stats.record_word(solved=True, difficulty="hard")

    assert "easy" in stats.stats_by_difficulty
    assert stats.stats_by_difficulty["easy"]["total"] == 3
    assert stats.stats_by_difficulty["easy"]["solved"] == 2
    assert "hard" in stats.stats_by_difficulty
    assert stats.stats_by_difficulty["hard"]["total"] == 1
    assert stats.stats_by_difficulty["hard"]["solved"] == 1


def test_game_stats_by_theme():
    """Test tracking stats by theme."""
    stats = GameStats()
    stats.record_word(solved=True, theme="technical")
    stats.record_word(solved=False, theme="technical")
    stats.record_word(solved=True, theme="literature")

    assert "technical" in stats.stats_by_theme
    assert stats.stats_by_theme["technical"]["total"] == 2
    assert stats.stats_by_theme["technical"]["solved"] == 1
    assert "literature" in stats.stats_by_theme
    assert stats.stats_by_theme["literature"]["total"] == 1
    assert stats.stats_by_theme["literature"]["solved"] == 1


def test_game_stats_time_tracking():
    """Test time tracking."""
    stats = GameStats()
    stats.record_word(solved=True, time_taken=5.0)
    stats.record_word(solved=True, time_taken=3.0)
    stats.record_word(solved=True, time_taken=7.0)

    assert stats.total_time_spent == 15.0
    assert stats.fastest_solve == 3.0
    assert stats.average_solve_time() == 5.0


def test_game_stats_solve_rate():
    """Test solve rate calculation."""
    stats = GameStats()
    stats.record_word(solved=True)
    stats.record_word(solved=True)
    stats.record_word(solved=False)
    stats.record_word(solved=True)

    assert stats.solve_rate() == 75.0  # 3 out of 4


def test_game_stats_achievements():
    """Test achievement unlocking."""
    stats = GameStats()

    # First solve achievement
    stats.record_word(solved=True)
    achievements = stats.check_achievements()
    assert "First Solve" in achievements
    assert "First Solve" in stats.achievements

    # Same achievement shouldn't unlock again
    achievements = stats.check_achievements()
    assert "First Solve" not in achievements


def test_game_stats_streak_achievements():
    """Test streak-based achievements."""
    stats = GameStats()

    # Build streak to 3
    for _ in range(3):
        stats.record_word(solved=True)

    achievements = stats.check_achievements()
    assert "Streak Starter" in achievements


def test_game_stats_save_and_load():
    """Test saving and loading statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test_stats.json"

        # Create and save stats
        stats = GameStats()
        stats.record_word(solved=True, difficulty="easy", time_taken=5.0)
        stats.record_word(solved=False, difficulty="hard")
        stats.current_streak = 1
        stats.longest_streak = 3
        stats.games_played = 1
        stats.achievements = ["First Solve"]
        stats.save(filepath)

        # Load stats
        loaded_stats = GameStats.load(filepath)
        assert loaded_stats.total_words == 2
        assert loaded_stats.words_solved == 1
        assert loaded_stats.current_streak == 1
        assert loaded_stats.longest_streak == 3
        assert loaded_stats.games_played == 1
        assert loaded_stats.achievements == ["First Solve"]
        assert loaded_stats.fastest_solve == 5.0


def test_game_stats_load_nonexistent():
    """Test loading from nonexistent file returns empty stats."""
    stats = GameStats.load(Path("/nonexistent/path/stats.json"))
    assert stats.total_words == 0
    assert stats.games_played == 0


def test_game_stats_summary():
    """Test summary generation."""
    stats = GameStats()
    stats.record_word(solved=True, difficulty="easy", time_taken=5.0)
    stats.record_word(solved=True, difficulty="easy", time_taken=3.0)
    stats.record_word(solved=False, difficulty="hard")
    stats.games_played = 1

    summary = stats.summary()
    assert "UNSCRAMBLE STATISTICS" in summary
    assert "Total Words: 3" in summary
    assert "Words Solved: 2" in summary
    assert "Solve Rate: 66.7%" in summary
    assert "easy" in summary.lower()
