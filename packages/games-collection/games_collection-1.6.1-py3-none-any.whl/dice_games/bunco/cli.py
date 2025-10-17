"""Command-line interface for running a Bunco tournament.

This script provides a simple CLI to set up and simulate a Bunco tournament.
It prompts for player names, runs the tournament, and then displays the
full bracket and a summary scoreboard.

Functions:
    _prompt_players: Collects a valid list of player names from user input.
    _render_bracket: Prints a formatted tournament bracket with match details.
    _render_scoreboard: Displays a summary of player performance.
    main: The main entry point for the CLI application.
"""

from __future__ import annotations

from typing import List

from .bunco import BuncoMatchResult, BuncoPlayerSummary, BuncoTournament


def _prompt_players() -> List[str]:
    """Collect player names from the command line.

    This function repeatedly prompts the user until they provide a comma-separated
    list of names where the total count is a power of two (e.g., 2, 4, 8).

    Returns:
        A list of validated player names.
    """
    while True:
        raw = input("Enter player names (comma separated, power of two): ").strip()
        names = [name.strip() for name in raw.split(",") if name.strip()]
        # The number of players must be a power of two for a single-elimination bracket.
        if len(names) >= 2 and (len(names) & (len(names) - 1) == 0):
            return names
        print("Please provide at least two names and ensure the count is a power of two (2, 4, 8, ...).")


def _render_bracket(bracket: List[List[BuncoMatchResult]]) -> None:
    """Print the tournament bracket in a human-readable format.

    Args:
        bracket: A list of rounds, where each round contains match results.
    """
    print("\nTournament Bracket")
    print("-" * 60)
    for round_index, matches in enumerate(bracket, start=1):
        print(f"Round {round_index}")
        for result in matches:
            matchup = " vs ".join(result.players)
            # Compile detailed results for each player in the match.
            details = ", ".join(
                f"{name}: {score} pts ({bunco} bunco, {mini} mini)"
                for name, score, bunco, mini in zip(result.players, result.scores, result.buncos, result.mini_buncos)
            )
            print(f"  Table {result.table_number}: {matchup}")
            print(f"    Winner: {result.winner}")
            print(f"    {details}")
        print()


def _render_scoreboard(records: List[BuncoPlayerSummary]) -> None:
    """Print the cumulative scoreboard for all players.

    The scoreboard is sorted by matches won and then by total points.

    Args:
        records: A list of player summary statistics.
    """
    print("\nScore Summary")
    print("-" * 60)
    # Define table headers.
    header = f"{'Player':<15}{'Wins':>6}{'Played':>8}{'Points':>10}{'Buncos':>10}{'Mini':>8}"
    print(header)
    print("-" * len(header))
    # Print a row for each player.
    for summary in records:
        row = summary.to_row()
        print(f"{row['name']:<15}{row['won']:>6}{row['played']:>8}{row['points']:>10}{row['buncos']:>10}{row['mini_buncos']:>8}")


def main() -> None:
    """Run the main Bunco tournament simulation.

    This function orchestrates the CLI application by:
    1. Welcoming the user.
    2. Prompting for player names.
    3. Initializing and running the tournament.
    4. Rendering the final bracket and scoreboard.
    5. Announcing the champion.
    """
    print("BUNCO".center(60, "="))
    print("This mode simulates a full Bunco tournament bracket and reports cumulative scoring.")

    # Get players and set up the tournament.
    players = _prompt_players()
    tournament = BuncoTournament(players)
    champion = tournament.run()

    # Display the results.
    _render_bracket(tournament.get_bracket())
    _render_scoreboard(tournament.get_score_summary())

    # Announce the final winner.
    print("\n" + "=" * 60)
    print(f"Champion: {champion}")


if __name__ == "__main__":
    main()
