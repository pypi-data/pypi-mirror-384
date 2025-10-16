"""Registration helpers wiring logic games into the progression service."""

from __future__ import annotations

import random
from typing import Any, Dict, Iterable, List

from .lights_out import LightsOutGame
from .minesweeper.minesweeper import Difficulty as MinesweeperDifficulty
from .minesweeper.minesweeper import MinesweeperGame
from .picross import PicrossGame
from .sliding_puzzle import SlidingPuzzleGame
from .sokoban import SokobanGame

from .progression import LOGIC_PUZZLE_SERVICE, LevelPack, LogicPuzzleDefinition, PuzzleDifficulty


_REGISTERED = False


def _minesweeper_factory(params: Dict[str, Any]) -> MinesweeperGame:
    difficulty_key = params.get("difficulty", "beginner").upper()
    rows = params.get("rows")
    cols = params.get("cols")
    mines = params.get("mines")
    if rows is not None and cols is not None and mines is not None:
        return MinesweeperGame(custom_rows=int(rows), custom_cols=int(cols), custom_mines=int(mines))
    difficulty = MinesweeperDifficulty[difficulty_key]
    return MinesweeperGame(difficulty=difficulty)


def _picross_factory(params: Dict[str, Any]) -> PicrossGame:
    size = int(params.get("size", 10))
    density = float(params.get("density", 0.45))
    seed = params.get("seed")
    rng = random.Random(seed)
    solution: List[List[int]] = []
    for _ in range(size):
        row = [1 if rng.random() < density else 0 for _ in range(size)]
        solution.append(row)
    if not any(any(cell for cell in row) for row in solution):
        solution[0][0] = 1
    return PicrossGame(solution=solution)


def _sliding_factory(params: Dict[str, Any]) -> SlidingPuzzleGame:
    size = int(params.get("size", 4))
    shuffle_moves = int(params.get("shuffle_moves", size * size * 12))
    return SlidingPuzzleGame(size=size, shuffle_moves=shuffle_moves)


def _lights_out_factory(params: Dict[str, Any]) -> LightsOutGame:
    size = int(params.get("size", 5))
    scramble = int(params.get("scramble_moves", size**2))
    return LightsOutGame(size=size, scramble_moves=scramble)


def _sokoban_factory(params: Dict[str, Any]) -> SokobanGame:
    level_index = int(params.get("level_index", 0))
    custom_level = params.get("custom_level")
    if custom_level:
        layout: Iterable[str] = list(custom_level)
        return SokobanGame(custom_level=tuple(layout))
    return SokobanGame(level_index=level_index)


