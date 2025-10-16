"""Ultimate Tic-Tac-Toe implementation.

Ultimate Tic-Tac-Toe is played on a 3x3 grid of 3x3 tic-tac-toe boards.
Players must win small boards to claim cells in the meta-board.
The game is won by getting three in a row on the meta-board.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .tic_tac_toe import TicTacToeGame


@dataclass
class UltimateTicTacToeGame:
    """Play ultimate tic-tac-toe with meta-board gameplay."""

    human_symbol: str = "X"
    computer_symbol: str = "O"
    starting_symbol: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize the ultimate tic-tac-toe game."""
        if self.human_symbol == self.computer_symbol:
            raise ValueError("Players must use distinct symbols.")

        # Create 9 small boards (3x3 grid of boards)
        self.small_boards: List[TicTacToeGame] = [
            TicTacToeGame(
                human_symbol=self.human_symbol,
                computer_symbol=self.computer_symbol,
                starting_symbol=self.human_symbol,  # Won't be used for turns
            )
            for _ in range(9)
        ]

        # Meta-board tracking which small boards have been won
        self.meta_board: List[Optional[str]] = [None] * 9

        # Active board index (which board the next move must be on)
        # None means any board can be played
        self.active_board: Optional[int] = None

        # Set starting player
        if self.starting_symbol is None:
            self.starting_symbol = self.human_symbol
        if self.starting_symbol not in {self.human_symbol, self.computer_symbol}:
            raise ValueError("Starting symbol must belong to one of the players.")
        self.current_turn = self.starting_symbol

    def reset(self) -> None:
        """Reset the game to initial state."""
        for board in self.small_boards:
            board.reset()
        self.meta_board = [None] * 9
        self.active_board = None
        self.current_turn = self.starting_symbol

    def is_board_active(self, board_index: int) -> bool:
        """Check if a board can be played on.

        Args:
            board_index: Index of the board to check (0-8).

        Returns:
            True if the board is active and can be played on.
        """
        # Board must not be won yet
        if self.meta_board[board_index] is not None:
            return False

        # If there's an active board restriction, must match
        if self.active_board is not None:
            return board_index == self.active_board

        # Otherwise, any unwon board is active
        return True

    def make_move(self, board_index: int, cell_index: int, symbol: str) -> bool:
        """Make a move on a specific board and cell.

        Args:
            board_index: Index of the small board (0-8).
            cell_index: Index of the cell within that board (0-8).
            symbol: The symbol to place.

        Returns:
            True if the move was successful, False otherwise.
        """
        # Validate board is active
        if not self.is_board_active(board_index):
            return False

        # Make the move on the small board
        board = self.small_boards[board_index]
        if not board.make_move(cell_index, symbol):
            return False

        # Check if this board is now won
        winner = board.winner()
        if winner:
            self.meta_board[board_index] = winner
        elif board.is_draw():
            self.meta_board[board_index] = "DRAW"

        # Set the next active board
        # The next move must be on the board corresponding to the cell just played
        if self.meta_board[cell_index] is None:
            self.active_board = cell_index
        else:
            # That board is already won/drawn, so any board is valid
            self.active_board = None

        return True

    def winner(self) -> Optional[str]:
        """Determine if there's a winner on the meta-board.

        Returns:
            The winning symbol, or None if no winner yet.
        """
        # Check all winning lines on the meta-board
        lines = [
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),
            (0, 4, 8),
            (2, 4, 6),
        ]

        for a, b, c in lines:
            if self.meta_board[a] is not None and self.meta_board[a] != "DRAW" and self.meta_board[a] == self.meta_board[b] == self.meta_board[c]:
                return self.meta_board[a]

        return None

    def is_draw(self) -> bool:
        """Check if the game is a draw.

        Returns:
            True if all boards are complete but there's no winner.
        """
        if self.winner():
            return False
        return all(cell is not None for cell in self.meta_board)

    def available_moves(self) -> List[Tuple[int, int]]:
        """Get all available moves.

        Returns:
            A list of (board_index, cell_index) tuples for valid moves.
        """
        moves = []
        for board_idx in range(9):
            if self.is_board_active(board_idx):
                board = self.small_boards[board_idx]
                for cell_idx in board.available_moves():
                    moves.append((board_idx, cell_idx))
        return moves

    def render(self, show_meta_status: bool = True) -> str:
        """Render the ultimate tic-tac-toe board.

        Args:
            show_meta_status: Whether to show the meta-board status.

        Returns:
            A string representation of the board.
        """
        lines = []

        if show_meta_status:
            lines.append("Meta-board status:")
            # Show which boards are won
            for row in range(3):
                row_str = "  "
                for col in range(3):
                    idx = row * 3 + col
                    status = self.meta_board[idx]
                    if status is None:
                        marker = "·"
                    elif status == "DRAW":
                        marker = "="
                    else:
                        marker = status

                    # Highlight active board
                    if self.active_board == idx:
                        marker = f"[{marker}]"
                    else:
                        marker = f" {marker} "
                    row_str += marker
                lines.append(row_str)
            lines.append("")

        # Render the full board
        lines.append("Full board (boards numbered 0-8, cells 0-8 within each):")

        # Build the visual representation
        for meta_row in range(3):
            # For each row of small boards
            for small_row in range(3):
                row_parts = []
                for meta_col in range(3):
                    board_idx = meta_row * 3 + meta_col
                    board = self.small_boards[board_idx]

                    # Get this row from the small board
                    start = small_row * 3
                    cells = []
                    for i in range(3):
                        cell = board.board[start + i]
                        cells.append(cell if cell != " " else "·")

                    row_parts.append(" ".join(cells))

                # Join small boards with separators
                lines.append("  " + "  │  ".join(row_parts))

            # Add separator between rows of small boards
            if meta_row < 2:
                lines.append("  " + "─" * 7 + "┼" + "─" * 7 + "┼" + "─" * 7)

        return "\n".join(lines)

    def swap_turn(self) -> None:
        """Swap the current turn between players."""
        self.current_turn = self.computer_symbol if self.current_turn == self.human_symbol else self.human_symbol

    def human_move(self, board_index: int, cell_index: int) -> bool:
        """Make a move for the human player.

        Args:
            board_index: Index of the board to play on.
            cell_index: Index of the cell to play on.

        Returns:
            True if the move was successful.
        """
        return self.make_move(board_index, cell_index, self.human_symbol)

    def computer_move(self) -> Tuple[int, int]:
        """Make a simple move for the computer.

        For simplicity, the computer picks the first available move.
        A more sophisticated AI could be implemented.

        Returns:
            The (board_index, cell_index) where the move was made.
        """
        moves = self.available_moves()
        if not moves:
            raise RuntimeError("No available moves!")

        # Simple strategy: prefer center cells and boards
        # Priority: center of center board, then center of any board, then any move
        center_board = 4
        center_cell = 4

        # Try center of center board
        if (center_board, center_cell) in moves:
            self.make_move(center_board, center_cell, self.computer_symbol)
            return (center_board, center_cell)

        # Try center cell of any active board
        for board_idx, cell_idx in moves:
            if cell_idx == center_cell:
                self.make_move(board_idx, cell_idx, self.computer_symbol)
                return (board_idx, cell_idx)

        # Take first available move
        board_idx, cell_idx = moves[0]
        self.make_move(board_idx, cell_idx, self.computer_symbol)
        return (board_idx, cell_idx)
