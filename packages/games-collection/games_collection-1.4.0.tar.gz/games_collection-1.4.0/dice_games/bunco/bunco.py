"""Bunco game engine."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Sequence

from common.game_engine import GameEngine, GameState


@dataclass
class BuncoPlayerSummary:
    """Aggregate statistics for a Bunco player."""

    name: str
    total_points: int = 0
    buncos: int = 0
    mini_buncos: int = 0
    matches_played: int = 0
    matches_won: int = 0

    def to_row(self) -> Dict[str, int | str]:
        """Return a dictionary representation suitable for UI tables."""

        return {
            "name": self.name,
            "points": self.total_points,
            "buncos": self.buncos,
            "mini_buncos": self.mini_buncos,
            "played": self.matches_played,
            "won": self.matches_won,
        }


@dataclass
class BuncoMatchResult:
    """Details from a single Bunco match during a tournament."""

    round_number: int
    table_number: int
    players: List[str]
    scores: List[int]
    buncos: List[int]
    mini_buncos: List[int]
    winner: str


class BuncoGame(GameEngine[str, int]):
    """Bunco party dice game.

    Roll three dice trying to match the round number.
    Bunco = all three dice match round number (21 points).
    """

    def __init__(self, num_players: int = 4, rng: random.Random | None = None) -> None:
        """Initialize game.

        Args:
            num_players: Number of players seated at a table.
            rng: Optional random generator for deterministic simulations.
        """
        self.num_players = max(2, num_players)
        self.rng = rng or random.Random()
        self.reset()

    def reset(self) -> None:
        """Reset game."""
        self.state = GameState.NOT_STARTED
        self.round_num = 1
        self.current_player_idx = 0
        self.scores = [0] * self.num_players
        self.round_points = 0
        self.player_stats = [{"buncos": 0, "mini_buncos": 0} for _ in range(self.num_players)]
        self.roll_history: List[Dict[str, int | List[int]]] = []

    def is_game_over(self) -> bool:
        """Check if game over."""
        return self.round_num > 6

    def get_current_player(self) -> int:
        """Get current player."""
        return self.current_player_idx

    def get_valid_moves(self) -> List[str]:
        """Get valid moves."""
        return ["roll"]

    def make_move(self, move: str) -> bool:
        """Roll dice."""
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        if move == "roll":
            dice = [self.rng.randint(1, 6) for _ in range(3)]
            points = 0
            result_type = "miss"

            # Bunco: all three match round
            if all(d == self.round_num for d in dice):
                points = 21
                result_type = "bunco"
                self.player_stats[self.current_player_idx]["buncos"] += 1
            # Mini-bunco: all three match (but not round)
            elif dice[0] == dice[1] == dice[2]:
                points = 5
                result_type = "mini_bunco"
                self.player_stats[self.current_player_idx]["mini_buncos"] += 1
            # Matches: count dice matching round
            else:
                points = dice.count(self.round_num)
                if points:
                    result_type = "match"

            self.scores[self.current_player_idx] += points

            # Next player or next round
            player_index = self.current_player_idx

            if points == 0:
                self.current_player_idx = (self.current_player_idx + 1) % self.num_players
                if self.current_player_idx == 0:
                    self.round_num += 1
                    self.round_points = 0
            else:
                self.round_points += points

            self.roll_history.append(
                {
                    "player": player_index,
                    "round": self.round_num,
                    "dice": dice.copy(),
                    "points": points,
                    "result": result_type,
                }
            )

            return True
        return False

    def get_winner(self) -> int | None:
        """Get winner."""
        if not self.is_game_over():
            return None
        return max(range(self.num_players), key=lambda i: self.scores[i])

    def get_game_state(self) -> GameState:
        """Get current game state.

        Returns:
            Current state of the game
        """
        return self.state

    def get_player_summary(self) -> List[Dict[str, int]]:
        """Return per-player scoring and bonus statistics."""

        summary = []
        for idx, stats in enumerate(self.player_stats):
            summary.append(
                {
                    "player_index": idx,
                    "score": self.scores[idx],
                    "buncos": stats["buncos"],
                    "mini_buncos": stats["mini_buncos"],
                }
            )
        return summary

    def get_roll_history(self) -> List[Dict[str, int | List[int]]]:
        """Return a copy of the roll-by-roll history."""

        return list(self.roll_history)


class BuncoTournament:
    """Simulate a single-elimination Bunco tournament."""

    def __init__(self, players: Sequence[str], rng: random.Random | None = None) -> None:
        """Create a tournament bracket.

        Args:
            players: Names of participants, must be a power-of-two count.
            rng: Optional random generator to produce reproducible brackets.
        """

        player_list = [name.strip() for name in players if name.strip()]
        if len(player_list) < 2 or len(player_list) & (len(player_list) - 1) != 0:
            raise ValueError("Number of players must be a power of two and at least two.")

        self.players: List[str] = player_list
        self.rng = rng or random.Random()
        self.match_history: List[BuncoMatchResult] = []
        self.rounds: List[List[BuncoMatchResult]] = []
        self.summaries: Dict[str, BuncoPlayerSummary] = {name: BuncoPlayerSummary(name=name) for name in self.players}
        self.champion: str | None = None

    def run(self) -> str:
        """Play out the tournament and return the champion's name."""

        active_players = self.players[:]
        self.match_history.clear()
        self.rounds.clear()
        for summary in self.summaries.values():
            summary.total_points = 0
            summary.buncos = 0
            summary.mini_buncos = 0
            summary.matches_played = 0
            summary.matches_won = 0

        round_number = 1
        while len(active_players) > 1:
            next_round: List[str] = []
            round_results: List[BuncoMatchResult] = []
            for table, idx in enumerate(range(0, len(active_players), 2), start=1):
                match_players = active_players[idx : idx + 2]
                game_rng = random.Random(self.rng.randint(0, 2**31 - 1))
                game = BuncoGame(num_players=len(match_players), rng=game_rng)
                while not game.is_game_over():
                    game.make_move("roll")

                player_summary = game.get_player_summary()
                scores = [player_summary[i]["score"] for i in range(len(match_players))]
                buncos = [player_summary[i]["buncos"] for i in range(len(match_players))]
                mini_buncos = [player_summary[i]["mini_buncos"] for i in range(len(match_players))]

                for local_idx, name in enumerate(match_players):
                    record = self.summaries[name]
                    record.total_points += scores[local_idx]
                    record.buncos += buncos[local_idx]
                    record.mini_buncos += mini_buncos[local_idx]
                    record.matches_played += 1

                winner_idx = game.get_winner()
                assert winner_idx is not None
                winner_name = match_players[winner_idx]
                self.summaries[winner_name].matches_won += 1
                next_round.append(winner_name)

                result = BuncoMatchResult(
                    round_number=round_number,
                    table_number=table,
                    players=match_players,
                    scores=scores,
                    buncos=buncos,
                    mini_buncos=mini_buncos,
                    winner=winner_name,
                )
                round_results.append(result)
                self.match_history.append(result)

            self.rounds.append(round_results)
            active_players = next_round
            round_number += 1

        self.champion = active_players[0]
        return self.champion

    def get_bracket(self) -> List[List[BuncoMatchResult]]:
        """Return the tournament bracket grouped by round."""

        return [list(round_matches) for round_matches in self.rounds]

    def get_score_summary(self) -> List[BuncoPlayerSummary]:
        """Return player summaries sorted by wins and points."""

        return sorted(
            (summary for summary in self.summaries.values()),
            key=lambda record: (record.matches_won, record.total_points),
            reverse=True,
        )