def register_default_logic_games() -> None:
    """Register default logic game definitions with the global service."""

    global _REGISTERED
    if _REGISTERED:
        return

    LOGIC_PUZZLE_SERVICE.register_puzzle(
        LogicPuzzleDefinition(
            game_key="logic_games.minesweeper",
            display_name="Minesweeper",
            level_packs=[
                LevelPack(
                    key="classic",
                    display_name="Classic Boards",
                    description="Standard grid sizes modelled after the classic PC release.",
                    difficulties=[
                        PuzzleDifficulty(
                            key="beginner",
                            display_name="Beginner",
                            generator=_minesweeper_factory,
                            parameters={"difficulty": "beginner"},
                        ),
                        PuzzleDifficulty(
                            key="intermediate",
                            display_name="Intermediate",
                            generator=_minesweeper_factory,
                            parameters={"difficulty": "intermediate"},
                            prerequisite_key="beginner",
                            unlock_after=3,
                        ),
                        PuzzleDifficulty(
                            key="expert",
                            display_name="Expert",
                            generator=_minesweeper_factory,
                            parameters={"difficulty": "expert"},
                            prerequisite_key="intermediate",
                            unlock_after=5,
                        ),
                    ],
                ),
                LevelPack(
                    key="custom",
                    display_name="Custom Challenges",
                    description="Larger layouts unlocked after mastering classic boards.",
                    unlock_requirement=12,
                    difficulties=[
                        PuzzleDifficulty(
                            key="mega",
                            display_name="Mega Grid",
                            generator=_minesweeper_factory,
                            parameters={"rows": 24, "cols": 24, "mines": 120},
                        ),
                    ],
                ),
            ],
        )
    )

    LOGIC_PUZZLE_SERVICE.register_puzzle(
        LogicPuzzleDefinition(
            game_key="logic_games.picross",
            display_name="Picross",
            level_packs=[
                LevelPack(
                    key="starter",
                    display_name="Starter Canvases",
                    description="Entry size picture grids for learning deduction patterns.",
                    difficulties=[
                        PuzzleDifficulty(
                            key="5x5",
                            display_name="5x5",
                            generator=_picross_factory,
                            parameters={"size": 5, "density": 0.4},
                        ),
                        PuzzleDifficulty(
                            key="10x10",
                            display_name="10x10",
                            generator=_picross_factory,
                            parameters={"size": 10, "density": 0.45},
                            prerequisite_key="5x5",
                            unlock_after=2,
                        ),
                    ],
                ),
                LevelPack(
                    key="artists",
                    display_name="Artist Sketches",
                    description="Larger canvases that unlock after clearing the fundamentals.",
                    unlock_requirement=6,
                    difficulties=[
                        PuzzleDifficulty(
                            key="15x15",
                            display_name="15x15",
                            generator=_picross_factory,
                            parameters={"size": 15, "density": 0.5},
                        ),
                    ],
                ),
            ],
        )
    )

    LOGIC_PUZZLE_SERVICE.register_puzzle(
        LogicPuzzleDefinition(
            game_key="logic_games.sliding_puzzle",
            display_name="Sliding Puzzle",
            level_packs=[
                LevelPack(
                    key="classic",
                    display_name="Classic Boards",
                    description="Scrambled numeric tiles with progressively larger grids.",
                    difficulties=[
                        PuzzleDifficulty(
                            key="3x3",
                            display_name="3x3",
                            generator=_sliding_factory,
                            parameters={"size": 3, "shuffle_moves": 80},
                        ),
                        PuzzleDifficulty(
                            key="4x4",
                            display_name="4x4",
                            generator=_sliding_factory,
                            parameters={"size": 4, "shuffle_moves": 160},
                            prerequisite_key="3x3",
                            unlock_after=3,
                        ),
                        PuzzleDifficulty(
                            key="5x5",
                            display_name="5x5",
                            generator=_sliding_factory,
                            parameters={"size": 5, "shuffle_moves": 260},
                            prerequisite_key="4x4",
                            unlock_after=5,
                        ),
                    ],
                ),
            ],
        )
    )

    LOGIC_PUZZLE_SERVICE.register_puzzle(
        LogicPuzzleDefinition(
            game_key="logic_games.lights_out",
            display_name="Lights Out",
            level_packs=[
                LevelPack(
                    key="studio",
                    display_name="Studio Fixtures",
                    description="Default boards with increasing scramble lengths.",
                    difficulties=[
                        PuzzleDifficulty(
                            key="5x5",
                            display_name="5x5",
                            generator=_lights_out_factory,
                            parameters={"size": 5},
                        ),
                        PuzzleDifficulty(
                            key="6x6",
                            display_name="6x6",
                            generator=_lights_out_factory,
                            parameters={"size": 6, "scramble_moves": 60},
                            prerequisite_key="5x5",
                            unlock_after=4,
                        ),
                    ],
                ),
            ],
        )
    )

    LOGIC_PUZZLE_SERVICE.register_puzzle(
        LogicPuzzleDefinition(
            game_key="logic_games.sokoban",
            display_name="Sokoban",
            level_packs=[
                LevelPack(
                    key="warehouse",
                    display_name="Warehouse League",
                    description="A curated set of crate logistics challenges.",
                    difficulties=[
                        PuzzleDifficulty(
                            key="training",
                            display_name="Training Floor",
                            generator=_sokoban_factory,
                            parameters={"level_index": 0},
                        ),
                        PuzzleDifficulty(
                            key="corridors",
                            display_name="Tight Corridors",
                            generator=_sokoban_factory,
                            parameters={"level_index": 1},
                            prerequisite_key="training",
                            unlock_after=2,
                        ),
                        PuzzleDifficulty(
                            key="tangle",
                            display_name="Warehouse Tangle",
                            generator=_sokoban_factory,
                            parameters={"level_index": 2},
                            prerequisite_key="corridors",
                            unlock_after=3,
                        ),
                    ],
                ),
            ],
        )
    )

    _REGISTERED = True


register_default_logic_games()


__all__ = ["register_default_logic_games"]
