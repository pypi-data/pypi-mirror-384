"""Tic-Tac-Toe with integrated analytics system.

This example demonstrates how to integrate the analytics system
with an existing game to track statistics, performance, and ratings.
"""

from __future__ import annotations

import pathlib
import time
from typing import Optional

from common.analytics import Dashboard, EloRating, GameStatistics, Heatmap, PerformanceMetrics
from paper_games.tic_tac_toe.tic_tac_toe import TicTacToe


class TicTacToeWithAnalytics:
    """Tic-Tac-Toe game with integrated analytics tracking."""

    def __init__(self, stats_dir: Optional[pathlib.Path] = None) -> None:
        """Initialize game with analytics.

        Args:
            stats_dir: Directory to save analytics data.
        """
        self.stats_dir = stats_dir or pathlib.Path("game_data")
        self.stats_dir.mkdir(exist_ok=True)

        # Load or create analytics trackers
        self.game_stats = self._load_or_create_stats()
        self.performance_metrics = self._load_or_create_metrics()
        self.elo_ratings = self._load_or_create_ratings()

        # Heatmap for move frequency
        self.move_heatmap = Heatmap(width=3, height=3)

    def _load_or_create_stats(self) -> GameStatistics:
        """Load or create game statistics."""
        stats_file = self.stats_dir / "game_stats.json"
        try:
            return GameStatistics.load(stats_file)
        except FileNotFoundError:
            return GameStatistics(game_name="Tic-Tac-Toe")

    def _load_or_create_metrics(self) -> PerformanceMetrics:
        """Load or create performance metrics."""
        metrics_file = self.stats_dir / "performance.json"
        try:
            return PerformanceMetrics.load(metrics_file)
        except FileNotFoundError:
            return PerformanceMetrics(game_name="Tic-Tac-Toe")

    def _load_or_create_ratings(self) -> EloRating:
        """Load or create ELO ratings."""
        ratings_file = self.stats_dir / "elo_ratings.json"
        return EloRating.load(ratings_file)

    def play_game(
        self,
        player1: str = "Human",
        player2: str = "Computer",
        board_size: int = 3,
    ) -> None:
        """Play a game with analytics tracking.

        Args:
            player1: Name of player 1.
            player2: Name of player 2.
            board_size: Size of the board.
        """
        game = TicTacToe(size=board_size)
        game_start = time.time()
        move_count = 0

        print(f"\n{'=' * 60}")
        print(f"Starting game: {player1} (X) vs {player2} (O)")
        print(f"{'=' * 60}\n")

        # Game loop
        while not game.is_finished():
            print(game.render())
            print()

            current_player = player1 if game.current_player == "X" else player2

            # Get move and track decision time
            decision_start = time.time()

            if current_player == "Human":
                try:
                    move = input(f"{current_player}'s move (row col): ").strip().split()
                    row, col = int(move[0]), int(move[1])
                except (ValueError, IndexError):
                    print("Invalid input. Please enter row and column (e.g., '0 1')")
                    continue
            else:
                # Computer move
                move = game.computer_turn()
                row, col = move
                print(f"{current_player} plays: {row} {col}")

            decision_time = time.time() - decision_start

            # Make move
            if game.make_move(row, col):
                move_count += 1

                # Record decision time
                self.performance_metrics.record_decision(
                    current_player,
                    decision_time,
                )

                # Update heatmap
                self.move_heatmap.increment(col, row)
            else:
                print("Invalid move!")

        # Game finished
        game_duration = time.time() - game_start
        winner = game.winner

        print(game.render())
        print()

        if winner:
            winner_name = player1 if winner == "X" else player2
            print(f"🎉 {winner_name} wins!")
        else:
            print("🤝 It's a draw!")

        print(f"Game lasted {game_duration:.1f}s with {move_count} moves")
        print()

        # Record analytics
        self._record_game_results(player1, player2, winner, game_duration)

        # Save analytics
        self._save_analytics()

    def _record_game_results(
        self,
        player1: str,
        player2: str,
        winner: Optional[str],
        duration: float,
    ) -> None:
        """Record game results in analytics.

        Args:
            player1: Name of player 1 (X).
            player2: Name of player 2 (O).
            winner: Winner symbol or None for draw.
            duration: Game duration in seconds.
        """
        # Determine winner name
        if winner == "X":
            winner_name = player1
        elif winner == "O":
            winner_name = player2
        else:
            winner_name = None

        # Record in game statistics
        self.game_stats.record_game(
            winner=winner_name,
            players=[player1, player2],
            duration=duration,
        )

        # Record game duration
        self.performance_metrics.record_game_duration(duration)

        # Update ELO ratings
        if winner_name == player1:
            score = 1.0
        elif winner_name == player2:
            score = 0.0
        else:
            score = 0.5

        self.elo_ratings.update_ratings(player1, player2, score)

    def _save_analytics(self) -> None:
        """Save all analytics data."""
        self.game_stats.save(self.stats_dir / "game_stats.json")
        self.performance_metrics.save(self.stats_dir / "performance.json")
        self.elo_ratings.save(self.stats_dir / "elo_ratings.json")

    def show_dashboard(self) -> None:
        """Display analytics dashboard."""
        dashboard = Dashboard(title="Tic-Tac-Toe Analytics Dashboard", width=80)

        # Game statistics section
        total_games = len(self.game_stats.game_history)
        dashboard.add_stat("Game Statistics", "Total Games", total_games)

        if total_games > 0:
            # Top players
            leaderboard = self.game_stats.get_leaderboard("win_rate")[:3]
            dashboard.add_section(
                "Top Players",
                [f"{i+1}. {p.player_id}: {p.wins}W-{p.losses}L-{p.draws}D " f"({p.win_rate():.1f}% win rate)" for i, p in enumerate(leaderboard)],
            )

        # Performance metrics
        if self.performance_metrics.game_durations:
            dashboard.add_stat(
                "Performance",
                "Avg Game Duration",
                f"{self.performance_metrics.average_game_duration():.1f}s",
            )
            dashboard.add_stat(
                "Performance",
                "Shortest Game",
                f"{self.performance_metrics.shortest_game():.1f}s",
            )

        # Decision times
        for player_id, metrics in self.performance_metrics.players.items():
            if metrics.total_decisions > 0:
                dashboard.add_stat(
                    f"{player_id} Stats",
                    "Avg Decision Time",
                    f"{metrics.average_decision_time():.2f}s",
                )
                dashboard.add_stat(
                    f"{player_id} Stats",
                    "Total Decisions",
                    metrics.total_decisions,
                )

        # ELO ratings chart
        ratings = dict(self.elo_ratings.get_leaderboard()[:5])
        if ratings:
            dashboard.add_chart("ELO Ratings", ratings, max_width=30)

        print(dashboard.render())

    def show_move_heatmap(self) -> None:
        """Display move frequency heatmap."""
        print("\n" + "=" * 60)
        print("Move Frequency Heatmap")
        print("=" * 60 + "\n")

        self.move_heatmap.normalize()
        print(self.move_heatmap.render_ascii())
        print()

        hotspots = self.move_heatmap.get_hotspots(threshold=0.5)
        if hotspots:
            print("Most Popular Positions:")
            for x, y, value in hotspots[:3]:
                print(f"  Position ({x}, {y}): {value:.2%}")
        print()


def main() -> None:
    """Run the analytics-integrated Tic-Tac-Toe game."""
    game = TicTacToeWithAnalytics()

    print("=" * 60)
    print("Tic-Tac-Toe with Analytics")
    print("=" * 60)
    print()
    print("This demo shows how analytics can be integrated into games.")
    print()

    # Play a few games
    num_games = 3

    for i in range(num_games):
        print(f"\nGame {i+1}/{num_games}")
        game.play_game("Alice", "Computer")

        if i < num_games - 1:
            input("\nPress Enter for next game...")

    # Show analytics
    print("\n" + "=" * 60)
    print("Analytics Summary")
    print("=" * 60 + "\n")

    game.show_dashboard()
    game.show_move_heatmap()

    print("\nAnalytics data saved to 'game_data/' directory")
    print("You can load and analyze this data later!\n")


if __name__ == "__main__":
    main()
