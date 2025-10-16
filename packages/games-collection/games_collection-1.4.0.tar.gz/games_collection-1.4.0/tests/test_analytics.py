"""Tests for the analytics and metrics system."""

from __future__ import annotations

import pathlib
import tempfile

import pytest

from common.analytics import Dashboard, EloRating, GameStatistics, GlickoRating, Heatmap, PerformanceMetrics, PlayerStats, ReplayAnalyzer
from common.analytics.rating_systems import calculate_ai_difficulty_rating


class TestPlayerStats:
    """Tests for PlayerStats class."""

    def test_initialization(self):
        """Test PlayerStats initialization."""
        stats = PlayerStats(player_id="player1")
        assert stats.player_id == "player1"
        assert stats.total_games == 0
        assert stats.wins == 0
        assert stats.losses == 0

    def test_record_win(self):
        """Test recording a win."""
        stats = PlayerStats(player_id="player1")
        stats.record_game("win", 120.0)

        assert stats.total_games == 1
        assert stats.wins == 1
        assert stats.current_win_streak == 1
        assert stats.longest_win_streak == 1

    def test_record_loss(self):
        """Test recording a loss."""
        stats = PlayerStats(player_id="player1")
        stats.record_game("loss", 90.0)

        assert stats.total_games == 1
        assert stats.losses == 1
        assert stats.current_loss_streak == 1

    def test_win_streak(self):
        """Test win streak tracking."""
        stats = PlayerStats(player_id="player1")
        stats.record_game("win", 100.0)
        stats.record_game("win", 100.0)
        stats.record_game("win", 100.0)

        assert stats.current_win_streak == 3
        assert stats.longest_win_streak == 3

    def test_streak_reset(self):
        """Test that streak resets on different result."""
        stats = PlayerStats(player_id="player1")
        stats.record_game("win", 100.0)
        stats.record_game("win", 100.0)
        stats.record_game("loss", 100.0)

        assert stats.current_win_streak == 0
        assert stats.longest_win_streak == 2
        assert stats.current_loss_streak == 1

    def test_win_rate(self):
        """Test win rate calculation."""
        stats = PlayerStats(player_id="player1")
        stats.record_game("win", 100.0)
        stats.record_game("loss", 100.0)
        stats.record_game("win", 100.0)

        assert stats.win_rate() == pytest.approx(66.67, rel=0.1)

    def test_serialization(self):
        """Test to_dict and from_dict."""
        stats = PlayerStats(player_id="player1")
        stats.record_game("win", 100.0)

        data = stats.to_dict()
        restored = PlayerStats.from_dict(data)

        assert restored.player_id == stats.player_id
        assert restored.wins == stats.wins
        assert restored.total_games == stats.total_games


