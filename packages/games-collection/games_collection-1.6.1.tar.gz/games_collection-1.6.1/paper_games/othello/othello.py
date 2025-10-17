"""Othello/Reversi engine with disc flipping mechanics and AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from common.game_engine import GameEngine, GameState

Player = str


@dataclass(frozen=True)
class OthelloMove:
    """Representation of an Othello move."""

    row: int
    column: int
    is_pass: bool = False

    def __post_init__(self) -> None:
        if self.is_pass:
            return
        if self.row < 0 or self.column < 0:
            raise ValueError("Board coordinates must be non-negative")


class OthelloGame(GameEngine[OthelloMove, Player]):
    """Game engine implementing standard Othello rules."""

    board_size = 8
    _directions: Tuple[Tuple[int, int], ...] = (
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    )

    def __init__(self) -> None:
        self._board: List[List[str]] = []
        self._current_player: Player = "black"
        self._winner: Optional[Player] = None
        self._state = GameState.NOT_STARTED
        self._consecutive_passes = 0
        self.reset()

    def reset(self) -> None:
        self._board = [["." for _ in range(self.board_size)] for _ in range(self.board_size)]
        mid = self.board_size // 2
        self._board[mid - 1][mid - 1] = "white"
        self._board[mid][mid] = "white"
        self._board[mid - 1][mid] = "black"
        self._board[mid][mid - 1] = "black"
        self._current_player = "black"
        self._winner = None
        self._state = GameState.IN_PROGRESS
        self._consecutive_passes = 0

    def is_game_over(self) -> bool:
        return self._state == GameState.FINISHED

    def get_current_player(self) -> Player:
        return self._current_player

    def get_valid_moves(self) -> List[OthelloMove]:
        if self.is_game_over():
            return []
        moves = self._valid_moves_for(self._board, self._current_player)
        if not moves:
            return [OthelloMove(-1, -1, is_pass=True)]
        return moves

    def make_move(self, move: OthelloMove) -> bool:
        if self.is_game_over():
            return False
        valid_moves = self.get_valid_moves()
        if move not in valid_moves:
            return False
        if move.is_pass:
            self._consecutive_passes += 1
            if self._consecutive_passes == 2:
                self._finalize_game()
                return True
            self._current_player = self._opponent(self._current_player)
            return True
        self._apply_move(self._board, self._current_player, move)
        self._consecutive_passes = 0
        self._current_player = self._opponent(self._current_player)
        if not self._valid_moves_for(self._board, self._current_player):
            self._consecutive_passes += 1
            if self._consecutive_passes == 2:
                self._finalize_game()
                return True
            self._current_player = self._opponent(self._current_player)
            if not self._valid_moves_for(self._board, self._current_player):
                self._finalize_game()
        if self._board_full(self._board):
            self._finalize_game()
        return True

    def get_winner(self) -> Optional[Player]:
        return self._winner

    def get_game_state(self) -> GameState:
        return self._state

    def get_state_representation(self) -> Sequence[Sequence[str]]:
        return tuple(tuple(row) for row in self._board)

    def simulate_move(self, move: OthelloMove) -> Tuple[List[List[str]], Player, bool, Optional[Player], int]:
        board_copy = [row[:] for row in self._board]
        current_player = self._current_player
        pass_count = self._consecutive_passes
        finished, winner, next_player, next_pass_count = self._apply_move_simulation(board_copy, current_player, move, pass_count)
        return board_copy, next_player, finished, winner, next_pass_count

    def _valid_moves_for(self, board: List[List[str]], player: Player) -> List[OthelloMove]:
        moves: List[OthelloMove] = []
        for row in range(self.board_size):
            for column in range(self.board_size):
                if board[row][column] != ".":
                    continue
                flips = self._discs_to_flip(board, player, row, column)
                if flips:
                    moves.append(OthelloMove(row, column))
        return moves

    def _apply_move(self, board: List[List[str]], player: Player, move: OthelloMove) -> None:
        flips = self._discs_to_flip(board, player, move.row, move.column)
        board[move.row][move.column] = player
        for row, column in flips:
            board[row][column] = player

    def _apply_move_simulation(
        self,
        board: List[List[str]],
        player: Player,
        move: OthelloMove,
        pass_count: int,
    ) -> Tuple[bool, Optional[Player], Player, int]:
        if move.is_pass:
            pass_count += 1
            if pass_count >= 2:
                winner = self._determine_winner(board)
                return True, winner, player, pass_count
            return False, None, self._opponent(player), pass_count
        self._apply_move(board, player, move)
        pass_count = 0
        next_player = self._opponent(player)
        if not self._valid_moves_for(board, next_player):
            pass_count += 1
            next_player = self._opponent(next_player)
            if not self._valid_moves_for(board, next_player):
                winner = self._determine_winner(board)
                return True, winner, next_player, pass_count
        if self._board_full(board):
            winner = self._determine_winner(board)
            return True, winner, next_player, pass_count
        return False, None, next_player, pass_count

    def _discs_to_flip(self, board: List[List[str]], player: Player, row: int, column: int) -> List[Tuple[int, int]]:
        flips: List[Tuple[int, int]] = []
        opponent = self._opponent(player)
        for delta_row, delta_column in self._directions:
            path = []
            current_row, current_column = row + delta_row, column + delta_column
            while self._on_board(current_row, current_column) and board[current_row][current_column] == opponent:
                path.append((current_row, current_column))
                current_row += delta_row
                current_column += delta_column
            if not path:
                continue
            if not self._on_board(current_row, current_column):
                continue
            if board[current_row][current_column] != player:
                continue
            flips.extend(path)
        return flips

    def _board_full(self, board: List[List[str]]) -> bool:
        return all(cell != "." for row in board for cell in row)

    def _determine_winner(self, board: List[List[str]]) -> Optional[Player]:
        black_count = sum(cell == "black" for row in board for cell in row)
        white_count = sum(cell == "white" for row in board for cell in row)
        if black_count > white_count:
            return "black"
        if white_count > black_count:
            return "white"
        return None

    def _finalize_game(self) -> None:
        self._state = GameState.FINISHED
        self._winner = self._determine_winner(self._board)

    def _on_board(self, row: int, column: int) -> bool:
        return 0 <= row < self.board_size and 0 <= column < self.board_size

    def _opponent(self, player: Player) -> Player:
        return "white" if player == "black" else "black"


class OthelloAI:
    """Heuristic-based minimax AI for Othello."""

    _weights: Tuple[Tuple[int, ...], ...] = (
        (120, -20, 20, 5, 5, 20, -20, 120),
        (-20, -40, -5, -5, -5, -5, -40, -20),
        (20, -5, 15, 3, 3, 15, -5, 20),
        (5, -5, 3, 3, 3, 3, -5, 5),
        (5, -5, 3, 3, 3, 3, -5, 5),
        (20, -5, 15, 3, 3, 15, -5, 20),
        (-20, -40, -5, -5, -5, -5, -40, -20),
        (120, -20, 20, 5, 5, 20, -20, 120),
    )

    def __init__(self, depth: int = 4) -> None:
        self.depth = depth

    def choose_move(self, game: OthelloGame) -> OthelloMove:
        moves = game.get_valid_moves()
        if not moves:
            raise ValueError("No available Othello moves")
        best_move = moves[0]
        best_score = float("-inf")
        for move in moves:
            board_copy, next_player, finished, winner, pass_count = game.simulate_move(move)
            score = self._minimax(
                board_copy,
                next_player,
                game.get_current_player(),
                self.depth - 1,
                -float("inf"),
                float("inf"),
                finished,
                winner,
                pass_count,
            )
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def _minimax(
        self,
        board: List[List[str]],
        current_player: Player,
        maximizing_player: Player,
        depth: int,
        alpha: float,
        beta: float,
        finished: bool,
        winner: Optional[Player],
        pass_count: int,
    ) -> float:
        if finished:
            if winner is None:
                return 0.0
            return 1000.0 if winner == maximizing_player else -1000.0
        if depth == 0:
            return self._evaluate(board, maximizing_player)
        helper = OthelloGame()
        helper._board = [row[:] for row in board]
        helper._current_player = current_player
        helper._consecutive_passes = pass_count
        moves = helper.get_valid_moves()
        if not moves:
            winner = helper._determine_winner(board)
            return 0.0 if winner is None else (1000.0 if winner == maximizing_player else -1000.0)
        if current_player == maximizing_player:
            value = float("-inf")
            for move in moves:
                next_board, next_player, finished_state, winner_state, pass_state = helper.simulate_move(move)
                value = max(
                    value,
                    self._minimax(
                        next_board,
                        next_player,
                        maximizing_player,
                        depth - 1,
                        alpha,
                        beta,
                        finished_state,
                        winner_state,
                        pass_state,
                    ),
                )
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        value = float("inf")
        for move in moves:
            next_board, next_player, finished_state, winner_state, pass_state = helper.simulate_move(move)
            value = min(
                value,
                self._minimax(
                    next_board,
                    next_player,
                    maximizing_player,
                    depth - 1,
                    alpha,
                    beta,
                    finished_state,
                    winner_state,
                    pass_state,
                ),
            )
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value

    def _evaluate(self, board: List[List[str]], player: Player) -> float:
        opponent = "white" if player == "black" else "black"
        score = 0.0
        for row_index, row in enumerate(board):
            for column_index, cell in enumerate(row):
                weight = self._weights[row_index][column_index]
                if cell == player:
                    score += weight
                elif cell == opponent:
                    score -= weight
        return score


class OthelloCLI:
    """Simple CLI for Othello."""

    def __init__(self) -> None:
        self._game = OthelloGame()
        self._ai = OthelloAI(depth=3)

    def run(self) -> None:
        while not self._game.is_game_over():
            self._render_board()
            moves = self._game.get_valid_moves()
            if self._game.get_current_player() == "black":
                move = self._prompt_move(moves)
            else:
                move = self._ai.choose_move(self._game)
                if move.is_pass:
                    print("AI passes")
                else:
                    print(f"AI plays at ({move.row}, {move.column})")
            if move is None:
                print("Invalid move input.")
                continue
            if not self._game.make_move(move):
                print("Move rejected. Try again.")
        self._render_board()
        winner = self._game.get_winner()
        if winner is None:
            print("The game is a draw.")
        else:
            print(f"{winner.title()} wins!")

    def _render_board(self) -> None:
        header = "  " + " ".join(str(index) for index in range(self._game.board_size))
        print(header)
        for row_index, row in enumerate(self._game.get_state_representation()):
            printable = ["." if cell == "." else cell[0].upper() for cell in row]
            print(f"{row_index} " + " ".join(printable))

    def _prompt_move(self, moves: List[OthelloMove]) -> Optional[OthelloMove]:
        try:
            raw = input("Enter move as row,col or 'pass': ")
        except EOFError:
            return None
        if raw.strip().lower() == "pass":
            for move in moves:
                if move.is_pass:
                    return move
            return None
        try:
            row_str, col_str = raw.split(",")
            row = int(row_str)
            column = int(col_str)
        except ValueError:
            return None
        for move in moves:
            if move.row == row and move.column == column:
                return move
        return None
