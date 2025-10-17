"""Tests for the daily challenge scheduler and validation helpers."""

from __future__ import annotations

from datetime import date, timedelta

from common.challenges import DifficultyLevel, get_default_challenge_manager
from common.daily_challenges import DailyChallengeScheduler


def test_scheduler_persists_selection(tmp_path) -> None:
    """Scheduler should persist selections so repeated lookups match."""

    manager = get_default_challenge_manager()
    storage = tmp_path / "schedule.json"
    scheduler = DailyChallengeScheduler(manager, storage_path=storage)

    target_day = date(2024, 1, 1)
    first = scheduler.get_challenge_for_date(target_day)

    # Reload the scheduler to confirm persistence across instances.
    scheduler_reloaded = DailyChallengeScheduler(manager, storage_path=storage)
    second = scheduler_reloaded.get_challenge_for_date(target_day)

    assert first.pack.name == second.pack.name
    assert first.challenge.id == second.challenge.id


def test_scheduler_rotates_difficulty_levels(tmp_path) -> None:
    """Scheduler should cycle through all difficulty levels over consecutive days."""

    manager = get_default_challenge_manager()
    scheduler = DailyChallengeScheduler(manager, storage_path=tmp_path / "rotation.json")

    start = date(2024, 5, 1)
    difficulties = [scheduler.get_challenge_for_date(start + timedelta(days=offset)).challenge.difficulty for offset in range(4)]

    assert set(difficulties) == {
        DifficultyLevel.BEGINNER,
        DifficultyLevel.INTERMEDIATE,
        DifficultyLevel.ADVANCED,
        DifficultyLevel.EXPERT,
    }

    repeat = scheduler.get_challenge_for_date(start + timedelta(days=4)).challenge.difficulty
    assert repeat == difficulties[0]


def test_sudoku_challenge_validation() -> None:
    """Sudoku challenge validation should succeed only when the board is solved."""

    manager = get_default_challenge_manager()
    pack = manager.get_pack("Sudoku Mastery")
    assert pack is not None

    challenge = pack.get_challenge("sudoku_jellyfish_master")
    assert challenge is not None

    builder = challenge.metadata.get("build_puzzle")
    assert callable(builder)

    puzzle = builder()
    assert not challenge.validate(puzzle)

    puzzle.board = [row[:] for row in puzzle.solution]
    assert challenge.validate(puzzle)
