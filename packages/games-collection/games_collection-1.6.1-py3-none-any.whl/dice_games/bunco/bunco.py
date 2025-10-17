"""Bunco game engine.

This module provides the core logic for playing a game of Bunco, a social dice
game based on rounds. It includes the main game engine (`BuncoGame`) which
handles the rules of rolling dice and scoring, as well as a `BuncoTournament`
class to simulate a multi-round tournament.

Classes:
    BuncoPlayerSummary: Holds aggregate statistics for a player.
    BuncoMatchResult: Contains the details of a single match.
    BuncoGame: Manages the state and rules of a single Bunco game.
    BuncoTournament: Simulates a single-elimination tournament.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Sequence

from common.game_engine import GameEngine, GameState


@dataclass
class BuncoPlayerSummary:
    """Aggregate statistics for a Bunco player across a tournament.

    Attributes:
        name: The player's name.
        total_points: Cumulative points scored.
        buncos: Total number of buncos rolled.
        mini_buncos: Total number of mini-buncos rolled.
        matches_played: Number of matches the player participated in.
        matches_won: Number of matches won.
    """

    name: str
    total_points: int = 0
    buncos: int = 0
    mini_buncos: int = 0
    matches_played: int = 0
    matches_won: int = 0

    def to_row(self) -> Dict[str, int | str]:
        """Return a dictionary representation suitable for UI tables.

        This format is often used for creating tables in command-line or
        graphical interfaces.

        Returns:
            A dictionary mapping stat names to values.
        """
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
    """Details from a single Bunco match during a tournament.

    Attributes:
        round_number: The tournament round this match occurred in.
        table_number: The table number for the match.
        players: A list of names of the players in the match.
        scores: The final scores for each player.
        buncos: The number of buncos each player rolled.
        mini_buncos: The number of mini-buncos each player rolled.
        winner: The name of the player who won the match.
    """

    round_number: int
    table_number: int
    players: List[str]
    scores: List[int]
    buncos: List[int]
    mini_buncos: List[int]
    winner: str


class BuncoGame(GameEngine[str, int]):
    """Bunco party dice game engine.

    This class enforces the rules of Bunco for a single table. Players take
    turns rolling three dice to score points by matching the current round
    number (1 through 6).

    Scoring Rules:
        - Bunco: Three-of-a-kind matching the round number (21 points).
        - Mini-Bunco: Three-of-a-kind not matching the round number (5 points).
        - Match: Each die that matches the round number (1 point).

    A player's turn continues as long as they score points. The game ends after
    the completion of round 6.
    """

    def __init__(self, num_players: int = 4, rng: random.Random | None = None) -> None:
        """Initialize the Bunco game.

        Args:
            num_players: The number of players at the table. Must be at least 2.
            rng: An optional random number generator for deterministic simulations.
        """
        self.num_players = max(2, num_players)
        self.rng = rng or random.Random()
        self.reset()

    def reset(self) -> None:
        """Reset the game to its initial state for a new match."""
        self.state = GameState.NOT_STARTED
        self.round_num = 1
        self.current_player_idx = 0
        self.scores = [0] * self.num_players
        self.round_points = 0  # Tracks points within a player's turn
        self.player_stats = [{"buncos": 0, "mini_buncos": 0} for _ in range(self.num_players)]
        self.roll_history: List[Dict[str, int | List[int]]] = []

    def is_game_over(self) -> bool:
        """Check if the game has concluded.

        The game is over after round 6 is complete.

        Returns:
            True if the game is over, otherwise False.
        """
        return self.round_num > 6

    def get_current_player(self) -> int:
        """Get the index of the current player.

        Returns:
            The zero-based index of the player whose turn it is.
        """
        return self.current_player_idx

    def get_valid_moves(self) -> List[str]:
        """Get the list of valid moves for the current state.

        In Bunco, the only move is to "roll".

        Returns:
            A list containing the string "roll".
        """
        return ["roll"]

    def make_move(self, move: str) -> bool:
        """Process a player's move.

        The only accepted move is "roll". Any other move is invalid.

        Args:
            move: The move to be made, expected to be "roll".

        Returns:
            True if the move was valid and processed, otherwise False.
        """
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        if move != "roll":
            return False

        # Roll three 6-sided dice
        dice = [self.rng.randint(1, 6) for _ in range(3)]
        points = 0
        result_type = "miss"

        # Check for scoring conditions
        if all(d == self.round_num for d in dice):
            # Bunco: all three dice match the current round number
            points = 21
            result_type = "bunco"
            self.player_stats[self.current_player_idx]["buncos"] += 1
        elif dice[0] == dice[1] == dice[2]:
            # Mini-Bunco: all three dice match each other, but not the round number
            points = 5
            result_type = "mini_bunco"
            self.player_stats[self.current_player_idx]["mini_buncos"] += 1
        else:
            # Standard match: count dice that match the round number
            match_points = dice.count(self.round_num)
            if match_points > 0:
                points = match_points
                result_type = "match"

        self.scores[self.current_player_idx] += points

        # Log the roll details
        self.roll_history.append(
            {
                "player": self.current_player_idx,
                "round": self.round_num,
                "dice": dice.copy(),
                "points": points,
                "result": result_type,
            }
        )

        # Determine if the turn passes to the next player
        if points == 0:
            # No points scored, turn ends
            self.current_player_idx = (self.current_player_idx + 1) % self.num_players
            if self.current_player_idx == 0:
                # A full table rotation has occurred, advance to the next round
                self.round_num += 1
                self.round_points = 0
        else:
            # Points were scored, player rolls again
            self.round_points += points

        return True

    def get_winner(self) -> int | None:
        """Determine the winner of the game.

        The winner is the player with the highest score after all rounds are complete.

        Returns:
            The index of the winning player, or None if the game is not over.
        """
        if not self.is_game_over():
            return None
        # Find the player with the maximum score
        return max(range(self.num_players), key=lambda i: self.scores[i])

    def get_game_state(self) -> GameState:
        """Get the current state of the game (e.g., not started, in progress).

        Returns:
            The current `GameState`.
        """
        return self.state

    def get_player_summary(self) -> List[Dict[str, int]]:
        """Return per-player scoring and bonus statistics for the current game.

        Returns:
            A list of dictionaries, each summarizing a player's performance.
        """
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
        """Return a copy of the roll-by-roll history of the game.

        Returns:
            A list of dictionaries, each detailing a single roll.
        """
        return list(self.roll_history)


class BuncoTournament:
    """Simulates a single-elimination Bunco tournament.

    This class organizes a series of Bunco games into a bracket, advancing
    winners to subsequent rounds until a single champion is determined.

    The number of players must be a power of two (e.g., 2, 4, 8, 16).
    """

    def __init__(self, players: Sequence[str], rng: random.Random | None = None) -> None:
        """Create a tournament bracket.

        Args:
            players: A sequence of player names. The count must be a power of two.
            rng: An optional random number generator for reproducible brackets.

        Raises:
            ValueError: If the number of players is not a power of two or is less than 2.
        """
        # Validate player list
        player_list = [name.strip() for name in players if name.strip()]
        if len(player_list) < 2 or (len(player_list) & (len(player_list) - 1) != 0):
            raise ValueError("Number of players must be a power of two and at least two.")

        self.players: List[str] = player_list
        self.rng = rng or random.Random()
        self.match_history: List[BuncoMatchResult] = []
        self.rounds: List[List[BuncoMatchResult]] = []
        self.summaries: Dict[str, BuncoPlayerSummary] = {name: BuncoPlayerSummary(name=name) for name in self.players}
        self.champion: str | None = None

    def run(self) -> str:
        """Play out the entire tournament and return the champion's name.

        This method simulates all matches in the tournament bracket, from the
        first round to the final.

        Returns:
            The name of the tournament champion.
        """
        active_players = self.players[:]
        self._reset_tournament_stats()

        round_number = 1
        while len(active_players) > 1:
            next_round_players: List[str] = []
            round_results: List[BuncoMatchResult] = []

            # Pair up active players for matches
            for table, idx in enumerate(range(0, len(active_players), 2), start=1):
                match_players = active_players[idx : idx + 2]

                # Simulate a single game between the two players
                game_rng = random.Random(self.rng.randint(0, 2**31 - 1))
                game = BuncoGame(num_players=len(match_players), rng=game_rng)
                while not game.is_game_over():
                    game.make_move("roll")

                # Process game results and update player summaries
                player_summary = game.get_player_summary()
                scores = [p["score"] for p in player_summary]
                buncos = [p["buncos"] for p in player_summary]
                mini_buncos = [p["mini_buncos"] for p in player_summary]

                for i, name in enumerate(match_players):
                    record = self.summaries[name]
                    record.total_points += scores[i]
                    record.buncos += buncos[i]
                    record.mini_buncos += mini_buncos[i]
                    record.matches_played += 1

                # Determine the winner and advance them to the next round
                winner_idx = game.get_winner()
                assert winner_idx is not None, "Game should have a winner."
                winner_name = match_players[winner_idx]
                self.summaries[winner_name].matches_won += 1
                next_round_players.append(winner_name)

                # Store the result of the match
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
            active_players = next_round_players
            round_number += 1

        # The last remaining player is the champion
        self.champion = active_players[0]
        return self.champion

    def _reset_tournament_stats(self) -> None:
        """Clear all previous tournament results and player statistics."""
        self.match_history.clear()
        self.rounds.clear()
        for summary in self.summaries.values():
            summary.total_points = 0
            summary.buncos = 0
            summary.mini_buncos = 0
            summary.matches_played = 0
            summary.matches_won = 0

    def get_bracket(self) -> List[List[BuncoMatchResult]]:
        """Return the tournament bracket, structured by rounds.

        Returns:
            A list of lists, where each inner list contains the match results
            for a single round.
        """
        return [list(round_matches) for round_matches in self.rounds]

    def get_score_summary(self) -> List[BuncoPlayerSummary]:
        """Return player summaries, sorted by wins and then by total points.

        Returns:
            A list of `BuncoPlayerSummary` objects in descending order of performance.
        """
        return sorted(
            self.summaries.values(),
            key=lambda record: (record.matches_won, record.total_points),
            reverse=True,
        )
