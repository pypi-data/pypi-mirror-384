"""A comprehensive Checkers implementation with full jump rules and a minimax AI.

This module provides a complete Checkers game engine, an AI opponent, and a
command-line interface. The game engine correctly implements all standard
rules, including forced captures, multi-jump (king) moves, and promotion.

The AI uses the minimax algorithm with alpha-beta pruning to determine the
best move, providing a challenging opponent. The CLI allows for interactive
gameplay in a terminal.

Classes:
    CheckersPiece: Represents a single piece on the board.
    CheckersMove: Defines a move, including its path and any captured pieces.
    CheckersGame: The main game engine that manages state and enforces rules.
    CheckersAI: A minimax-based AI opponent.
    CheckersCLI: A command-line interface for playing the game.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from common.game_engine import GameEngine, GameState

# Type aliases for clarity.
Coordinate = Tuple[int, int]
BoardType = List[List[Optional["CheckersPiece"]]]


@dataclass(frozen=True)
class CheckersPiece:
    """Represents a single checkers piece.

    Attributes:
        color (str): The color of the piece ("black" or "white").
        king (bool): True if the piece is a king, False otherwise.
    """

    color: str
    king: bool = False

    def movement_directions(self) -> Tuple[Coordinate, ...]:
        """Returns the allowed movement deltas for the piece based on its
        type (regular or king) and color.
        """
        if self.king:
            return ((-1, -1), (-1, 1), (1, -1), (1, 1))
        return ((1, -1), (1, 1)) if self.color == "black" else ((-1, -1), (-1, 1))


@dataclass(frozen=True)
class CheckersMove:
    """Represents a move, defined by a path of coordinates and captured pieces.

    Attributes:
        path (Tuple[Coordinate, ...]): A sequence of coordinates representing the
                                       path of the move.
        captures (Tuple[Coordinate, ...]): A sequence of coordinates of the
                                           pieces captured during the move.
    """

    path: Tuple[Coordinate, ...]
    captures: Tuple[Coordinate, ...] = ()

    def __post_init__(self) -> None:
        if len(self.path) < 2:
            raise ValueError("A move must include at least a start and end coordinate.")

    @property
    def is_jump(self) -> bool:
        """Returns True if the move involves capturing one or more pieces."""
        return bool(self.captures)


class CheckersGame(GameEngine[CheckersMove, str]):
    """A Checkers game engine that implements standard rules, including
    forced captures, jump chains, and king promotion.
    """

    board_size = 8

    def __init__(self) -> None:
        self._board: BoardType = []
        self._current_player = "black"
        self._winner: Optional[str] = None
        self._state = GameState.NOT_STARTED
        self.reset()

    def reset(self) -> None:
        """Resets the board to the standard initial arrangement."""
        self._board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        for row in range(3):
            for col in range(self.board_size):
                if (row + col) % 2 == 1:
                    self._board[row][col] = CheckersPiece("black")
        for row in range(self.board_size - 3, self.board_size):
            for col in range(self.board_size):
                if (row + col) % 2 == 1:
                    self._board[row][col] = CheckersPiece("white")
        self._current_player = "black"
        self._winner = None
        self._state = GameState.IN_PROGRESS

    def is_game_over(self) -> bool:
        """Returns True if the game has finished."""
        return self._state == GameState.FINISHED

    def get_current_player(self) -> str:
        """Returns the color of the current player."""
        return self._current_player

    def get_valid_moves(self) -> List[CheckersMove]:
        """Returns a list of all valid moves for the current player.
        If captures are possible, only capturing moves are returned.
        """
        if self.is_game_over():
            return []
        capturing, normal = self._collect_moves(self._board, self._current_player)
        return capturing if capturing else normal

    def make_move(self, move: CheckersMove) -> bool:
        """Applies a move to the board and updates the game state.

        Args:
            move (CheckersMove): The move to be made.

        Returns:
            bool: True if the move was valid and applied, False otherwise.
        """
        if self.is_game_over() or move not in self.get_valid_moves():
            return False
        next_player, winner, draw = self._apply_move_on_board(self._board, move, self._current_player)
        if draw:
            self._winner = None
            self._state = GameState.FINISHED
        elif winner is not None:
            self._winner = winner
            self._state = GameState.FINISHED
        else:
            self._current_player = next_player
        return True

    def get_winner(self) -> Optional[str]:
        """Returns the color of the winning player, or None for a draw or ongoing game."""
        return self._winner

    def get_game_state(self) -> GameState:
        """Returns the current state of the game (e.g., IN_PROGRESS, FINISHED)."""
        return self._state

    def get_state_representation(self) -> Sequence[Sequence[Optional[Tuple[str, bool]]]]:
        """Returns a serializable representation of the board state."""
        return tuple(tuple((p.color, p.king) if p else None for p in row) for row in self._board)

    def clone_board(self) -> BoardType:
        """Creates a deep copy of the current board."""
        return [[piece for piece in row] for row in self._board]

    def simulate_move(self, move: CheckersMove) -> Tuple[BoardType, str, Optional[str], bool]:
        """Simulates a move on a copy of the board to evaluate its outcome.

        Args:
            move (CheckersMove): The move to simulate.

        Returns:
            A tuple containing the new board state, the next player, the winner (if any),
            and a flag indicating a draw.
        """
        board_copy = self.clone_board()
        next_player, winner, draw = self._apply_move_on_board(board_copy, move, self._current_player)
        return board_copy, next_player, winner, draw

    def _collect_moves(self, board: BoardType, player: str) -> Tuple[List[CheckersMove], List[CheckersMove]]:
        """Collects all possible capturing and non-capturing moves for a player."""
        capturing: List[CheckersMove] = []
        normal: List[CheckersMove] = []
        for row, col in self._iter_player_pieces(board, player):
            piece = board[row][col]
            # If any jump is found, we can ignore simple moves for this piece.
            jumps = self._find_jump_sequences(board, (row, col), piece)
            if jumps:
                capturing.extend(jumps)
            else:
                normal.extend(self._find_simple_moves(board, (row, col), piece))
        return capturing, normal

    def _iter_player_pieces(self, board: BoardType, player: str) -> Iterable[Coordinate]:
        """Yields the coordinates of all pieces belonging to a player."""
        for r in range(self.board_size):
            for c in range(self.board_size):
                piece = board[r][c]
                if piece and piece.color == player:
                    yield (r, c)

    def _find_simple_moves(self, board: BoardType, pos: Coordinate, piece: CheckersPiece) -> List[CheckersMove]:
        """Finds all simple (non-capturing) moves for a piece."""
        moves: List[CheckersMove] = []
        for dr, dc in piece.movement_directions():
            target = (pos[0] + dr, pos[1] + dc)
            if self._is_on_board(target) and board[target[0]][target[1]] is None:
                moves.append(CheckersMove(path=(pos, target)))
        return moves

    def _find_jump_sequences(self, board: BoardType, pos: Coordinate, piece: CheckersPiece) -> List[CheckersMove]:
        """Finds all possible jump sequences (including multi-jumps) for a piece."""
        return self._search_captures(board, pos, piece, [pos], [])

    def _search_captures(
        self, board: BoardType, pos: Coordinate, piece: CheckersPiece, path: List[Coordinate], captures: List[Coordinate]
    ) -> List[CheckersMove]:
        """Recursively searches for all possible jump sequences from a given position."""
        results: List[CheckersMove] = []
        for dr, dc in piece.movement_directions():
            middle = (pos[0] + dr, pos[1] + dc)
            landing = (pos[0] + 2 * dr, pos[1] + 2 * dc)

            if not (self._is_on_board(middle) and self._is_on_board(landing)):
                continue

            middle_piece = board[middle[0]][middle[1]]
            if not (middle_piece and middle_piece.color != piece.color and board[landing[0]][landing[1]] is None):
                continue

            board_copy = self._clone_board(board)
            board_copy[pos[0]][pos[1]] = None
            board_copy[middle[0]][middle[1]] = None
            promoted_piece = CheckersPiece(piece.color, True) if not piece.king and self._should_promote(piece.color, landing[0]) else piece
            board_copy[landing[0]][landing[1]] = promoted_piece

            extended_path = path + [landing]
            extended_captures = captures + [middle]

            # If the piece was just promoted, it cannot continue jumping in the same turn.
            if promoted_piece.king and not piece.king:
                results.append(CheckersMove(path=tuple(extended_path), captures=tuple(extended_captures)))
                continue

            # Recursively search for more captures from the landing position.
            child_moves = self._search_captures(board_copy, landing, promoted_piece, extended_path, extended_captures)
            if child_moves:
                results.extend(child_moves)
            else:
                results.append(CheckersMove(path=tuple(extended_path), captures=tuple(extended_captures)))
        return results

    def _apply_move_on_board(self, board: BoardType, move: CheckersMove, player: str) -> Tuple[str, Optional[str], bool]:
        """Applies a move to a given board and determines the outcome."""
        start_row, start_col = move.path[0]
        piece = board[start_row][start_col]
        if not (piece and piece.color == player):
            raise ValueError("Invalid move application: piece mismatch")

        board[start_row][start_col] = None
        for capture in move.captures:
            board[capture[0]][capture[1]] = None

        end_row, end_col = move.path[-1]
        promote = not piece.king and self._should_promote(piece.color, end_row)
        board[end_row][end_col] = CheckersPiece(piece.color, king=piece.king or promote)

        opponent = self._opponent(player)
        if not self._has_pieces(board, opponent) or not self._collect_moves(board, opponent)[0] and not self._collect_moves(board, opponent)[1]:
            return player, player, False  # Current player wins.

        if not self._has_pieces(board, player) or not self._collect_moves(board, player)[0] and not self._collect_moves(board, player)[1]:
            return opponent, opponent, False  # Opponent wins.

        return opponent, None, False  # Game continues.

    def _should_promote(self, color: str, row: int) -> bool:
        """Checks if a piece should be promoted to a king."""
        return (color == "black" and row == self.board_size - 1) or (color == "white" and row == 0)

    def _has_pieces(self, board: BoardType, player: str) -> bool:
        """Checks if a player has any pieces left on the board."""
        return any(p for row in board for p in row if p and p.color == player)

    def _is_on_board(self, pos: Coordinate) -> bool:
        """Checks if a coordinate is within the board's boundaries."""
        return 0 <= pos[0] < self.board_size and 0 <= pos[1] < self.board_size

    def _opponent(self, player: str) -> str:
        """Returns the opposing player's color."""
        return "white" if player == "black" else "black"

    def _clone_board(self, board: BoardType) -> BoardType:
        """Creates a deep copy of a board."""
        return [[piece for piece in row] for row in board]


