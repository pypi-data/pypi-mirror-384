from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import List

from common.profile import PlayerProfile
from common.profile_service import ProfileService


def _load_profile(path: Path, player_id: str) -> PlayerProfile:
    return PlayerProfile.load(path, player_id, player_id.title())


def test_profile_service_records_and_persists(tmp_path: Path) -> None:
    service = ProfileService(profile_dir=tmp_path)

    session = service.start_session("tic_tac_toe")
    unlocked = session.complete(result="win", experience=250, metadata={"perfect_game": True})

    assert "tic_tac_toe_first_win" in unlocked
    assert "tic_tac_toe_perfect" in unlocked

    profile_path = tmp_path / "default.json"
    assert profile_path.exists()

    reloaded = _load_profile(profile_path, "default")
    assert reloaded.experience == service.active_profile.experience
    assert reloaded.level == service.active_profile.level
    assert reloaded.total_games_played() == service.active_profile.total_games_played()


def test_profile_service_records_daily_challenge(tmp_path: Path) -> None:
    """Daily challenge completions should be persisted for the active profile."""

    service = ProfileService(profile_dir=tmp_path)

    unlocked = service.record_daily_challenge_completion("challenge_x", when=date(2024, 2, 1))
    assert "daily_challenge_first_completion" in unlocked
    assert service.active_profile.daily_challenge_progress.is_completed(date(2024, 2, 1))

    profile_path = tmp_path / "default.json"
    reloaded = _load_profile(profile_path, "default")
    assert reloaded.daily_challenge_progress.is_completed(date(2024, 2, 1))


def test_profile_service_rename_and_reset(tmp_path: Path) -> None:
    service = ProfileService(profile_dir=tmp_path)
    service.active_profile.display_name = "Original"
    service.save_active_profile()

    renamed = service.rename_active_profile("hero", "Hero Player")
    assert renamed.player_id == "hero"
    assert renamed.display_name == "Hero Player"
    assert (tmp_path / "hero.json").exists()
    assert not (tmp_path / "default.json").exists()

    loss_session = service.start_session("nim")
    loss_session.complete(result="loss", experience=100, metadata=None)
    assert service.active_profile.experience == 100

    reset = service.reset_active_profile()
    assert reset.experience == 0
    assert reset.level == 1
    assert (tmp_path / "hero.json").exists()


def test_profile_service_supports_multiple_profiles(tmp_path: Path) -> None:
    service = ProfileService(profile_dir=tmp_path)

    second = service.select_profile("second", "Second Player")
    assert second.player_id == "second"
    assert (tmp_path / "second.json").exists()

    available: List[str] = service.list_profiles()
    assert "second" in available
    assert "default" in available

    service.select_profile("default")
    summary = service.summary()
    assert "Second Player" not in summary
    assert service.active_profile.player_id == "default"
