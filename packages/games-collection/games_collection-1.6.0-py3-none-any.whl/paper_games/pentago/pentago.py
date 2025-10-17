"""Core logic, command line interface, and AI opponent for Pentago.

Pentago is a two-player abstract strategy game played on a 6x6 board that is
subdivided into four 3x3 quadrants. Players take turns placing a marble of
their colour on an empty space and then rotating one quadrant either clockwise
or counter-clockwise. A player wins by forming a line of five marbles
horizontally, vertically, or diagonally after the rotation step. If both
players achieve five-in-a-row on the same turn the game ends in a draw.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Sequence, Tuple, TypedDict

from common.ai_strategy import HeuristicStrategy
from common.game_engine import GameEngine, GameState

Board = List[List[int]]
RotationDirection = Literal["CW", "CCW"]

BOARD_SIZE = 6
QUADRANT_SIZE = 3
QUADRANTS = (0, 1, 2, 3)
ROTATIONS = ("CW", "CCW")
LINE_VECTORS = ((0, 1), (1, 0), (1, 1), (1, -1))
CENTER_CELLS = ((2, 2), (2, 3), (3, 2), (3, 3))


class PentagoState(TypedDict):
    """Serializable representation of the current game state."""

    board: Tuple[Tuple[int, ...], ...]
    current_player: int
    state: str


@dataclass(frozen=True)
class PentagoMove:
    """Representation of a full Pentago turn."""

    row: int
    column: int
    quadrant: int
    direction: RotationDirection


class PentagoGame(GameEngine[PentagoMove, int]):
    """Game engine implementation for Pentago."""

    def __init__(self) -> None:
        self._board: Board = []
        self._current_player = 1
        self._winner: Optional[int] = None
        self._state = GameState.NOT_STARTED
        self._winning_players: set[int] = set()
        self.reset()

    def reset(self) -> None:
        """Reset the board, winner, and turn information."""

        self._board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self._current_player = 1
        self._winner = None
        self._winning_players.clear()
        self._state = GameState.IN_PROGRESS

    def is_game_over(self) -> bool:
        """Return whether the game has finished."""

        return self._state == GameState.FINISHED

    def get_current_player(self) -> int:
        """Return the identifier of the current player."""

        return self._current_player

    def get_valid_moves(self) -> List[PentagoMove]:
        """Return all placement and rotation combinations that are legal."""

        if self.is_game_over():
            return []
        moves: List[PentagoMove] = []
        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                if self._board[row][column] != 0:
                    continue
                for quadrant in QUADRANTS:
                    for direction in ROTATIONS:
                        moves.append(PentagoMove(row=row, column=column, quadrant=quadrant, direction=direction))
        return moves

    def make_move(self, move: PentagoMove) -> bool:
        """Apply a placement and rotation turn to the current board."""

        if self.is_game_over():
            return False
        if not self.can_place(move.row, move.column):
            return False
        if move.quadrant not in QUADRANTS:
            return False
        if move.direction not in ROTATIONS:
            return False

        self.apply_move_to_board(self._board, move, self._current_player)
        winners = self._detect_winners_on_board(self._board)
        if winners:
            self._state = GameState.FINISHED
            self._winning_players = set(winners)
            if len(winners) == 1:
                self._winner = next(iter(winners))
            else:
                self._winner = None
            return True
        if self._is_board_full(self._board):
            self._state = GameState.FINISHED
            self._winner = None
            self._winning_players.clear()
            return True

        self._winning_players.clear()
        self._current_player = 2 if self._current_player == 1 else 1
        return True

    def get_winner(self) -> Optional[int]:
        """Return the winning player identifier if the game has a single winner."""

        return self._winner

    def get_game_state(self) -> GameState:
        """Return the current game state indicator."""

        return self._state

    def get_state_representation(self) -> PentagoState:
        """Return a serialisable snapshot of the game."""

        board_snapshot = tuple(tuple(cell for cell in row) for row in self._board)
        return PentagoState(board=board_snapshot, current_player=self._current_player, state=self._state.value)

    def get_board_snapshot(self) -> Board:
        """Return a deep copy of the internal board for analysis or rendering."""

        return [row[:] for row in self._board]

    def get_winning_players(self) -> Tuple[int, ...]:
        """Return the players that achieved a winning line on the last turn."""

        return tuple(sorted(self._winning_players))

    def can_place(self, row: int, column: int) -> bool:
        """Return whether a marble can be placed at the requested location."""

        if not self._is_within_bounds(row, column):
            return False
        return self._board[row][column] == 0

    @staticmethod
    def apply_move_to_board(board: Board, move: PentagoMove, player: int) -> None:
        """Apply a Pentago move to the provided board representation."""

        board[move.row][move.column] = player
        PentagoGame._rotate_quadrant_on_board(board, move.quadrant, move.direction)

    @staticmethod
    def _rotate_quadrant_on_board(board: Board, quadrant: int, direction: RotationDirection) -> None:
        """Rotate a 3x3 quadrant either clockwise or counter-clockwise."""

        row_offset = (quadrant // 2) * QUADRANT_SIZE
        column_offset = (quadrant % 2) * QUADRANT_SIZE
        quadrant_cells = [row[column_offset : column_offset + QUADRANT_SIZE] for row in board[row_offset : row_offset + QUADRANT_SIZE]]
        if direction == "CW":
            rotated = [[quadrant_cells[QUADRANT_SIZE - 1 - column][row] for column in range(QUADRANT_SIZE)] for row in range(QUADRANT_SIZE)]
        else:
            rotated = [[quadrant_cells[column][QUADRANT_SIZE - 1 - row] for column in range(QUADRANT_SIZE)] for row in range(QUADRANT_SIZE)]
        for local_row in range(QUADRANT_SIZE):
            for local_column in range(QUADRANT_SIZE):
                board[row_offset + local_row][column_offset + local_column] = rotated[local_row][local_column]

    @staticmethod
    def _detect_winners_on_board(board: Board) -> set[int]:
        """Return the set of players that currently have five-in-a-row."""

        winners: set[int] = set()
        for player in (1, 2):
            if PentagoGame._has_five_in_a_row(board, player):
                winners.add(player)
        return winners

    @staticmethod
    def _has_five_in_a_row(board: Board, player: int) -> bool:
        """Return whether the player has a contiguous line of five marbles."""

        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                if board[row][column] != player:
                    continue
                for delta_row, delta_column in LINE_VECTORS:
                    if PentagoGame._is_line_start(board, row, column, delta_row, delta_column, player):
                        if PentagoGame._line_length(board, row, column, delta_row, delta_column, player) >= 5:
                            return True
        return False

    @staticmethod
    def _is_line_start(board: Board, row: int, column: int, delta_row: int, delta_column: int, player: int) -> bool:
        """Return whether the coordinate is the start of a line for the player."""

        previous_row = row - delta_row
        previous_column = column - delta_column
        if not PentagoGame._is_within_bounds(previous_row, previous_column):
            return True
        return board[previous_row][previous_column] != player

    @staticmethod
    def _line_length(board: Board, row: int, column: int, delta_row: int, delta_column: int, player: int) -> int:
        """Return the length of the contiguous line from the starting coordinate."""

        length = 0
        current_row, current_column = row, column
        while PentagoGame._is_within_bounds(current_row, current_column) and board[current_row][current_column] == player:
            length += 1
            current_row += delta_row
            current_column += delta_column
        return length

    @staticmethod
    def _is_board_full(board: Board) -> bool:
        """Return whether the board has no empty cells."""

        return all(cell != 0 for row in board for cell in row)

    @staticmethod
    def _is_within_bounds(row: int, column: int) -> bool:
        """Return whether the coordinates are within the board boundaries."""

        return 0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE

    @staticmethod
    def _max_line_length(board: Board, player: int) -> int:
        """Return the longest contiguous line of marbles for the given player."""

        maximum = 0
        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                if board[row][column] != player:
                    continue
                for delta_row, delta_column in LINE_VECTORS:
                    if PentagoGame._is_line_start(board, row, column, delta_row, delta_column, player):
                        maximum = max(maximum, PentagoGame._line_length(board, row, column, delta_row, delta_column, player))
        return maximum


class PentagoAI:
    """Heuristic based AI opponent that evaluates full Pentago turns."""

    def __init__(self, player: int = 2) -> None:
        self.player = player
        self._strategy = HeuristicStrategy(self._evaluate_move)

    def choose_move(self, game: PentagoGame) -> PentagoMove:
        """Return the highest scoring move for the current game state."""

        valid_moves = game.get_valid_moves()
        return self._strategy.select_move(valid_moves, game)

    def _evaluate_move(self, move: PentagoMove, game: PentagoGame) -> float:
        """Return a heuristic score for the provided move."""

        board_copy = game.get_board_snapshot()
        PentagoGame.apply_move_to_board(board_copy, move, game.get_current_player())
        winners = PentagoGame._detect_winners_on_board(board_copy)
        opponent = 1 if self.player == 2 else 2
        if self.player in winners and opponent not in winners:
            return 1_000_000.0
        if opponent in winners and self.player not in winners:
            return -1_000_000.0
        if len(winners) == 2:
            return 5_000.0
        if PentagoGame._is_board_full(board_copy):
            return 0.0

        my_longest = PentagoGame._max_line_length(board_copy, self.player)
        opponent_longest = PentagoGame._max_line_length(board_copy, opponent)
        centre_control = sum(1 for row, column in CENTER_CELLS if board_copy[row][column] == self.player)
        return (my_longest - opponent_longest) * 100.0 + centre_control * 5.0


class PentagoCLI:
    """Command line interface for local human or solo play."""

    TOKEN_MAP: Dict[int, str] = {0: ".", 1: "X", 2: "O"}

    def __init__(self) -> None:
        self.game = PentagoGame()
        self._ai: Optional[PentagoAI] = None

    def run(self) -> None:
        """Run the Pentago command line application."""

        print("Pentago - place a marble then rotate a quadrant.")
        print("Enter 'q' at any prompt to exit. Board coordinates use 1-based indices.")
        solo_mode = self._prompt_mode()
        if solo_mode is None:
            print("Exiting Pentago.")
            return
        if solo_mode:
            self._ai = PentagoAI(player=2)
            print("You are Player 1 (X). The AI plays as Player 2 (O).")
        else:
            print("Two-player mode. Player 1 uses X, Player 2 uses O.")

        while not self.game.is_game_over():
            print()
            print("Current board:")
            self._render_board()
            current_player = self.game.get_current_player()
            if self._ai and current_player == self._ai.player:
                self._handle_ai_turn()
            else:
                if not self._handle_human_turn(current_player):
                    print("Exiting Pentago.")
                    return

        print()
        print("Final board:")
        self._render_board()
        winners = self.game.get_winning_players()
        if len(winners) == 1:
            print(f"Player {winners[0]} wins!")
        elif len(winners) > 1:
            print("Both players completed five-in-a-row. The game is a draw!")
        else:
            print("The game ended in a draw.")

    def _prompt_mode(self) -> Optional[bool]:
        """Return True for solo play, False for local play, or None to exit."""

        while True:
            try:
                response = input("Choose mode: [1] Two players, [2] Solo vs AI (default 2): ").strip()
            except EOFError:
                return None
            if not response:
                return True
            lowered = response.lower()
            if lowered in {"q", "quit"}:
                return None
            if lowered == "1":
                return False
            if lowered == "2":
                return True
            print("Invalid selection. Please choose 1 or 2.")

    def _handle_human_turn(self, player: int) -> bool:
        """Solicit a full move from a human player."""

        while True:
            placement = self._prompt_placement(player)
            if placement is None:
                return False
            row, column = placement
            if not self.game.can_place(row, column):
                print("That space is not available. Choose another.")
                continue
            print("Board after placement:")
            preview_board = self._board_with_placement(row, column, player)
            self._render_board(preview_board)
            rotation = self._prompt_rotation()
            if rotation is None:
                return False
            quadrant, direction = rotation
            move = PentagoMove(row=row, column=column, quadrant=quadrant, direction=direction)
            if self.game.make_move(move):
                print("Board after rotation:")
                self._render_board()
                if len(self.game.get_winning_players()) == 2:
                    print("Both players achieved five-in-a-row!")
                return True
            print("That move was invalid. Please try again.")

    def _handle_ai_turn(self) -> None:
        """Execute the AI controlled player's turn."""

        assert self._ai is not None
        move = self._ai.choose_move(self.game)
        print(f"AI places at row {move.row + 1}, column {move.column + 1} and rotates quadrant {move.quadrant + 1} {move.direction}.")
        preview_board = self._board_with_placement(move.row, move.column, self.game.get_current_player())
        print("Board after AI placement:")
        self._render_board(preview_board)
        self.game.make_move(move)
        print("Board after AI rotation:")
        self._render_board()
        if len(self.game.get_winning_players()) == 2:
            print("Both players achieved five-in-a-row!")

    def _prompt_placement(self, player: int) -> Optional[Tuple[int, int]]:
        """Prompt the user for a placement coordinate."""

        while True:
            try:
                response = input(f"Player {player}, enter row and column (e.g. 3 4): ").strip()
            except EOFError:
                return None
            if not response:
                print("Please enter two numbers between 1 and 6.")
                continue
            lowered = response.lower()
            if lowered in {"q", "quit"}:
                return None
            parts = response.replace(",", " ").split()
            if len(parts) != 2 or not all(part.isdigit() for part in parts):
                print("Please enter two numbers between 1 and 6.")
                continue
            row = int(parts[0]) - 1
            column = int(parts[1]) - 1
            if not PentagoGame._is_within_bounds(row, column):
                print("Coordinates must be between 1 and 6.")
                continue
            return row, column

    def _prompt_rotation(self) -> Optional[Tuple[int, RotationDirection]]:
        """Prompt the user to choose a quadrant and direction to rotate."""

        while True:
            try:
                response = input("Choose quadrant (1-4) and direction (CW/CCW): ").strip()
            except EOFError:
                return None
            if not response:
                print("Please specify a quadrant and direction.")
                continue
            lowered = response.lower()
            if lowered in {"q", "quit"}:
                return None
            parts = response.replace(",", " ").split()
            if len(parts) != 2:
                print("Enter the quadrant number and direction.")
                continue
            quadrant_text, direction_text = parts
            if not quadrant_text.isdigit():
                print("Quadrant must be 1, 2, 3, or 4.")
                continue
            quadrant = int(quadrant_text) - 1
            direction = direction_text.upper()
            if quadrant not in QUADRANTS:
                print("Quadrant must be 1, 2, 3, or 4.")
                continue
            if direction not in ROTATIONS:
                print("Direction must be CW or CCW.")
                continue
            return quadrant, direction

    def _board_with_placement(self, row: int, column: int, player: int) -> Board:
        """Return a board snapshot that includes a tentative placement."""

        board = self.game.get_board_snapshot()
        board[row][column] = player
        return board

    def _render_board(self, board: Optional[Sequence[Sequence[int]]] = None) -> None:
        """Pretty print the board optionally using a provided representation."""

        representation: Sequence[Sequence[int]]
        if board is None:
            state = self.game.get_state_representation()
            representation = state["board"]
        else:
            representation = board
        for index, row in enumerate(representation):
            row_values = list(row)
            left = " ".join(self.TOKEN_MAP[value] for value in row_values[:3])
            right = " ".join(self.TOKEN_MAP[value] for value in row_values[3:])
            print(f"{left} | {right}")
            if index == QUADRANT_SIZE - 1:
                print("------+------")
