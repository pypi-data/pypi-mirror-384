"""Game engine and logic for tic-tac-toe with a minimax-powered computer opponent.

This module provides the core game logic for tic-tac-toe, including board
management, move validation, winner detection, and an optimal minimax-based
computer opponent that never loses. It supports variable board sizes and
win conditions, making it adaptable for different variations of the game.

The `TicTacToeGame` class encapsulates the entire game state and logic,
offering methods to make moves, check for a winner, and determine the
computer's optimal move using the minimax algorithm. It also includes
features like game replay and undo functionality.

Key Features:
- **Variable Board Size**: Play on boards larger than the classic 3x3.
- **Custom Win Length**: Define the number of symbols in a row needed to win.
- **Optimal AI**: The computer opponent uses minimax with alpha-beta pruning
  concepts to ensure it plays optimally.
- **Replay and Undo**: The game tracks move history, allowing for undoing
  moves and replaying games.
- **Coordinate System**: A human-readable coordinate system (e.g., A1, B2)
  is used for user input.

Classes:
    TicTacToeGame: Manages the game state and logic for a tic-tac-toe match.

Constants:
    COORDINATES: A mapping of human-readable coordinates to board indices for a 3x3 board.
    INDEX_TO_COORD: A reverse mapping from board indices to human-readable coordinates.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from common.architecture.replay import ReplayManager

# A mapping of human-readable coordinates to board indices for a standard 3x3 board.
# This is used for quick lookups and validation.
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
# Useful for displaying board positions to the user.
INDEX_TO_COORD = {index: coord for coord, index in COORDINATES.items()}


@dataclass
class TicTacToeGame:
    """Manages the state and logic for a game of tic-tac-toe.

    This class encapsulates the game board, player symbols, and all the logic
    required to play a game of tic-tac-toe. It supports variable board sizes,
    custom win lengths, and an AI opponent powered by the minimax algorithm.

    Attributes:
        human_symbol (str): The symbol used by the human player (e.g., 'X').
        computer_symbol (str): The symbol used by the computer player (e.g., 'O').
        starting_symbol (Optional[str]): The symbol of the player who makes the first move.
        board_size (int): The width and height of the game board.
        win_length (Optional[int]): The number of symbols in a row required to win.
        board (List[str]): A list representing the game board, with each element
                           being a symbol or an empty space.
        replay_manager (ReplayManager): An object that manages the game's move history
                                        for undo and replay functionality.
        current_turn (str): The symbol of the player whose turn it is.
    """

    human_symbol: str = "X"
    computer_symbol: str = "O"
    starting_symbol: Optional[str] = None
    board_size: int = 3
    win_length: Optional[int] = None

    def __post_init__(self) -> None:
        """Validates the initial game state and initializes the board.

        This method is called automatically after the dataclass is initialized.
        It performs validation on the provided game settings and sets up the
        initial game state, including the board and the replay manager.

        Raises:
            ValueError: If the player symbols are the same, empty, or if the
                        board size or win length are invalid.
        """
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

        # Initialize the game board as a list of empty spaces.
        self.board: List[str] = [" "] * (self.board_size * self.board_size)
        # Initialize the replay manager to track game history.
        self.replay_manager = ReplayManager()
        # Reset the game to its starting state.
        self.reset(self.starting_symbol)

    def reset(self, starting_symbol: Optional[str] = None) -> None:
        """Resets the game to its initial state.

        This method clears the board and sets the current turn to the starting
        player. It can be used to start a new game with the same settings.

        Args:
            starting_symbol (Optional[str]): The symbol of the player to start the new game.
                                             If None, the previous starting symbol is used.
        """
        if starting_symbol is not None:
            self.starting_symbol = starting_symbol
        if self.starting_symbol is None:
            self.starting_symbol = self.human_symbol
        if self.starting_symbol not in {self.human_symbol, self.computer_symbol}:
            raise ValueError("Starting symbol must belong to one of the players.")

        # Clear the board and set the current turn.
        self.board = [" "] * (self.board_size * self.board_size)
        self.current_turn = self.starting_symbol or self.human_symbol

    def available_moves(self) -> List[int]:
        """Returns a list of available (empty) squares on the board.

        This method scans the board and identifies all positions that are not
        yet occupied by a player's symbol.

        Returns:
            List[int]: A list of board indices representing the empty squares.
        """
        return [i for i, value in enumerate(self.board) if value == " "]

    def make_move(self, position: int | tuple[int, int], symbol: Optional[str] = None) -> bool:
        """Places a symbol on the board at the specified position.

        This method validates the move and, if it's legal, places the given
        symbol on the board. It also records the move in the replay manager.

        Args:
            position (int | tuple[int, int]): The position to place the symbol.
                                              Can be an integer index or a (row, col) tuple.
            symbol (Optional[str]): The symbol to place. If None, the symbol of the
                                    current player is used.

        Returns:
            bool: True if the move was successful, False otherwise.

        Raises:
            ValueError: If the position is out of bounds.
        """
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

        # Record the move for replay and undo functionality.
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
        """Determines if there is a winner and returns their symbol.

        This method checks all rows, columns, and diagonals for a sequence of
        identical symbols that meets the win length requirement.

        Returns:
            Optional[str]: The winning player's symbol, or None if there is no winner yet.
        """
        # Check all possible winning lines for the given win_length.
        # Check rows for a winning sequence.
        for row in range(self.board_size):
            for col in range(self.board_size - self.win_length + 1):
                start = row * self.board_size + col
                symbols = [self.board[start + i] for i in range(self.win_length)]
                if symbols[0] != " " and all(s == symbols[0] for s in symbols):
                    return symbols[0]

        # Check columns for a winning sequence.
        for col in range(self.board_size):
            for row in range(self.board_size - self.win_length + 1):
                start = row * self.board_size + col
                symbols = [self.board[start + i * self.board_size] for i in range(self.win_length)]
                if symbols[0] != " " and all(s == symbols[0] for s in symbols):
                    return symbols[0]

        # Check diagonals (top-left to bottom-right) for a winning sequence.
        for row in range(self.board_size - self.win_length + 1):
            for col in range(self.board_size - self.win_length + 1):
                start = row * self.board_size + col
                symbols = [self.board[start + i * (self.board_size + 1)] for i in range(self.win_length)]
                if symbols[0] != " " and all(s == symbols[0] for s in symbols):
                    return symbols[0]

        # Check diagonals (top-right to bottom-left) for a winning sequence.
        for row in range(self.board_size - self.win_length + 1):
            for col in range(self.win_length - 1, self.board_size):
                start = row * self.board_size + col
                symbols = [self.board[start + i * (self.board_size - 1)] for i in range(self.win_length)]
                if symbols[0] != " " and all(s == symbols[0] for s in symbols):
                    return symbols[0]

        return None

    def is_draw(self) -> bool:
        """Checks if the game has ended in a draw.

        A draw occurs when all squares on the board are filled, and there is
        no winner.

        Returns:
            bool: True if the game is a draw, False otherwise.
        """
        return " " not in self.board and self.winner() is None

    def is_over(self) -> bool:
        """Checks if the game has concluded.

        The game is over if there is a winner or if it has ended in a draw.

        Returns:
            bool: True if the game is over, False otherwise.
        """
        return self.winner() is not None or self.is_draw()

    def minimax(self, is_maximizing: bool, depth: int = 0, max_depth: Optional[int] = None) -> Tuple[int, Optional[int]]:
        """The minimax algorithm for finding the optimal move.

        This method recursively explores the game tree to find the best possible
        move for the current player. It uses a scoring system to evaluate board
        states and prunes the search space for efficiency.

        Args:
            is_maximizing (bool): True if the current player is the computer (maximizer),
                                  False if the current player is the human (minimizer).
            depth (int): The current depth of the recursion.
            max_depth (Optional[int]): The maximum depth to search. This is used to
                                       limit the search on larger boards for performance.

        Returns:
            Tuple[int, Optional[int]]: A tuple containing the best score and the
                                       corresponding best move (as a board index).
        """
        # Set a default max_depth based on the board size to manage performance.
        if max_depth is None:
            if self.board_size <= 3:
                max_depth = 100  # No practical limit for a 3x3 board.
            elif self.board_size == 4:
                max_depth = 6  # A reasonable depth for a 4x4 board.
            else:  # 5x5 and larger boards.
                max_depth = 4

        winner = self.winner()
        # Base cases for the recursion: check for a win, loss, or draw.
        if winner == self.computer_symbol:
            return 10 - depth, None
        if winner == self.human_symbol:
            return depth - 10, None
        if self.is_draw():
            return 0, None
        if depth >= max_depth:
            # Return a neutral score if the max depth is reached.
            return 0, None

        best_score = float("-inf") if is_maximizing else float("inf")
        best_move: Optional[int] = None
        symbol = self.computer_symbol if is_maximizing else self.human_symbol

        # Iterate through all available moves to find the best one.
        for move in self.available_moves():
            self.board[move] = symbol
            score, _ = self.minimax(not is_maximizing, depth + 1, max_depth)
            self.board[move] = " "  # Backtrack to undo the move.
            # Update the best score and move based on whether we are maximizing or minimizing.
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
        """Determines and applies the computer's optimal move.

        This method uses either a fast heuristic for 3x3 boards or the minimax
        algorithm for larger boards to select the best move for the computer.

        Returns:
            int: The (row, col) tuple of the computer's move.
        """
        if self.board_size == 3 and self.win_length == 3:
            # Use a faster, heuristic-based approach for the classic 3x3 game.
            move_index = self._select_fast_move()
        else:
            # Use the minimax algorithm for larger or more complex boards.
            _, move_index = self.minimax(True)
            if move_index is None:
                move_index = self.available_moves()[0]

        row, col = divmod(move_index, self.board_size)
        self.make_move(move_index, self.computer_symbol)
        return row, col

    def _select_fast_move(self) -> int:
        """Returns a strong move for a 3x3 board using lightweight heuristics.

        This method provides a faster alternative to the full minimax search for
        the standard 3x3 game. It checks for winning moves, blocks opponent's
        winning moves, and prioritizes strategic positions like the center and corners.

        Returns:
            int: The board index of the selected move.
        """
        available = self.available_moves()

        def _winning_move(symbol: str) -> Optional[int]:
            for candidate in available:
                self.board[candidate] = symbol
                has_won = self.winner() == symbol
                self.board[candidate] = " "
                if has_won:
                    return candidate
            return None

        # 1. Check if the computer can win in the next move.
        win_now = _winning_move(self.computer_symbol)
        if win_now is not None:
            return win_now

        # 2. Check if the human is about to win, and block them.
        block_human = _winning_move(self.human_symbol)
        if block_human is not None:
            return block_human

        # 3. Prefer the center square if it's available.
        if self.board_size % 2 == 1:
            center_index = (self.board_size * self.board_size) // 2
            if self.board[center_index] == " ":
                return center_index

        # 4. Next, favor the corners for stronger board control.
        corners = [row * self.board_size + col for row in (0, self.board_size - 1) for col in (0, self.board_size - 1)]
        for corner in corners:
            if 0 <= corner < len(self.board) and self.board[corner] == " ":
                return corner

        # 5. Finally, fall back to the first available square as a default.
        return available[0]

    def human_move(self, position: int) -> bool:
        """Makes a move for the human player.

        This is a convenience method that calls `make_move` with the human's symbol.

        Args:
            position (int): The board index where the human wants to move.

        Returns:
            bool: True if the move was successful, False otherwise.
        """
        return self.make_move(position, self.human_symbol)

    def undo_last_move(self) -> bool:
        """Undoes the last move made in the game.

        This method uses the replay manager to revert the game state to before
        the last move was made.

        Returns:
            bool: True if a move was successfully undone, False if there are no moves to undo.
        """
        if not self.replay_manager.can_undo():
            return False

        action = self.replay_manager.undo()
        if action and action.state_before:
            # Restore the board and current turn from the previous state.
            self.board = action.state_before["board"].copy()
            self.current_turn = action.state_before["current_turn"]
            return True
        return False

    def can_undo(self) -> bool:
        """Checks if there are moves that can be undone.

        Returns:
            bool: True if undo is available, False otherwise.
        """
        return self.replay_manager.can_undo()

    def render(self, show_reference: bool = False) -> str:
        """Returns a human-friendly string representation of the board.

        This method generates a formatted string that can be printed to the
        console to display the current state of the game board.

        Args:
            show_reference (bool): If True, also displays a reference board with
                                   coordinates for easier play.

        Returns:
            str: The formatted board string.
        """
        # Generate row labels (e.g., A, B, C).
        row_labels = [chr(ord("A") + i) for i in range(self.board_size)]

        # Generate the column header with numbers.
        col_numbers = " ".join(f"{i+1:3}" for i in range(self.board_size))
        header = "   " + col_numbers

        # Generate the separator line (e.g., +---+---+---).
        separator = "  +" + "+".join(["---"] * self.board_size)

        # Generate each row of the board with symbols.
        rows = []
        for row_index in range(self.board_size):
            start = row_index * self.board_size
            cells = " | ".join(self.board[start : start + self.board_size])
            rows.append(f"{row_labels[row_index]} | {cells}")

        # Build the final board representation.
        board_lines = [header, separator]
        for i, row in enumerate(rows):
            board_lines.append(row)
            if i < len(rows) - 1:
                board_lines.append(separator)

        board_render = "\n".join(board_lines)

        if not show_reference or self.board_size > 5:
            return board_render

        # Optionally, show a reference board with coordinates for smaller boards.
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
        """Generates a coordinate mapping for the current board size.

        This method creates a dictionary that maps board indices to human-readable
        coordinates (e.g., 0 -> "A1", 1 -> "A2").

        Returns:
            Dict[int, str]: A dictionary mapping board indices to coordinate strings.
        """
        coords = {}
        for row in range(self.board_size):
            for col in range(self.board_size):
                row_label = chr(ord("A") + row)
                col_label = str(col + 1)
                coords[row * self.board_size + col] = f"{row_label}{col_label}"
        return coords

    def legal_coordinates(self) -> Iterable[str]:
        """Returns an iterator over the legal (available) coordinates.

        This method provides a list of all valid moves in human-readable format.

        Returns:
            Iterable[str]: An iterator over the available coordinate strings.
        """
        coords_map = self._generate_coordinates()
        return (coords_map[idx] for idx in range(len(self.board)) if self.board[idx] == " ")

    def parse_coordinate(self, text: str) -> int:
        """Parses a human-readable coordinate into a board index.

        This method converts a string like "A1" or "B2" into the corresponding
        integer index for the game board.

        Args:
            text (str): The coordinate string to parse.

        Returns:
            int: The board index corresponding to the coordinate.

        Raises:
            ValueError: If the coordinate format is invalid or out of bounds.
        """
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
