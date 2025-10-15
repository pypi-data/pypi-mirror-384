"""Sprouts game implementation with CLI and heuristic AI support."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import cos, pi, sin, sqrt
from random import choice
from typing import Dict, List, Optional, Tuple

from common.game_engine import GameEngine, GameState

SproutsMove = Tuple[int, int]


@dataclass
class _Dot:
    """Container describing a Sprouts vertex."""

    identifier: int
    degree: int
    x: float
    y: float

    def clone(self) -> _Dot:
        """Create a copy of the dot."""

        return _Dot(self.identifier, self.degree, self.x, self.y)


@dataclass(frozen=True)
class _Segment:
    """Straight segment connecting two dots."""

    start: int
    end: int


class SproutsInvalidMove(Exception):
    """Raised when a move violates Sprouts rules."""


class SproutsGame(GameEngine[SproutsMove, int]):
    """Core Sprouts engine tracking topology and enforcing move legality."""

    def __init__(self, initial_dots: int = 3) -> None:
        self._initial_dots = initial_dots
        self._dots: Dict[int, _Dot] = {}
        self._segments: List[_Segment] = []
        self._connections: List[Tuple[int, int, int]] = []
        self._current_player = 1
        self._state = GameState.IN_PROGRESS
        self._next_dot_id = 0
        self._last_error: Optional[str] = None
        self._initialise_dots()

    def _initialise_dots(self) -> None:
        """Populate the board with equally spaced initial dots."""

        self._dots.clear()
        self._segments.clear()
        self._connections.clear()
        self._state = GameState.IN_PROGRESS
        self._current_player = 1
        self._next_dot_id = 0
        radius = 0.45
        for index in range(self._initial_dots):
            angle = 2 * pi * index / max(self._initial_dots, 1)
            self._dots[index] = _Dot(index, 0, 0.5 + radius * cos(angle), 0.5 + radius * sin(angle))
            self._next_dot_id = index + 1

    def reset(self) -> None:
        """Reset the game to the starting configuration."""

        self._initialise_dots()

    def is_game_over(self) -> bool:
        """Return whether the game has ended."""

        return self._state == GameState.FINISHED

    def get_current_player(self) -> int:
        """Return the identifier of the active player."""

        return self._current_player

    def get_valid_moves(self) -> List[SproutsMove]:
        """Enumerate every legal move available to the current player."""

        moves: List[SproutsMove] = []
        for move in product(self._dots.keys(), repeat=2):
            if self._is_move_legal(move):
                moves.append(move)
        return moves

    def _is_move_legal(self, move: SproutsMove) -> bool:
        try:
            self._prepare_move(move)
        except SproutsInvalidMove:
            return False
        return True

    def make_move(self, move: SproutsMove) -> bool:
        """Apply a legal Sprouts move."""

        try:
            segments, new_dot = self._prepare_move(move)
        except SproutsInvalidMove as error:
            self._last_error = str(error)
            return False

        start, end = move
        if start == end:
            self._dots[start].degree += 2
        else:
            self._dots[start].degree += 1
            self._dots[end].degree += 1

        self._dots[new_dot.identifier] = new_dot
        self._connections.append((start, end, new_dot.identifier))
        self._segments.extend(segments)
        self._current_player = 3 - self._current_player
        self._next_dot_id += 1
        self._last_error = None
        self._update_state()
        return True

    def _update_state(self) -> None:
        if not self.get_valid_moves():
            self._state = GameState.FINISHED

    def get_winner(self) -> Optional[int]:
        """Return the winner if the game has ended."""

        if not self.is_game_over():
            return None
        return 3 - self._current_player

    def get_game_state(self) -> GameState:
        """Return the current game state enum."""

        return self._state

    def get_state_representation(self) -> Dict[str, object]:
        """Return a JSON-friendly view of the state."""

        dots = {dot_id: {"degree": dot.degree, "x": dot.x, "y": dot.y} for dot_id, dot in self._dots.items()}
        return {
            "dots": dots,
            "segments": [(segment.start, segment.end) for segment in self._segments],
            "connections": list(self._connections),
            "current_player": self._current_player,
            "state": self._state.name,
        }

    def get_last_error(self) -> Optional[str]:
        """Return the most recent invalid move explanation."""

        return self._last_error

    def remaining_lives(self, dot_id: int) -> int:
        """Return the remaining lives (edges available) for a dot."""

        return 3 - self._dots[dot_id].degree

    def total_remaining_lives(self) -> int:
        """Return the aggregate remaining lives in the position."""

        return sum(self.remaining_lives(dot_id) for dot_id in self._dots)

    def has_moves_remaining(self) -> bool:
        """Return whether any moves are still legal."""

        return bool(self.get_valid_moves())

    def clone(self) -> SproutsGame:
        """Return a deep copy of the game state."""

        clone = SproutsGame(self._initial_dots)
        clone._dots = {identifier: dot.clone() for identifier, dot in self._dots.items()}
        clone._segments = list(self._segments)
        clone._connections = list(self._connections)
        clone._current_player = self._current_player
        clone._state = self._state
        clone._next_dot_id = self._next_dot_id
        clone._last_error = self._last_error
        return clone

    def simulate_move(self, move: SproutsMove) -> Optional[SproutsGame]:
        """Return a clone with the move applied or ``None`` when illegal."""

        clone = self.clone()
        if not clone.make_move(move):
            return None
        return clone

    def compute_nimber(self, cache: Optional[Dict[str, int]] = None) -> int:
        """Return the Sprouts nimber (Grundy number) for the current state."""

        if cache is None:
            cache = {}
        key = self._nimber_key()
        if key in cache:
            return cache[key]

        moves = self.get_valid_moves()
        if not moves:
            cache[key] = 0
            return 0

        reachable = set()
        for move in moves:
            simulated = self.simulate_move(move)
            if simulated is None:
                continue
            reachable.add(simulated.compute_nimber(cache))
        grundy = 0
        while grundy in reachable:
            grundy += 1
        cache[key] = grundy
        return grundy

    def suggest_move(self) -> Optional[SproutsMove]:
        """Return an AI generated move using a heuristic evaluation."""

        moves = self.get_valid_moves()
        if not moves:
            return None

        best_score = float("inf")
        best_move: Optional[SproutsMove] = None
        for move in moves:
            simulated = self.simulate_move(move)
            if simulated is None:
                continue
            score = simulated.total_remaining_lives()
            if score < best_score:
                best_score = score
                best_move = move
        return best_move or choice(moves)

    def _prepare_move(self, move: SproutsMove) -> Tuple[List[_Segment], _Dot]:
        if self._state == GameState.FINISHED:
            raise SproutsInvalidMove("The game is already finished.")

        start, end = move
        if start not in self._dots or end not in self._dots:
            raise SproutsInvalidMove("Both endpoints must reference existing dots.")

        if start == end:
            if self.remaining_lives(start) < 2:
                raise SproutsInvalidMove("Loops require two remaining lives on the chosen dot.")
        else:
            if self.remaining_lives(start) <= 0 or self.remaining_lives(end) <= 0:
                raise SproutsInvalidMove("Each endpoint must have at least one remaining life.")

        new_identifier = self._next_dot_id
        new_dot = self._generate_new_dot(move, new_identifier)
        segments = [
            _Segment(start, new_identifier),
            _Segment(new_identifier, end),
        ]

        dots = {**self._dots, new_identifier: new_dot}
        for segment in segments:
            self._validate_segment(segment, dots)

        return segments, new_dot

    def _validate_segment(self, segment: _Segment, dots: Dict[int, _Dot]) -> None:
        start = dots[segment.start]
        end = dots[segment.end]
        for existing in self._segments:
            if {segment.start, segment.end} & {existing.start, existing.end}:
                continue
            existing_start = self._dots[existing.start]
            existing_end = self._dots[existing.end]
            if _segments_intersect((start.x, start.y), (end.x, end.y), (existing_start.x, existing_start.y), (existing_end.x, existing_end.y)):
                raise SproutsInvalidMove("The proposed line crosses an existing connection.")

    def _generate_new_dot(self, move: SproutsMove, identifier: int) -> _Dot:
        start_dot = self._dots[move[0]]
        end_dot = self._dots[move[1]]
        if move[0] == move[1]:
            angle = (identifier + 1) * pi / 6
            offset = 0.08
            x = start_dot.x + offset * cos(angle)
            y = start_dot.y + offset * sin(angle)
            return _Dot(identifier, 2, x, y)

        dx = end_dot.x - start_dot.x
        dy = end_dot.y - start_dot.y
        length = sqrt(dx * dx + dy * dy) or 1.0
        offset = 0.06 + 0.01 * identifier
        mid_x = (start_dot.x + end_dot.x) / 2
        mid_y = (start_dot.y + end_dot.y) / 2
        x = mid_x - (dy / length) * offset
        y = mid_y + (dx / length) * offset
        return _Dot(identifier, 2, x, y)

    def _nimber_key(self) -> str:
        dot_section = ";".join(f"{dot.identifier}:{dot.degree}" for dot in sorted(self._dots.values(), key=lambda item: item.identifier))
        connection_section = ";".join(f"{start}-{end}-{mid}" for start, end, mid in sorted(self._connections))
        return f"{dot_section}|{connection_section}"


def _segments_intersect(p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float], p4: Tuple[float, float]) -> bool:
    """Return whether two segments intersect in the plane."""

    def orientation(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    o1 = orientation(p1, p2, p3)
    o2 = orientation(p1, p2, p4)
    o3 = orientation(p3, p4, p1)
    o4 = orientation(p3, p4, p2)

    if o1 == 0 and o2 == 0 and o3 == 0 and o4 == 0:
        return _on_segment(p1, p3, p2) or _on_segment(p1, p4, p2) or _on_segment(p3, p1, p4) or _on_segment(p3, p2, p4)
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def _on_segment(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> bool:
    return min(a[0], c[0]) <= b[0] <= max(a[0], c[0]) and min(a[1], c[1]) <= b[1] <= max(a[1], c[1])


class SproutsCLI:
    """Interactive command line interface for Sprouts."""

    def __init__(self, initial_dots: int = 3) -> None:
        self.game = SproutsGame(initial_dots)
        self._ai_player: Optional[int] = None

    def run(self) -> None:
        """Launch the CLI loop."""

        print("Sprouts - Enhanced Implementation")
        print("Players alternately connect dots using up to three lines per dot.")
        print("Enter moves as 'a b' to connect dots or 'loop a' to draw a loop.")
        mode = self._prompt_mode()
        print()
        while not self.game.is_game_over():
            print(self._render_board())
            print(f"Remaining lives: {self.game.total_remaining_lives()}")
            if self._ai_player == self.game.get_current_player():
                move = self.game.suggest_move()
                if move is None:
                    break
                print(f"AI selects move {move[0]} -> {move[1]}\n")
                self.game.make_move(move)
                continue
            move = self._prompt_move(mode)
            if move is None:
                print("No legal moves remain. Ending the game.")
                break
            if not self.game.make_move(move):
                print(f"Illegal move: {self.game.get_last_error()}\n")
        print(self._render_board())
        winner = self.game.get_winner()
        if winner is None:
            print("The game ends in a stalemate.")
        else:
            print(f"Player {winner} wins! (nimber {self.game.compute_nimber()})")

    def _prompt_mode(self) -> str:
        while True:
            selection = input("Select mode: [h]uman vs human, [c]omputer opponent, [a]nalysis> ").strip().lower()
            if selection in {"h", "c", "a"}:
                self._ai_player = 2 if selection == "c" else None
                return selection
            print("Invalid selection. Please enter h, c, or a.")

    def _prompt_move(self, mode: str) -> Optional[SproutsMove]:
        if not self.game.get_valid_moves():
            return None
        if mode == "a":
            suggested = self.game.suggest_move()
            if suggested is not None:
                print(f"Suggested move: {suggested[0]} -> {suggested[1]}")
        raw = input(f"Player {self.game.get_current_player()} move> ").strip().lower()
        if raw in {"hint", "?"}:
            suggestion = self.game.suggest_move()
            if suggestion is None:
                print("No legal moves available.")
            else:
                print(f"Hint: connect {suggestion[0]} -> {suggestion[1]}.")
            return self._prompt_move(mode)
        if raw.startswith("loop"):
            parts = raw.split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("Use 'loop <dot>' with a valid dot id.")
                return self._prompt_move(mode)
            return int(parts[1]), int(parts[1])
        parts = raw.split()
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            print("Enter moves as two integers like '1 2'.")
            return self._prompt_move(mode)
        return int(parts[0]), int(parts[1])

    def _render_board(self) -> str:
        width = 41
        height = 21
        board = [[" "] * width for _ in range(height)]

        for segment in self.game._segments:
            start = self.game._dots[segment.start]
            end = self.game._dots[segment.end]
            for step in range(25):
                t = step / 24
                x = start.x + (end.x - start.x) * t
                y = start.y + (end.y - start.y) * t
                gx, gy = self._coords_to_grid(x, y, width, height)
                if board[gy][gx] == " ":
                    board[gy][gx] = "-"

        for dot in self.game._dots.values():
            gx, gy = self._coords_to_grid(dot.x, dot.y, width, height)
            label = str(dot.identifier % 10)
            board[gy][gx] = label

        lines = ["+" + "".join(board[row]) + "+" for row in range(height)]
        return "\n".join(lines)

    @staticmethod
    def _coords_to_grid(x: float, y: float, width: int, height: int) -> Tuple[int, int]:
        gx = min(max(int(round(x * (width - 1))), 0), width - 1)
        gy = min(max(int(round(y * (height - 1))), 0), height - 1)
        return gx, gy


__all__ = ["SproutsCLI", "SproutsGame", "SproutsInvalidMove", "SproutsMove"]
