"""Connect Four implementation with event-driven architecture and autosave."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from common.architecture.events import EventBus, GameEventType
from common.architecture.persistence import SaveLoadManager
from common.game_engine import GameEngine, GameState

_AUTOSAVE_NAME = "connect_four_autosave"
_AUTOSAVE_PATH = Path("./saves") / f"{_AUTOSAVE_NAME}.save"


@dataclass(frozen=True)
class ConnectFourMove:
    """Representation of a Connect Four move."""

    column: int


class ConnectFourGame(GameEngine[ConnectFourMove, int]):
    """Connect Four implementation with gravity, events, and persistence helpers."""

    def __init__(
        self,
        rows: int = 6,
        columns: int = 7,
        connect_length: int = 4,
        *,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        super().__init__(event_bus=event_bus)
        self.rows = rows
        self.columns = columns
        self.connect_length = connect_length
        self._board: List[List[int]] = []
        self._current_player = 1
        self._winner: Optional[int] = None
        self._state = GameState.NOT_STARTED
        self.reset()

    def reset(self) -> None:
        """Reset the board to the initial empty state."""

        self._board = [[0 for _ in range(self.columns)] for _ in range(self.rows)]
        self._current_player = 1
        self._winner = None
        self._state = GameState.IN_PROGRESS
        self.emit_event(
            GameEventType.GAME_INITIALIZED,
            {
                "rows": self.rows,
                "columns": self.columns,
                "connect_length": self.connect_length,
            },
        )
        self.emit_event(
            GameEventType.GAME_START,
            {
                "current_player": self._current_player,
            },
        )

    def is_game_over(self) -> bool:
        """Return whether the game has finished."""

        return self._state == GameState.FINISHED

    def get_current_player(self) -> int:
        """Return the identifier of the current player (1 or 2)."""

        return self._current_player

    def get_valid_moves(self) -> List[ConnectFourMove]:
        """Return all valid column drops for the current board state."""

        if self.is_game_over():
            return []
        return [ConnectFourMove(column=index) for index in range(self.columns) if self._board[0][index] == 0]

    def make_move(self, move: ConnectFourMove) -> bool:
        """Drop a token in the requested column if the move is valid."""

        if self.is_game_over():
            return False
        if move.column < 0 or move.column >= self.columns:
            return False
        drop_row = self._find_drop_row(move.column)
        if drop_row is None:
            return False

        self._board[drop_row][move.column] = self._current_player
        payload: Dict[str, Any] = {
            "player": self._current_player,
            "column": move.column,
            "row": drop_row,
            "board": self.get_state_representation(),
        }

        if self._check_winner(drop_row, move.column):
            self._winner = self._current_player
            self._state = GameState.FINISHED
            payload["result"] = "win"
            self.emit_event(GameEventType.ACTION_PROCESSED, payload)
            self.emit_event(
                GameEventType.GAME_OVER,
                {
                    "winner": self._winner,
                    "board": self.get_state_representation(),
                    "moves_played": self._count_filled_cells(),
                },
            )
        elif not any(cell == 0 for cell in self._board[0]):
            self._winner = None
            self._state = GameState.FINISHED
            payload["result"] = "draw"
            self.emit_event(GameEventType.ACTION_PROCESSED, payload)
            self.emit_event(
                GameEventType.GAME_OVER,
                {
                    "winner": None,
                    "board": self.get_state_representation(),
                    "moves_played": self._count_filled_cells(),
                },
            )
        else:
            self._current_player = 2 if self._current_player == 1 else 1
            payload["result"] = "continue"
            payload["next_player"] = self._current_player
            self.emit_event(GameEventType.ACTION_PROCESSED, payload)
            self.emit_event(
                GameEventType.TURN_COMPLETE,
                {
                    "current_player": self._current_player,
                    "board": self.get_state_representation(),
                },
            )
        return True

    def get_winner(self) -> Optional[int]:
        """Return the winner if the game is finished."""

        return self._winner

    def get_game_state(self) -> GameState:
        """Return the current game state."""

        return self._state

    def get_state_representation(self) -> Sequence[Sequence[int]]:
        """Return a tuple-based representation of the board for serialization."""

        return tuple(tuple(row) for row in self._board)

    def to_state(self) -> Dict[str, Any]:
        """Return a serializable snapshot of the current game state."""

        return {
            "rows": self.rows,
            "columns": self.columns,
            "connect_length": self.connect_length,
            "board": [row.copy() for row in self._board],
            "current_player": self._current_player,
            "winner": self._winner,
            "state": self._state.value,
        }

    @classmethod
    def from_state(
        cls,
        state: Dict[str, Any],
        *,
        event_bus: Optional[EventBus] = None,
    ) -> "ConnectFourGame":
        """Restore a :class:`ConnectFourGame` from serialized state."""

        game: "ConnectFourGame" = cls.__new__(cls)
        GameEngine.__init__(game, event_bus=event_bus)
        game.rows = int(state.get("rows", 6))
        game.columns = int(state.get("columns", 7))
        game.connect_length = int(state.get("connect_length", 4))
        board_state = state.get("board", [[0 for _ in range(game.columns)] for _ in range(game.rows)])
        game._board = [list(map(int, row)) for row in board_state]
        game._current_player = int(state.get("current_player", 1))
        winner = state.get("winner")
        game._winner = None if winner is None else int(winner)
        game_state_value = state.get("state", GameState.IN_PROGRESS.value)
        game._state = GameState(game_state_value)

        game.emit_event(
            GameEventType.GAME_INITIALIZED,
            {
                "rows": game.rows,
                "columns": game.columns,
                "connect_length": game.connect_length,
                "loaded": True,
            },
        )
        if game._state == GameState.FINISHED:
            game.emit_event(
                GameEventType.GAME_OVER,
                {
                    "winner": game._winner,
                    "board": game.get_state_representation(),
                    "loaded": True,
                },
            )
        else:
            game.emit_event(
                GameEventType.GAME_START,
                {
                    "current_player": game._current_player,
                    "loaded": True,
                },
            )

        return game

    def _find_drop_row(self, column: int) -> Optional[int]:
        """Return the row index where the token will land for the given column."""

        for index in range(self.rows - 1, -1, -1):
            if self._board[index][column] == 0:
                return index
        return None

    def _check_winner(self, row: int, column: int) -> bool:
        """Check if the last move created a connect-length line."""

        player = self._board[row][column]
        directions = ((1, 0), (0, 1), (1, 1), (1, -1))
        for delta_row, delta_col in directions:
            if self._count_consecutive(row, column, delta_row, delta_col, player) >= self.connect_length:
                return True
        return False

    def _count_consecutive(self, row: int, column: int, delta_row: int, delta_column: int, player: int) -> int:
        """Count consecutive pieces in both directions for a given vector."""

        total = 1
        total += self._count_single_direction(row, column, delta_row, delta_column, player)
        total += self._count_single_direction(row, column, -delta_row, -delta_column, player)
        return total

    def _count_single_direction(self, row: int, column: int, delta_row: int, delta_column: int, player: int) -> int:
        """Count consecutive pieces in a single direction."""

        count = 0
        current_row, current_column = row + delta_row, column + delta_column
        while 0 <= current_row < self.rows and 0 <= current_column < self.columns:
            if self._board[current_row][current_column] != player:
                break
            count += 1
            current_row += delta_row
            current_column += delta_column
        return count

    def _count_filled_cells(self) -> int:
        """Return the number of occupied cells on the board."""

        return sum(1 for row in self._board for cell in row if cell != 0)


class ConnectFourCLI:
    """Simple text-based interface for Connect Four with autosave."""

    def __init__(
        self,
        rows: int = 6,
        columns: int = 7,
        *,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self._rows = rows
        self._columns = columns
        self._event_bus = event_bus
        self._save_manager = SaveLoadManager()
        self._game = ConnectFourGame(rows=rows, columns=columns, event_bus=event_bus)

    def run(self) -> None:
        """Run a blocking command-line game until completion."""

        resumed_game = self._load_autosave()
        if resumed_game is not None:
            self._game = resumed_game
            print("Resumed saved Connect Four match.")

        while not self._game.is_game_over():
            self._render_board()
            column = self._prompt_move()
            if column is None:
                print("Invalid input. Please try again.")
                continue
            if not self._game.make_move(ConnectFourMove(column=column)):
                print("Column is full or invalid. Try another column.")
                continue
            self._save_autosave()

        self._render_board()
        winner = self._game.get_winner()
        if winner is None:
            print("The game ended in a draw.")
        else:
            print(f"Player {winner} wins!")

        self._clear_autosave()

    def _render_board(self) -> None:
        """Display the current board state to the console."""

        for row in self._game.get_state_representation():
            print("|" + " ".join("." if cell == 0 else ("X" if cell == 1 else "O") for cell in row) + "|")
        print(" " + " ".join(str(index) for index in range(self._game.columns)))

    def _prompt_move(self) -> Optional[int]:
        """Prompt the user for a move and validate the input."""

        try:
            value = input(f"Player {self._game.get_current_player()}, choose a column: ")
        except EOFError:
            return None
        if not value.isdigit():
            return None
        return int(value)

    def _load_autosave(self) -> Optional[ConnectFourGame]:
        """Load an autosaved game if one is available and accepted."""

        if not _AUTOSAVE_PATH.exists():
            return None

        try:
            choice = input("Found a saved Connect Four match. Resume? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = ""

        if not choice.startswith("y"):
            self._save_manager.delete_save(_AUTOSAVE_PATH)
            return None

        try:
            data = self._save_manager.load(_AUTOSAVE_PATH)
        except FileNotFoundError:
            return None

        state = data.get("state", {})
        if not state:
            return None

        return ConnectFourGame.from_state(state, event_bus=self._event_bus)

    def _save_autosave(self) -> None:
        """Persist the current game state to disk."""

        metadata = {
            "current_player": str(self._game.get_current_player()),
            "rows": str(self._game.rows),
            "columns": str(self._game.columns),
        }
        self._save_manager.save("connect_four", self._game.to_state(), save_name=_AUTOSAVE_NAME, metadata=metadata)

    def _clear_autosave(self) -> None:
        """Remove any existing autosave once the match ends."""

        if _AUTOSAVE_PATH.exists():
            self._save_manager.delete_save(_AUTOSAVE_PATH)
