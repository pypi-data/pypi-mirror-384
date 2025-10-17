"""Central registry for achievements shared across all games.

This module aggregates cross-game achievements with game-specific entries and
provides helper utilities for wiring the achievement system into both CLI and
GUI contexts.  Achievements registered through this registry are automatically
connected to the global :class:`~common.achievements.AchievementManager` that is
attached to each :class:`~common.profile.PlayerProfile`.

The registry also exposes notification helpers that broadcast newly unlocked
achievements over the global event bus, enabling command-line summaries and GUI
pop-up announcements without every game having to implement bespoke logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence

from common.achievements import Achievement, AchievementCategory, AchievementManager, AchievementRarity, create_common_achievements
from common.architecture.events import Event, FunctionEventHandler, get_global_event_bus

# Canonical event name that will be emitted when one or more achievements are
# unlocked.  Consumers (CLI helpers, GUIs, plugins) can subscribe to this event
# to display contextual notifications to players.
ACHIEVEMENT_UNLOCKED_EVENT = "achievement.unlocked"


def _safe_register(manager: AchievementManager, achievement: Achievement) -> None:
    """Register ``achievement`` with ``manager`` if not already present."""

    if achievement.id in manager.achievements:
        return
    manager.register_achievement(achievement)


def _game_condition(game_id: str, predicate: Callable[[Dict[str, int]], bool]) -> Callable[[Dict], bool]:
    """Create a condition that only executes ``predicate`` for ``game_id``."""

    def _condition(stats: Dict) -> bool:
        if stats.get("game_id") != game_id:
            return False
        game_stats = {
            "wins": stats.get("game_wins", 0),
            "games_played": stats.get("game_games_played", 0),
            "win_streak": stats.get("game_win_streak", 0),
            "best_win_streak": stats.get("game_best_win_streak", 0),
            "perfect_games": stats.get("game_perfect_games", 0),
        }
        return predicate(game_stats)

    return _condition


@dataclass
class _GameAchievementConfig:
    """Container describing the achievements that belong to a game."""

    achievements: Sequence[Achievement]


class AchievementRegistry:
    """Aggregate and register core and game-specific achievements."""

    def __init__(self) -> None:
        self._core_achievements: List[Achievement] = create_common_achievements()
        self._game_achievements: Dict[str, _GameAchievementConfig] = self._build_game_configs()
        self._cli_handler_registered = False
        self._gui_handlers: Dict[int, FunctionEventHandler] = {}

    def _build_game_configs(self) -> Dict[str, _GameAchievementConfig]:
        """Create the built-in catalogue of game specific achievements."""

        return {
            "tic_tac_toe": _GameAchievementConfig(
                achievements=[
                    Achievement(
                        id="tic_tac_toe_first_win",
                        name="Grid Graduate",
                        description="Win your first game of Tic-Tac-Toe.",
                        category=AchievementCategory.GAMEPLAY,
                        rarity=AchievementRarity.COMMON,
                        game="tic_tac_toe",
                        points=15,
                        condition=_game_condition("tic_tac_toe", lambda stats: stats["wins"] >= 1),
                    ),
                    Achievement(
                        id="tic_tac_toe_streak_3",
                        name="Grid Dominator",
                        description="Achieve a 3 game winning streak in Tic-Tac-Toe.",
                        category=AchievementCategory.MASTERY,
                        rarity=AchievementRarity.UNCOMMON,
                        game="tic_tac_toe",
                        points=35,
                        condition=_game_condition("tic_tac_toe", lambda stats: stats["best_win_streak"] >= 3),
                    ),
                    Achievement(
                        id="tic_tac_toe_perfect",
                        name="Perfectionist",
                        description="Win a Tic-Tac-Toe game without letting the opponent score.",
                        category=AchievementCategory.SPECIAL,
                        rarity=AchievementRarity.RARE,
                        game="tic_tac_toe",
                        points=75,
                        hidden=True,
                        condition=_game_condition("tic_tac_toe", lambda stats: stats["perfect_games"] >= 1),
                    ),
                ]
            ),
            "hangman": _GameAchievementConfig(
                achievements=[
                    Achievement(
                        id="hangman_first_win",
                        name="Word Wrangler",
                        description="Win your first game of Hangman.",
                        category=AchievementCategory.GAMEPLAY,
                        rarity=AchievementRarity.COMMON,
                        game="hangman",
                        points=15,
                        condition=_game_condition("hangman", lambda stats: stats["wins"] >= 1),
                    ),
                    Achievement(
                        id="hangman_streak_5",
                        name="Noose Dodger",
                        description="Secure a five game win streak in Hangman.",
                        category=AchievementCategory.MASTERY,
                        rarity=AchievementRarity.RARE,
                        game="hangman",
                        points=55,
                        condition=_game_condition("hangman", lambda stats: stats["best_win_streak"] >= 5),
                    ),
                ]
            ),
            "blackjack": _GameAchievementConfig(
                achievements=[
                    Achievement(
                        id="blackjack_hot_streak",
                        name="Hot Hand",
                        description="Win three blackjack hands in a row.",
                        category=AchievementCategory.MASTERY,
                        rarity=AchievementRarity.UNCOMMON,
                        game="blackjack",
                        points=40,
                        condition=_game_condition("blackjack", lambda stats: stats["win_streak"] >= 3),
                    ),
                    Achievement(
                        id="blackjack_card_shark",
                        name="Card Shark",
                        description="Win twenty blackjack games.",
                        category=AchievementCategory.PROGRESSION,
                        rarity=AchievementRarity.RARE,
                        game="blackjack",
                        points=70,
                        condition=_game_condition("blackjack", lambda stats: stats["wins"] >= 20),
                    ),
                ]
            ),
            "nim": _GameAchievementConfig(
                achievements=[
                    Achievement(
                        id="nim_first_win",
                        name="Pile Pioneer",
                        description="Win your first game of Nim.",
                        category=AchievementCategory.GAMEPLAY,
                        rarity=AchievementRarity.COMMON,
                        game="nim",
                        points=15,
                        condition=_game_condition("nim", lambda stats: stats["wins"] >= 1),
                    ),
                    Achievement(
                        id="nim_perfect",
                        name="Mathematical Maestro",
                        description="Win a game of Nim without allowing the opponent a final move.",
                        category=AchievementCategory.SPECIAL,
                        rarity=AchievementRarity.EPIC,
                        game="nim",
                        points=90,
                        hidden=True,
                        condition=_game_condition("nim", lambda stats: stats["perfect_games"] >= 1),
                    ),
                ]
            ),
            "connect_four": _GameAchievementConfig(
                achievements=[
                    Achievement(
                        id="connect_four_first_win",
                        name="Line Breaker",
                        description="Win your first game of Connect Four.",
                        category=AchievementCategory.GAMEPLAY,
                        rarity=AchievementRarity.COMMON,
                        game="connect_four",
                        points=15,
                        condition=_game_condition("connect_four", lambda stats: stats["wins"] >= 1),
                    ),
                    Achievement(
                        id="connect_four_streak_4",
                        name="Vertical Virtuoso",
                        description="Achieve a four game win streak in Connect Four.",
                        category=AchievementCategory.MASTERY,
                        rarity=AchievementRarity.UNCOMMON,
                        game="connect_four",
                        points=45,
                        condition=_game_condition("connect_four", lambda stats: stats["best_win_streak"] >= 4),
                    ),
                ]
            ),
            "go_fish": _GameAchievementConfig(
                achievements=[
                    Achievement(
                        id="go_fish_collector",
                        name="Net Gain",
                        description="Win five games of Go Fish.",
                        category=AchievementCategory.GAMEPLAY,
                        rarity=AchievementRarity.UNCOMMON,
                        game="go_fish",
                        points=30,
                        condition=_game_condition("go_fish", lambda stats: stats["wins"] >= 5),
                    ),
                    Achievement(
                        id="go_fish_streak_3",
                        name="School Leader",
                        description="Maintain a three game win streak in Go Fish.",
                        category=AchievementCategory.MASTERY,
                        rarity=AchievementRarity.RARE,
                        game="go_fish",
                        points=55,
                        condition=_game_condition("go_fish", lambda stats: stats["best_win_streak"] >= 3),
                    ),
                ]
            ),
            "sudoku": _GameAchievementConfig(
                achievements=[
                    Achievement(
                        id="sudoku_first_completion",
                        name="Puzzle Novice",
                        description="Complete your first Sudoku grid.",
                        category=AchievementCategory.GAMEPLAY,
                        rarity=AchievementRarity.COMMON,
                        game="sudoku",
                        points=20,
                        condition=_game_condition("sudoku", lambda stats: stats["wins"] >= 1),
                    ),
                    Achievement(
                        id="sudoku_dedicated_solver",
                        name="Grid Analyst",
                        description="Finish ten Sudoku challenges.",
                        category=AchievementCategory.PROGRESSION,
                        rarity=AchievementRarity.UNCOMMON,
                        game="sudoku",
                        points=55,
                        condition=_game_condition("sudoku", lambda stats: stats["games_played"] >= 10),
                    ),
                ]
            ),
            "battleship": _GameAchievementConfig(
                achievements=[
                    Achievement(
                        id="battleship_fleet_commander",
                        name="Fleet Commander",
                        description="Win your first Battleship engagement.",
                        category=AchievementCategory.GAMEPLAY,
                        rarity=AchievementRarity.COMMON,
                        game="battleship",
                        points=20,
                        condition=_game_condition("battleship", lambda stats: stats["wins"] >= 1),
                    ),
                    Achievement(
                        id="battleship_unsinkable",
                        name="Unsinkable",
                        description="Secure a three game Battleship win streak.",
                        category=AchievementCategory.MASTERY,
                        rarity=AchievementRarity.RARE,
                        game="battleship",
                        points=65,
                        condition=_game_condition("battleship", lambda stats: stats["best_win_streak"] >= 3),
                    ),
                ]
            ),
            "daily_challenge": _GameAchievementConfig(
                achievements=[
                    Achievement(
                        id="daily_challenge_first_completion",
                        name="Routine Starter",
                        description="Complete your first daily challenge.",
                        category=AchievementCategory.GAMEPLAY,
                        rarity=AchievementRarity.COMMON,
                        game="daily_challenge",
                        points=20,
                        condition=_game_condition("daily_challenge", lambda stats: stats["wins"] >= 1),
                    ),
                    Achievement(
                        id="daily_challenge_streak_3",
                        name="Consistent Challenger",
                        description="Complete daily challenges three days in a row.",
                        category=AchievementCategory.MASTERY,
                        rarity=AchievementRarity.UNCOMMON,
                        game="daily_challenge",
                        points=45,
                        condition=_game_condition("daily_challenge", lambda stats: stats["best_win_streak"] >= 3),
                    ),
                    Achievement(
                        id="daily_challenge_streak_7",
                        name="Weekly Warrior",
                        description="Maintain a seven day daily challenge streak.",
                        category=AchievementCategory.MASTERY,
                        rarity=AchievementRarity.RARE,
                        game="daily_challenge",
                        points=80,
                        condition=_game_condition("daily_challenge", lambda stats: stats["best_win_streak"] >= 7),
                    ),
                ]
            ),
        }

    def register_all(self, manager: AchievementManager) -> None:
        """Register every known achievement with ``manager``."""

        for achievement in self._core_achievements:
            _safe_register(manager, achievement)

        for config in self._game_achievements.values():
            for achievement in config.achievements:
                _safe_register(manager, achievement)

    def iter_game_achievements(self) -> Iterable[Achievement]:
        """Iterate over all game-specific achievements."""

        for config in self._game_achievements.values():
            for achievement in config.achievements:
                yield achievement

    def notify_unlocks(
        self,
        unlocked_ids: Sequence[str],
        manager: AchievementManager,
        *,
        player_id: str,
        game_id: str,
        stats: Mapping[str, object],
    ) -> None:
        """Emit an event describing ``unlocked_ids`` for downstream listeners."""

        if not unlocked_ids:
            return

        achievements = [manager.achievements[aid] for aid in unlocked_ids if aid in manager.achievements]
        if not achievements:
            return

        event_bus = get_global_event_bus()
        event_bus.emit(
            ACHIEVEMENT_UNLOCKED_EVENT,
            data={
                "player_id": player_id,
                "game_id": game_id,
                "achievements": achievements,
                "stats": dict(stats),
            },
            source=self.__class__.__name__,
        )

    def enable_cli_notifications(self) -> None:
        """Install a CLI notification handler for unlocked achievements."""

        if self._cli_handler_registered:
            return

        def _handler(event: Event) -> None:
            achievements: List[Achievement] = event.data.get("achievements", [])
            if not achievements:
                return

            try:
                from common.cli_utils import ASCIIArt, Color, TextStyle
            except ImportError:  # pragma: no cover - defensive fallback
                ASCIIArt = None  # type: ignore[assignment]
                Color = None  # type: ignore[assignment]
                TextStyle = None  # type: ignore[assignment]

            message_lines = [
                "🏆 Achievement Unlocked!",
                "",
            ]
            for achievement in achievements:
                message_lines.append(f"{achievement.name} — {achievement.description}")

            message = "\n".join(message_lines)

            if ASCIIArt is not None and Color is not None and TextStyle is not None:
                banner = ASCIIArt.banner("ACHIEVEMENT", color=Color.YELLOW)
                box = ASCIIArt.box(message, color=Color.MAGENTA)
                print(f"{banner}\n{box}\n{TextStyle.RESET}")
            else:  # pragma: no cover - limited environment fallback
                print(message)

        handler = FunctionEventHandler(_handler, {ACHIEVEMENT_UNLOCKED_EVENT})
        get_global_event_bus().subscribe(ACHIEVEMENT_UNLOCKED_EVENT, handler)
        self._cli_handler_registered = True

    def enable_gui_notifications(self, root: object) -> None:
        """Install a Tkinter pop-up handler that reacts to unlock events."""

        try:
            from tkinter import messagebox
        except Exception:  # pragma: no cover - Tkinter unavailable
            return

        root_id = id(root)
        if root_id in self._gui_handlers:
            return

        def _handler(event: Event) -> None:
            achievements: List[Achievement] = event.data.get("achievements", [])
            if not achievements:
                return

            names = "\n".join(f"• {achievement.name}" for achievement in achievements)

            def _show_popup() -> None:
                messagebox.showinfo("Achievement Unlocked", f"You earned:\n{names}")

            try:
                root.after(0, _show_popup)
            except AttributeError:  # pragma: no cover - fallback when root lacks after
                _show_popup()

        handler = FunctionEventHandler(_handler, {ACHIEVEMENT_UNLOCKED_EVENT})
        get_global_event_bus().subscribe(ACHIEVEMENT_UNLOCKED_EVENT, handler)
        self._gui_handlers[root_id] = handler


_REGISTRY: Optional[AchievementRegistry] = None


def get_achievement_registry() -> AchievementRegistry:
    """Return the singleton :class:`AchievementRegistry` instance."""

    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = AchievementRegistry()
    return _REGISTRY
