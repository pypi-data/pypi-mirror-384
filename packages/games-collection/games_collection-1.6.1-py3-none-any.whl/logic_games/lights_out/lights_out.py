"""Lights Out game engine with a physically-inspired simulation.

This module contains the core logic for the Lights Out game, a classic
toggle puzzle. The implementation goes beyond a simple state machine by
simulating physical properties of light bulbs, such as brightness, energy
consumption, and ambient light reflection.

The `LightsOutGame` class serves as the main engine, managing the game state,
rules, and simulation parameters. It ensures that every puzzle is solvable
by generating scrambled boards from a solved state. The engine is designed
to be independent of the user interface, making it suitable for use in
both CLI and GUI applications.

Attributes:
    _NEIGHBOR_DELTAS: A tuple of coordinate offsets used to identify a
        bulb and its adjacent neighbors (up, down, left, right).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from common.game_engine import GameEngine, GameState

# Deltas for finding neighbors, including the bulb itself (0,0).
_NEIGHBOR_DELTAS: Tuple[Tuple[int, int], ...] = (
    (0, 0),  # The bulb itself
    (-1, 0),  # Up
    (1, 0),  # Down
    (0, -1),  # Left
    (0, 1),  # Right
)


@dataclass
class LightBulb:
    """Represents a single light bulb on the game grid.

    This class models a physical light bulb, tracking not only its on/off
    state but also its brightness and the number of times it has been
    toggled. The brightness is influenced by whether the bulb is on and
    by the ambient light from its neighbors.

    Attributes:
        is_on: True if the bulb is on, False otherwise.
        brightness: The current brightness level of the bulb (0.0 to 1.0).
        toggle_count: The number of times this bulb has been toggled.
    """

    is_on: bool = False
    brightness: float = 0.0
    toggle_count: int = 0

    def toggle(self) -> None:
        """Toggle the on/off state of the bulb and increment the toggle count."""
        self.is_on = not self.is_on
        self.toggle_count += 1


class LightsOutGame(GameEngine[Tuple[int, int], int]):
    """A Lights Out toggle puzzle with a physically-inspired simulation.

    This game engine manages the grid of light bulbs, game rules, and a
    simulation of physical properties like power consumption and brightness.
    It ensures that all generated puzzles are solvable.

    The move type is a tuple of (row, col), and the player is represented
    by an integer (0 for the single player).

    Attributes:
        size: The dimension of the square game grid.
        grid: A 2D list representing the grid of `LightBulb` instances.
        state: The current `GameState` of the puzzle.
        moves: The number of moves made by the player.
        total_time_seconds: The cumulative simulated time for all moves.
        total_energy_kwh: The total simulated energy consumed by the grid.
    """

    def __init__(
        self,
        size: int = 5,
        *,
        scramble_moves: int | None = None,
        on_brightness: float = 1.0,
        ambient_reflection: float = 0.18,
        move_duration_seconds: float = 4.5,
        bulb_wattage: float = 60.0,
        standby_wattage: float = 0.3,
        lux_per_bulb: float = 320.0,
    ) -> None:
        """Initialize the game with a given size and simulation parameters.

        Args:
            size: The size of the square grid (e.g., 5 for a 5x5 board).
            scramble_moves: The number of random moves to make to scramble
                the board. Defaults to size*size.
            on_brightness: The brightness of a bulb when it is fully on.
            ambient_reflection: The fraction of a neighbor's brightness
                that reflects onto an off bulb.
            move_duration_seconds: The simulated duration of a single move.
            bulb_wattage: The power draw of a single 'on' bulb in watts.
            standby_wattage: The power draw of a single 'off' bulb.
            lux_per_bulb: The estimated brightness in lux per unit of
                bulb brightness.
        """
        self.size = size
        self.scramble_moves = scramble_moves if scramble_moves is not None else size**2
        self.on_brightness = on_brightness
        self.ambient_reflection = ambient_reflection
        self.move_duration_seconds = move_duration_seconds
        self.bulb_wattage = bulb_wattage
        self.standby_wattage = standby_wattage
        self.lux_per_bulb = lux_per_bulb

        self.grid: List[List[LightBulb]] = []
        self.state = GameState.NOT_STARTED
        self.moves = 0
        self.total_time_seconds = 0.0
        self.total_energy_kwh = 0.0
        self._current_power_draw = 0.0

        self.reset()

    def reset(self) -> None:
        """Reset the game to a new, solvable scrambled configuration."""
        self.state = GameState.NOT_STARTED
        self.moves = 0
        self.total_time_seconds = 0.0
        self.total_energy_kwh = 0.0
        self.grid = [[LightBulb() for _ in range(self.size)] for _ in range(self.size)]

        self._scramble_grid()
        self._recalculate_brightness()
        self._current_power_draw = self.calculate_power_draw()

    def _scramble_grid(self) -> None:
        """Scramble the board by applying random valid moves from a solved state.

        This method ensures that the generated puzzle is always solvable.
        If the board is still solved after scrambling, one final toggle is
        applied to guarantee a challenge.
        """
        if self.scramble_moves <= 0:
            return

        positions = self.get_valid_moves()
        for _ in range(self.scramble_moves):
            move = random.choice(positions)
            self._apply_toggle(move)

        # Ensure the puzzle is not already solved after scrambling.
        if self.is_game_over():
            self._apply_toggle(random.choice(positions))

    def _apply_toggle(self, move: Tuple[int, int]) -> bool:
        """Toggle the targeted bulb and its orthogonal neighbors.

        Args:
            move: A tuple (row, col) indicating the target bulb.

        Returns:
            True if the move was valid and applied, False otherwise.
        """
        r, c = move
        if not (0 <= r < self.size and 0 <= c < self.size):
            return False

        for dr, dc in _NEIGHBOR_DELTAS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                self.grid[nr][nc].toggle()

        return True

    def _recalculate_brightness(self) -> None:
        """Update the brightness of all bulbs on the grid.

        A bulb's brightness depends on its on/off state and the light
        reflected from its neighbors (ambient light).
        """
        for r, row in enumerate(self.grid):
            for c, bulb in enumerate(row):
                if bulb.is_on:
                    target_brightness = self.on_brightness
                else:
                    # Calculate ambient light from neighbors.
                    neighbors_on = sum(
                        1 for dr, dc in _NEIGHBOR_DELTAS[1:] if 0 <= r + dr < self.size and 0 <= c + dc < self.size and self.grid[r + dr][c + dc].is_on
                    )
                    target_brightness = min(
                        self.on_brightness,
                        neighbors_on * self.ambient_reflection,
                    )

                bulb.brightness = max(0.0, min(self.on_brightness, target_brightness))

    def is_game_over(self) -> bool:
        """Check if the game is over (all lights are off).

        Returns:
            True if all bulbs are off, False otherwise.
        """
        return all(not bulb.is_on for row in self.grid for bulb in row)

    def get_current_player(self) -> int:
        """Return the current player. In this single-player game, it is always 0.

        Returns:
            The integer representing the current player.
        """
        return 0

    def get_valid_moves(self) -> List[Tuple[int, int]]:
        """Return a list of all valid moves (all grid coordinates).

        Returns:
            A list of (row, col) tuples representing all possible moves.
        """
        return [(r, c) for r in range(self.size) for c in range(self.size)]

    def make_move(self, move: Tuple[int, int]) -> bool:
        """Apply a player's move and update the simulation metrics.

        Args:
            move: A tuple (row, col) for the bulb to toggle.

        Returns:
            True if the move was successfully made, False otherwise.
        """
        if self.state == GameState.FINISHED:
            return False

        previous_power = self._current_power_draw
        if not self._apply_toggle(move):
            return False

        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        # Update simulation metrics based on the move.
        self.total_time_seconds += self.move_duration_seconds
        self.total_energy_kwh += (previous_power / 1000.0) * (self.move_duration_seconds / 3600.0)
        self.moves += 1

        self._recalculate_brightness()
        self._current_power_draw = self.calculate_power_draw()

        if self.is_game_over():
            self.state = GameState.FINISHED

        return True

    def calculate_power_draw(self) -> float:
        """Calculate the instantaneous power draw of the entire grid in watts.

        Returns:
            The total power consumption in watts.
        """
        power = 0.0
        for row in self.grid:
            for bulb in row:
                power += self.bulb_wattage if bulb.is_on else self.standby_wattage
        return power

    def calculate_room_brightness(self) -> float:
        """Estimate the total brightness of the room in lux.

        Returns:
            The estimated room brightness in lux.
        """
        return sum(bulb.brightness for row in self.grid for bulb in row) * self.lux_per_bulb

    def get_state_representation(self) -> Dict[str, object]:
        """Return a dictionary representing the full state of the game.

        This is useful for UIs or logging that need a snapshot of the game.

        Returns:
            A dictionary containing detailed state information.
        """
        return {
            "grid": [[bulb.is_on for bulb in row] for row in self.grid],
            "brightness": [[bulb.brightness for bulb in row] for row in self.grid],
            "moves": self.moves,
            "power_draw_w": self._current_power_draw,
            "total_energy_kwh": self.total_energy_kwh,
            "room_brightness_lux": self.calculate_room_brightness(),
        }

    def get_winner(self) -> int | None:
        """Return the winner of the game.

        In this single-player game, player 0 wins when the puzzle is solved.

        Returns:
            0 if the game is won, otherwise None.
        """
        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Return the current state of the game.

        Returns:
            The current `GameState` enum member.
        """
        return self.state
