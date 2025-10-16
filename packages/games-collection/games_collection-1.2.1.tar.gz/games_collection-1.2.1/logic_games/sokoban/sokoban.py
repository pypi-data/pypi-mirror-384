"""Sokoban game engine with authentic warehouse-style behaviour.

This module implements a feature-rich Sokoban engine that models classic
warehouse puzzles where a porter pushes crates onto designated storage spots.
It supports multiple handcrafted levels, undo functionality, accurate goal
tracking, and detailed move statistics to deliver a realistic Sokoban
experience for the command-line interface and potential future front ends.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple, cast

from common.game_engine import GameEngine, GameState


class SokobanGame(GameEngine[str, int]):
    """Sokoban box-pushing puzzle game engine.

    The game uses the standard Sokoban symbols:

    * ``#`` – wall tiles that block movement
    * ``@`` – player on a floor tile
    * ``+`` – player standing on a goal tile
    * ``$`` – crate on a floor tile
    * ``*`` – crate sitting on a goal tile
    * ``.`` – empty goal tile
    * `` `` (space) – walkable floor tile

    Attributes:
        moves: Total number of moves the player has taken on the current level
        pushes: Number of moves that involved pushing a crate
        level_index: Index of the currently loaded built-in level (-1 for custom)
        level_name: Friendly name of the active level
    """

    LEVELS: Tuple[Dict[str, Sequence[str]], ...] = (
        {
            "name": "Training Floor",
            "layout": (
                "######",
                "# .  #",
                "# $$ #",
                "#  @ #",
                "# .  #",
                "######",
            ),
        },
        {
            "name": "Tight Corridors",
            "layout": (
                "########",
                "#  .  #",
                "# $$# #",
                "#  .  #",
                "# #$# #",
                "#  @  #",
                "#  .  #",
                "########",
            ),
        },
        {
            "name": "Warehouse Tangle",
            "layout": (
                "    ######",
                "#### #   #",
                "#  ### # #",
                "# $  . . #",
                "## # $ $##",
                "#  .#@#. #",
                "# $ $ # ##",
                "# . .  $ #",
                "##########",
            ),
        },
    )

    PLAYER_TILES = {"@", "+"}
    BOX_TILES = {"$", "*"}
    GOAL_TILES = {".", "+", "*"}
    FLOOR_TILES = {" ", "."}
    DIRECTIONS: Dict[str, Tuple[int, int]] = {"u": (-1, 0), "d": (1, 0), "l": (0, -1), "r": (0, 1)}

    def __init__(self, level_index: int = 0, custom_level: Sequence[str] | None = None) -> None:
        """Initialise the Sokoban game engine.

        Args:
            level_index: Index of the predefined level to load.
            custom_level: Optional custom level layout that overrides ``level_index``.

        Raises:
            ValueError: If the provided ``level_index`` is invalid or the layout is malformed.
        """

        self.moves = 0
        self.pushes = 0
        self.history: List[Dict[str, object]] = []
        self.goal_positions: set[Tuple[int, int]] = set()
        self.level_index = -1
        self.level_name = "Custom Level"
        self._base_layout: Sequence[str] = ()

        if custom_level is not None:
            self._set_base_layout(tuple(custom_level))
            self.reset()
        else:
            self.load_level(level_index)

    def reset(self) -> None:
        """Reset the active level to its original configuration."""

        self.state = GameState.NOT_STARTED
        self.moves = 0
        self.pushes = 0
        self.history = []
        self._build_grid(self._base_layout)

    def load_level(self, level_index: int) -> None:
        """Load one of the predefined Sokoban levels by index.

        Args:
            level_index: Position within :data:`LEVELS` identifying the desired level.

        Raises:
            ValueError: If ``level_index`` is outside the available range.
        """

        if level_index < 0 or level_index >= len(self.LEVELS):
            raise ValueError(f"Level index {level_index} is out of range.")

        data = self.LEVELS[level_index]
        self.level_index = level_index
        self.level_name = data["name"]
        self._set_base_layout(tuple(data["layout"]))
        self.reset()

    def get_board(self) -> List[str]:
        """Return a snapshot of the current board state as strings."""

        return ["".join(row) for row in self.grid]

    def undo_last_move(self) -> bool:
        """Revert the game state to the position before the most recent move."""

        if not self.history:
            return False

        snapshot = self.history.pop()
        self._apply_snapshot(snapshot)
        return True

    def is_game_over(self) -> bool:
        """Check whether every goal tile is occupied by a crate or the player."""

        return all(self.grid[r][c] in {"*", "+"} for r, c in self.goal_positions)

    def get_current_player(self) -> int:
        """Return the identifier of the current player (always zero for Sokoban)."""

        return 0

    def get_valid_moves(self) -> List[str]:
        """Return a list of movement directions that are currently legal."""

        if self.state == GameState.FINISHED:
            return []

        valid_moves: List[str] = []
        for key, vector in self.DIRECTIONS.items():
            target = self._offset_position(self.player_pos, vector)
            if self._can_step(target, vector):
                valid_moves.append(key)
        return valid_moves

    def make_move(self, move: str) -> bool:
        """Attempt to move the player in the specified direction.

        Args:
            move: One of ``"u"``, ``"d"``, ``"l"``, or ``"r"`` representing up, down, left, or right.

        Returns:
            True if the move was performed; False if it was invalid or would cause an illegal push.
        """

        if move not in self.DIRECTIONS:
            return False
        if self.state == GameState.FINISHED:
            return False

        direction = self.DIRECTIONS[move]
        target = self._offset_position(self.player_pos, direction)
        if not self._can_step(target, direction):
            return False

        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        self.history.append(self._snapshot_state())
        pushed = self._prepare_box_move(target, direction)
        self._move_player(target)

        self.moves += 1
        if pushed:
            self.pushes += 1

        if self.is_game_over():
            self.state = GameState.FINISHED

        return True

    def get_winner(self) -> int | None:
        """Return the player identifier if the puzzle is solved, otherwise ``None``."""

        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Return the :class:`~common.game_engine.GameState` describing the game status."""

        return self.state

    def _set_base_layout(self, layout: Sequence[str]) -> None:
        """Store the base layout that will be used on reset."""

        self._base_layout = layout

    def _build_grid(self, layout: Sequence[str]) -> None:
        """Construct the internal grid representation from the textual layout."""

        if not layout:
            raise ValueError("Level layout must contain at least one row.")

        width = max(len(row) for row in layout)
        grid: List[List[str]] = []
        goals: set[Tuple[int, int]] = set()
        player_position: Tuple[int, int] | None = None
        box_count = 0

        for r, row in enumerate(layout):
            padded_row = row.ljust(width)
            grid_row = list(padded_row)
            for c, cell in enumerate(grid_row):
                if cell in self.PLAYER_TILES:
                    if player_position is not None:
                        raise ValueError("Level must contain exactly one player.")
                    player_position = (r, c)
                if cell in self.GOAL_TILES:
                    goals.add((r, c))
                if cell in self.BOX_TILES:
                    box_count += 1
            grid.append(grid_row)

        if player_position is None:
            raise ValueError("Level must define a player start position.")
        if not goals:
            raise ValueError("Level must include at least one goal tile.")
        if box_count == 0:
            raise ValueError("Level must contain at least one crate.")
        if box_count != len(goals):
            raise ValueError("Number of crates must match number of goal tiles for a valid level.")

        self.grid = grid
        self.player_pos = player_position
        self.goal_positions = goals

    def _find_player(self) -> Tuple[int, int]:
        """Return the current player position (legacy helper for tests)."""

        return self.player_pos

    def _can_step(self, target: Tuple[int, int], direction: Tuple[int, int]) -> bool:
        """Determine if the player can move into ``target`` considering pushes."""

        if not self._is_within_bounds(target):
            return False

        tile = self.grid[target[0]][target[1]]
        if tile == "#":
            return False
        if tile in self.BOX_TILES:
            destination = self._offset_position(target, direction)
            return self._can_push_box(destination)
        return tile in self.FLOOR_TILES or target in self.goal_positions

    def _prepare_box_move(self, box_position: Tuple[int, int], direction: Tuple[int, int]) -> bool:
        """Push a box if the target tile currently holds one."""

        tile = self.grid[box_position[0]][box_position[1]]
        if tile not in self.BOX_TILES:
            return False

        destination = self._offset_position(box_position, direction)
        self._move_box(box_position, destination)
        return True

    def _move_box(self, source: Tuple[int, int], destination: Tuple[int, int]) -> None:
        """Move a crate from ``source`` to ``destination`` updating goal markers."""

        dest_tile = "*" if destination in self.goal_positions else "$"
        self.grid[destination[0]][destination[1]] = dest_tile
        self.grid[source[0]][source[1]] = "." if source in self.goal_positions else " "

    def _move_player(self, destination: Tuple[int, int]) -> None:
        """Place the player on ``destination`` updating the previous tile."""

        pr, pc = self.player_pos
        self.grid[pr][pc] = "." if (pr, pc) in self.goal_positions else " "
        self.grid[destination[0]][destination[1]] = "+" if destination in self.goal_positions else "@"
        self.player_pos = destination

    def _can_push_box(self, destination: Tuple[int, int]) -> bool:
        """Return True if a crate can be pushed into ``destination``."""

        if not self._is_within_bounds(destination):
            return False

        tile = self.grid[destination[0]][destination[1]]
        if tile in self.BOX_TILES or tile == "#":
            return False
        return tile in self.FLOOR_TILES or destination in self.goal_positions

    def _is_within_bounds(self, position: Tuple[int, int]) -> bool:
        """Check whether ``position`` refers to a valid tile on the board."""

        rows = len(self.grid)
        if rows == 0:
            return False
        cols = len(self.grid[0])
        return 0 <= position[0] < rows and 0 <= position[1] < cols

    def _offset_position(self, position: Tuple[int, int], direction: Tuple[int, int]) -> Tuple[int, int]:
        """Return a new position by applying ``direction`` to ``position``."""

        return position[0] + direction[0], position[1] + direction[1]

    def _snapshot_state(self) -> Dict[str, object]:
        """Capture a snapshot of the mutable game state."""

        return {
            "grid": [row.copy() for row in self.grid],
            "player_pos": self.player_pos,
            "moves": self.moves,
            "pushes": self.pushes,
            "state": self.state,
        }

    def _apply_snapshot(self, snapshot: Dict[str, object]) -> None:
        """Restore the game state from ``snapshot``."""

        grid_snapshot = cast(List[List[str]], snapshot["grid"])
        self.grid = [row.copy() for row in grid_snapshot]
        self.player_pos = cast(Tuple[int, int], snapshot["player_pos"])
        self.moves = cast(int, snapshot["moves"])
        self.pushes = cast(int, snapshot["pushes"])
        self.state = cast(GameState, snapshot["state"])
