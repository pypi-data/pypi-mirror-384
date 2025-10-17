"""Game engine and logic for the mathematical game of Nim and its variants.

This module provides the core game logic for Nim, including the game state,
move validation, and an optimal computer opponent based on nim-sum calculations.
The computer player uses combinatorial game theory to find winning moves when
possible.

This module also includes variants:
- NorthcottGame: A game where players slide pieces towards each other
- WythoffGame: A variant with two heaps where diagonal moves are allowed
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterable, List, Tuple


@dataclass
class NimGame:
    """Classic Nim with configurable rules and an optimal computer opponent."""

    heaps: List[int] = field(default_factory=lambda: [3, 4, 5])
    misere: bool = False  # In misere Nim, the player who takes the last object loses.
    rng: random.Random = field(default_factory=random.Random)
    num_players: int = 2  # Number of players (2 or more for multiplayer)
    current_player: int = 0  # Track which player's turn it is (0-indexed)
    max_take: int | None = None  # Maximum objects that can be taken per turn (None = unlimited)

    def __post_init__(self) -> None:
        """Validates the initial game state after the dataclass is created."""
        if not self.heaps or any(heap <= 0 for heap in self.heaps):
            raise ValueError("Heaps must contain positive integers.")
        if self.num_players < 2:
            raise ValueError("Must have at least 2 players.")
        if self.max_take is not None and self.max_take < 1:
            raise ValueError("max_take must be at least 1 if specified.")

    # ------------------------------------------------------------------
    # Game state helpers
    def is_over(self) -> bool:
        """Checks if the game is over (all heaps are empty)."""
        return all(heap == 0 for heap in self.heaps)

    def non_empty_heaps(self) -> Iterable[int]:
        """Returns an iterator over the non-empty heaps."""
        return (heap for heap in self.heaps if heap > 0)

    def player_move(self, heap_index: int, count: int) -> None:
        """Applies a player's move to the game state and advances to next player."""
        if heap_index not in range(len(self.heaps)):
            raise ValueError("Invalid heap index.")
        if count <= 0:
            raise ValueError("You must remove at least one object.")
        if count > self.heaps[heap_index]:
            raise ValueError("Cannot remove more objects than the heap contains.")
        if self.max_take is not None and count > self.max_take:
            raise ValueError(f"Cannot take more than {self.max_take} objects per turn.")
        self.heaps[heap_index] -= count
        if not self.is_over():
            self.current_player = (self.current_player + 1) % self.num_players

    # ------------------------------------------------------------------
    # Combinatorial analysis helpers
    def nim_sum(self) -> int:
        """Calculates the Nim-sum of the current heaps, a key concept in Nim strategy."""
        nim_sum = 0
        for heap in self.heaps:
            nim_sum ^= heap
        return nim_sum

    def _available_moves(self) -> List[Tuple[int, int]]:
        """Returns a list of all possible moves (heap_index, count)."""
        moves: List[Tuple[int, int]] = []
        for heap_index, heap in enumerate(self.heaps):
            if heap == 0:
                continue
            max_take_from_heap = heap if self.max_take is None else min(heap, self.max_take)
            for take in range(1, max_take_from_heap + 1):
                moves.append((heap_index, take))
        return moves

    def _nim_sum_after_move(self, heap_index: int, remove: int) -> int:
        """Calculates what the Nim-sum would be after a given move."""
        new_heaps = list(self.heaps)
        new_heaps[heap_index] -= remove
        nim_sum = 0
        for heap in new_heaps:
            nim_sum ^= heap
        return nim_sum

    def _all_non_zero_heaps_are_singletons(self) -> bool:
        """Checks if all non-empty heaps have a size of 1."""
        return all(heap == 1 for heap in self.non_empty_heaps())

    def get_strategy_hint(self) -> str:
        """Provides an educational hint about the current position.

        Returns:
            A string explaining the current game state and optimal strategy.
        """
        current_nim_sum = self.nim_sum()

        # Explain nim-sum concept
        heap_xor_parts = []
        for i, heap in enumerate(self.heaps):
            heap_xor_parts.append(f"Heap {i + 1}: {heap} (binary: {bin(heap)[2:].zfill(4)})")

        hint = "=== Strategy Analysis ===\n"
        hint += "Current heaps:\n  " + "\n  ".join(heap_xor_parts) + "\n"
        hint += f"\nNim-sum (XOR of all heaps): {current_nim_sum} (binary: {bin(current_nim_sum)[2:].zfill(4)})\n"

        # Special case for misère
        if self.misere and self._all_non_zero_heaps_are_singletons():
            non_empty = sum(1 for h in self.heaps if h > 0)
            hint += "\n★ Misère Endgame:\n"
            hint += f"  All heaps are size 1. There are {non_empty} heaps remaining.\n"
            if non_empty % 2 == 1:
                hint += "  In misère rules, you WANT to leave an even number of heaps.\n"
            else:
                hint += "  In misère rules, you WANT to leave an odd number of heaps.\n"
            return hint

        if current_nim_sum == 0:
            hint += "\n★ Position Analysis: LOSING POSITION\n"
            hint += "  The Nim-sum is 0, meaning your opponent has the advantage.\n"
            hint += "  Any move you make will give them a winning position.\n"
            hint += "  Try to force them into making a mistake!\n"
        else:
            hint += "\n★ Position Analysis: WINNING POSITION\n"
            hint += "  The Nim-sum is non-zero, meaning you can win with optimal play!\n"
            hint += "  Strategy: Find a move that makes the Nim-sum 0.\n"

            # Find and explain winning moves
            winning_moves = []
            for heap_index, remove in self._available_moves():
                if self._nim_sum_after_move(heap_index, remove) == 0:
                    winning_moves.append((heap_index, remove))

            if winning_moves:
                hint += "\n  Winning moves:\n"
                for heap_idx, remove_count in winning_moves[:3]:  # Show up to 3 examples
                    new_heap_size = self.heaps[heap_idx] - remove_count
                    hint += f"    - Remove {remove_count} from Heap {heap_idx + 1} (leaving {new_heap_size})\n"
                if len(winning_moves) > 3:
                    hint += f"    ... and {len(winning_moves) - 3} more winning moves\n"

        return hint

    # ------------------------------------------------------------------
    # Computer strategy
    def computer_move(self, explain: bool = False) -> tuple[int, int] | tuple[int, int, str]:
        """Determines and applies the optimal computer move.

        Args:
            explain: If True, returns an explanation of the strategy used.

        Returns:
            If explain is False: (heap_index, remove_count)
            If explain is True: (heap_index, remove_count, explanation)
        """
        explanation = ""

        # Special case for misere Nim when all heaps are size 1.
        if self.misere and self._all_non_zero_heaps_are_singletons():
            heap_index = next(index for index, heap in enumerate(self.heaps) if heap > 0)
            remove = 1
            self.heaps[heap_index] -= remove
            if explain:
                non_empty_count = sum(1 for h in self.heaps if h > 0)
                explanation = f"Misère endgame: All heaps are size 1. Leaving {non_empty_count} heaps (odd/even determines winner)."
            return (heap_index, remove, explanation) if explain else (heap_index, remove)

        current_nim_sum = self.nim_sum()
        if current_nim_sum == 0:
            # If the Nim-sum is 0, the current player is in a losing position.
            # The computer makes a random move as a fallback.
            heap_index, remove = self._fallback_move()
            if explain:
                explanation = "Nim-sum is 0 (losing position). No winning move available. Making arbitrary move."
        else:
            # If the Nim-sum is non-zero, there is a winning move.
            # The computer finds a move that results in a Nim-sum of 0.
            winning_moves = [(heap_index, remove) for heap_index, remove in self._available_moves() if self._nim_sum_after_move(heap_index, remove) == 0]
            if not winning_moves:
                heap_index, remove = self._fallback_move()
                if explain:
                    explanation = f"Nim-sum is {current_nim_sum} but no winning move found (shouldn't happen). Making arbitrary move."
            else:
                heap_index, remove = min(
                    winning_moves,
                    key=lambda move: (self.heaps[move[0]] - move[1], move[0]),
                )
                if explain:
                    explanation = f"Nim-sum is {current_nim_sum} (winning position). Removing {remove} from heap {heap_index + 1} to achieve Nim-sum of 0."
        self.heaps[heap_index] -= remove
        return (heap_index, remove, explanation) if explain else (heap_index, remove)

    def _fallback_move(self) -> Tuple[int, int]:
        """A non-optimal move to make when no winning move is available."""
        heap_index = next(index for index, heap in enumerate(self.heaps) if heap > 0)
        return heap_index, 1

    # ------------------------------------------------------------------
    # Presentation helpers
    def render(self, graphical: bool = False) -> str:
        """Renders the current state of the heaps as a string.

        Args:
            graphical: If True, uses vertical graphical representation with blocks.
                      If False, uses horizontal representation with sticks.
        """
        if graphical:
            return self._render_graphical()
        return self._render_simple()

    def _render_simple(self) -> str:
        """Renders heaps horizontally with stick symbols."""
        display_parts = []
        for i, heap in enumerate(self.heaps):
            sticks = "|" * min(heap, 12)
            if heap > 12:
                sticks += "…"
            display_parts.append(f"Heap {i + 1}: {sticks} ({heap})")
        return "  ".join(display_parts)

    def _render_graphical(self) -> str:
        """Renders heaps vertically as stacked blocks."""
        if not self.heaps:
            return "No heaps remaining"

        max_height = max(self.heaps)
        if max_height == 0:
            return "All heaps are empty"

        # Limit display height for very large heaps
        display_height = min(max_height, 15)
        lines = []

        # Build from top to bottom
        for level in range(display_height, 0, -1):
            line_parts = []
            for i, heap in enumerate(self.heaps):
                if heap >= level:
                    line_parts.append("  ▓▓▓  ")
                else:
                    line_parts.append("       ")
            lines.append("".join(line_parts))

        # Add base line
        base_parts = []
        for i, heap in enumerate(self.heaps):
            base_parts.append(f" [{heap:>3}] ")
        lines.append("".join(base_parts))

        # Add heap labels
        label_parts = []
        for i in range(len(self.heaps)):
            label_parts.append(f" Heap{i+1}")
        lines.append("".join(label_parts))

        if max_height > display_height:
            lines.insert(0, "  (showing top 15 levels only)")

        return "\n".join(lines)


