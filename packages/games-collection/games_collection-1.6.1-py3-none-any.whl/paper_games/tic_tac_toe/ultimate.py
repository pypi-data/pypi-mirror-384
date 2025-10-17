"""Ultimate Tic-Tac-Toe game logic and state management.

This module implements the rules and gameplay for Ultimate Tic-Tac-Toe, a
variant of the classic game played on a 3x3 grid of smaller 3x3 boards.
The core concept is that a move in a small board dictates which board the
opponent must play in next.

The `UltimateTicTacToeGame` class manages the overall game state, including:
- A grid of 9 `TicTacToeGame` instances for the small boards.
- A "meta-board" to track which player has won each small board.
- The logic for determining the active board for the next move.
- A simple AI for the computer opponent.

Key Game Rules:
1. To win the game, a player must win three small boards in a row on the
   meta-board.
2. The cell where a player makes a move determines the board where the
   opponent must play next. For example, a move in the top-left cell of a
   small board sends the opponent to the top-left board.
3. If the target board is already won or drawn, the opponent can play on
   any available board.

Classes:
    UltimateTicTacToeGame: Manages the state and logic for an Ultimate
                           Tic-Tac-Toe match.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .tic_tac_toe import TicTacToeGame


@dataclass
class UltimateTicTacToeGame:
    """Manages the state and logic for an Ultimate Tic-Tac-Toe game.

    This class encapsulates the entire game, including the 9 small boards,
    the meta-board, and the rules for player interaction. It provides methods
    for making moves, checking for winners, and rendering the game state.

    Attributes:
        human_symbol (str): The symbol for the human player.
        computer_symbol (str): The symbol for the computer player.
        starting_symbol (Optional[str]): The symbol of the player who starts.
        small_boards (List[TicTacToeGame]): A list of 9 `TicTacToeGame` instances.
        meta_board (List[Optional[str]]): A list representing the 3x3 meta-board,
                                          tracking wins, losses, and draws.
        active_board (Optional[int]): The index of the board where the next move
                                      must be played. If None, any board is valid.
        current_turn (str): The symbol of the current player.
    """

    human_symbol: str = "X"
    computer_symbol: str = "O"
    starting_symbol: Optional[str] = None

    def __post_init__(self) -> None:
        """Initializes the Ultimate Tic-Tac-Toe game and its components.

        This method sets up the 9 small boards, the meta-board, and determines
        the starting player. It is called automatically after the dataclass
        is initialized.

        Raises:
            ValueError: If the human and computer symbols are the same.
        """
        if self.human_symbol == self.computer_symbol:
            raise ValueError("Players must use distinct symbols.")

        # Create a 3x3 grid of small Tic-Tac-Toe boards.
        self.small_boards: List[TicTacToeGame] = [
            TicTacToeGame(
                human_symbol=self.human_symbol,
                computer_symbol=self.computer_symbol,
                starting_symbol=self.human_symbol,  # This won't be used for turn management.
            )
            for _ in range(9)
        ]

        # The meta-board tracks the winner of each small board.
        self.meta_board: List[Optional[str]] = [None] * 9

        # The active_board determines where the next move must be played.
        # `None` means any open board is a valid target.
        self.active_board: Optional[int] = None

        # Set the starting player for the game.
        if self.starting_symbol is None:
            self.starting_symbol = self.human_symbol
        if self.starting_symbol not in {self.human_symbol, self.computer_symbol}:
            raise ValueError("Starting symbol must belong to one of the players.")
        self.current_turn = self.starting_symbol

    def reset(self) -> None:
        """Resets the game to its initial state.

        This method clears all small boards, the meta-board, and resets the
        active board and current turn, allowing for a new game to be played.
        """
        for board in self.small_boards:
            board.reset()
        self.meta_board = [None] * 9
        self.active_board = None
        self.current_turn = self.starting_symbol

    def is_board_active(self, board_index: int) -> bool:
        """Checks if a specific small board can be played on.

        A board is considered active if it is the designated `active_board`
        or if any board is playable, and it has not yet been won or drawn.

        Args:
            board_index (int): The index of the board to check (0-8).

        Returns:
            bool: True if the board can be played on, False otherwise.
        """
        # A board that is already won or drawn cannot be played on.
        if self.meta_board[board_index] is not None:
            return False

        # If there is a specific active board, only it can be played on.
        if self.active_board is not None:
            return board_index == self.active_board

        # Otherwise, any board that is not won or drawn is active.
        return True

    def make_move(self, board_index: int, cell_index: int, symbol: str) -> bool:
        """Makes a move on a specific board and cell.

        This method validates the move, places the symbol on the board, updates
        the meta-board if a small board is won, and determines the next
        active board.

        Args:
            board_index (int): The index of the small board to play on (0-8).
            cell_index (int): The index of the cell within that board (0-8).
            symbol (str): The player's symbol to place.

        Returns:
            bool: True if the move was successful, False otherwise.
        """
        # Ensure the selected board is active and playable.
        if not self.is_board_active(board_index):
            return False

        # Make the move on the corresponding small board.
        board = self.small_boards[board_index]
        if not board.make_move(cell_index, symbol):
            return False

        # Check if this move wins the small board.
        winner = board.winner()
        if winner:
            self.meta_board[board_index] = winner
        elif board.is_draw():
            self.meta_board[board_index] = "DRAW"

        # Determine the next active board based on the cell just played.
        # The next move must be on the board corresponding to the cell's index.
        if self.meta_board[cell_index] is None:
            self.active_board = cell_index
        else:
            # If the target board is already won or drawn, any open board is valid.
            self.active_board = None

        return True

    def winner(self) -> Optional[str]:
        """Determines if there is a winner on the meta-board.

        This method checks for three-in-a-row on the meta-board, which
        signifies an overall game win.

        Returns:
            Optional[str]: The winning player's symbol, or None if there is no winner yet.
        """
        # Define all possible winning lines on the 3x3 meta-board.
        lines = [
            (0, 1, 2),  # Top row
            (3, 4, 5),  # Middle row
            (6, 7, 8),  # Bottom row
            (0, 3, 6),  # Left column
            (1, 4, 7),  # Middle column
            (2, 5, 8),  # Right column
            (0, 4, 8),  # Top-left to bottom-right diagonal
            (2, 4, 6),  # Top-right to bottom-left diagonal
        ]

        for a, b, c in lines:
            if self.meta_board[a] is not None and self.meta_board[a] != "DRAW" and self.meta_board[a] == self.meta_board[b] == self.meta_board[c]:
                return self.meta_board[a]

        return None

    def is_draw(self) -> bool:
        """Checks if the entire game has ended in a draw.

        A draw occurs if all small boards are complete (won or drawn), and
        there is no winner on the meta-board.

        Returns:
            bool: True if the game is a draw, False otherwise.
        """
        if self.winner():
            return False
        return all(cell is not None for cell in self.meta_board)

    def available_moves(self) -> List[Tuple[int, int]]:
        """Gets a list of all available moves.

        This method returns all valid moves, which are the empty cells on
        any active board.

        Returns:
            List[Tuple[int, int]]: A list of (board_index, cell_index) tuples
                                   representing all valid moves.
        """
        moves = []
        for board_idx in range(9):
            if self.is_board_active(board_idx):
                board = self.small_boards[board_idx]
                for cell_idx in board.available_moves():
                    moves.append((board_idx, cell_idx))
        return moves

    def render(self, show_meta_status: bool = True) -> str:
        """Renders the Ultimate Tic-Tac-Toe board as a string.

        This method creates a human-readable text representation of the game,
        including the meta-board status and the full grid of small boards.

        Args:
            show_meta_status (bool): Whether to include the meta-board status
                                     at the top of the render.

        Returns:
            str: A string representation of the board.
        """
        lines = []

        if show_meta_status:
            lines.append("Meta-board status:")
            # Display which boards have been won, lost, or drawn.
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

                    # Highlight the active board for the next move.
                    if self.active_board == idx:
                        marker = f"[{marker}]"
                    else:
                        marker = f" {marker} "
                    row_str += marker
                lines.append(row_str)
            lines.append("")

        # Render the full 9x9 grid of cells.
        lines.append("Full board (boards numbered 0-8, cells 0-8 within each):")

        # Build the visual representation row by row.
        for meta_row in range(3):
            # Iterate through each row of the small boards.
            for small_row in range(3):
                row_parts = []
                for meta_col in range(3):
                    board_idx = meta_row * 3 + meta_col
                    board = self.small_boards[board_idx]

                    # Get the current row from the small board.
                    start = small_row * 3
                    cells = []
                    for i in range(3):
                        cell = board.board[start + i]
                        cells.append(cell if cell != " " else "·")

                    row_parts.append(" ".join(cells))

                # Join the small board rows with separators.
                lines.append("  " + "  │  ".join(row_parts))

            # Add a separator between the rows of small boards.
            if meta_row < 2:
                lines.append("  " + "─" * 7 + "┼" + "─" * 7 + "┼" + "─" * 7)

        return "\n".join(lines)

    def swap_turn(self) -> None:
        """Swaps the current turn between the two players."""
        self.current_turn = self.computer_symbol if self.current_turn == self.human_symbol else self.human_symbol

    def human_move(self, board_index: int, cell_index: int) -> bool:
        """Makes a move for the human player.

        This is a convenience method that calls `make_move` with the human's symbol.

        Args:
            board_index (int): The index of the board to play on.
            cell_index (int): The index of the cell to play on.

        Returns:
            bool: True if the move was successful.
        """
        return self.make_move(board_index, cell_index, self.human_symbol)

    def computer_move(self) -> Tuple[int, int]:
        """Makes a simple, heuristic-based move for the computer.

        This AI uses a basic strategy:
        1. Prioritize the center cell of the center board.
        2. Prioritize the center cell of any other active board.
        3. Default to the first available move.

        A more sophisticated AI (e.g., using minimax) could be implemented for
        stronger gameplay.

        Returns:
            Tuple[int, int]: The (board_index, cell_index) where the move was made.

        Raises:
            RuntimeError: If there are no available moves for the computer to make.
        """
        moves = self.available_moves()
        if not moves:
            raise RuntimeError("No available moves!")

        # Simple strategy: prioritize center cells and boards.
        # The highest priority is the center of the center board (board 4, cell 4).
        center_board = 4
        center_cell = 4

        # 1. Try to take the center of the center board.
        if (center_board, center_cell) in moves:
            self.make_move(center_board, center_cell, self.computer_symbol)
            return (center_board, center_cell)

        # 2. Try to take the center cell of any other active board.
        for board_idx, cell_idx in moves:
            if cell_idx == center_cell:
                self.make_move(board_idx, cell_idx, self.computer_symbol)
                return (board_idx, cell_idx)

        # 3. If no strategic moves are available, take the first available move.
        board_idx, cell_idx = moves[0]
        self.make_move(board_idx, cell_idx, self.computer_symbol)
        return (board_idx, cell_idx)