class CheckersAI:
    """A minimax-based AI opponent for the Checkers game.

    This AI uses alpha-beta pruning to efficiently search the game tree and
    a heuristic evaluation function to score board states.
    """

    def __init__(self, depth: int = 6) -> None:
        self.depth = depth
        self._helper = CheckersGame()

    def choose_move(self, game: CheckersGame) -> CheckersMove:
        """Chooses the best move for the AI using the minimax algorithm.

        Args:
            game (CheckersGame): The current game state.

        Returns:
            CheckersMove: The best move found by the AI.
        """
        moves = game.get_valid_moves()
        if not moves:
            raise ValueError("No valid moves available for the AI.")

        best_score = float("-inf")
        best_move = moves[0]
        for move in moves:
            board_copy, next_player, winner, draw = game.simulate_move(move)
            score = self._minimax(board_copy, next_player, game.get_current_player(), self.depth - 1, -float("inf"), float("inf"), winner, draw)
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def _minimax(
        self, board: BoardType, current_player: str, maximizing_player: str, depth: int, alpha: float, beta: float, winner: Optional[str], draw: bool
    ) -> float:
        """The minimax algorithm with alpha-beta pruning."""
        if winner is not None:
            return 1000.0 if winner == maximizing_player else -1000.0
        if draw:
            return 0.0
        if depth == 0:
            return self._evaluate(board, maximizing_player)

        capturing, normal = self._helper._collect_moves(board, current_player)
        moves = capturing if capturing else normal
        if not moves:
            return -1000.0 if current_player == maximizing_player else 1000.0

        if current_player == maximizing_player:
            value = float("-inf")
            for move in moves:
                board_copy = self._helper._clone_board(board)
                next_player, new_winner, new_draw = self._helper._apply_move_on_board(board_copy, move, current_player)
                value = max(value, self._minimax(board_copy, next_player, maximizing_player, depth - 1, alpha, beta, new_winner, new_draw))
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        else:
            value = float("inf")
            for move in moves:
                board_copy = self._helper._clone_board(board)
                next_player, new_winner, new_draw = self._helper._apply_move_on_board(board_copy, move, current_player)
                value = min(value, self._minimax(board_copy, next_player, maximizing_player, depth - 1, alpha, beta, new_winner, new_draw))
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value

    def _evaluate(self, board: BoardType, player: str) -> float:
        """A heuristic evaluation function for scoring a board state."""
        score = 0.0
        for r, row in enumerate(board):
            for c, piece in enumerate(row):
                if piece:
                    multiplier = 1.0 if piece.color == player else -1.0
                    king_bonus = 1.5 if piece.king else 1.0
                    advancement = (r if piece.color == "black" else (self.board_size - 1 - r)) / 10.0
                    score += multiplier * (king_bonus + advancement)
        return score