class TestGameStatistics:
    """Tests for GameStatistics class."""

    def test_initialization(self):
        """Test GameStatistics initialization."""
        stats = GameStatistics(game_name="TestGame")
        assert stats.game_name == "TestGame"
        assert len(stats.players) == 0

    def test_record_game(self):
        """Test recording a game."""
        stats = GameStatistics(game_name="TestGame")
        stats.record_game(
            winner="player1",
            players=["player1", "player2"],
            duration=120.0,
        )

        assert len(stats.players) == 2
        assert stats.players["player1"].wins == 1
        assert stats.players["player2"].losses == 1

    def test_record_draw(self):
        """Test recording a draw."""
        stats = GameStatistics(game_name="TestGame")
        stats.record_game(
            winner=None,
            players=["player1", "player2"],
            duration=120.0,
        )

        assert stats.players["player1"].draws == 1
        assert stats.players["player2"].draws == 1

    def test_leaderboard(self):
        """Test leaderboard generation."""
        stats = GameStatistics(game_name="TestGame")
        stats.record_game("player1", ["player1", "player2"], 100.0)
        stats.record_game("player1", ["player1", "player2"], 100.0)
        stats.record_game("player2", ["player1", "player2"], 100.0)

        leaderboard = stats.get_leaderboard("win_rate")
        assert leaderboard[0].player_id == "player1"

    def test_save_load(self):
        """Test save and load functionality."""
        stats = GameStatistics(game_name="TestGame")
        stats.record_game("player1", ["player1", "player2"], 100.0)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = pathlib.Path(tmpdir) / "stats.json"
            stats.save(filepath)

            loaded = GameStatistics.load(filepath)
            assert loaded.game_name == "TestGame"
            assert len(loaded.players) == 2


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics class."""

    def test_initialization(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics(game_name="TestGame")
        assert metrics.game_name == "TestGame"

    def test_record_decision(self):
        """Test recording a decision."""
        metrics = PerformanceMetrics(game_name="TestGame")
        metrics.record_decision("player1", 2.5, quality=0.8)

        player_metrics = metrics.players["player1"]
        assert player_metrics.total_decisions == 1
        assert player_metrics.decision_times[0] == 2.5

    def test_average_decision_time(self):
        """Test average decision time calculation."""
        metrics = PerformanceMetrics(game_name="TestGame")
        metrics.record_decision("player1", 2.0)
        metrics.record_decision("player1", 4.0)
        metrics.record_decision("player1", 3.0)

        avg_time = metrics.players["player1"].average_decision_time()
        assert avg_time == pytest.approx(3.0)

    def test_game_duration_tracking(self):
        """Test game duration tracking."""
        metrics = PerformanceMetrics(game_name="TestGame")
        metrics.record_game_duration(120.0)
        metrics.record_game_duration(180.0)

        assert metrics.average_game_duration() == pytest.approx(150.0)
        assert metrics.shortest_game() == pytest.approx(120.0)
        assert metrics.longest_game() == pytest.approx(180.0)


class TestEloRating:
    """Tests for EloRating system."""

    def test_initialization(self):
        """Test EloRating initialization."""
        elo = EloRating()
        assert elo.default_rating == 1500.0
        assert elo.k_factor == 32.0

    def test_get_rating(self):
        """Test getting player rating."""
        elo = EloRating()
        rating = elo.get_rating("player1")
        assert rating == 1500.0

    def test_expected_score(self):
        """Test expected score calculation."""
        elo = EloRating()
        expected = elo.expected_score(1500.0, 1500.0)
        assert expected == pytest.approx(0.5)

    def test_update_ratings_winner(self):
        """Test rating update for winner."""
        elo = EloRating()
        new_a, new_b = elo.update_ratings("player1", "player2", 1.0)

        assert new_a > 1500.0
        assert new_b < 1500.0

    def test_update_ratings_draw(self):
        """Test rating update for draw."""
        elo = EloRating()
        new_a, new_b = elo.update_ratings("player1", "player2", 0.5)

        # Equal ratings should stay equal after draw
        assert new_a == pytest.approx(1500.0)
        assert new_b == pytest.approx(1500.0)

    def test_leaderboard(self):
        """Test leaderboard generation."""
        elo = EloRating()
        elo.update_ratings("player1", "player2", 1.0)
        elo.update_ratings("player1", "player3", 1.0)

        leaderboard = elo.get_leaderboard()
        assert leaderboard[0][0] == "player1"

    def test_save_load(self):
        """Test save and load functionality."""
        elo = EloRating()
        elo.update_ratings("player1", "player2", 1.0)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = pathlib.Path(tmpdir) / "elo.json"
            elo.save(filepath)

            loaded = EloRating.load(filepath)
            assert loaded.get_rating("player1") == elo.get_rating("player1")


class TestGlickoRating:
    """Tests for Glicko-2 rating system."""

    def test_initialization(self):
        """Test GlickoRating initialization."""
        glicko = GlickoRating()
        assert glicko.default_rating == 1500.0

    def test_get_rating(self):
        """Test getting player rating."""
        glicko = GlickoRating()
        rating = glicko.get_rating("player1")

        assert rating["rating"] == 1500.0
        assert "rd" in rating
        assert "volatility" in rating

    def test_update_ratings(self):
        """Test rating update."""
        glicko = GlickoRating()
        new_a, new_b = glicko.update_ratings("player1", "player2", 1.0)

        assert new_a["rating"] > 1500.0
        assert new_b["rating"] < 1500.0


class TestReplayAnalyzer:
    """Tests for ReplayAnalyzer."""

    def test_initialization(self):
        """Test ReplayAnalyzer initialization."""
        analyzer = ReplayAnalyzer(game_name="TestGame")
        assert analyzer.game_name == "TestGame"
        assert len(analyzer.move_history) == 0

    def test_add_move(self):
        """Test adding moves."""
        analyzer = ReplayAnalyzer(game_name="TestGame")
        analyzer.add_move({"type": "move", "position": "A1"})

        assert len(analyzer.move_history) == 1

    def test_pattern_detection(self):
        """Test pattern detection."""
        analyzer = ReplayAnalyzer(game_name="TestGame")
        analyzer.add_move({"type": "move", "position": "A1"})
        analyzer.add_move({"type": "move", "position": "B2"})
        analyzer.add_move({"type": "move", "position": "A1"})

        def detector(moves):
            return [i for i, m in enumerate(moves) if m["position"] == "A1"]

        pattern = analyzer.detect_pattern(
            "a1_moves",
            "Moves to A1",
            detector,
        )

        assert pattern.occurrences == 2

    def test_heatmap_data(self):
        """Test heatmap data generation."""
        analyzer = ReplayAnalyzer(game_name="TestGame")
        analyzer.add_move({"position": "A1"})
        analyzer.add_move({"position": "A1"})
        analyzer.add_move({"position": "B2"})

        heatmap_data = analyzer.get_position_heatmap_data()
        assert heatmap_data["A1"] == 2
        assert heatmap_data["B2"] == 1


class TestHeatmap:
    """Tests for Heatmap visualization."""

    def test_initialization(self):
        """Test Heatmap initialization."""
        heatmap = Heatmap(width=3, height=3)
        assert heatmap.width == 3
        assert heatmap.height == 3

    def test_set_get_value(self):
        """Test setting and getting values."""
        heatmap = Heatmap(width=3, height=3)
        heatmap.set_value(1, 1, 0.5)

        assert heatmap.get_value(1, 1) == 0.5
        assert heatmap.get_value(0, 0) == 0.0

    def test_increment(self):
        """Test incrementing values."""
        heatmap = Heatmap(width=3, height=3)
        heatmap.increment(1, 1)
        heatmap.increment(1, 1)

        assert heatmap.get_value(1, 1) == 2.0

    def test_normalize(self):
        """Test normalization."""
        heatmap = Heatmap(width=3, height=3)
        heatmap.set_value(0, 0, 100.0)
        heatmap.set_value(1, 1, 50.0)

        heatmap.normalize()

        assert heatmap.get_value(0, 0) == 1.0
        assert heatmap.get_value(1, 1) == 0.5

    def test_hotspots(self):
        """Test hotspot detection."""
        heatmap = Heatmap(width=3, height=3)
        heatmap.set_value(0, 0, 0.9)
        heatmap.set_value(1, 1, 0.8)
        heatmap.set_value(2, 2, 0.5)

        hotspots = heatmap.get_hotspots(threshold=0.7)

        assert len(hotspots) == 2
        assert hotspots[0][2] == 0.9  # Highest value first


class TestDashboard:
    """Tests for Dashboard visualization."""

    def test_initialization(self):
        """Test Dashboard initialization."""
        dashboard = Dashboard(title="Test Dashboard")
        assert dashboard.title == "Test Dashboard"

    def test_add_section(self):
        """Test adding sections."""
        dashboard = Dashboard(title="Test")
        dashboard.add_section("Stats", ["Line 1", "Line 2"])

        assert len(dashboard.sections) == 1

    def test_add_stat(self):
        """Test adding statistics."""
        dashboard = Dashboard(title="Test")
        dashboard.add_stat("Performance", "Games", 100)
        dashboard.add_stat("Performance", "Win Rate", 0.75, ".2%")

        assert len(dashboard.sections) == 1
        assert len(dashboard.sections[0]["content"]) == 2

    def test_render(self):
        """Test rendering dashboard."""
        dashboard = Dashboard(title="Test Dashboard")
        dashboard.add_section("Stats", ["Stat 1", "Stat 2"])

        rendered = dashboard.render()
        assert "Test Dashboard" in rendered
        assert "Stats" in rendered


class TestAIDifficultyRating:
    """Tests for AI difficulty rating calculation."""

    def test_easy_difficulty(self):
        """Test easy difficulty rating."""
        rating = calculate_ai_difficulty_rating(
            win_rate=0.3,
            average_game_length=15.0,
            move_quality=0.4,
        )

        assert rating < 50.0

    def test_hard_difficulty(self):
        """Test hard difficulty rating."""
        rating = calculate_ai_difficulty_rating(
            win_rate=0.9,
            average_game_length=25.0,
            move_quality=0.95,
        )

        assert rating > 80.0

    def test_bounds(self):
        """Test that rating stays within bounds."""
        rating = calculate_ai_difficulty_rating(
            win_rate=1.5,  # Invalid, but should be clamped
            average_game_length=100.0,
            move_quality=1.2,  # Invalid, but should be clamped
        )

        assert 0 <= rating <= 100
