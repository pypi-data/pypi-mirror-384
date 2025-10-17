"""Game engine and logic for Battleship with a hunting AI opponent.

This module provides the core game logic for Battleship, including ship placement,
shot validation, and an AI opponent that uses a "hunt and target" strategy to
find and sink ships efficiently. It supports various board sizes, fleet
configurations, and game modes like salvo mode.

The main classes in this module are:
- `Ship`: Represents a single ship with its name, length, and hit status.
- `Board`: Manages the game board, including ship placement, shot tracking,
  and rendering.
- `BattleshipGame`: Orchestrates the entire game, managing the player and
  opponent boards, AI logic, and game state.

The AI's strategy involves:
1. **Hunting**: Systematically checking coordinates (e.g., in a checkerboard
   pattern) to find a ship.
2. **Targeting**: Once a hit is registered, creating a queue of adjacent
   coordinates to explore and sink the ship.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Iterable, List, Optional, Sequence, Set, Tuple

# A type alias for a coordinate tuple (row, column) for clarity.
Coordinate = Tuple[int, int]


@dataclass
class Ship:
    """Represents a single ship on the game board.

    This class tracks the ship's name, length, the coordinates it occupies,
    and which of those coordinates have been hit.

    Attributes:
        name (str): The name of the ship (e.g., "Carrier").
        length (int): The number of cells the ship occupies.
        coordinates (Set[Coordinate]): The set of coordinates the ship occupies.
        hits (Set[Coordinate]): The set of coordinates that have been hit.
    """

    name: str
    length: int
    coordinates: Set[Coordinate]
    hits: Set[Coordinate] = field(default_factory=set)

    def register_hit(self, coord: Coordinate) -> None:
        """Registers a hit on one of the ship's coordinates.

        Args:
            coord (Coordinate): The coordinate that was hit.
        """
        self.hits.add(coord)

    @property
    def is_sunk(self) -> bool:
        """Checks if the ship has been completely sunk.

        A ship is sunk if the number of hits equals its length.

        Returns:
            bool: True if the ship is sunk, False otherwise.
        """
        return len(self.hits) == len(self.coordinates)


class Board:
    """Manages the game board, including ships, shots, and rendering.

    This class is responsible for placing ships, receiving shots, and
    providing a visual representation of the board state.
    """

    def __init__(self, size: int) -> None:
        """Initializes the board with a given size.

        Args:
            size (int): The width and height of the board.

        Raises:
            ValueError: If the board size is less than 4.
        """
        if size < 4:
            raise ValueError("Board must be at least 4x4.")
        self.size = size
        self.ships: List[Ship] = []
        self.occupied: Set[Coordinate] = set()
        self.shots: Dict[Coordinate, str] = {}

    def in_bounds(self, coord: Coordinate) -> bool:
        """Checks if a coordinate is within the board's boundaries.

        Args:
            coord (Coordinate): The coordinate to check.

        Returns:
            bool: True if the coordinate is in bounds, False otherwise.
        """
        row, col = coord
        return 0 <= row < self.size and 0 <= col < self.size

    def place_ship(self, name: str, length: int, start: Coordinate, orientation: str) -> None:
        """Places a single ship on the board.

        Args:
            name (str): The name of the ship.
            length (int): The length of the ship.
            start (Coordinate): The starting coordinate (top-left) of the ship.
            orientation (str): The orientation of the ship ('h' for horizontal,
                               'v' for vertical).

        Raises:
            ValueError: If the orientation is invalid, the placement is out of
                        bounds, or it overlaps with another ship.
        """
        orientation = orientation.lower()
        if orientation not in {"h", "v"}:
            raise ValueError("Orientation must be 'h' or 'v'.")
        row, col = start
        # Determine all coordinates the ship will occupy based on its orientation.
        if orientation == "h":
            coords = {(row, col + offset) for offset in range(length)}
        else:
            coords = {(row + offset, col) for offset in range(length)}
        # Validate that the ship is within bounds and does not overlap with others.
        if not all(self.in_bounds(coord) for coord in coords):
            raise ValueError("Ship placement is out of bounds.")
        if any(coord in self.occupied for coord in coords):
            raise ValueError("Ships cannot overlap.")
        # Create the ship and add it to the board.
        ship = Ship(name=name, length=length, coordinates=coords)
        self.ships.append(ship)
        self.occupied.update(coords)

    def randomly_place_ships(self, ships: Sequence[Tuple[str, int]], rng: random.Random) -> None:
        """Randomly places a fleet of ships on the board.

        This method attempts to place each ship in a random position and
        orientation until a valid placement is found.

        Args:
            ships (Sequence[Tuple[str, int]]): A sequence of (name, length) tuples
                                               for the ships to be placed.
            rng (random.Random): The random number generator to use.

        Raises:
            RuntimeError: If it fails to place all ships after many attempts.
        """
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
                    continue  # Try again if placement is invalid.
                placed = True

    def receive_shot(self, coord: Coordinate) -> Tuple[str, Optional[str]]:
        """Receives a shot at a given coordinate and determines the result.

        Args:
            coord (Coordinate): The coordinate being targeted.

        Returns:
            Tuple[str, Optional[str]]: A tuple containing the result of the shot
                                       ("hit", "miss", or "sunk") and the name of
                                       the ship that was hit, if any.

        Raises:
            ValueError: If the shot is out of bounds or has already been made.
        """
        if not self.in_bounds(coord):
            raise ValueError("Shot outside the board.")
        if coord in self.shots:
            raise ValueError("Coordinate has already been targeted.")
        # Check if the shot hit any of the ships on the board.
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
        """Checks if all ships on the board have been sunk.

        Returns:
            bool: True if all ships are sunk, False otherwise.
        """
        return all(ship.is_sunk for ship in self.ships)

    def render(self, *, show_ships: bool = False) -> str:
        """Renders the board as a formatted string for display.

        Args:
            show_ships (bool): If True, displays the positions of the ships on
                               the board. This is typically used for the player's
                               own board.

        Returns:
            str: A string representation of the board.
        """
        header = "   " + " ".join(f"{col:2}" for col in range(self.size))
        rows = [header]
        for row in range(self.size):
            cells: List[str] = []
            for col in range(self.size):
                coord = (row, col)
                # Determine the appropriate marker for each cell.
                if coord in self.shots:
                    marker = self.shots[coord]
                    if marker == "miss":
                        cells.append("o")  # Miss
                    elif marker == "hit":
                        cells.append("X")  # Hit
                    else:  # Sunk
                        cells.append("X")
                elif show_ships and coord in self.occupied:
                    cells.append("█")  # Ship
                else:
                    cells.append("~")  # Water
            rows.append(f"{row:2} " + "  ".join(cells))
        return "\n".join(rows)


# A tuple defining the default fleet of ships for a standard game of Battleship.
DEFAULT_FLEET: Tuple[Tuple[str, int], ...] = (
    ("Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
)

# An extended fleet with more ship types for larger games.
EXTENDED_FLEET: Tuple[Tuple[str, int], ...] = (
    ("Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
    ("Patrol Boat", 2),
    ("Frigate", 3),
)

# A smaller fleet suitable for 8x8 boards.
SMALL_FLEET: Tuple[Tuple[str, int], ...] = (
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
)


class BattleshipGame:
    """Orchestrates a full game of Battleship against a computer opponent.

    This class manages the game state, including both the player's and the
    opponent's boards, and controls the AI's behavior based on the selected
    difficulty level.
    """

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
        """Initializes the game with a given size, fleet, and other settings.

        Args:
            size (int): The size of the game board (e.g., 8 for 8x8).
            fleet (Sequence[Tuple[str, int]]): A sequence of (ship_name, ship_length) tuples.
            rng (Optional[random.Random]): A random number generator for reproducible games.
            difficulty (str): The AI difficulty level ("easy", "medium", or "hard").
            two_player (bool): If True, enables two-player hot-seat mode (no AI).
            salvo_mode (bool): If True, allows multiple shots per turn based on the
                               number of remaining ships.
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
        # The AI uses a hunting strategy that checks even/odd coordinates first
        # to efficiently find ships (a checkerboard pattern).
        self._ai_hunt_even: List[Coordinate] = [coord for coord in coords if (coord[0] + coord[1]) % 2 == 0]
        self._ai_hunt_odd: List[Coordinate] = [coord for coord in coords if (coord[0] + coord[1]) % 2 == 1]
        # A queue for the AI to store potential targets after a hit.
        self._ai_targets: Deque[Coordinate] = deque()

    def setup_random(self) -> None:
        """Sets up the game with randomly placed ships for both the player and the opponent."""
        self.player_board.randomly_place_ships(self.fleet, self.rng)
        self.opponent_board.randomly_place_ships(self.fleet, self.rng)

    def setup_player_ships(
        self,
        placements: Iterable[Tuple[str, int, Coordinate, str]],
    ) -> None:
        """Sets up the player's ships based on the given placements and randomly
        places the opponent's ships.

        Args:
            placements (Iterable[Tuple[str, int, Coordinate, str]]): An iterable of
                tuples, each containing the ship's name, length, starting
                coordinate, and orientation.
        """
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
        """Processes a player's shot at the opponent's board.

        Args:
            coord (Coordinate): The coordinate to shoot at.

        Returns:
            Tuple[str, Optional[str]]: The result of the shot and the name of the
                                       ship that was hit, if any.
        """
        result, ship_name = self.opponent_board.receive_shot(coord)
        return result, ship_name

    def ai_shoot(self) -> Tuple[Coordinate, str, Optional[str]]:
        """Processes the AI's shot at the player's board using its hunting strategy.

        Returns:
            Tuple[Coordinate, str, Optional[str]]: The coordinate the AI targeted,
                                                   the result of the shot, and the
                                                   name of the ship hit, if any.
        """
        # For "easy" difficulty, the AI just makes random shots.
        if self.difficulty == "easy":
            available = [(r, c) for r in range(self.size) for c in range(self.size) if (r, c) not in self.player_board.shots]
            if not available:
                raise RuntimeError("AI has no available shots left.")
            target = self.rng.choice(available)
        else:
            # For "medium" and "hard" difficulties, use the hunt-and-target strategy.
            # "Hard" difficulty always prioritizes targets, while "medium" does so 70% of the time.
            should_hunt = self.difficulty == "hard" or (self.difficulty == "medium" and self.rng.random() < 0.7)

            # Prioritize targets in the queue if available.
            if should_hunt and self._ai_targets:
                while self._ai_targets:
                    target = self._ai_targets.popleft()
                    if target in self.player_board.shots:
                        continue  # Skip already-shot targets.
                    break
                else:
                    target = self._get_hunt_target()
            else:
                target = self._get_hunt_target()

        result, ship_name = self.player_board.receive_shot(target)
        # If the shot is a hit, add neighboring cells to the target queue.
        if result in {"hit", "sunk"}:
            self._enqueue_targets(target)
        # If a ship is sunk, clear out any invalid targets from the queue.
        if result == "sunk":
            self._flush_invalid_targets()
        return target, result, ship_name

    def _get_hunt_target(self) -> Coordinate:
        """Gets the next hunting target for the AI from the pre-shuffled lists.

        Returns:
            Coordinate: The next coordinate to target in hunting mode.
        """
        # If there are no immediate targets, fall back to the hunting pattern.
        if self._ai_hunt_even:
            return self._ai_hunt_even.pop()
        elif self._ai_hunt_odd:
            return self._ai_hunt_odd.pop()
        else:
            raise RuntimeError("AI has no available shots left.")

    def _enqueue_targets(self, coord: Coordinate) -> None:
        """Adds valid neighboring cells to the AI's target queue after a successful hit.

        Args:
            coord (Coordinate): The coordinate that was hit.
        """
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
        """Removes already-shot coordinates from the AI's target queue.

        This is typically called after a ship is sunk to clean up the queue.
        """
        self._ai_targets = deque(coord for coord in self._ai_targets if coord not in self.player_board.shots)

    def render(self) -> str:
        """Renders both the player's and the opponent's boards side-by-side.

        Returns:
            str: A formatted string showing both game boards.
        """
        player = self.player_board.render(show_ships=True)
        opponent = self.opponent_board.render(show_ships=False)
        divider = "\n" + "=" * (self.size * 3) + "\n"
        return f"Your Fleet:\n{player}{divider}Enemy Waters:\n{opponent}"

    def player_has_lost(self) -> bool:
        """Checks if the player has lost the game (all their ships are sunk).

        Returns:
            bool: True if the player has lost, False otherwise.
        """
        return self.player_board.all_sunk()

    def opponent_has_lost(self) -> bool:
        """Checks if the opponent has lost the game (all their ships are sunk).

        Returns:
            bool: True if the opponent has lost, False otherwise.
        """
        return self.opponent_board.all_sunk()

    def get_salvo_count(self, player: str = "player") -> int:
        """Returns the number of shots available for a player in salvo mode.

        In salvo mode, the number of shots is equal to the number of unsunk ships.

        Args:
            player (str): "player" or "opponent" to count their remaining ships.

        Returns:
            int: The number of unsunk ships for the specified player.
        """
        board = self.player_board if player == "player" else self.opponent_board
        return sum(1 for ship in board.ships if not ship.is_sunk)