class CheckersCLI:
    """A command-line interface for playing Checkers."""

    def __init__(self) -> None:
        self._game = CheckersGame()
        self._ai = CheckersAI(depth=4)

    def run(self) -> None:
        """Starts and manages a game of Checkers in the terminal."""
        while not self._game.is_game_over():
            self._render_board()
            if self._game.get_current_player() == "black":
                move = self._prompt_player_move()
            else:
                move = self._ai.choose_move(self._game)
                print(f"AI moves from {move.path[0]} to {move.path[-1]}")

            if move is None:
                print("Invalid move input. Try again.")
                continue
            if not self._game.make_move(move):
                print("Move rejected. Try again.")

        self._render_board()
        winner = self._game.get_winner()
        print("The game is a draw." if winner is None else f"{winner.title()} wins the game!")

    def _render_board(self) -> None:
        """Renders the current board state to the console."""
        print("  " + " ".join(str(c) for c in range(self._game.board_size)))
        for r, row in enumerate(self._game.get_state_representation()):
            printable = []
            for piece in row:
                if piece is None:
                    printable.append(".")
                else:
                    symbol = "b" if piece[0] == "black" else "w"
                    if piece[1]:  # Is king
                        symbol = symbol.upper()
                    printable.append(symbol)
            print(f"{r} " + " ".join(printable))

    def _prompt_player_move(self) -> Optional[CheckersMove]:
        """Prompts the player for their move and validates it."""
        try:
            raw = input("Enter move as start_row,start_col-end_row,end_col: ")
        except EOFError:
            return None
        try:
            start_str, end_str = raw.split("-")
            start_row, start_col = map(int, start_str.split(","))
            end_row, end_col = map(int, end_str.split(","))
        except ValueError:
            return None

        # Find the full move object that matches the player's input.
        move = CheckersMove(path=((start_row, start_col), (end_row, end_col)))
        for valid_move in self._game.get_valid_moves():
            if valid_move.path[:2] == move.path:
                return valid_move
        return None
