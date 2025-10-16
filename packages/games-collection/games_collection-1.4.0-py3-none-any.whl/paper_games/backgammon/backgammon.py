"""Backgammon engine, heuristics, and command line interface.

This module provides a full featured representation of a backgammon match.
The game engine keeps track of all points on the board, each player's bar and
bear-off trays, the doubling cube, and match scoring. Legal moves are generated
for any dice roll, including entering checkers from the bar, hitting blots,
handling doubles, and bearing off. The command line interface renders an ASCII
board and allows a human opponent to play against a lightweight AI based on
heuristics that evaluate pip counts, hits, and bear-off progress.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from common.game_engine import GameEngine, GameState

NUM_POINTS = 24
CHECKERS_PER_PLAYER = 15
BAR = "bar"
BEAR_OFF = "bear_off"


@dataclass
class PointState:
    """Representation of a single point on the backgammon board."""

    owner: Optional[int]
    count: int


@dataclass(frozen=True)
class Move:
    """Representation of a single checker move."""

    source: int | str
    target: int | str
    die: int
    hit: bool = False


class BackgammonGame(GameEngine[Tuple[Move, ...], int]):
    """Full featured backgammon game engine."""

    def __init__(self, match_length: Optional[int] = None) -> None:
        self.match_length = match_length
        self.scores: Dict[int, int] = {1: 0, -1: 0}
        self.points: List[PointState] = []
        self.bars: Dict[int, int] = {1: 0, -1: 0}
        self.bear_off: Dict[int, int] = {1: 0, -1: 0}
        self._dice: List[int] = []
        self._current_player = 1
        self._state = GameState.NOT_STARTED
        self._winner: Optional[int] = None
        self.cube_value = 1
        self.cube_owner: Optional[int] = None
        self.pending_double_from: Optional[int] = None
        self.reset()

    def reset(self) -> None:
        """Reset the game board to the traditional starting position."""

        self.points = [PointState(None, 0) for _ in range(NUM_POINTS)]
        self._place_checkers(23, 1, 2)
        self._place_checkers(12, 1, 5)
        self._place_checkers(7, 1, 3)
        self._place_checkers(5, 1, 5)
        self._place_checkers(0, -1, 2)
        self._place_checkers(11, -1, 5)
        self._place_checkers(16, -1, 3)
        self._place_checkers(18, -1, 5)
        self.bars = {1: 0, -1: 0}
        self.bear_off = {1: 0, -1: 0}
        self._dice = []
        self._current_player = 1
        self._state = GameState.IN_PROGRESS
        self._winner = None
        self.cube_value = 1
        self.cube_owner = None
        self.pending_double_from = None

    def _place_checkers(self, index: int, player: int, count: int) -> None:
        """Place a set of checkers on a point."""

        self.points[index].owner = player
        self.points[index].count = count

    def is_game_over(self) -> bool:
        """Return True if the current game has finished."""

        return self._state == GameState.FINISHED

    def get_current_player(self) -> int:
        """Return the player whose turn it is (1 or -1)."""

        return self._current_player

    def roll_dice(self) -> Tuple[int, int]:
        """Roll two dice and prepare the move list for the player."""

        if self.pending_double_from is not None:
            raise RuntimeError("Cannot roll while a doubling decision is pending.")
        die_one = random.randint(1, 6)
        die_two = random.randint(1, 6)
        if die_one == die_two:
            self._dice = [die_one] * 4
        else:
            self._dice = [die_one, die_two]
        return die_one, die_two

    def set_dice(self, dice: Sequence[int]) -> None:
        """Set dice manually for deterministic scenarios such as tests."""

        expanded = list(dice)
        if len(expanded) == 2 and expanded[0] == expanded[1]:
            expanded = [expanded[0]] * 4
        self._dice = expanded

    def get_valid_moves(self) -> List[Tuple[Move, ...]]:
        """Return sequences of moves that satisfy the current dice roll."""

        if not self._dice:
            return []
        sequences: List[Tuple[Move, ...]] = []
        dice = list(self._dice)
        self._generate_sequences(
            board=self.points,
            bars=self.bars,
            bear_off=self.bear_off,
            dice=dice,
            player=self._current_player,
            path=[],
            sequences=sequences,
        )
        if not sequences:
            return []
        max_moves = max(len(sequence) for sequence in sequences)
        best_sequences = [sequence for sequence in sequences if len(sequence) == max_moves]
        if max_moves == 1 and best_sequences:
            highest_die_played = max(move.die for sequence in best_sequences for move in sequence)
            best_sequences = [sequence for sequence in best_sequences if sequence and sequence[0].die == highest_die_played]
        return best_sequences

    def _generate_sequences(
        self,
        board: List[PointState],
        bars: Dict[int, int],
        bear_off: Dict[int, int],
        dice: List[int],
        player: int,
        path: List[Move],
        sequences: List[Tuple[Move, ...]],
    ) -> None:
        """Recursively build all legal move sequences for the dice provided."""

        any_move = False
        for index, die in enumerate(dice):
            remaining = dice[:index] + dice[index + 1 :]
            single_moves = self._generate_single_die_moves(board, bars, player, die)
            for move in single_moves:
                any_move = True
                new_board = [PointState(point.owner, point.count) for point in board]
                new_bars = dict(bars)
                new_bear_off = dict(bear_off)
                self._apply_move_to_state(new_board, new_bars, new_bear_off, move, player)
                path.append(move)
                self._generate_sequences(new_board, new_bars, new_bear_off, remaining, player, path, sequences)
                path.pop()
        if not any_move:
            sequences.append(tuple(path))

    def _generate_single_die_moves(
        self,
        board: List[PointState],
        bars: Dict[int, int],
        player: int,
        die: int,
    ) -> List[Move]:
        """Generate all single-die moves for the current player."""

        moves: List[Move] = []
        if bars[player] > 0:
            target = self._entry_point(player, die)
            if target is not None and not self._is_blocked(board[target], player):
                hit = board[target].owner == -player and board[target].count == 1
                moves.append(Move(BAR, target, die, hit))
            return moves
        direction = self._direction(player)
        for index, point in enumerate(board):
            if point.owner != player or point.count == 0:
                continue
            destination = index + direction * die
            if self._can_bear_off(player, board, bars, index, die):
                moves.append(Move(index, BEAR_OFF, die, False))
            elif 0 <= destination < NUM_POINTS and not self._is_blocked(board[destination], player):
                hit = board[destination].owner == -player and board[destination].count == 1
                moves.append(Move(index, destination, die, hit))
        return moves

    def _entry_point(self, player: int, die: int) -> Optional[int]:
        """Return the entry point index for a checker leaving the bar."""

        if not 1 <= die <= 6:
            return None
        if player == 1:
            return NUM_POINTS - die
        return die - 1

    def _direction(self, player: int) -> int:
        """Return the movement direction for the player."""

        return -1 if player == 1 else 1

    def _is_blocked(self, point: PointState, player: int) -> bool:
        """Return True if the point is blocked for the player."""

        return point.owner == -player and point.count >= 2

    def _can_bear_off(self, player: int, board: List[PointState], bars: Dict[int, int], index: int, die: int) -> bool:
        """Return True if a checker can bear off from the given point."""

        if bars[player] > 0:
            return False
        if not self._all_in_home_board(player, board):
            return False
        direction = self._direction(player)
        destination = index + direction * die
        if player == 1 and destination < 0:
            return index == self._furthest_checker_index(player, board)
        if player == -1 and destination >= NUM_POINTS:
            return index == self._furthest_checker_index(player, board)
        return destination == -1 if player == 1 else destination == NUM_POINTS

    def _all_in_home_board(self, player: int, board: List[PointState]) -> bool:
        """Return True if all checkers for the player are in the home board."""

        start, end = (0, 6) if player == 1 else (NUM_POINTS - 6, NUM_POINTS)
        for index, point in enumerate(board):
            if point.owner == player and point.count > 0:
                if not start <= index < end:
                    return False
        return True

    def _furthest_checker_index(self, player: int, board: List[PointState]) -> int:
        """Return the furthest checker index for oversize dice bearing off."""

        if player == 1:
            for index in range(5, -1, -1):
                if board[index].owner == player and board[index].count > 0:
                    return index
            return 0
        for index in range(NUM_POINTS - 6, NUM_POINTS):
            if board[index].owner == player and board[index].count > 0:
                return index
        return NUM_POINTS - 1

    def _apply_move_to_state(
        self,
        board: List[PointState],
        bars: Dict[int, int],
        bear_off: Dict[int, int],
        move: Move,
        player: int,
    ) -> None:
        """Apply a move to a copied board state."""

        if move.source == BAR:
            bars[player] -= 1
        else:
            source_point = board[int(move.source)]
            source_point.count -= 1
            if source_point.count == 0:
                source_point.owner = None
        if move.target == BEAR_OFF:
            bear_off[player] += 1
            return
        destination_point = board[int(move.target)]
        if move.hit:
            bars[-player] += 1
            destination_point.count = 0
        if destination_point.count == 0:
            destination_point.owner = player
            destination_point.count = 1
        else:
            destination_point.count += 1

    def make_move(self, move: Tuple[Move, ...]) -> bool:
        """Apply the provided move sequence if it is legal."""

        if self.pending_double_from is not None:
            raise RuntimeError("Cannot move while a doubling decision is pending.")
        legal_moves = self.get_valid_moves()
        if move not in legal_moves:
            return False
        for single in move:
            self._apply_move_to_state(self.points, self.bars, self.bear_off, single, self._current_player)
        self._dice = []
        if self.bear_off[self._current_player] >= CHECKERS_PER_PLAYER:
            self._complete_game(self._current_player)
        else:
            self._current_player *= -1
        return True

    def _complete_game(self, winner: int) -> None:
        """Finalize the game, compute match points, and update scores."""

        multiplier = self._result_multiplier(winner)
        points = self.cube_value * multiplier
        self.scores[winner] += points
        self._winner = winner
        self._state = GameState.FINISHED
        if self.match_length is not None and self.scores[winner] >= self.match_length:
            self.scores[winner] = self.match_length

    def _result_multiplier(self, winner: int) -> int:
        """Return 1, 2, or 3 for normal, gammon, or backgammon wins."""

        loser = -winner
        if self.bear_off[loser] > 0:
            return 1
        if self.bars[loser] > 0 or self._has_checker_in_winner_home(loser, winner):
            return 3
        return 2

    def _has_checker_in_winner_home(self, player: int, winner: int) -> bool:
        """Return True if player still has a checker in the winner's home board."""

        if winner == 1:
            home_range = range(0, 6)
        else:
            home_range = range(NUM_POINTS - 6, NUM_POINTS)
        for index in home_range:
            if self.points[index].owner == player and self.points[index].count > 0:
                return True
        return False

    def end_turn(self) -> None:
        """End the turn without a move (for example when no moves are available)."""

        self._dice = []
        self._current_player *= -1

    def get_winner(self) -> Optional[int]:
        """Return the winner of the current game if finished."""

        return self._winner

    def get_game_state(self) -> GameState:
        """Return the current game state enumeration."""

        return self._state

    def get_state_representation(self) -> Dict[str, object]:
        """Return a dictionary suitable for rendering or debugging."""

        return {
            "points": [(point.owner, point.count) for point in self.points],
            "bars": dict(self.bars),
            "bear_off": dict(self.bear_off),
            "dice": list(self._dice),
            "current_player": self._current_player,
            "cube_value": self.cube_value,
            "cube_owner": self.cube_owner,
            "pending_double_from": self.pending_double_from,
            "scores": dict(self.scores),
        }

    def get_pip_count(self, player: int) -> int:
        """Return the pip count for the specified player."""

        total = 0
        for index, point in enumerate(self.points):
            if point.owner == player and point.count > 0:
                distance = self._distance_to_bear_off(player, index)
                total += distance * point.count
        total += self.bars[player] * 25
        return total

    def _distance_to_bear_off(self, player: int, index: int) -> int:
        """Return the pip distance from the point index to the bear-off tray."""

        if player == 1:
            return index + 1
        return NUM_POINTS - index

    def evaluate_move(self, sequence: Tuple[Move, ...]) -> float:
        """Return a heuristic score for a move sequence."""

        board_copy = [PointState(point.owner, point.count) for point in self.points]
        bars_copy = dict(self.bars)
        bear_off_copy = dict(self.bear_off)
        player = self._current_player
        for move in sequence:
            self._apply_move_to_state(board_copy, bars_copy, bear_off_copy, move, player)
        pip_before = self.get_pip_count(player)
        pip_after = self._pip_count_with_state(board_copy, bars_copy, player)
        score = (pip_before - pip_after) * 0.5
        score += (bear_off_copy[player] - self.bear_off[player]) * 2
        score -= (bars_copy[player] - self.bars[player]) * 5
        score += sum(1 for move in sequence if move.hit) * 1.5
        return score

    def _pip_count_with_state(self, board: List[PointState], bars: Dict[int, int], player: int) -> int:
        """Compute pip count for a hypothetical state."""

        total = 0
        for index, point in enumerate(board):
            if point.owner == player and point.count > 0:
                total += self._distance_to_bear_off(player, index) * point.count
        total += bars[player] * 25
        return total

    def offer_double(self) -> None:
        """Offer the doubling cube to the opponent."""

        if self.pending_double_from is not None:
            raise RuntimeError("A doubling offer is already pending.")
        if self.cube_owner not in (None, self._current_player):
            raise RuntimeError("Cube is owned by the opponent.")
        self.pending_double_from = self._current_player

    def accept_double(self, player: int) -> None:
        """Accept a doubling cube offer."""

        if self.pending_double_from is None:
            raise RuntimeError("No doubling offer to accept.")
        if player == self.pending_double_from:
            raise RuntimeError("Offering player cannot accept their own double.")
        self.cube_value *= 2
        self.cube_owner = player
        self.pending_double_from = None

    def decline_double(self, player: int) -> None:
        """Decline a doubling cube offer, awarding the game to the opponent."""

        if self.pending_double_from is None:
            raise RuntimeError("No doubling offer to decline.")
        if player == self.pending_double_from:
            raise RuntimeError("Offering player cannot decline their own double.")
        winner = self.pending_double_from
        self.pending_double_from = None
        self._winner = winner
        self._state = GameState.FINISHED
        self.scores[winner] += self.cube_value
        if self.match_length is not None and self.scores[winner] >= self.match_length:
            self.scores[winner] = self.match_length
        self._dice = []

    def load_position(
        self,
        points: Sequence[Tuple[Optional[int], int]],
        bars: Optional[Dict[int, int]] = None,
        bear_off: Optional[Dict[int, int]] = None,
        current_player: Optional[int] = None,
    ) -> None:
        """Load a custom position for analysis or tests."""

        if len(points) != NUM_POINTS:
            raise ValueError("Expected 24 points in the position description.")
        self.points = [PointState(owner, count) for owner, count in points]
        self.bars = dict(bars or {1: 0, -1: 0})
        self.bear_off = dict(bear_off or {1: 0, -1: 0})
        if current_player is not None:
            self._current_player = current_player
        self._state = GameState.IN_PROGRESS
        self._winner = None
        self._dice = []