@dataclass
class NorthcottGame:
    """Northcott's Game - a Nim-like game where pieces slide on rows.

    In this game, each row has two pieces (one for each player) that can
    slide left or right but cannot pass each other. The game uses the
    'gap' between pieces as the Nim heap value. The last player to move wins.
    """

    board_size: int = 8  # Width of each row
    num_rows: int = 3  # Number of rows
    # Each row has (white_position, black_position) - positions are 0-indexed
    rows: List[Tuple[int, int]] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        """Initialize the game with random or default positions."""
        if not self.rows:
            # Initialize with random positions
            for _ in range(self.num_rows):
                white_pos = self.rng.randint(0, self.board_size // 2 - 1)
                black_pos = self.rng.randint(self.board_size // 2 + 1, self.board_size - 1)
                self.rows.append((white_pos, black_pos))

        if len(self.rows) != self.num_rows:
            raise ValueError(f"Expected {self.num_rows} rows, got {len(self.rows)}")

    def get_gaps(self) -> List[int]:
        """Get the gap sizes between pieces in each row (these form the Nim heaps)."""
        return [black - white - 1 for white, black in self.rows]

    def nim_sum(self) -> int:
        """Calculate the Nim-sum of the gaps."""
        result = 0
        for gap in self.get_gaps():
            result ^= gap
        return result

    def is_over(self) -> bool:
        """Check if the game is over (all gaps are 0)."""
        return all(gap == 0 for gap in self.get_gaps())

    def make_move(self, row_index: int, piece: str, new_position: int) -> None:
        """Move a piece in a row.

        Args:
            row_index: Which row (0-indexed)
            piece: 'white' or 'black'
            new_position: The new position for the piece
        """
        if row_index not in range(len(self.rows)):
            raise ValueError("Invalid row index")

        white_pos, black_pos = self.rows[row_index]

        if piece == "white":
            if new_position >= black_pos:
                raise ValueError("White piece cannot move past black piece")
            if new_position < 0 or new_position >= self.board_size:
                raise ValueError("Position out of bounds")
            self.rows[row_index] = (new_position, black_pos)
        elif piece == "black":
            if new_position <= white_pos:
                raise ValueError("Black piece cannot move past white piece")
            if new_position < 0 or new_position >= self.board_size:
                raise ValueError("Position out of bounds")
            self.rows[row_index] = (white_pos, new_position)
        else:
            raise ValueError("Piece must be 'white' or 'black'")

    def computer_move(self) -> Tuple[int, str, int]:
        """Make an optimal move for the computer.

        Returns:
            (row_index, piece_color, new_position)
        """
        # Use Nim strategy - try to make Nim-sum = 0
        current_nim_sum = self.nim_sum()
        gaps = self.get_gaps()

        if current_nim_sum == 0:
            # Losing position, make any move
            for row_idx, gap in enumerate(gaps):
                if gap > 0:
                    white_pos, black_pos = self.rows[row_idx]
                    # Move white piece right by 1
                    new_pos = white_pos + 1
                    self.make_move(row_idx, "white", new_pos)
                    return (row_idx, "white", new_pos)
        else:
            # Find a winning move
            for row_idx, gap in enumerate(gaps):
                white_pos, black_pos = self.rows[row_idx]
                target_gap = gap ^ current_nim_sum

                if target_gap < gap:
                    # We can achieve this by moving pieces closer
                    new_gap = target_gap
                    # Try moving white piece right
                    new_white = black_pos - new_gap - 1
                    if new_white > white_pos and new_white < black_pos:
                        self.make_move(row_idx, "white", new_white)
                        return (row_idx, "white", new_white)
                    # Try moving black piece left
                    new_black = white_pos + new_gap + 1
                    if new_black < black_pos and new_black > white_pos:
                        self.make_move(row_idx, "black", new_black)
                        return (row_idx, "black", new_black)

        # Fallback: make any legal move
        for row_idx, gap in enumerate(gaps):
            if gap > 0:
                white_pos, black_pos = self.rows[row_idx]
                new_pos = white_pos + 1
                self.make_move(row_idx, "white", new_pos)
                return (row_idx, "white", new_pos)

        raise RuntimeError("No legal moves available")

    def render(self) -> str:
        """Render the game board."""
        lines = ["=== Northcott's Game ==="]
        gaps = self.get_gaps()
        lines.append(f"Nim-sum of gaps: {self.nim_sum()}\n")

        for i, (white_pos, black_pos) in enumerate(self.rows):
            row = ["."] * self.board_size
            row[white_pos] = "W"
            row[black_pos] = "B"
            gap = gaps[i]
            lines.append(f"Row {i + 1}: {''.join(row)} (gap: {gap})")

        return "\n".join(lines)


@dataclass
class WythoffGame:
    """Wythoff's Game - a Nim variant with two heaps and diagonal moves.

    Players can remove any number from one heap (like Nim), or remove
    the same number from both heaps (diagonal move). The last player
    to move wins.
    """

    heap1: int = 5
    heap2: int = 8

    def __post_init__(self) -> None:
        """Validate initial state."""
        if self.heap1 < 0 or self.heap2 < 0:
            raise ValueError("Heaps must be non-negative")

    def is_over(self) -> bool:
        """Check if the game is over."""
        return self.heap1 == 0 and self.heap2 == 0

    def make_move(self, from_heap1: int, from_heap2: int) -> None:
        """Remove items from heaps.

        Args:
            from_heap1: Number to remove from heap 1
            from_heap2: Number to remove from heap 2

        Valid moves:
        - (n, 0): Remove n from heap 1
        - (0, n): Remove n from heap 2
        - (n, n): Remove n from both heaps
        """
        if from_heap1 < 0 or from_heap2 < 0:
            raise ValueError("Cannot remove negative amounts")
        if from_heap1 == 0 and from_heap2 == 0:
            raise ValueError("Must remove at least one item")
        if from_heap1 > 0 and from_heap2 > 0 and from_heap1 != from_heap2:
            raise ValueError("When removing from both heaps, must remove same amount")
        if from_heap1 > self.heap1 or from_heap2 > self.heap2:
            raise ValueError("Cannot remove more than heap contains")

        self.heap1 -= from_heap1
        self.heap2 -= from_heap2

    def _is_cold_position(self, h1: int, h2: int) -> bool:
        """Check if a position is a 'cold' (losing) position in Wythoff's game.

        Cold positions follow the Beatty sequence with golden ratio.
        """
        if h1 == 0 and h2 == 0:
            return True

        # Normalize so h1 <= h2
        a, b = min(h1, h2), max(h1, h2)

        # Check against known cold positions using golden ratio
        phi = (1 + 5**0.5) / 2  # Golden ratio

        # Check if this matches a Wythoff pair
        # For small values, we can compute exactly
        for k in range(max(a, b) + 1):
            a_k = int(k * phi)
            b_k = int(k * phi * phi)
            if (a, b) == (a_k, b_k):
                return True

        return False

    def computer_move(self) -> Tuple[int, int]:
        """Make an optimal move for the computer.

        Returns:
            (remove_from_heap1, remove_from_heap2)
        """
        # Try all possible moves and find one that leaves opponent in cold position
        # Try removing from heap1 only
        for remove in range(1, self.heap1 + 1):
            if self._is_cold_position(self.heap1 - remove, self.heap2):
                self.make_move(remove, 0)
                return (remove, 0)

        # Try removing from heap2 only
        for remove in range(1, self.heap2 + 1):
            if self._is_cold_position(self.heap1, self.heap2 - remove):
                self.make_move(0, remove)
                return (0, remove)

        # Try diagonal moves
        for remove in range(1, min(self.heap1, self.heap2) + 1):
            if self._is_cold_position(self.heap1 - remove, self.heap2 - remove):
                self.make_move(remove, remove)
                return (remove, remove)

        # No winning move found, make any move
        if self.heap1 > 0:
            self.make_move(1, 0)
            return (1, 0)
        else:
            self.make_move(0, 1)
            return (0, 1)

    def render(self) -> str:
        """Render the game state."""
        lines = ["=== Wythoff's Game ==="]
        lines.append(f"Heap 1: {'|' * min(self.heap1, 20)} ({self.heap1})")
        lines.append(f"Heap 2: {'|' * min(self.heap2, 20)} ({self.heap2})")

        is_cold = self._is_cold_position(self.heap1, self.heap2)
        status = "COLD (losing)" if is_cold else "HOT (winning)"
        lines.append(f"\nPosition status: {status}")

        return "\n".join(lines)
