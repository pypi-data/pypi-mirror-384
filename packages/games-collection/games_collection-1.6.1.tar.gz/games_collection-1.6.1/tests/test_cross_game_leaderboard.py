"""Tests for the cross-game leaderboard service."""

from __future__ import annotations

from pathlib import Path

from common.leaderboard_service import CrossGameLeaderboardService
from common.profile_service import ProfileService


def test_cross_game_leaderboard_orders_by_wins(tmp_path: Path) -> None:
    """Leaderboard entries should be ordered by wins when requested."""

    service = ProfileService(profile_dir=tmp_path)
    session = service.start_session("tic_tac_toe")
    session.complete(result="win", experience=200, metadata={"perfect_game": True})

    service.select_profile("rival", "Rival Player")
    for _ in range(3):
        service.record_game("tic_tac_toe", result="win", playtime=45.0)
    service.save_active_profile()

    service.select_profile("default")
    leaderboard = service.leaderboard(sort_by="wins", limit=5)
    assert leaderboard[0].player_id == "rival"
    assert leaderboard[0].total_wins == 3
    assert any(entry.player_id == "default" for entry in leaderboard)


def test_leaderboard_includes_active_unsaved_progress(tmp_path: Path) -> None:
    """Active profile progress should appear even before persistence."""

    service = ProfileService(profile_dir=tmp_path)
    service.record_game("hangman", result="win", playtime=30.0)

    leaderboard = service.leaderboard(limit=3)
    assert leaderboard, "Expected at least one leaderboard entry"
    assert leaderboard[0].total_wins >= 1

    aggregator = CrossGameLeaderboardService(service.profile_dir, active_profile=service.active_profile)
    analytics = aggregator.analytics_snapshot()
    assert "hangman" in analytics
    hangman_stats = analytics["hangman"]
    assert hangman_stats.players[service.active_profile.player_id].wins == 1
