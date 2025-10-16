"""Tests for the logic games progression service and GUI integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from common.educational import StrategyTip, StrategyTipProvider, TutorialMode, TutorialStep
from common.game_engine import GameEngine, GameState
from common.tutorial_registry import GLOBAL_TUTORIAL_REGISTRY, TutorialMetadata, TutorialRegistration
from common.tutorial_registry import SimpleProgressProbabilityCalculator
from logic_games.progression import LOGIC_PUZZLE_SERVICE, LevelPack, LogicPuzzleDefinition, LogicPuzzleService, PuzzleDifficulty


class DummyGame(GameEngine[None, int]):
    """Minimal game engine used for testing progression logic."""

    def __init__(self) -> None:
        self.state = GameState.NOT_STARTED

    def reset(self) -> None:
        self.state = GameState.NOT_STARTED

    def is_game_over(self) -> bool:
        return False

    def get_current_player(self) -> int:
        return 0

    def get_valid_moves(self) -> List[None]:
        return []

    def make_move(self, move: None) -> bool:
        return True

    def get_winner(self) -> Optional[int]:
        return None

    def get_game_state(self) -> GameState:
        return self.state


@dataclass
class _GeneratorRecorder:
    """Utility helper to capture parameters passed to a generator."""

    seen: List[Dict[str, Any]]

    def __call__(self, params: Dict[str, Any]) -> DummyGame:
        self.seen.append(dict(params))
        return DummyGame()


def _register_demo_tutorial(game_key: str) -> None:
    class DemoTutorial(TutorialMode[None, None]):
        def _create_tutorial_steps(self) -> List[TutorialStep]:
            return [TutorialStep(title="Intro", description="Start solving", hint="Try a corner.")]

    metadata = TutorialMetadata(
        game_key=game_key,
        display_name="Demo Logic",
        category="logic_games",
        doc_path="docs/demo.md",
        summary="Demo tutorial",
        hints=["Study the board edges."],
    )
    provider = StrategyTipProvider()
    provider.add_tip(StrategyTip(title="Corner", description="Work from the corners", difficulty="beginner"))
    registration = TutorialRegistration(
        metadata=metadata,
        tutorial_class=DemoTutorial,
        strategy_provider=provider,
        probability_calculator=SimpleProgressProbabilityCalculator(),
    )
    GLOBAL_TUTORIAL_REGISTRY.register(registration)


def test_progression_unlocks_with_level_packs() -> None:
    service = LogicPuzzleService()
    recorder = _GeneratorRecorder(seen=[])
    service.register_puzzle(
        LogicPuzzleDefinition(
            game_key="tests.logic.puzzle",
            display_name="Logic Trial",
            level_packs=[
                LevelPack(
                    key="basics",
                    display_name="Basics",
                    description="Intro levels",
                    difficulties=[
                        PuzzleDifficulty(key="easy", display_name="Easy", generator=recorder),
                        PuzzleDifficulty(
                            key="medium",
                            display_name="Medium",
                            generator=recorder,
                            prerequisite_key="easy",
                            unlock_after=2,
                        ),
                    ],
                ),
                LevelPack(
                    key="advanced",
                    display_name="Advanced",
                    description="Unlock after training",
                    unlock_requirement=4,
                    difficulties=[PuzzleDifficulty(key="hard", display_name="Hard", generator=recorder)],
                ),
            ],
        )
    )

    available = service.get_available_difficulties("tests.logic.puzzle", "tester")
    assert [difficulty.key for difficulty in available] == ["easy"]

    for _ in range(2):
        service.record_completion("tests.logic.puzzle", "easy", "tester", duration=15.0)

    available = service.get_available_difficulties("tests.logic.puzzle", "tester")
    assert [difficulty.key for difficulty in available] == ["easy", "medium"]

    for _ in range(2):
        service.record_completion("tests.logic.puzzle", "medium", "tester", duration=20.0)

    available = service.get_available_difficulties("tests.logic.puzzle", "tester")
    assert [difficulty.key for difficulty in available] == ["easy", "medium", "hard"]

    puzzles = service.generate_puzzle_set("tests.logic.puzzle", "medium", count=3, parameter_grid=[{"seed": 1}, {"seed": 2}])
    assert len(puzzles) == 3
    assert len(recorder.seen) >= 3
    assert recorder.seen[1]["seed"] == 2


def test_hint_system_prefers_tutorial_steps() -> None:
    key = "tests.logic.hints"
    _register_demo_tutorial(key)
    service = LogicPuzzleService()
    recorder = _GeneratorRecorder(seen=[])
    service.register_puzzle(
        LogicPuzzleDefinition(
            game_key=key,
            display_name="Hint Trial",
            level_packs=[
                LevelPack(
                    key="primary",
                    display_name="Primary",
                    description="Single level",
                    difficulties=[PuzzleDifficulty(key="easy", display_name="Easy", generator=recorder)],
                )
            ],
        )
    )

    hint = service.get_hint(key, "easy")
    assert hint is not None
    assert "corner" in hint["hint"].lower()


def test_leaderboard_tracking_uses_analytics() -> None:
    service = LogicPuzzleService()
    recorder = _GeneratorRecorder(seen=[])
    key = "tests.logic.analytics"
    service.register_puzzle(
        LogicPuzzleDefinition(
            game_key=key,
            display_name="Analytics Trial",
            level_packs=[
                LevelPack(
                    key="core",
                    display_name="Core",
                    description="Single level",
                    difficulties=[PuzzleDifficulty(key="solo", display_name="Solo", generator=recorder)],
                )
            ],
        )
    )

    for duration in (9.0, 7.5, 8.0):
        service.record_completion(key, "solo", "player_a", duration=duration)
    service.record_completion(key, "solo", "player_b", duration=6.0)

    leaderboard = service.leaderboard(key)
    assert leaderboard[0]["player"] == "player_a"
    assert leaderboard[0]["wins"] == 3
    summary = service.completion_summary(key, "player_a")
    assert summary == {"solo": 3}


def test_global_service_registered_games() -> None:
    assert LOGIC_PUZZLE_SERVICE.registered_games(), "Default logic games should be registered"