class BackgammonAI:
    """Simple heuristic-based AI for backgammon."""

    def choose_move(self, game: BackgammonGame) -> Optional[Tuple[Move, ...]]:
        """Select the highest scoring legal move sequence."""

        legal = game.get_valid_moves()
        if not legal:
            return None
        return max(legal, key=game.evaluate_move)


class BackgammonCLI:
    """ASCII command line interface for backgammon."""

    def __init__(self, ai: Optional[BackgammonAI] = None) -> None:
        self.game = BackgammonGame()
        self.ai = ai or BackgammonAI()

    def run(self) -> None:
        """Run the interactive command line experience."""

        print("Backgammon - Interactive CLI")
        while not self.game.is_game_over():
            if not self.game.get_state_representation()["dice"]:
                dice = self.game.roll_dice()
                print(f"Player {self.game.get_current_player()} rolled {dice}.")
            self._render_board()
            legal_moves = self.game.get_valid_moves()
            if not legal_moves:
                print("No legal moves available. Passing turn.")
                self.game.end_turn()
                continue
            if self.game.get_current_player() == -1:
                choice = self.ai.choose_move(self.game)
                if choice is None:
                    self.game.end_turn()
                    continue
                print("AI chooses:")
                self._print_move(choice)
                self.game.make_move(choice)
            else:
                choice = self._prompt_move(legal_moves)
                if choice is None:
                    self.game.end_turn()
                else:
                    self.game.make_move(choice)
        winner = self.game.get_winner()
        if winner is not None:
            print(f"Player {winner} wins! Current scores: {self.game.scores}")

    def _render_board(self) -> None:
        """Render the board in ASCII form."""

        state = self.game.get_state_representation()
        points = state["points"]
        top = points[12:24]
        bottom = points[0:12]
        print("+----------------------------+")
        print("|Upper Board|")
        self._render_row(list(reversed(top)))
        print("|Lower Board|")
        self._render_row(bottom)
        print(f"Bars: P1={state['bars'][1]} P2={state['bars'][-1]}")
        print(f"Bear Off: P1={state['bear_off'][1]} P2={state['bear_off'][-1]}")
        print(f"Doubling Cube: value={state['cube_value']} owner={state['cube_owner']}")
        print(f"Scores: {state['scores']}")

    def _render_row(self, row: List[Tuple[Optional[int], int]]) -> None:
        """Render a row of twelve points."""

        buffer = []
        for owner, count in row:
            if owner is None or count == 0:
                buffer.append(" . ")
            else:
                symbol = "X" if owner == 1 else "O"
                buffer.append(f"{symbol}{count:>2}")
        print(" ".join(buffer))

    def _prompt_move(self, legal_moves: List[Tuple[Move, ...]]) -> Optional[Tuple[Move, ...]]:
        """Prompt the user to choose a move sequence."""

        for index, sequence in enumerate(legal_moves, start=1):
            print(f"{index}: {self._format_move(sequence)}")
        choice = input("Choose move (or press Enter to pass): ")
        if not choice.strip():
            return None
        try:
            selection = int(choice)
            return legal_moves[selection - 1]
        except (ValueError, IndexError):
            print("Invalid selection; passing turn.")
            return None

    def _format_move(self, sequence: Tuple[Move, ...]) -> str:
        """Format a move sequence for display."""

        return ", ".join(f"{move.source}->{move.target} using {move.die}{' hit' if move.hit else ''}" for move in sequence)

    def _print_move(self, sequence: Tuple[Move, ...]) -> None:
        """Print a move sequence in a friendly format."""

        print(self._format_move(sequence))
