"""This module demonstrates the integration of the analytics system with a playable game.

It wraps the existing `TicTacToe` game engine and adds a layer of analytics
tracking on top of it. This example serves as a practical guide for how to
instrument a game to collect, save, and display meaningful data.

The key features demonstrated are:
- Persisting and loading analytics data (`GameStatistics`, `PerformanceMetrics`, `EloRating`).
- Recording game outcomes, player decisions, and timings during gameplay.
- Generating and displaying a consolidated `Dashboard` with key metrics.
- Using a `Heatmap` to visualize strategic data, such as move frequency.
"""

from __future__ import annotations

import pathlib
import time
from typing import Optional

from common.analytics import Dashboard, EloRating, GameStatistics, Heatmap, PerformanceMetrics
from paper_games.tic_tac_toe.tic_tac_toe import TicTacToe


class TicTacToeWithAnalytics:
    """A wrapper for the Tic-Tac-Toe game that integrates analytics tracking.

    This class manages the lifecycle of a Tic-Tac-Toe game while interfacing with
    various analytics components to record and report on gameplay data.
    """

    def __init__(self, stats_dir: Optional[pathlib.Path] = None) -> None:
        """Initializes the game and its associated analytics trackers.

        Args:
            stats_dir: The directory where analytics data will be saved and loaded from.
                       Defaults to a 'game_data' directory in the current folder.
        """
        self.stats_dir = stats_dir or pathlib.Path("game_data")
        self.stats_dir.mkdir(exist_ok=True)

        # Load existing analytics data or create new tracker instances.
        self.game_stats = self._load_or_create_stats()
        self.performance_metrics = self._load_or_create_metrics()
        self.elo_ratings = self._load_or_create_ratings()

        # Initialize a heatmap to track the frequency of moves on the 3x3 board.
        self.move_heatmap = Heatmap(width=3, height=3)

    def _load_or_create_stats(self) -> GameStatistics:
        """Loads game statistics from a file or creates a new instance."""
        stats_file = self.stats_dir / "tic_tac_toe_stats.json"
        try:
            return GameStatistics.load(stats_file)
        except FileNotFoundError:
            return GameStatistics(game_name="Tic-Tac-Toe")

    def _load_or_create_metrics(self) -> PerformanceMetrics:
        """Loads performance metrics from a file or creates a new instance."""
        metrics_file = self.stats_dir / "tic_tac_toe_performance.json"
        try:
            return PerformanceMetrics.load(metrics_file)
        except FileNotFoundError:
            return PerformanceMetrics(game_name="Tic-Tac-Toe")

    def _load_or_create_ratings(self) -> EloRating:
        """Loads ELO ratings from a file or creates a new instance."""
        ratings_file = self.stats_dir / "tic_tac_toe_elo_ratings.json"
        return EloRating.load(ratings_file)

    def play_game(self, player1: str = "Human", player2: str = "Computer", board_size: int = 3) -> None:
        """Plays a single game of Tic-Tac-Toe with full analytics tracking.

        Args:
            player1: The name of the player who will be 'X'.
            player2: The name of the player who will be 'O'.
            board_size: The size of the game board (e.g., 3 for a 3x3 grid).
        """
        game = TicTacToe(size=board_size)
        game_start_time = time.time()
        move_count = 0

        print(f"\n{'=' * 60}")
        print(f"Starting New Game: {player1} (X) vs. {player2} (O)")
        print(f"{'=' * 60}\n")

        # Main game loop
        while not game.is_finished():
            print(game.render())
            print()

            current_player_name = player1 if game.current_player == "X" else player2

            # Time the player's decision-making process.
            decision_start_time = time.time()

            if current_player_name == "Human":
                try:
                    move_input = input(f"{current_player_name}'s turn (row col): ").strip().split()
                    row, col = int(move_input[0]), int(move_input[1])
                except (ValueError, IndexError):
                    print("Invalid input. Please use the format 'row col' (e.g., '0 1').")
                    continue
            else:
                # AI's turn
                move = game.computer_turn()
                row, col = move
                print(f"{current_player_name} plays: {row} {col}")

            decision_time = time.time() - decision_start_time

            # Attempt to make the move.
            if game.make_move(row, col):
                move_count += 1

                # Record the performance of the decision.
                self.performance_metrics.record_decision(current_player_name, decision_time)

                # Increment the count for this position on the heatmap.
                self.move_heatmap.increment(col, row)
            else:
                print("That's an invalid move! Please try again.")

        # --- Game Finished ---
        game_duration = time.time() - game_start_time
        winner_symbol = game.winner

        print("\n" + game.render())
        if winner_symbol:
            winner_name = player1 if winner_symbol == "X" else player2
            print(f"🎉 Game Over! {winner_name} wins!")
        else:
            print("🤝 Game Over! It's a draw.")

        print(f"Game lasted {game_duration:.1f} seconds with {move_count} moves.\n")

        # Record the results in the analytics system.
        self._record_game_results(player1, player2, winner_symbol, game_duration)

        # Persist the updated analytics data to disk.
        self._save_analytics()

    def _record_game_results(self, player1: str, player2: str, winner_symbol: Optional[str], duration: float) -> None:
        """Records the outcome of a completed game across all relevant trackers.

        Args:
            player1: Name of player 'X'.
            player2: Name of player 'O'.
            winner_symbol: The symbol of the winner ('X' or 'O'), or None for a draw.
            duration: The total duration of the game in seconds.
        """
        if winner_symbol == "X":
            winner_name = player1
            score = 1.0
        elif winner_symbol == "O":
            winner_name = player2
            score = 0.0
        else:
            winner_name = None
            score = 0.5  # Draw

        # Record the game outcome (win/loss/draw).
        self.game_stats.record_game(winner=winner_name, players=[player1, player2], duration=duration)

        # Record the total game duration for performance analysis.
        self.performance_metrics.record_game_duration(duration)

        # Update the ELO ratings of the two players based on the outcome.
        self.elo_ratings.update_ratings(player1, player2, score)

    def _save_analytics(self) -> None:
        """Saves all analytics data to their respective files."""
        self.game_stats.save(self.stats_dir / "tic_tac_toe_stats.json")
        self.performance_metrics.save(self.stats_dir / "tic_tac_toe_performance.json")
        self.elo_ratings.save(self.stats_dir / "tic_tac_toe_elo_ratings.json")
        # Note: The heatmap is not saved in this example, but could be serialized as well.

    def show_dashboard(self) -> None:
        """Generates and displays a text-based dashboard summarizing the analytics."""
        dashboard = Dashboard(title="Tic-Tac-Toe Analytics Dashboard", width=80)

        # Add overall game statistics.
        total_games = len(self.game_stats.game_history)
        dashboard.add_stat("Game Statistics", "Total Games Played", total_games)

        if total_games > 0:
            # Display top players by win rate.
            top_players = self.game_stats.get_leaderboard("win_rate")[:3]
            leaderboard_text = [f"{i+1}. {p.player_id}: {p.wins}W-{p.losses}L-{p.draws}D ({p.win_rate():.1f}% win rate)" for i, p in enumerate(top_players)]
            dashboard.add_section("Top Players by Win Rate", leaderboard_text)

        # Add performance metrics.
        if self.performance_metrics.game_durations:
            dashboard.add_stat("Performance", "Avg. Game Duration", f"{self.performance_metrics.average_game_duration():.1f}s")
            dashboard.add_stat("Performance", "Shortest Game", f"{self.performance_metrics.shortest_game():.1f}s")

        # Add ELO ratings as a bar chart.
        elo_leaderboard = self.elo_ratings.get_leaderboard()[:5]
        if elo_leaderboard:
            dashboard.add_chart("ELO Ratings", dict(elo_leaderboard), max_width=30)

        print(dashboard.render())

    def show_move_heatmap(self) -> None:
        """Displays a heatmap of move frequency."""
        print("\n" + "=" * 60)
        print("Move Frequency Heatmap")
        print("=" * 60 + "\n")

        self.move_heatmap.normalize()  # Normalize values to a 0-1 scale for rendering.
        print(self.move_heatmap.render_ascii())
        print()

        # Identify the most popular opening moves.
        hotspots = self.move_heatmap.get_hotspots(threshold=0.5)
        if hotspots:
            print("Most Popular Positions:")
            for x, y, value in hotspots[:3]:
                print(f"  - Position ({x}, {y}): {value:.1%}")
        print()


def main() -> None:
    """Main function to run the analytics-integrated Tic-Tac-Toe demonstration."""
    game_with_analytics = TicTacToeWithAnalytics()

    print("=" * 60)
    print("Tic-Tac-Toe with Integrated Analytics")
    print("=" * 60)
    print("\nThis demo shows how the analytics system can be integrated into a game.")

    # Simulate a few games to generate some data.
    num_games_to_play = 3
    for i in range(num_games_to_play):
        print(f"\n--- Playing Game {i+1}/{num_games_to_play} ---")
        game_with_analytics.play_game("Alice", "Computer")
        if i < num_games_to_play - 1:
            input("\nPress Enter to start the next game...")

    # Display the collected analytics.
    print("\n" + "=" * 60)
    print("Analytics Summary")
    print("=" * 60 + "\n")

    game_with_analytics.show_dashboard()
    game_with_analytics.show_move_heatmap()

    print(f"\nAnalytics data has been saved to the '{game_with_analytics.stats_dir}/' directory.")
    print("Run this script again to continue adding to the dataset.")


if __name__ == "__main__":
    main()
