"""Integration tests for the central achievement registry."""

from __future__ import annotations

import pathlib
from typing import List

from common.achievements import AchievementManager, create_common_achievements
from common.achievements_registry import (
    ACHIEVEMENT_UNLOCKED_EVENT,
    AchievementRegistry,
    get_achievement_registry,
)
from common.architecture.events import FunctionEventHandler, get_global_event_bus
from common.profile import PlayerProfile


def test_registry_registers_core_and_game_achievements() -> None:
    """The registry should register cross-game and per-game achievements."""

    registry = AchievementRegistry()
    manager = AchievementManager()

    registry.register_all(manager)

    core_ids = {achievement.id for achievement in create_common_achievements()}
    game_ids = {achievement.id for achievement in registry.iter_game_achievements()}

    assert core_ids.issubset(manager.achievements.keys())
    assert game_ids.issubset(manager.achievements.keys())


def test_player_profile_unlocks_emit_events(tmp_path: pathlib.Path) -> None:
    """Recording games on a profile should unlock achievements and emit events."""

    bus = get_global_event_bus()
    captured_events: List = []
    handler = FunctionEventHandler(lambda event: captured_events.append(event), {ACHIEVEMENT_UNLOCKED_EVENT})
    bus.subscribe(ACHIEVEMENT_UNLOCKED_EVENT, handler)

    profile = PlayerProfile(player_id="tester", display_name="Tester")

    unlocked = profile.record_game("tic_tac_toe", "win", metadata={"perfect_game": True})

    assert "first_win" in unlocked
    assert "tic_tac_toe_first_win" in unlocked
    assert "tic_tac_toe_perfect" in unlocked

    assert captured_events, "Expected an achievement unlock event to be emitted"
    event = captured_events[0]
    assert event.data["player_id"] == "tester"
    unlocked_ids = {achievement.id for achievement in event.data["achievements"]}
    assert "tic_tac_toe_first_win" in unlocked_ids

    bus.unsubscribe(ACHIEVEMENT_UNLOCKED_EVENT, handler)


def test_achievement_progress_persists_across_sessions(tmp_path: pathlib.Path) -> None:
    """Unlocked achievements should persist when saving and loading profiles."""

    profile = PlayerProfile(player_id="multi", display_name="Multi")
    profile.record_game("tic_tac_toe", "win")
    profile.record_game("hangman", "win")

    profile_path = tmp_path / "profile.json"
    profile.save(profile_path)

    loaded = PlayerProfile.load(profile_path, "multi", "Multi")
    registry = get_achievement_registry()
    registry.register_all(loaded.achievement_manager)

    assert loaded.achievement_manager.is_unlocked("first_win")
    assert loaded.achievement_manager.is_unlocked("tic_tac_toe_first_win")
    assert loaded.achievement_manager.is_unlocked("hangman_first_win")
