"""Unit tests for the recommendation service."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict

import pytest

from common.analytics.game_stats import GameStatistics, PlayerStats
from common.profile import GameProfile, PlayerProfile
from common.recommendation_service import GameDescriptor, RecommendationService


def build_stats(game_name: str, total_games: int, challenge_completions: int) -> GameStatistics:
    """Create analytics data for a game."""

    stats = GameStatistics(game_name=game_name)
    stats.players["community"] = PlayerStats(player_id="community", total_games=total_games, wins=total_games // 2)
    stats.game_history = [{"metadata": {"challenge_completed": index < challenge_completions}} for index in range(max(total_games, 1))]
    return stats


class TestRecommendationService:
    """Test suite for the recommendation engine."""

    @pytest.fixture()
    def descriptors(self) -> Dict[str, GameDescriptor]:
        """Return a catalogue used in tests."""

        return {
            "hearts": GameDescriptor(
                game_id="hearts",
                name="Hearts",
                mechanics=("trick-taking", "hand-management"),
                average_duration=1800,
            ),
            "spades": GameDescriptor(
                game_id="spades",
                name="Spades",
                mechanics=("trick-taking", "bidding"),
                average_duration=2100,
            ),
            "farkle": GameDescriptor(
                game_id="farkle",
                name="Farkle",
                mechanics=("push-your-luck", "dice"),
                average_duration=900,
            ),
        }

    def test_recommendations_prioritise_similar_mechanics(self, descriptors: Dict[str, GameDescriptor]) -> None:
        """Recommendations highlight trick-taking games for a trick-taking fan."""

        profile = PlayerProfile(player_id="p1", display_name="Player One")
        profile.game_profiles["hearts"] = GameProfile(game_id="hearts", games_played=25, wins=15, total_playtime=25 * 1800)
        profile.game_profiles["farkle"] = GameProfile(game_id="farkle", games_played=4, wins=2, total_playtime=4 * 900)

        analytics = {
            "spades": build_stats("Spades", total_games=80, challenge_completions=40),
            "farkle": build_stats("Farkle", total_games=30, challenge_completions=5),
        }

        service = RecommendationService(descriptors)
        results = service.recommend(profile, analytics, limit=2)

        assert results, "Expected at least one recommendation"
        assert results[0].game_id == "spades"
        assert any("trick" in reason for reason in results[0].reasons)
        assert "Spades" in results[0].explanation

    def test_cache_and_feedback_adjust_scores(self, descriptors: Dict[str, GameDescriptor]) -> None:
        """Feedback influences future recommendations once the cache expires."""

        profile = PlayerProfile(player_id="p2", display_name="Player Two")
        profile.game_profiles["hearts"] = GameProfile(game_id="hearts", games_played=12, wins=8, total_playtime=12 * 1700)

        analytics = {
            "spades": build_stats("Spades", total_games=60, challenge_completions=20),
            "farkle": build_stats("Farkle", total_games=50, challenge_completions=10),
        }

        service = RecommendationService(descriptors, cache_ttl=timedelta(hours=4))

        initial_results = service.recommend(profile, analytics, limit=3)
        analytics["farkle"].players["community"].total_games = 5
        cached_results = service.recommend(profile, analytics, limit=3)
        assert cached_results == initial_results

        service.record_feedback(profile, "farkle", accepted=False)
        profile.recommendation_cache.cached_at = (datetime.now() - timedelta(hours=6)).isoformat()

        refreshed_results = service.recommend(profile, analytics, limit=3)

        initial_scores = {result.game_id: result.score for result in initial_results}
        refreshed_scores = {result.game_id: result.score for result in refreshed_results}
        assert refreshed_scores["farkle"] < initial_scores["farkle"]
