"""Game engine and logic for Battleship with a hunting AI opponent.

This module provides the core game logic for Battleship, including ship placement,
shot validation, and an AI opponent that uses a hunting strategy to find and
sink ships efficiently.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Iterable, List, Optional, Sequence, Set, Tuple

# Type alias for a coordinate tuple.
Coordinate = Tuple[int, int]


@dataclass
class Ship:
    """Representation of a single ship on the board."""

    name: str
    length: int
    coordinates: Set[Coordinate]
    hits: Set[Coordinate] = field(default_factory=set)

    def register_hit(self, coord: Coordinate) -> None:
        """Registers a hit on the ship."""
        self.hits.add(coord)

    @property
    def is_sunk(self) -> bool:
        """Checks if the ship has been sunk."""
        return len(self.hits) == len(self.coordinates)


class Board:
    """Board that tracks ships, shots, and rendering."""

    def __init__(self, size: int) -> None:
        """Initializes the board with a given size."""
        if size < 4:
            raise ValueError("Board must be at least 4x4.")
        self.size = size
        self.ships: List[Ship] = []
        self.occupied: Set[Coordinate] = set()
        self.shots: Dict[Coordinate, str] = {}

    def in_bounds(self, coord: Coordinate) -> bool:
        """Checks if a coordinate is within the board's bounds."""
        row, col = coord
        return 0 <= row < self.size and 0 <= col < self.size

    def place_ship(self, name: str, length: int, start: Coordinate, orientation: str) -> None:
        """Places a ship on the board."""
        orientation = orientation.lower()
        if orientation not in {"h", "v"}:
            raise ValueError("Orientation must be 'h' or 'v'.")
        row, col = start
        # Determine all coordinates the ship will occupy.
        if orientation == "h":
            coords = {(row, col + offset) for offset in range(length)}
        else:
            coords = {(row + offset, col) for offset in range(length)}
        # Check if the ship is out of bounds or overlaps with another ship.
        if not all(self.in_bounds(coord) for coord in coords):
            raise ValueError("Ship placement is out of bounds.")
        if any(coord in self.occupied for coord in coords):
            raise ValueError("Ships cannot overlap.")
        # Create the ship and add it to the board.
        ship = Ship(name=name, length=length, coordinates=coords)
        self.ships.append(ship)
        self.occupied.update(coords)

    def randomly_place_ships(self, ships: Sequence[Tuple[str, int]], rng: random.Random) -> None:
        """Randomly places ships on the board."""
        for name, length in ships:
            placed = False
            attempts = 0
            while not placed:
                attempts += 1
                if attempts > 1000:
                    raise RuntimeError("Failed to place ships without overlap.")
                # Choose a random orientation and starting coordinate.
                orientation = rng.choice(["h", "v"])
                row = rng.randrange(self.size)
                col = rng.randrange(self.size)
                try:
                    self.place_ship(name, length, (row, col), orientation)
                except ValueError:
                    continue
                placed = True

    def receive_shot(self, coord: Coordinate) -> Tuple[str, Optional[str]]:
        """Receives a shot at a given coordinate."""
        if not self.in_bounds(coord):
            raise ValueError("Shot outside the board.")
        if coord in self.shots:
            raise ValueError("Coordinate has already been targeted.")
        # Check if the shot hit any ship.
        for ship in self.ships:
            if coord in ship.coordinates:
                ship.register_hit(coord)
                result = "sunk" if ship.is_sunk else "hit"
                self.shots[coord] = result
                return result, ship.name
        # If no ship was hit, it's a miss.
        self.shots[coord] = "miss"
        return "miss", None

    def all_sunk(self) -> bool:
        """Checks if all ships on the board have been sunk."""
        return all(ship.is_sunk for ship in self.ships)

    def render(self, *, show_ships: bool = False) -> str:
        """Renders the board as a string."""
        header = "   " + " ".join(f"{col:2}" for col in range(self.size))
        rows = [header]
        for row in range(self.size):
            cells: List[str] = []
            for col in range(self.size):
                coord = (row, col)
                # Determine the marker for the current cell.
                if coord in self.shots:
                    marker = self.shots[coord]
                    if marker == "miss":
                        cells.append("o")
                    elif marker == "hit":
                        cells.append("X")
                    else:  # sunk
                        cells.append("X")
                elif show_ships and coord in self.occupied:
                    cells.append("█")
                else:
                    cells.append("~")
            rows.append(f"{row:2} " + "  ".join(cells))
        return "\n".join(rows)


