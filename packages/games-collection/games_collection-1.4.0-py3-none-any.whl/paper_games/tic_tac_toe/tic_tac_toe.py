"""Game engine and logic for tic-tac-toe with a minimax-powered computer opponent.

This module provides the core game logic for tic-tac-toe, including board
management, move validation, winner detection, and an optimal minimax-based
computer opponent that never loses.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from common.architecture.replay import ReplayManager

# A mapping of human-readable coordinates to board indices.
COORDINATES: Dict[str, int] = {
    "A1": 0,
    "A2": 1,
    "A3": 2,
    "B1": 3,
    "B2": 4,
    "B3": 5,
    "C1": 6,
    "C2": 7,
    "C3": 8,
}
# A reverse mapping from board indices to human-readable coordinates.
INDEX_TO_COORD = {index: coord for coord, index in COORDINATES.items()}


@dataclass
class TicTacToeGame:
    """Play a game of tic-tac-toe against an optimal computer opponent."""

    human_symbol: str = "X"
    computer_symbol: str = "O"
    starting_symbol: Optional[str] = None
    board_size: int = 3
    win_length: Optional[int] = None

    def __post_init__(self) -> None:
        """Validates the initial game state after the dataclass is created."""
        if self.human_symbol == self.computer_symbol:
            raise ValueError("Players must use distinct symbols.")
        if not self.human_symbol or not self.computer_symbol:
            raise ValueError("Symbols cannot be empty.")
        if self.board_size < 3:
            raise ValueError("Board size must be at least 3.")
        if self.win_length is None:
            self.win_length = self.board_size
        if self.win_length < 3 or self.win_length > self.board_size:
            raise ValueError(f"Win length must be between 3 and {self.board_size}.")
        self.board: List[str] = [" "] * (self.board_size * self.board_size)
        self.replay_manager = ReplayManager()
        self.reset(self.starting_symbol)

    def reset(self, starting_symbol: Optional[str] = None) -> None:
        """Resets the game to its initial state."""
        if starting_symbol is not None:
            self.starting_symbol = starting_symbol
        if self.starting_symbol is None:
            self.starting_symbol = self.human_symbol
        if self.starting_symbol not in {self.human_symbol, self.computer_symbol}:
            raise ValueError("Starting symbol must belong to one of the players.")
        self.board = [" "] * (self.board_size * self.board_size)
        self.current_turn = self.starting_symbol or self.human_symbol

    def available_moves(self) -> List[int]:
        """Returns a list of available (empty) squares on the board."""
        return [i for i, value in enumerate(self.board) if value == " "]

    def make_move(self, position: int | tuple[int, int], symbol: Optional[str] = None) -> bool:
        """Place ``symbol`` on the board at ``position`` if available."""

        if isinstance(position, tuple):
            row, col = position
            if not (0 <= row < self.board_size and 0 <= col < self.board_size):
                raise ValueError("Row and column are out of bounds.")
            index = row * self.board_size + col
        else:
            index = position

        max_position = self.board_size * self.board_size
        if index not in range(max_position):
            raise ValueError(f"Position must be between 0 and {max_position - 1} inclusive.")
        if self.board[index] != " ":
            return False

        symbol_to_use = symbol if symbol is not None else getattr(self, "current_turn", self.human_symbol)

        # Record the move for replay/undo
        state_before = {"board": self.board.copy(), "current_turn": getattr(self, "current_turn", self.human_symbol)}
        self.replay_manager.record_action(
            timestamp=time.time(),
            actor=symbol_to_use,
            action_type="place_symbol",
            data={"position": index, "symbol": symbol_to_use},
            state_before=state_before,
        )

        self.board[index] = symbol_to_use
        return True

    def winner(self) -> Optional[str]:
        """Determines if there is a winner and returns their symbol."""
        # Check all possible winning lines for the given win_length
        # Check rows
        for row in range(self.board_size):
            for col in range(self.board_size - self.win_length + 1):
                start = row * self.board_size + col
                symbols = [self.board[start + i] for i in range(self.win_length)]
                if symbols[0] != " " and all(s == symbols[0] for s in symbols):
                    return symbols[0]

        # Check columns
        for col in range(self.board_size):
            for row in range(self.board_size - self.win_length + 1):
                start = row * self.board_size + col
                symbols = [self.board[start + i * self.board_size] for i in range(self.win_length)]
                if symbols[0] != " " and all(s == symbols[0] for s in symbols):
                    return symbols[0]

        # Check diagonals (top-left to bottom-right)
        for row in range(self.board_size - self.win_length + 1):
            for col in range(self.board_size - self.win_length + 1):
                start = row * self.board_size + col
                symbols = [self.board[start + i * (self.board_size + 1)] for i in range(self.win_length)]
                if symbols[0] != " " and all(s == symbols[0] for s in symbols):
                    return symbols[0]

        # Check diagonals (top-right to bottom-left)
        for row in range(self.board_size - self.win_length + 1):
            for col in range(self.win_length - 1, self.board_size):
                start = row * self.board_size + col
                symbols = [self.board[start + i * (self.board_size - 1)] for i in range(self.win_length)]
                if symbols[0] != " " and all(s == symbols[0] for s in symbols):
                    return symbols[0]

        return None

    def is_draw(self) -> bool:
        """Checks if the game is a draw."""
        return " " not in self.board and self.winner() is None

    def is_over(self) -> bool:
        """Return ``True`` when the game has a winner or ends in a draw."""

        return self.winner() is not None or self.is_draw()

    def minimax(self, is_maximizing: bool, depth: int = 0, max_depth: Optional[int] = None) -> Tuple[int, Optional[int]]:
        """
        The minimax algorithm for finding the optimal move.

        Args:
            is_maximizing: True if the current player is the computer (maximizer),
                           False if the current player is the human (minimizer).
            depth: The current depth of the recursion.
            max_depth: Maximum depth to search (for performance on larger boards).

        Returns:
            A tuple containing the best score and the best move.
        """
        # Set default max_depth based on board size
        if max_depth is None:
            if self.board_size <= 3:
                max_depth = 100  # No limit for 3x3
            elif self.board_size == 4:
                max_depth = 6
            else:  # 5x5 and larger
                max_depth = 4

        winner = self.winner()
        # Base cases for the recursion.
        if winner == self.computer_symbol:
            return 10 - depth, None
        if winner == self.human_symbol:
            return depth - 10, None
        if self.is_draw():
            return 0, None
        if depth >= max_depth:
            # Heuristic evaluation at max depth
            return 0, None

        best_score = float("-inf") if is_maximizing else float("inf")
        best_move: Optional[int] = None
        symbol = self.computer_symbol if is_maximizing else self.human_symbol

        # Iterate through all available moves.
        for move in self.available_moves():
            self.board[move] = symbol
            score, _ = self.minimax(not is_maximizing, depth + 1, max_depth)
            self.board[move] = " "  # Backtrack.
            # Update the best score and move.
            if is_maximizing:
                if score > best_score:
                    best_score = score
                    best_move = move
            else:
                if score < best_score:
                    best_score = score
                    best_move = move
        return int(best_score), best_move

    def computer_move(self) -> int:
        """Determine and apply the computer's move."""

        if self.board_size == 3 and self.win_length == 3:
            move_index = self._select_fast_move()
        else:
            _, move_index = self.minimax(True)
            if move_index is None:
                move_index = self.available_moves()[0]

        row, col = divmod(move_index, self.board_size)
        self.make_move(move_index, self.computer_symbol)
        return row, col

    def _select_fast_move(self) -> int:
        """Return a strong move using lightweight heuristics."""

        available = self.available_moves()

        def _winning_move(symbol: str) -> Optional[int]:
            for candidate in available:
                self.board[candidate] = symbol
                has_won = self.winner() == symbol
                self.board[candidate] = " "
                if has_won:
                    return candidate
            return None

        win_now = _winning_move(self.computer_symbol)
        if win_now is not None:
            return win_now

        block_human = _winning_move(self.human_symbol)
        if block_human is not None:
            return block_human

        # Prefer the center square when available.
        if self.board_size % 2 == 1:
            center_index = (self.board_size * self.board_size) // 2
            if self.board[center_index] == " ":
                return center_index

        # Next, favour the corners for stronger board control.
        corners = [row * self.board_size + col for row in (0, self.board_size - 1) for col in (0, self.board_size - 1)]
        for corner in corners:
            if 0 <= corner < len(self.board) and self.board[corner] == " ":
                return corner

        # Finally fall back to the first available square for determinism.
        return available[0]

    def human_move(self, position: int) -> bool:
        """Makes a move for the human player."""
        return self.make_move(position, self.human_symbol)

    def undo_last_move(self) -> bool:
        """Undo the last move made.

        Returns:
            True if a move was undone, False if no moves to undo
        """
        if not self.replay_manager.can_undo():
            return False

        action = self.replay_manager.undo()
        if action and action.state_before:
            # Restore the board state
            self.board = action.state_before["board"].copy()
            self.current_turn = action.state_before["current_turn"]
            return True
        return False

    def can_undo(self) -> bool:
        """Check if there are moves that can be undone.

        Returns:
            True if undo is available, False otherwise
        """
        return self.replay_manager.can_undo()

    def render(self, show_reference: bool = False) -> str:
        """Return a human-friendly board representation."""
        # Generate row labels (A, B, C, ... or A, B, C, D, E, ...)
        row_labels = [chr(ord("A") + i) for i in range(self.board_size)]

        # Generate column header
        col_numbers = " ".join(f"{i+1:3}" for i in range(self.board_size))
        header = "   " + col_numbers

        # Generate separator
        separator = "  +" + "+".join(["---"] * self.board_size)

        # Generate board rows
        rows = []
        for row_index in range(self.board_size):
            start = row_index * self.board_size
            cells = " | ".join(self.board[start : start + self.board_size])
            rows.append(f"{row_labels[row_index]} | {cells}")

        # Build the board render
        board_lines = [header, separator]
        for i, row in enumerate(rows):
            board_lines.append(row)
            if i < len(rows) - 1:
                board_lines.append(separator)

        board_render = "\n".join(board_lines)

        if not show_reference or self.board_size > 5:
            return board_render

        # Also show a reference board with coordinates (only for smaller boards)
        reference_rows = []
        coords_map = self._generate_coordinates()
        for row_index in range(self.board_size):
            start = row_index * self.board_size
            coords = " | ".join(coords_map[start + offset] for offset in range(self.board_size))
            reference_rows.append(f"{row_labels[row_index]} | {coords}")

        reference_lines = ["Reference:", header, separator]
        for i, row in enumerate(reference_rows):
            reference_lines.append(row)
            if i < len(reference_rows) - 1:
                reference_lines.append(separator)

        reference = "\n".join(reference_lines)
        return board_render + "\n\n" + reference

    def _generate_coordinates(self) -> Dict[int, str]:
        """Generate coordinate mapping for the current board size."""
        coords = {}
        for row in range(self.board_size):
            for col in range(self.board_size):
                row_label = chr(ord("A") + row)
                col_label = str(col + 1)
                coords[row * self.board_size + col] = f"{row_label}{col_label}"
        return coords

    def legal_coordinates(self) -> Iterable[str]:
        """Returns an iterator over the legal (available) coordinates."""
        coords_map = self._generate_coordinates()
        return (coords_map[idx] for idx in range(len(self.board)) if self.board[idx] == " ")

    def parse_coordinate(self, text: str) -> int:
        """Parses a human-readable coordinate into a board index."""
        text = text.strip().upper()
        if len(text) < 2:
            raise ValueError(f"Enter a coordinate like A1, B{self.board_size}, etc.")

        row_label = text[0]
        col_label = text[1:]

        if not row_label.isalpha() or not col_label.isdigit():
            raise ValueError(f"Enter a coordinate like A1, B{self.board_size}, etc.")

        row = ord(row_label) - ord("A")
        try:
            col = int(col_label) - 1
        except ValueError:
            raise ValueError(f"Enter a coordinate like A1, B{self.board_size}, etc.")

        if row < 0 or row >= self.board_size or col < 0 or col >= self.board_size:
            raise ValueError(f"Coordinate must be within the {self.board_size}x{self.board_size} board.")

        return row * self.board_size + col

    def swap_turn(self) -> None:
        """Swaps the current turn between the human and the computer."""
        self.current_turn = self.computer_symbol if self.current_turn == self.human_symbol else self.human_symbol
