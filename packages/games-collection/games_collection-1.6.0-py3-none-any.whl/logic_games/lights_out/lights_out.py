"""Lights Out game engine."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from common.game_engine import GameEngine, GameState

_NEIGHBOR_DELTAS: Tuple[Tuple[int, int], ...] = (
    (0, 0),
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
)


@dataclass
class LightBulb:
    """Representation of a single light bulb on the grid."""

    is_on: bool = False
    brightness: float = 0.0
    toggle_count: int = 0

    def toggle(self) -> None:
        """Toggle the state of the bulb and track wear."""
        self.is_on = not self.is_on
        self.toggle_count += 1


class LightsOutGame(GameEngine[Tuple[int, int], int]):
    """Lights Out toggle puzzle game with physical-inspired simulation."""

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
        """Initialize the game with simulation parameters."""

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
        """Reset game to a solvable scrambled configuration."""

        self.state = GameState.NOT_STARTED
        self.moves = 0
        self.total_time_seconds = 0.0
        self.total_energy_kwh = 0.0
        self.grid = [[LightBulb() for _ in range(self.size)] for _ in range(self.size)]

        self._scramble_grid()
        self._recalculate_brightness()
        self._current_power_draw = self.calculate_power_draw()

    def _scramble_grid(self) -> None:
        """Scramble the board by performing random valid moves from a solved state."""

        if self.scramble_moves <= 0:
            return

        positions = self.get_valid_moves()
        for _ in range(self.scramble_moves):
            move = random.choice(positions)
            self._apply_toggle(move)

        # Ensure the puzzle is not already solved.
        if self.is_game_over():
            self._apply_toggle(random.choice(positions))

    def _apply_toggle(self, move: Tuple[int, int]) -> bool:
        """Toggle the targeted bulb and its neighbors."""

        r, c = move
        if not (0 <= r < self.size and 0 <= c < self.size):
            return False

        for dr, dc in _NEIGHBOR_DELTAS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                self.grid[nr][nc].toggle()

        return True

    def _recalculate_brightness(self) -> None:
        """Update brightness values based on on/off state and nearby lights."""

        for r, row in enumerate(self.grid):
            for c, bulb in enumerate(row):
                if bulb.is_on:
                    target_brightness = self.on_brightness
                else:
                    neighbors_on = sum(
                        1 for dr, dc in _NEIGHBOR_DELTAS[1:] if 0 <= r + dr < self.size and 0 <= c + dc < self.size and self.grid[r + dr][c + dc].is_on
                    )
                    target_brightness = min(
                        self.on_brightness,
                        neighbors_on * self.ambient_reflection,
                    )

                bulb.brightness = max(0.0, min(self.on_brightness, target_brightness))

    def is_game_over(self) -> bool:
        """Check if all lights are off."""

        return all(not bulb.is_on for row in self.grid for bulb in row)

    def get_current_player(self) -> int:
        """Get current player (single-player game)."""

        return 0

    def get_valid_moves(self) -> List[Tuple[int, int]]:
        """Get all valid coordinates on the board."""

        return [(r, c) for r in range(self.size) for c in range(self.size)]

    def make_move(self, move: Tuple[int, int]) -> bool:
        """Apply a move, updating simulation metrics along the way."""

        if self.state == GameState.FINISHED:
            return False

        previous_power = self._current_power_draw
        if not self._apply_toggle(move):
            return False

        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        self.total_time_seconds += self.move_duration_seconds
        self.total_energy_kwh += (previous_power / 1000.0) * (self.move_duration_seconds / 3600.0)
        self.moves += 1

        self._recalculate_brightness()
        self._current_power_draw = self.calculate_power_draw()

        if self.is_game_over():
            self.state = GameState.FINISHED

        return True

    def calculate_power_draw(self) -> float:
        """Calculate the instantaneous power draw of the grid in watts."""

        power = 0.0
        for row in self.grid:
            for bulb in row:
                power += self.bulb_wattage if bulb.is_on else self.standby_wattage
        return power

    def calculate_room_brightness(self) -> float:
        """Estimate total room brightness in lux."""

        return sum(bulb.brightness for row in self.grid for bulb in row) * self.lux_per_bulb

    def get_state_representation(self) -> Dict[str, object]:
        """Provide a structured representation of the current game state."""

        return {
            "grid": [[bulb.is_on for bulb in row] for row in self.grid],
            "brightness": [[bulb.brightness for bulb in row] for row in self.grid],
            "moves": self.moves,
            "power_draw_w": self._current_power_draw,
            "total_energy_kwh": self.total_energy_kwh,
            "room_brightness_lux": self.calculate_room_brightness(),
        }

    def get_winner(self) -> int | None:
        """Get winner (player 0 wins when puzzle is solved)."""

        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Get current game state.

        Returns:
            Current state of the game
        """

        return self.state
