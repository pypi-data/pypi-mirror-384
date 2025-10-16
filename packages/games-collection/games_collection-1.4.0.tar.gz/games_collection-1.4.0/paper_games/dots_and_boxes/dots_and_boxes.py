"""Game engine and logic for Dots and Boxes with a chain-aware AI.

This module provides the core game logic for Dots and Boxes, including edge
claiming, box completion tracking, and an AI opponent that uses chain analysis
to make strategic decisions.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

# Type aliases for clarity.
Player = str
EdgeKey = Tuple[str, int, int]


@dataclass
class DotsAndBoxes:
    """Manage a dots and boxes board with a chain-aware computer opponent."""

    size: int = 2
    human_name: str = "Human"
    computer_name: str = "Computer"
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        """Initializes the board state after the dataclass is created."""
        if self.size < 1:
            raise ValueError("Size must be at least 1.")
        # Horizontal edges are stored with (row, col) keys.
        self.horizontal_edges: Dict[Tuple[int, int], Optional[Player]] = {(row, col): None for row in range(self.size + 1) for col in range(self.size)}
        # Vertical edges are stored with (row, col) keys.
        self.vertical_edges: Dict[Tuple[int, int], Optional[Player]] = {(row, col): None for row in range(self.size) for col in range(self.size + 1)}
        # Boxes are stored with (row, col) keys, representing the top-left corner.
        self.boxes: Dict[Tuple[int, int], Optional[Player]] = {(row, col): None for row in range(self.size) for col in range(self.size)}
        self.scores = {self.human_name: 0, self.computer_name: 0}

    # ------------------------------------------------------------------
    # Basic board helpers
    def available_edges(self) -> List[EdgeKey]:
        """Returns a list of all available (unclaimed) edges."""
        edges: List[EdgeKey] = []
        for (row, col), owner in self.horizontal_edges.items():
            if owner is None:
                edges.append(("h", row, col))
        for (row, col), owner in self.vertical_edges.items():
            if owner is None:
                edges.append(("v", row, col))
        return edges

    def _edge_map(self, orientation: str) -> Dict[Tuple[int, int], Optional[Player]]:
        """Returns the appropriate edge map based on orientation."""
        if orientation == "h":
            return self.horizontal_edges
        if orientation == "v":
            return self.vertical_edges
        raise ValueError("Orientation must be 'h' or 'v'.")

    def _boxes_touching_edge(self, orientation: str, row: int, col: int) -> Iterable[Tuple[int, int]]:
        """Yields the coordinates of boxes that share a given edge."""
        if orientation == "h":
            if row < self.size:
                yield (row, col)
            if row > 0:
                yield (row - 1, col)
        else:  # vertical
            if col < self.size:
                yield (row, col)
            if col > 0:
                yield (row, col - 1)

    def _box_edges(self, box: Tuple[int, int]) -> List[EdgeKey]:
        """Returns a list of the four edges that form a given box."""
        row, col = box
        return [
            ("h", row, col),
            ("h", row + 1, col),
            ("v", row, col),
            ("v", row, col + 1),
        ]

    def claim_edge(self, orientation: str, row: int, col: int, player: Player) -> int:
        """Claims an edge for a player and updates the score if a box is completed."""
        edge_map = self._edge_map(orientation)
        key = (row, col)
        if key not in edge_map:
            raise ValueError("Invalid edge coordinates.")
        if edge_map[key] is not None:
            raise ValueError("Edge already claimed.")

        edge_map[key] = player
        completed = 0
        # Check if this move completed any boxes.
        for box in self._boxes_touching_edge(orientation, row, col):
            if self.boxes[box] is None and self._is_box_complete(box):
                self.boxes[box] = player
                self.scores[player] += 1
                completed += 1
        return completed

    def _is_box_complete(self, box: Tuple[int, int]) -> bool:
        """Checks if a given box has all four of its edges claimed."""
        return all((self._edge_map(orient)[(row, col)] is not None) for orient, row, col in self._box_edges(box))

    def _count_box_edges(self, box: Tuple[int, int]) -> int:
        """Counts the number of claimed edges for a given box."""
        return sum(1 for orient, row, col in self._box_edges(box) if self._edge_map(orient)[(row, col)] is not None)

    def is_finished(self) -> bool:
        """Checks if the game is over (all boxes are claimed)."""
        return all(owner is not None for owner in self.boxes.values())

    def game_over(self) -> bool:
        """Compatibility wrapper expected by older tests."""

        return self.is_finished()

    # ------------------------------------------------------------------
    # Computer player
    def computer_turn(self) -> List[Tuple[EdgeKey, int]]:
        """Play until the computer must hand back the move.

        Returns a history of moves and the number of boxes completed by each move.
        """

        moves: List[Tuple[EdgeKey, int]] = []

        def apply_move(move: EdgeKey) -> int:
            """Applies a move and records it."""
            orient, row, col = move
            completed = self.claim_edge(orient, row, col, player=self.computer_name)
            moves.append((move, completed))
            return completed

        # The computer will keep making moves as long as it can complete a box.
        while True:
            scoring_move = self._find_scoring_move()
            if not scoring_move:
                break
            apply_move(scoring_move)
            if self.is_finished():
                return moves

        if self.is_finished():
            return moves

        # If no scoring moves are available, find a safe move that doesn't create a third edge.
        safe_moves = [move for move in self.available_edges() if not self._creates_third_edge(move)]
        if safe_moves:
            next_move = self.rng.choice(safe_moves)
        else:
            # If no safe moves, choose the move that opens the smallest chain for the opponent.
            next_move = self._choose_chain_starter()

        completed = apply_move(next_move)
        # After making a move, check again for scoring opportunities.
        while completed and not self.is_finished():
            scoring_move = self._find_scoring_move()
            if not scoring_move:
                break
            completed = apply_move(scoring_move)

        return moves

    def make_computer_move(self) -> List[Tuple[EdgeKey, int]]:
        """Execute the computer's turn and return the moves performed."""

        return self.computer_turn()

    def _find_scoring_move(self) -> Optional[EdgeKey]:
        """Finds a move that will complete at least one box."""
        for move in self.available_edges():
            if self._would_complete_box(move):
                return move
        return None

    def _would_complete_box(self, move: EdgeKey) -> bool:
        """Checks if a given move would complete a box."""
        orient, row, col = move
        for box in self._boxes_touching_edge(orient, row, col):
            if self.boxes[box] is None and self._count_box_edges(box) == 3:
                return True
        return False

    def _creates_third_edge(self, move: EdgeKey) -> bool:
        """Checks if a move would create a third edge on an incomplete box."""
        orient, row, col = move
        for box in self._boxes_touching_edge(orient, row, col):
            if self.boxes[box] is not None:
                continue
            occupied = self._count_box_edges(box)
            if occupied == 2:
                return True
        return False

    def _choose_chain_starter(self) -> EdgeKey:
        """Chooses a move that starts a chain, minimizing the opponent's gain."""
        candidates = [move for move in self.available_edges() if self._creates_third_edge(move)]
        if not candidates:
            return self.rng.choice(self.available_edges())

        def chain_penalty(move: EdgeKey) -> Tuple[int, EdgeKey]:
            """Calculates the penalty for a move (length of the chain it opens)."""
            return (self._chain_length_if_opened(move), move)

        # Choose the move with the smallest penalty.
        return min(candidates, key=chain_penalty)

    def _chain_length_if_opened(self, move: EdgeKey) -> int:
        """Calculates the length of the chain that would be opened by a given move."""
        orient, row, col = move
        # Create a copy of the board state to simulate the move.
        horizontal = self.horizontal_edges.copy()
        vertical = self.vertical_edges.copy()
        boxes = self.boxes.copy()

        def edge_map_local(o: str) -> Dict[Tuple[int, int], Optional[Player]]:
            """Local version of _edge_map for the simulation."""
            return horizontal if o == "h" else vertical

        def is_box_complete_local(box: Tuple[int, int]) -> bool:
            """Local version of _is_box_complete for the simulation."""
            return all(edge_map_local(o)[(r, c)] is not None for o, r, c in self._box_edges(box))

        def claim_edge_local(local_move: EdgeKey, player: Player) -> int:
            """Local version of claim_edge for the simulation."""
            o, r, c = local_move
            edge_map_local(o)[(r, c)] = player
            completed_local = 0
            for box in self._boxes_touching_edge(o, r, c):
                if boxes[box] is None and is_box_complete_local(box):
                    boxes[box] = player
                    completed_local += 1
            return completed_local

        # Simulate the computer's move.
        claim_edge_local(move, self.computer_name)

        captured_by_opponent = 0
        while True:
            # Find a box that the opponent is forced to complete.
            forced_box = next(
                (
                    box
                    for box, owner in boxes.items()
                    if owner is None and sum(1 for o, r, c in self._box_edges(box) if edge_map_local(o)[(r, c)] is not None) == 3
                ),
                None,
            )
            if forced_box is None:
                break
            # Find the missing edge and claim it for the opponent.
            missing_edge = next((edge for edge in self._box_edges(forced_box) if edge_map_local(edge[0])[edge[1:]] is None))
            captured_by_opponent += claim_edge_local(missing_edge, self.human_name)
        return captured_by_opponent

    # ------------------------------------------------------------------
    # Rendering helpers
    def render(self) -> str:
        """Renders the current state of the board as a string."""
        header = "   " + "   ".join(f"{col}" for col in range(self.size))
        lines: List[str] = [header]
        for row in range(self.size):
            top = [f"{row} "]
            for col in range(self.size):
                top.append(".")
                owner = self.horizontal_edges[(row, col)]
                top.append("---" if owner else "   ")
            top.append(".")
            lines.append("".join(top))

            middle = ["  "]
            for col in range(self.size):
                owner = self.vertical_edges[(row, col)]
                middle.append("|" if owner else " ")
                box_owner = self.boxes[(row, col)]
                if box_owner:
                    middle.append(f" {box_owner[0]} ")
                else:
                    middle.append("   ")
            owner = self.vertical_edges[(row, self.size)]
            middle.append("|" if owner else " ")
            lines.append("".join(middle))
        bottom = [f"{self.size} "]
        row = self.size
        for col in range(self.size):
            bottom.append(".")
            owner = self.horizontal_edges[(row, col)]
            bottom.append("---" if owner else "   ")
        bottom.append(".")
        lines.append("".join(bottom))
        return "\n".join(lines)
