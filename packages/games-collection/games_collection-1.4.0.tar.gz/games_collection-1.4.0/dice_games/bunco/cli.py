"""CLI for Bunco."""

from __future__ import annotations

from typing import List

from .bunco import BuncoMatchResult, BuncoPlayerSummary, BuncoTournament


def _prompt_players() -> List[str]:
    """Collect player names from the command line."""

    while True:
        raw = input("Enter player names (comma separated, power of two): ").strip()
        names = [name.strip() for name in raw.split(",") if name.strip()]
        if len(names) >= 2 and len(names) & (len(names) - 1) == 0:
            return names
        print("Please provide at least two names and ensure the count is a power of two (2, 4, 8, ...).")


def _render_bracket(bracket: List[List[BuncoMatchResult]]) -> None:
    """Print the tournament bracket."""

    print("\nTournament Bracket")
    print("-" * 60)
    for round_index, matches in enumerate(bracket, start=1):
        print(f"Round {round_index}")
        for result in matches:
            matchup = " vs ".join(result.players)
            details = ", ".join(
                f"{name}: {score} pts ({bunco} bunco, {mini} mini)"
                for name, score, bunco, mini in zip(result.players, result.scores, result.buncos, result.mini_buncos)
            )
            print(f"  Table {result.table_number}: {matchup}")
            print(f"    Winner: {result.winner}")
            print(f"    {details}")
        print()


def _render_scoreboard(records: List[BuncoPlayerSummary]) -> None:
    """Print the cumulative scoreboard."""

    print("\nScore Summary")
    print("-" * 60)
    header = f"{'Player':<15}{'Wins':>6}{'Played':>8}{'Points':>10}{'Buncos':>10}{'Mini':>8}"
    print(header)
    print("-" * len(header))
    for summary in records:
        row = summary.to_row()
        print(f"{row['name']:<15}{row['won']:>6}{row['played']:>8}{row['points']:>10}{row['buncos']:>10}{row['mini_buncos']:>8}")


def main() -> None:
    """Run Bunco tournament mode."""

    print("BUNCO".center(60, "="))
    print("This mode simulates a full Bunco tournament bracket and reports cumulative scoring.")

    players = _prompt_players()
    tournament = BuncoTournament(players)
    champion = tournament.run()

    _render_bracket(tournament.get_bracket())
    _render_scoreboard(tournament.get_score_summary())

    print("\n" + "=" * 60)
    print(f"Champion: {champion}")


if __name__ == "__main__":
    main()
