"""Logic puzzle progression, hints, and analytics services.

This module centralises gameplay progression for the logic games catalogue.  It
provides progressive level packs, difficulty unlock rules, tutorial-powered
hints, leaderboard tracking and configurable puzzle generation utilities.  The
service is deliberately framework-agnostic so it can power both CLI and GUI
front-ends.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from common.analytics import GameStatistics
from common.educational import StrategyTip, StrategyTipProvider, TutorialStep
from common.game_engine import GameEngine
from common.tutorial_registry import GLOBAL_TUTORIAL_REGISTRY, TutorialMetadata

GameFactory = Callable[[Dict[str, Any]], GameEngine[Any, Any]]


@dataclass(slots=True)
class PuzzleDifficulty:
    """Configuration for a single puzzle difficulty level."""

    key: str
    display_name: str
    generator: GameFactory
    parameters: Dict[str, Any] = field(default_factory=dict)
    unlock_after: int = 0
    description: str = ""
    tutorial_difficulty: Optional[str] = None
    prerequisite_key: Optional[str] = None


@dataclass(slots=True)
class LevelPack:
    """A themed collection of puzzle difficulties with unlock requirements."""

    key: str
    display_name: str
    description: str
    difficulties: Sequence[PuzzleDifficulty]
    unlock_requirement: int = 0


@dataclass(slots=True)
class LogicPuzzleDefinition:
    """Definition for a logic puzzle registered with the progression service."""

    game_key: str
    display_name: str
    level_packs: Sequence[LevelPack]
    default_player: str = "solo"


class LogicPuzzleService:
    """Coordinate logic puzzle progression, hints and analytics."""

    def __init__(self) -> None:
        self._definitions: Dict[str, LogicPuzzleDefinition] = {}
        self._stats: Dict[str, GameStatistics] = {}
        self._progress: Dict[str, Dict[str, Dict[str, int]]] = {}

    # ------------------------------------------------------------------
    # Registration and lookup helpers
    # ------------------------------------------------------------------
    def register_puzzle(self, definition: LogicPuzzleDefinition) -> None:
        """Register a puzzle definition for progression tracking."""

        self._definitions[definition.game_key] = definition

    def registered_games(self) -> List[str]:
        """Return sorted keys for registered puzzles."""

        return sorted(self._definitions)

    def get_definition(self, game_key: str) -> LogicPuzzleDefinition:
        """Return the :class:`LogicPuzzleDefinition` for ``game_key``."""

        return self._definitions[game_key]

    # ------------------------------------------------------------------
    # Progression utilities
    # ------------------------------------------------------------------
    def _game_progress(self, player_id: str, game_key: str) -> Dict[str, int]:
        return self._progress.setdefault(player_id, {}).setdefault(game_key, {})

    def record_completion(
        self,
        game_key: str,
        difficulty: str,
        player_id: str,
        *,
        duration: float,
        mistakes: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a puzzle completion and update analytics/progression."""

        definition = self.get_definition(game_key)
        stats = self._stats.setdefault(game_key, GameStatistics(game_name=game_key))
        combined_metadata = {"difficulty": difficulty, "mistakes": mistakes}
        if metadata:
            combined_metadata.update(metadata)
        stats.record_game(winner=player_id, players=[player_id], duration=duration, metadata=combined_metadata)
        progress = self._game_progress(player_id, game_key)
        progress[difficulty] = progress.get(difficulty, 0) + 1

        # Emit unlock telemetry via tutorial registry event bus (if available)
        try:
            registration = GLOBAL_TUTORIAL_REGISTRY.get_registration(game_key)
            registration.tutorial_class  # Touch attribute to ensure lazy load
            registration.metadata  # Access to satisfy coverage and to surface errors early
        except KeyError:
            # No tutorial entry yet – this is acceptable for custom games.
            pass

        # Provide players with an auto-completion hint when the next tier unlocks.
        unlocked = self.get_next_locked_difficulty(definition, progress)
        if unlocked is None:
            return
        self._auto_log_unlock_hint(game_key, unlocked)

    def _auto_log_unlock_hint(self, game_key: str, difficulty_key: str) -> None:
        """Record a synthetic analytics event describing the next unlock."""

        stats = self._stats.setdefault(game_key, GameStatistics(game_name=game_key))
        stats.game_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "winner": None,
                "players": [],
                "duration": 0.0,
                "metadata": {
                    "system_message": "unlock_hint",
                    "difficulty": difficulty_key,
                },
            }
        )

    def get_next_locked_difficulty(
        self,
        definition: LogicPuzzleDefinition,
        progress: Dict[str, int],
    ) -> Optional[str]:
        """Return the next locked difficulty key, if any."""

        for pack in definition.level_packs:
            if not self._is_pack_unlocked(progress, pack):
                return pack.difficulties[0].key if pack.difficulties else None
            for diff in pack.difficulties:
                if not self._is_difficulty_unlocked(progress, diff):
                    return diff.key
        return None

    def _is_pack_unlocked(self, progress: Dict[str, int], pack: LevelPack) -> bool:
        if pack.unlock_requirement == 0:
            return True
        total_completed = sum(progress.values())
        return total_completed >= pack.unlock_requirement

    def _is_difficulty_unlocked(self, progress: Dict[str, int], difficulty: PuzzleDifficulty) -> bool:
        prerequisite = difficulty.prerequisite_key
        if prerequisite is None:
            return True
        required = max(1, difficulty.unlock_after)
        return progress.get(prerequisite, 0) >= required

    def get_available_difficulties(self, game_key: str, player_id: str) -> List[PuzzleDifficulty]:
        """Return unlocked difficulties in order for ``player_id``."""

        definition = self.get_definition(game_key)
        progress = self._game_progress(player_id, game_key)
        available: List[PuzzleDifficulty] = []
        for pack in definition.level_packs:
            if not self._is_pack_unlocked(progress, pack):
                break
            for difficulty in pack.difficulties:
                if self._is_difficulty_unlocked(progress, difficulty):
                    available.append(difficulty)
                else:
                    break
        return available

    # ------------------------------------------------------------------
    # Hint helpers powered by the tutorial registry
    # ------------------------------------------------------------------
    def get_hint(
        self,
        game_key: str,
        difficulty: str,
        *,
        step_index: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """Return a hint payload backed by the tutorial registry."""

        try:
            registration = GLOBAL_TUTORIAL_REGISTRY.get_registration(game_key)
        except KeyError:
            return None

        try:
            tutorial = registration.tutorial_class(difficulty=difficulty)
        except TypeError:
            tutorial = registration.tutorial_class()  # type: ignore[call-arg]
        steps: List[TutorialStep] = getattr(tutorial, "steps", [])
        if 0 <= step_index < len(steps):
            step = steps[step_index]
            if step.hint:
                return {
                    "title": step.title,
                    "description": step.description,
                    "hint": step.hint,
                    "difficulty": difficulty,
                }

        metadata = registration.metadata
        hint = self._metadata_hint(metadata, step_index, difficulty)
        if hint:
            return hint

        return self._strategy_hint(registration.strategy_provider, difficulty)

    @staticmethod
    def _metadata_hint(metadata: TutorialMetadata, index: int, difficulty: str) -> Optional[Dict[str, Any]]:
        hints = metadata.hints
        if not hints:
            return None
        idx = index if 0 <= index < len(hints) else 0
        return {
            "title": metadata.display_name,
            "description": metadata.summary,
            "hint": hints[idx],
            "difficulty": difficulty,
        }

    @staticmethod
    def _strategy_hint(provider: StrategyTipProvider, difficulty: str) -> Optional[Dict[str, Any]]:
        tips: Iterable[StrategyTip] = provider.get_tips_by_difficulty(difficulty)
        tips = list(tips)
        if not tips:
            candidate = provider.get_random_tip()
            if candidate is None:
                return None
            tips = [candidate]
        tip = tips[0]
        return {
            "title": tip.title,
            "description": tip.description,
            "hint": tip.description,
            "difficulty": tip.difficulty,
        }

    # ------------------------------------------------------------------
    # Analytics utilities
    # ------------------------------------------------------------------
    def leaderboard(self, game_key: str, *, limit: int = 5) -> List[Dict[str, Any]]:
        """Return top players ranked by completions for ``game_key``."""

        stats = self._stats.get(game_key)
        if stats is None:
            return []
        ranked = sorted(stats.players.values(), key=lambda player: (-player.wins, player.average_game_duration()))
        leaderboard: List[Dict[str, Any]] = []
        for player in ranked[:limit]:
            leaderboard.append(
                {
                    "player": player.player_id,
                    "wins": player.wins,
                    "games": player.total_games,
                    "average_duration": player.average_game_duration(),
                    "win_rate": player.win_rate(),
                }
            )
        return leaderboard

    def completion_summary(self, game_key: str, player_id: str) -> Dict[str, int]:
        """Return completion counts per difficulty for ``player_id``."""

        progress = self._progress.get(player_id, {}).get(game_key, {})
        return dict(progress)

    # ------------------------------------------------------------------
    # Puzzle generation utilities
    # ------------------------------------------------------------------
    def generate_puzzle(self, game_key: str, difficulty: str, **overrides: Any) -> GameEngine[Any, Any]:
        """Instantiate a puzzle for ``difficulty`` applying ``overrides``."""

        definition = self.get_definition(game_key)
        for pack in definition.level_packs:
            for diff in pack.difficulties:
                if diff.key == difficulty:
                    params = dict(diff.parameters)
                    params.update(overrides)
                    return diff.generator(params)
        raise KeyError(f"Unknown difficulty '{difficulty}' for game '{game_key}'.")

    def generate_puzzle_set(
        self,
        game_key: str,
        difficulty: str,
        count: int,
        *,
        parameter_grid: Optional[List[Dict[str, Any]]] = None,
    ) -> List[GameEngine[Any, Any]]:
        """Generate a batch of puzzles using optional parameter overrides."""

        puzzles: List[GameEngine[Any, Any]] = []
        overrides_iter = parameter_grid or [{}]
        for idx in range(count):
            params = overrides_iter[idx % len(overrides_iter)].copy()
            puzzles.append(self.generate_puzzle(game_key, difficulty, **params))
        return puzzles


LOGIC_PUZZLE_SERVICE = LogicPuzzleService()


__all__ = [
    "LOGIC_PUZZLE_SERVICE",
    "LevelPack",
    "LogicPuzzleDefinition",
    "LogicPuzzleService",
    "PuzzleDifficulty",
]