# Default fleet of ships for a standard game of Battleship.
DEFAULT_FLEET: Tuple[Tuple[str, int], ...] = (
    ("Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
)

# Extended fleet with more ship types
EXTENDED_FLEET: Tuple[Tuple[str, int], ...] = (
    ("Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
    ("Patrol Boat", 2),
    ("Frigate", 3),
)

# Small fleet for 8x8 boards
SMALL_FLEET: Tuple[Tuple[str, int], ...] = (
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
)


class BattleshipGame:
    """Full Battleship game against a computer opponent."""

    def __init__(
        self,
        *,
        size: int = 10,
        fleet: Sequence[Tuple[str, int]] = DEFAULT_FLEET,
        rng: Optional[random.Random] = None,
        difficulty: str = "medium",
        two_player: bool = False,
        salvo_mode: bool = False,
    ) -> None:
        """Initializes the game with a given size, fleet, and random number generator.

        Args:
            size: Board size (e.g., 8 for 8x8, 10 for 10x10)
            fleet: Sequence of (ship_name, ship_length) tuples
            rng: Random number generator for reproducible games
            difficulty: AI difficulty level ("easy", "medium", "hard")
            two_player: If True, enables 2-player hot-seat mode (no AI)
            salvo_mode: If True, allows multiple shots per turn based on remaining ships
        """
        self.rng = rng or random.Random()
        self.size = size
        self.fleet = tuple(fleet)
        self.difficulty = difficulty
        self.two_player = two_player
        self.salvo_mode = salvo_mode
        self.player_board = Board(size)
        self.opponent_board = Board(size)
        coords = [(r, c) for r in range(size) for c in range(size)]
        self.rng.shuffle(coords)
        # AI hunting strategy: check even/odd coordinates first.
        self._ai_hunt_even: List[Coordinate] = [coord for coord in coords if (coord[0] + coord[1]) % 2 == 0]
        self._ai_hunt_odd: List[Coordinate] = [coord for coord in coords if (coord[0] + coord[1]) % 2 == 1]
        self._ai_targets: Deque[Coordinate] = deque()

    def setup_random(self) -> None:
        """Sets up the game with randomly placed ships for both player and opponent."""
        self.player_board.randomly_place_ships(self.fleet, self.rng)
        self.opponent_board.randomly_place_ships(self.fleet, self.rng)

    def setup_player_ships(
        self,
        placements: Iterable[Tuple[str, int, Coordinate, str]],
    ) -> None:
        """Sets up the player's ships based on the given placements."""
        for name, length in self.fleet:
            matching = [p for p in placements if p[0] == name]
            if not matching:
                raise ValueError(f"Placement missing for ship '{name}'.")
            ship_name, ship_length, start, orientation = matching[0]
            if ship_length != length:
                raise ValueError(f"Incorrect length for ship '{name}'.")
            self.player_board.place_ship(ship_name, ship_length, start, orientation)
        self.opponent_board.randomly_place_ships(self.fleet, self.rng)

    def player_shoot(self, coord: Coordinate) -> Tuple[str, Optional[str]]:
        """Player shoots at the opponent's board."""
        result, ship_name = self.opponent_board.receive_shot(coord)
        return result, ship_name

    def ai_shoot(self) -> Tuple[Coordinate, str, Optional[str]]:
        """AI shoots at the player's board."""
        # Easy difficulty: just random shots
        if self.difficulty == "easy":
            available = [(r, c) for r in range(self.size) for c in range(self.size) if (r, c) not in self.player_board.shots]
            if not available:
                raise RuntimeError("AI has no available shots left.")
            target = self.rng.choice(available)
        else:
            # Medium/Hard difficulty: use hunting strategy
            # Hard difficulty: always prioritize targets, medium: 70% of the time
            should_hunt = self.difficulty == "hard" or (self.difficulty == "medium" and self.rng.random() < 0.7)

            # Prioritize targets in the queue.
            if should_hunt and self._ai_targets:
                while self._ai_targets:
                    target = self._ai_targets.popleft()
                    if target in self.player_board.shots:
                        continue
                    break
                else:
                    target = self._get_hunt_target()
            else:
                target = self._get_hunt_target()

        result, ship_name = self.player_board.receive_shot(target)
        # If it's a hit, add neighboring cells to the target queue.
        if result in {"hit", "sunk"}:
            self._enqueue_targets(target)
        # If a ship is sunk, remove invalid targets from the queue.
        if result == "sunk":
            self._flush_invalid_targets()
        return target, result, ship_name

    def _get_hunt_target(self) -> Coordinate:
        """Gets the next hunting target for the AI."""
        # If no targets, fall back to hunting mode.
        if self._ai_hunt_even:
            return self._ai_hunt_even.pop()
        elif self._ai_hunt_odd:
            return self._ai_hunt_odd.pop()
        else:
            raise RuntimeError("AI has no available shots left.")

    def _enqueue_targets(self, coord: Coordinate) -> None:
        """Adds neighboring cells to the AI's target queue."""
        row, col = coord
        neighbors = [
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ]
        for neighbor in neighbors:
            if self.player_board.in_bounds(neighbor) and neighbor not in self.player_board.shots and neighbor not in self._ai_targets:
                self._ai_targets.append(neighbor)

    def _flush_invalid_targets(self) -> None:
        """Removes invalid targets from the AI's target queue."""
        self._ai_targets = deque(coord for coord in self._ai_targets if coord not in self.player_board.shots)

    def render(self) -> str:
        """Renders both the player's and opponent's boards."""
        player = self.player_board.render(show_ships=True)
        opponent = self.opponent_board.render(show_ships=False)
        divider = "\n" + "=" * (self.size * 3) + "\n"
        return f"Your Fleet:\n{player}{divider}Enemy Waters:\n{opponent}"

    def player_has_lost(self) -> bool:
        """Checks if the player has lost the game."""
        return self.player_board.all_sunk()

    def opponent_has_lost(self) -> bool:
        """Checks if the opponent has lost the game."""
        return self.opponent_board.all_sunk()

    def get_salvo_count(self, player: str = "player") -> int:
        """Returns the number of shots available in salvo mode.

        Args:
            player: "player" or "opponent" to count their remaining ships

        Returns:
            Number of unsunk ships (number of shots in salvo mode)
        """
        board = self.player_board if player == "player" else self.opponent_board
        return sum(1 for ship in board.ships if not ship.is_sunk)
