"""Sokoban game engine with authentic warehouse-style behavior.

This module provides a feature-rich Sokoban engine that models the classic
warehouse puzzle, where a worker pushes crates onto designated storage goals.
The engine supports multiple handcrafted levels, undo functionality, accurate
goal tracking, and detailed move statistics.

This implementation is designed to be independent of the user interface,
making it suitable for both command-line and graphical front-ends.

Classes:
    SokobanGame: The main game engine for Sokoban puzzles.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple, cast

from common.game_engine import GameEngine, GameState


class SokobanGame(GameEngine[str, int]):
    """The game engine for the Sokoban box-pushing puzzle.

    The game uses the standard set of Sokoban symbols to represent the
    game board and its elements:

    - ``#``: A wall tile that blocks movement.
    - ``@``: The player on a regular floor tile.
    - ``+``: The player standing on a goal tile.
    - ``$``: A crate on a regular floor tile.
    - ``*``: A crate resting on a goal tile.
    - ``.``: An empty goal tile.
    - `` `` (space): A walkable floor tile.

    Attributes:
        moves: The total number of moves made by the player in the current level.
        pushes: The number of moves that involved pushing a crate.
        level_index: The index of the currently loaded built-in level.
            This is -1 for custom levels.
        level_name: The display name of the active level.
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
        """Initialize the Sokoban game engine.

        Args:
            level_index: The index of the predefined level to load.
            custom_level: An optional custom level layout that overrides
                the `level_index`.

        Raises:
            ValueError: If the provided `level_index` is invalid or the
                level layout is malformed.
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
        """Load one of the predefined Sokoban levels by its index.

        Args:
            level_index: The index of the desired level in the `LEVELS` list.

        Raises:
            ValueError: If the `level_index` is outside the valid range.
        """
        if not (0 <= level_index < len(self.LEVELS)):
            raise ValueError(f"Level index {level_index} is out of range.")

        data = self.LEVELS[level_index]
        self.level_index = level_index
        self.level_name = str(data["name"])
        self._set_base_layout(tuple(data["layout"]))
        self.reset()

    def get_board(self) -> List[str]:
        """Return a snapshot of the current board state as a list of strings."""
        return ["".join(row) for row in self.grid]

    def undo_last_move(self) -> bool:
        """Revert the game state to before the most recent move.

        Returns:
            True if a move was successfully undone, False otherwise.
        """
        if not self.history:
            return False

        snapshot = self.history.pop()
        self._apply_snapshot(snapshot)
        return True

    def is_game_over(self) -> bool:
        """Return True if every goal tile is occupied by a crate."""
        return all(self.grid[r][c] == "*" for r, c in self.goal_positions)

    def get_current_player(self) -> int:
        """Return the identifier of the current player (always 0 for Sokoban)."""
        return 0

    def get_valid_moves(self) -> List[str]:
        """Return a list of all currently legal movement directions.

        Returns:
            A list of strings representing the valid directions ('u', 'd', 'l', 'r').
        """
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
            move: A string representing the direction ('u', 'd', 'l', or 'r').

        Returns:
            True if the move was valid and performed, False otherwise.
        """
        if move not in self.DIRECTIONS or self.state == GameState.FINISHED:
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
        """Return the player identifier if the puzzle is solved.

        Returns:
            0 if the game is won, otherwise None.
        """
        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Return the current `GameState` of the puzzle."""
        return self.state

    def _set_base_layout(self, layout: Sequence[str]) -> None:
        """Store the base layout to be used for resetting the level."""
        self._base_layout = layout

    def _build_grid(self, layout: Sequence[str]) -> None:
        """Construct the internal grid from a textual level layout.

        Args:
            layout: A sequence of strings representing the level.

        Raises:
            ValueError: If the layout is malformed (e.g., no player,
                mismatched box/goal counts).
        """
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
        """Determine if the player can move to the target, considering pushes."""
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
        """Push a box if one exists at the target position."""
        tile = self.grid[box_position[0]][box_position[1]]
        if tile not in self.BOX_TILES:
            return False

        destination = self._offset_position(box_position, direction)
        self._move_box(box_position, destination)
        return True

    def _move_box(self, source: Tuple[int, int], destination: Tuple[int, int]) -> None:
        """Move a crate from a source to a destination, updating tiles."""
        dest_tile = "*" if destination in self.goal_positions else "$"
        self.grid[destination[0]][destination[1]] = dest_tile
        self.grid[source[0]][source[1]] = "." if source in self.goal_positions else " "

    def _move_player(self, destination: Tuple[int, int]) -> None:
        """Move the player to a new destination, updating tiles."""
        pr, pc = self.player_pos
        self.grid[pr][pc] = "." if (pr, pc) in self.goal_positions else " "
        self.grid[destination[0]][destination[1]] = "+" if destination in self.goal_positions else "@"
        self.player_pos = destination

    def _can_push_box(self, destination: Tuple[int, int]) -> bool:
        """Return True if a crate can be pushed into the destination tile."""
        if not self._is_within_bounds(destination):
            return False

        tile = self.grid[destination[0]][destination[1]]
        return tile not in self.BOX_TILES and tile != "#"

    def _is_within_bounds(self, position: Tuple[int, int]) -> bool:
        """Check if a position is within the valid board boundaries."""
        rows = len(self.grid)
        if rows == 0:
            return False
        cols = len(self.grid[0])
        return 0 <= position[0] < rows and 0 <= position[1] < cols

    def _offset_position(self, position: Tuple[int, int], direction: Tuple[int, int]) -> Tuple[int, int]:
        """Calculate a new position by applying a directional offset."""
        return position[0] + direction[0], position[1] + direction[1]

    def _snapshot_state(self) -> Dict[str, object]:
        """Capture a snapshot of the mutable game state for the undo history."""
        return {
            "grid": [row.copy() for row in self.grid],
            "player_pos": self.player_pos,
            "moves": self.moves,
            "pushes": self.pushes,
            "state": self.state,
        }

    def _apply_snapshot(self, snapshot: Dict[str, object]) -> None:
        """Restore the game state from a snapshot."""
        grid_snapshot = cast(List[List[str]], snapshot["grid"])
        self.grid = [row.copy() for row in grid_snapshot]
        self.player_pos = cast(Tuple[int, int], snapshot["player_pos"])
        self.moves = cast(int, snapshot["moves"])
        self.pushes = cast(int, snapshot["pushes"])
        self.state = cast(GameState, snapshot["state"])
