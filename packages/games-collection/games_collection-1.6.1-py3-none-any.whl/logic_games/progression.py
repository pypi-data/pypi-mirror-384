"""Logic puzzle progression, hints, and analytics services.

This module centralizes gameplay progression for the logic games catalog. It
provides a framework for defining level packs, difficulty progression, and
unlock rules. The `LogicPuzzleService` is the main entry point, offering
functionality for tracking player progress, providing hints, and generating
leaderboards.

The service is designed to be framework-agnostic, allowing it to power both
command-line and graphical user interfaces. It integrates with the global
tutorial registry to provide contextual hints and tips.

Classes:
    PuzzleDifficulty: Configuration for a single puzzle difficulty level.
    LevelPack: A themed collection of puzzle difficulties.
    LogicPuzzleDefinition: The complete definition for a logic puzzle.
    LogicPuzzleService: A service to manage puzzle progression and analytics.

Factories:
    GameFactory: A callable that creates a game engine instance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from common.analytics import GameStatistics
from common.educational import StrategyTip, StrategyTipProvider, TutorialStep
from common.game_engine import GameEngine
from common.tutorial_registry import GLOBAL_TUTORIAL_REGISTRY, TutorialMetadata

# A factory function for creating game engine instances.
GameFactory = Callable[[Dict[str, Any]], GameEngine[Any, Any]]


@dataclass(slots=True)
class PuzzleDifficulty:
    """Configuration for a single puzzle difficulty level.

    Attributes:
        key: A unique identifier for this difficulty level.
        display_name: The human-readable name for this difficulty.
        generator: A factory function to create a game instance.
        parameters: A dictionary of parameters to pass to the generator.
        unlock_after: The number of completions of the prerequisite
            difficulty required to unlock this one.
        description: A brief description of the difficulty level.
        tutorial_difficulty: The corresponding difficulty key in the
            tutorial registry.
        prerequisite_key: The key of the difficulty that must be completed
            to unlock this one.
    """

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
    """A themed collection of puzzle difficulties with unlock requirements.

    Attributes:
        key: A unique identifier for the level pack.
        display_name: The human-readable name for the pack.
        description: A brief description of the level pack's theme.
        difficulties: A sequence of `PuzzleDifficulty` instances in this pack.
        unlock_requirement: The total number of puzzle completions required
            to unlock this pack.
    """

    key: str
    display_name: str
    description: str
    difficulties: Sequence[PuzzleDifficulty]
    unlock_requirement: int = 0


@dataclass(slots=True)
class LogicPuzzleDefinition:
    """The complete definition for a logic puzzle, including all its level packs.

    Attributes:
        game_key: A unique identifier for the game.
        display_name: The human-readable name of the game.
        level_packs: A sequence of `LevelPack` instances for this game.
        default_player: The default player ID to use for solo play.
    """

    game_key: str
    display_name: str
    level_packs: Sequence[LevelPack]
    default_player: str = "solo"


class LogicPuzzleService:
    """A service to coordinate logic puzzle progression, hints, and analytics.

    This service acts as a central hub for managing the player's journey
    through the logic puzzles. It handles puzzle registration, tracks
    completions, determines unlockable content, and provides hints and
    leaderboard data.
    """

    def __init__(self) -> None:
        """Initialize the LogicPuzzleService."""
        self._definitions: Dict[str, LogicPuzzleDefinition] = {}
        self._stats: Dict[str, GameStatistics] = {}
        self._progress: Dict[str, Dict[str, Dict[str, int]]] = {}

    # ------------------------------------------------------------------
    # Registration and lookup helpers
    # ------------------------------------------------------------------
    def register_puzzle(self, definition: LogicPuzzleDefinition) -> None:
        """Register a puzzle definition for progression tracking.

        Args:
            definition: The `LogicPuzzleDefinition` to register.
        """
        self._definitions[definition.game_key] = definition

    def registered_games(self) -> List[str]:
        """Return a sorted list of keys for all registered puzzles."""
        return sorted(self._definitions)

    def get_definition(self, game_key: str) -> LogicPuzzleDefinition:
        """Return the `LogicPuzzleDefinition` for the specified game key.

        Args:
            game_key: The key of the game to look up.

        Returns:
            The corresponding puzzle definition.
        """
        return self._definitions[game_key]

    # ------------------------------------------------------------------
    # Progression utilities
    # ------------------------------------------------------------------
    def _game_progress(self, player_id: str, game_key: str) -> Dict[str, int]:
        """Retrieve the progress data for a specific player and game."""
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
        """Record a puzzle completion and update analytics and progression.

        Args:
            game_key: The key of the completed game.
            difficulty: The key of the completed difficulty.
            player_id: The ID of the player who completed the puzzle.
            duration: The time taken to complete the puzzle, in seconds.
            mistakes: The number of mistakes made during the puzzle.
            metadata: Additional metadata about the completion.
        """
        definition = self.get_definition(game_key)
        stats = self._stats.setdefault(game_key, GameStatistics(game_name=game_key))
        combined_metadata = {"difficulty": difficulty, "mistakes": mistakes}
        if metadata:
            combined_metadata.update(metadata)
        stats.record_game(winner=player_id, players=[player_id], duration=duration, metadata=combined_metadata)
        progress = self._game_progress(player_id, game_key)
        progress[difficulty] = progress.get(difficulty, 0) + 1

        # Emit unlock telemetry via the tutorial registry's event bus.
        try:
            registration = GLOBAL_TUTORIAL_REGISTRY.get_registration(game_key)
            registration.tutorial_class  # Touch attribute to ensure lazy load.
            registration.metadata  # Access to satisfy coverage and surface errors early.
        except KeyError:
            # No tutorial entry exists, which is acceptable for custom games.
            pass

        # Provide players with a hint when the next tier unlocks.
        unlocked = self.get_next_locked_difficulty(definition, progress)
        if unlocked is None:
            return
        self._auto_log_unlock_hint(game_key, unlocked)

    def _auto_log_unlock_hint(self, game_key: str, difficulty_key: str) -> None:
        """Record a synthetic analytics event to signify an unlock."""
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
        """Return the key of the next locked difficulty, if any.

        Args:
            definition: The puzzle definition to check against.
            progress: The player's current progress data.

        Returns:
            The key of the next locked difficulty, or None if all are unlocked.
        """
        for pack in definition.level_packs:
            if not self._is_pack_unlocked(progress, pack):
                return pack.difficulties[0].key if pack.difficulties else None
            for diff in pack.difficulties:
                if not self._is_difficulty_unlocked(progress, diff):
                    return diff.key
        return None

    def _is_pack_unlocked(self, progress: Dict[str, int], pack: LevelPack) -> bool:
        """Check if a level pack is unlocked based on the player's progress."""
        if pack.unlock_requirement == 0:
            return True
        total_completed = sum(progress.values())
        return total_completed >= pack.unlock_requirement

    def _is_difficulty_unlocked(self, progress: Dict[str, int], difficulty: PuzzleDifficulty) -> bool:
        """Check if a specific difficulty is unlocked."""
        prerequisite = difficulty.prerequisite_key
        if prerequisite is None:
            return True
        required = max(1, difficulty.unlock_after)
        return progress.get(prerequisite, 0) >= required

    def get_available_difficulties(self, game_key: str, player_id: str) -> List[PuzzleDifficulty]:
        """Return a list of all unlocked difficulties for a given player.

        Args:
            game_key: The key of the game.
            player_id: The ID of the player.

        Returns:
            A list of `PuzzleDifficulty` instances that are available.
        """
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
        """Return a hint payload, backed by the tutorial registry.

        Args:
            game_key: The key of the game for which a hint is requested.
            difficulty: The current difficulty level.
            step_index: The index of the tutorial step for the hint.

        Returns:
            A dictionary containing the hint, or None if no hint is found.
        """
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
        """Generate a hint from the tutorial's metadata."""
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
        """Generate a hint from the strategy tip provider."""
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
        """Return the top players, ranked by completions, for a given game.

        Args:
            game_key: The key of the game for the leaderboard.
            limit: The maximum number of players to return.

        Returns:
            A list of dictionaries, each representing a player on the leaderboard.
        """
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
        """Return a summary of completion counts per difficulty for a player.

        Args:
            game_key: The key of the game.
            player_id: The ID of the player.

        Returns:
            A dictionary mapping difficulty keys to completion counts.
        """
        progress = self._progress.get(player_id, {}).get(game_key, {})
        return dict(progress)

    # ------------------------------------------------------------------
    # Puzzle generation utilities
    # ------------------------------------------------------------------
    def generate_puzzle(self, game_key: str, difficulty: str, **overrides: Any) -> GameEngine[Any, Any]:
        """Instantiate a puzzle for a given difficulty, with optional overrides.

        Args:
            game_key: The key of the game to generate.
            difficulty: The key of the difficulty to generate.
            overrides: Keyword arguments to override default parameters.

        Returns:
            An instance of the game engine for the specified puzzle.

        Raises:
            KeyError: If the difficulty or game key is not found.
        """
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
        """Generate a batch of puzzles with optional parameter overrides.

        Args:
            game_key: The key of the game to generate.
            difficulty: The key of the difficulty to generate.
            count: The number of puzzles to generate.
            parameter_grid: A list of parameter dictionaries to cycle through.

        Returns:
            A list of generated game engine instances.
        """
        puzzles: List[GameEngine[Any, Any]] = []
        overrides_iter = parameter_grid or [{}]
        for idx in range(count):
            params = overrides_iter[idx % len(overrides_iter)].copy()
            puzzles.append(self.generate_puzzle(game_key, difficulty, **params))
        return puzzles


# A global instance of the LogicPuzzleService for convenient access.
LOGIC_PUZZLE_SERVICE = LogicPuzzleService()


__all__ = [
    "LOGIC_PUZZLE_SERVICE",
    "LevelPack",
    "LogicPuzzleDefinition",
    "LogicPuzzleService",
    "PuzzleDifficulty",
]
