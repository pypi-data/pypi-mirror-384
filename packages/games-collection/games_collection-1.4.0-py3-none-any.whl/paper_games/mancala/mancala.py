"""Mancala (Kalah) engine with capture rules and a strategy AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from common.game_engine import GameEngine, GameState


@dataclass(frozen=True)
class MancalaMove:
    """Representation of a Mancala move by pit index."""

    pit_index: int


class MancalaGame(GameEngine[MancalaMove, int]):
    """Implementation of Mancala with stone sowing and captures."""

    pits_per_side = 6
    stores = 2

    def __init__(self, stones_per_pit: int = 4) -> None:
        self.stones_per_pit = stones_per_pit
        self._board: List[int] = []
        self._current_player = 0
        self._winner: Optional[int] = None
        self._state = GameState.NOT_STARTED
        self.reset()

    def reset(self) -> None:
        """Reset the board to the initial stones distribution."""

        total_pits = self.pits_per_side * 2 + self.stores
        self._board = [self.stones_per_pit] * total_pits
        self._board[self._store_index(0)] = 0
        self._board[self._store_index(1)] = 0
        self._current_player = 0
        self._winner = None
        self._state = GameState.IN_PROGRESS

    def is_game_over(self) -> bool:
        return self._state == GameState.FINISHED

    def get_current_player(self) -> int:
        return self._current_player

    def get_valid_moves(self) -> List[MancalaMove]:
        if self.is_game_over():
            return []
        pits = self._player_pits(self._current_player)
        return [MancalaMove(index) for index in pits if self._board[index] > 0]

    def make_move(self, move: MancalaMove) -> bool:
        if self.is_game_over():
            return False
        if move not in self.get_valid_moves():
            return False
        next_player, finished, winner = self._apply_move(self._board, self._current_player, move.pit_index)
        if finished:
            self._winner = winner
            self._state = GameState.FINISHED
        else:
            self._current_player = next_player
        return True

    def get_winner(self) -> Optional[int]:
        return self._winner

    def get_game_state(self) -> GameState:
        return self._state

    def get_state_representation(self) -> Sequence[int]:
        return tuple(self._board)

    def simulate_move(self, move: MancalaMove) -> Tuple[List[int], int, bool, Optional[int]]:
        board_copy = list(self._board)
        next_player, finished, winner = self._apply_move(board_copy, self._current_player, move.pit_index)
        return board_copy, next_player, finished, winner

    def _apply_move(self, board: List[int], player: int, pit_index: int) -> Tuple[int, bool, Optional[int]]:
        last_index = self._sow_stones(board, player, pit_index)
        self._capture_if_applicable(board, player, last_index)
        finished, winner = self._check_game_end(board)
        if finished:
            return player, True, winner
        if last_index == self._store_index(player):
            return player, False, None
        return self._opponent(player), False, None

    def _sow_stones(self, board: List[int], player: int, pit_index: int) -> int:
        stones = board[pit_index]
        board[pit_index] = 0
        index = pit_index
        while stones > 0:
            index = (index + 1) % len(board)
            if index == self._store_index(self._opponent(player)):
                continue
            board[index] += 1
            stones -= 1
        return index

    def _capture_if_applicable(self, board: List[int], player: int, last_index: int) -> None:
        if last_index == self._store_index(player):
            return
        if last_index not in self._player_pits(player):
            return
        if board[last_index] != 1:
            return
        opposite_index = self._opposite_pit(last_index)
        if board[opposite_index] == 0:
            return
        store_index = self._store_index(player)
        board[store_index] += board[opposite_index] + 1
        board[last_index] = 0
        board[opposite_index] = 0

    def _check_game_end(self, board: List[int]) -> Tuple[bool, Optional[int]]:
        player_zero_empty = all(board[index] == 0 for index in self._player_pits(0))
        player_one_empty = all(board[index] == 0 for index in self._player_pits(1))
        if not (player_zero_empty or player_one_empty):
            return False, None
        if not player_zero_empty:
            self._collect_remaining(board, 0)
        if not player_one_empty:
            self._collect_remaining(board, 1)
        store_zero = board[self._store_index(0)]
        store_one = board[self._store_index(1)]
        if store_zero > store_one:
            return True, 0
        if store_one > store_zero:
            return True, 1
        return True, None

    def _collect_remaining(self, board: List[int], player: int) -> None:
        pits = self._player_pits(player)
        captured = sum(board[index] for index in pits)
        for index in pits:
            board[index] = 0
        board[self._store_index(player)] += captured

    def _player_pits(self, player: int) -> range:
        if player == 0:
            return range(0, self.pits_per_side)
        return range(self.pits_per_side + 1, self.pits_per_side * 2 + 1)

    def _store_index(self, player: int) -> int:
        if player == 0:
            return self.pits_per_side
        return len(self._board) - 1

    def _opposite_pit(self, index: int) -> int:
        return len(self._board) - 2 - index

    def _opponent(self, player: int) -> int:
        return 1 - player


class MancalaAI:
    """Heuristic minimax AI for Mancala."""

    def __init__(self, depth: int = 6) -> None:
        self.depth = depth

    def choose_move(self, game: MancalaGame) -> MancalaMove:
        moves = game.get_valid_moves()
        if not moves:
            raise ValueError("No valid Mancala moves available")
        best_move = moves[0]
        best_score = float("-inf")
        for move in moves:
            board_copy, next_player, finished, winner = game.simulate_move(move)
            score = self._minimax(board_copy, next_player, game.get_current_player(), self.depth - 1, -float("inf"), float("inf"), finished, winner)
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def _minimax(
        self,
        board: List[int],
        current_player: int,
        maximizing_player: int,
        depth: int,
        alpha: float,
        beta: float,
        finished: bool,
        winner: Optional[int],
    ) -> float:
        if finished:
            if winner is None:
                return 0.0
            return 1000.0 if winner == maximizing_player else -1000.0
        if depth == 0:
            return self._evaluate(board, maximizing_player)
        helper = MancalaGame()
        helper._board = list(board)
        helper._current_player = current_player
        moves = helper.get_valid_moves()
        if not moves:
            return self._evaluate(board, maximizing_player)
        if current_player == maximizing_player:
            value = float("-inf")
            for move in moves:
                next_board, next_player, finished_state, winner_state = helper.simulate_move(move)
                value = max(
                    value,
                    self._minimax(next_board, next_player, maximizing_player, depth - 1, alpha, beta, finished_state, winner_state),
                )
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        value = float("inf")
        for move in moves:
            next_board, next_player, finished_state, winner_state = helper.simulate_move(move)
            value = min(
                value,
                self._minimax(next_board, next_player, maximizing_player, depth - 1, alpha, beta, finished_state, winner_state),
            )
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value

    def _evaluate(self, board: List[int], player: int) -> float:
        opponent = 1 - player
        store_diff = board[MancalaGame()._store_index(player)] - board[MancalaGame()._store_index(opponent)]
        pit_diff = sum(board[index] for index in MancalaGame()._player_pits(player)) - sum(board[index] for index in MancalaGame()._player_pits(opponent))
        return store_diff * 3 + pit_diff


class MancalaCLI:
    """Simple text user interface for Mancala."""

    def __init__(self) -> None:
        self._game = MancalaGame()
        self._ai = MancalaAI(depth=5)

    def run(self) -> None:
        while not self._game.is_game_over():
            self._render_board()
            if self._game.get_current_player() == 0:
                move = self._prompt_move()
            else:
                move = self._ai.choose_move(self._game)
                print(f"AI selects pit {move.pit_index}")
            if move is None:
                print("Invalid move selection.")
                continue
            if not self._game.make_move(move):
                print("Move rejected, choose another pit.")
        self._render_board()
        winner = self._game.get_winner()
        if winner is None:
            print("The game ended in a tie.")
        else:
            print(f"Player {winner + 1} wins!")

    def _render_board(self) -> None:
        board = self._game.get_state_representation()
        top_row = list(board[12:6:-1])
        bottom_row = list(board[0:6])
        print("      " + "  ".join(f"{value:2d}" for value in top_row))
        print(f"P2[{board[13]:2d}]" + " " * 17 + f"[{board[6]:2d}]P1")
        print("      " + "  ".join(f"{value:2d}" for value in bottom_row))

    def _prompt_move(self) -> Optional[MancalaMove]:
        try:
            raw = input("Choose a pit (0-5): ")
        except EOFError:
            return None
        if not raw.isdigit():
            return None
        pit_index = int(raw)
        move = MancalaMove(pit_index)
        valid_moves = self._game.get_valid_moves()
        for valid in valid_moves:
            if valid.pit_index == move.pit_index:
                return valid
        return None
