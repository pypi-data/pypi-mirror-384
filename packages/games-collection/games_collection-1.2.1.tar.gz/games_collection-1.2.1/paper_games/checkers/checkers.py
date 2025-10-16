"""Checkers implementation featuring full jump rules and minimax AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from common.game_engine import GameEngine, GameState

Coordinate = Tuple[int, int]
BoardType = List[List[Optional["CheckersPiece"]]]


@dataclass(frozen=True)
class CheckersPiece:
    """Representation of a checkers piece."""

    color: str
    king: bool = False

    def movement_directions(self) -> Tuple[Coordinate, ...]:
        """Return allowed movement deltas for the piece."""

        if self.king:
            return ((-1, -1), (-1, 1), (1, -1), (1, 1))
        if self.color == "black":
            return ((1, -1), (1, 1))
        return ((-1, -1), (-1, 1))


@dataclass(frozen=True)
class CheckersMove:
    """A move defined by a path and captured pieces."""

    path: Tuple[Coordinate, ...]
    captures: Tuple[Coordinate, ...] = ()

    def __post_init__(self) -> None:
        if len(self.path) < 2:
            raise ValueError("A move must include at least a start and end coordinate")

    @property
    def is_jump(self) -> bool:
        """Return whether the move captures opponent pieces."""

        return bool(self.captures)


class CheckersGame(GameEngine[CheckersMove, str]):
    """Checkers engine providing jump chains and king promotion."""

    board_size = 8

    def __init__(self) -> None:
        self._board: BoardType = []
        self._current_player = "black"
        self._winner: Optional[str] = None
        self._state = GameState.NOT_STARTED
        self.reset()

    def reset(self) -> None:
        """Reset the board to the standard initial arrangement."""

        self._board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        for row in range(3):
            for column in range(self.board_size):
                if (row + column) % 2 == 1:
                    self._board[row][column] = CheckersPiece("black")
        for row in range(self.board_size - 3, self.board_size):
            for column in range(self.board_size):
                if (row + column) % 2 == 1:
                    self._board[row][column] = CheckersPiece("white")
        self._current_player = "black"
        self._winner = None
        self._state = GameState.IN_PROGRESS

    def is_game_over(self) -> bool:
        return self._state == GameState.FINISHED

    def get_current_player(self) -> str:
        return self._current_player

    def get_valid_moves(self) -> List[CheckersMove]:
        if self.is_game_over():
            return []
        capturing, normal = self._collect_moves(self._board, self._current_player)
        return capturing if capturing else normal

    def make_move(self, move: CheckersMove) -> bool:
        if self.is_game_over():
            return False
        valid_moves = self.get_valid_moves()
        if move not in valid_moves:
            return False
        next_player, winner, draw = self._apply_move_on_board(self._board, move, self._current_player)
        if draw:
            self._winner = None
            self._state = GameState.FINISHED
            return True
        if winner is not None:
            self._winner = winner
            self._state = GameState.FINISHED
            return True
        self._current_player = next_player
        return True

    def get_winner(self) -> Optional[str]:
        return self._winner

    def get_game_state(self) -> GameState:
        return self._state

    def get_state_representation(self) -> Sequence[Sequence[Optional[Tuple[str, bool]]]]:
        return tuple(tuple((piece.color, piece.king) if piece else None for piece in row) for row in self._board)

    def clone_board(self) -> BoardType:
        return [[piece for piece in row] for row in self._board]

    def simulate_move(self, move: CheckersMove) -> Tuple[BoardType, str, Optional[str], bool]:
        board_copy = self.clone_board()
        next_player, winner, draw = self._apply_move_on_board(board_copy, move, self._current_player)
        return board_copy, next_player, winner, draw

    def _collect_moves(self, board: BoardType, player: str) -> Tuple[List[CheckersMove], List[CheckersMove]]:
        capturing: List[CheckersMove] = []
        normal: List[CheckersMove] = []
        for row, column in self._iter_player_pieces(board, player):
            piece = board[row][column]
            capturing.extend(self._find_jump_sequences(board, (row, column), piece))
            if capturing:
                continue
            normal.extend(self._find_simple_moves(board, (row, column), piece))
        return capturing, normal

    def _iter_player_pieces(self, board: BoardType, player: str) -> Iterable[Coordinate]:
        for row in range(self.board_size):
            for column in range(self.board_size):
                piece = board[row][column]
                if piece and piece.color == player:
                    yield (row, column)

    def _find_simple_moves(self, board: BoardType, position: Coordinate, piece: CheckersPiece) -> List[CheckersMove]:
        moves: List[CheckersMove] = []
        for delta_row, delta_column in piece.movement_directions():
            target = (position[0] + delta_row, position[1] + delta_column)
            if not self._is_on_board(target):
                continue
            if board[target[0]][target[1]] is None:
                move = CheckersMove(path=(position, target))
                moves.append(move)
        return moves

    def _find_jump_sequences(self, board: BoardType, position: Coordinate, piece: CheckersPiece) -> List[CheckersMove]:
        return self._search_captures(board, position, piece, [position], [])

    def _search_captures(
        self,
        board: BoardType,
        position: Coordinate,
        piece: CheckersPiece,
        path: List[Coordinate],
        captures: List[Coordinate],
    ) -> List[CheckersMove]:
        results: List[CheckersMove] = []
        for delta_row, delta_column in piece.movement_directions():
            middle = (position[0] + delta_row, position[1] + delta_column)
            landing = (position[0] + 2 * delta_row, position[1] + 2 * delta_column)
            if not self._is_on_board(middle) or not self._is_on_board(landing):
                continue
            middle_piece = board[middle[0]][middle[1]]
            if middle_piece is None or middle_piece.color == piece.color:
                continue
            if board[landing[0]][landing[1]] is not None:
                continue
            board_copy = self._clone_board(board)
            board_copy[position[0]][position[1]] = None
            board_copy[middle[0]][middle[1]] = None
            promoted_piece = piece
            if not piece.king and self._should_promote(piece.color, landing[0]):
                promoted_piece = CheckersPiece(piece.color, True)
            board_copy[landing[0]][landing[1]] = promoted_piece
            extended_path = path + [landing]
            extended_captures = captures + [middle]
            if promoted_piece.king and not piece.king:
                results.append(CheckersMove(path=tuple(extended_path), captures=tuple(extended_captures)))
                continue
            child_moves = self._search_captures(board_copy, landing, promoted_piece, extended_path, extended_captures)
            if child_moves:
                results.extend(child_moves)
            else:
                results.append(CheckersMove(path=tuple(extended_path), captures=tuple(extended_captures)))
        return results

    def _apply_move_on_board(self, board: BoardType, move: CheckersMove, player: str) -> Tuple[str, Optional[str], bool]:
        start_row, start_column = move.path[0]
        piece = board[start_row][start_column]
        if piece is None or piece.color != player:
            raise ValueError("Invalid move application: piece mismatch")
        board[start_row][start_column] = None
        for intermediate in move.path[1:-1]:
            board[intermediate[0]][intermediate[1]] = None
        for capture in move.captures:
            board[capture[0]][capture[1]] = None
        end_row, end_column = move.path[-1]
        promote = not piece.king and self._should_promote(piece.color, end_row)
        board[end_row][end_column] = CheckersPiece(piece.color, king=piece.king or promote)
        opponent = self._opponent(player)
        if not self._has_pieces(board, opponent):
            return player, player, False
        opponent_captures, opponent_normal = self._collect_moves(board, opponent)
        opponent_moves = opponent_captures if opponent_captures else opponent_normal
        if not opponent_moves:
            player_captures, player_normal = self._collect_moves(board, player)
            player_moves = player_captures if player_captures else player_normal
            if not player_moves:
                return player, None, True
            return player, player, False
        if not self._has_pieces(board, player):
            return opponent, opponent, False
        return opponent, None, False

    def _should_promote(self, color: str, row: int) -> bool:
        return (color == "black" and row == self.board_size - 1) or (color == "white" and row == 0)

    def _has_pieces(self, board: BoardType, player: str) -> bool:
        return any(piece for row in board for piece in row if piece and piece.color == player)

    def _is_on_board(self, position: Coordinate) -> bool:
        return 0 <= position[0] < self.board_size and 0 <= position[1] < self.board_size

    def _opponent(self, player: str) -> str:
        return "white" if player == "black" else "black"

    def _clone_board(self, board: BoardType) -> BoardType:
        return [[piece for piece in row] for row in board]


class CheckersAI:
    """Minimax-based opponent for Checkers."""

    def __init__(self, depth: int = 6) -> None:
        self.depth = depth
        self._helper = CheckersGame()

    def choose_move(self, game: CheckersGame) -> CheckersMove:
        moves = game.get_valid_moves()
        if not moves:
            raise ValueError("No valid moves available for the AI")
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
        self,
        board: BoardType,
        current_player: str,
        maximizing_player: str,
        depth: int,
        alpha: float,
        beta: float,
        winner: Optional[str],
        draw: bool,
    ) -> float:
        if winner is not None:
            return 1000.0 if winner == maximizing_player else -1000.0
        if draw:
            return 0.0
        if depth == 0:
            return self._evaluate(board, maximizing_player)
        capturing, normal = self._helper._collect_moves(board, current_player)
        moves = capturing if capturing else normal
        if not moves:
            if current_player == maximizing_player:
                return -1000.0
            return 1000.0
        if current_player == maximizing_player:
            value = float("-inf")
            for move in moves:
                board_copy = self._helper._clone_board(board)
                next_player, winner, draw = self._helper._apply_move_on_board(board_copy, move, current_player)
                value = max(value, self._minimax(board_copy, next_player, maximizing_player, depth - 1, alpha, beta, winner, draw))
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        value = float("inf")
        for move in moves:
            board_copy = self._helper._clone_board(board)
            next_player, winner, draw = self._helper._apply_move_on_board(board_copy, move, current_player)
            value = min(value, self._minimax(board_copy, next_player, maximizing_player, depth - 1, alpha, beta, winner, draw))
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value

    def _evaluate(self, board: BoardType, player: str) -> float:
        score = 0.0
        for row_index, row in enumerate(board):
            for column_index, piece in enumerate(row):
                if piece is None:
                    continue
                multiplier = 1.0 if piece.color == player else -1.0
                king_bonus = 1.5 if piece.king else 1.0
                advancement = (row_index if piece.color == "black" else (CheckersGame.board_size - 1 - row_index)) / 10.0
                score += multiplier * (king_bonus + advancement)
        return score


class CheckersCLI:
    """Command line interface for Checkers."""

    def __init__(self) -> None:
        self._game = CheckersGame()
        self._ai = CheckersAI(depth=4)

    def run(self) -> None:
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
        if winner is None:
            print("The game is a draw.")
        else:
            print(f"{winner.title()} wins the game!")

    def _render_board(self) -> None:
        print("  " + " ".join(str(column) for column in range(self._game.board_size)))
        for row_index, row in enumerate(self._game.get_state_representation()):
            printable = []
            for cell in row:
                if cell is None:
                    printable.append(".")
                else:
                    symbol = "b" if cell[0] == "black" else "w"
                    if cell[1]:
                        symbol = symbol.upper()
                    printable.append(symbol)
            print(f"{row_index} " + " ".join(printable))

    def _prompt_player_move(self) -> Optional[CheckersMove]:
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
        move = CheckersMove(path=((start_row, start_col), (end_row, end_col)))
        valid_moves = self._game.get_valid_moves()
        for valid in valid_moves:
            if valid.path[:2] == move.path:
                return valid
        return None
