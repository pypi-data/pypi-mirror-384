"""This module provides a comprehensive demonstration of the analytics and metrics system.

It showcases the capabilities of various components within the `common.analytics`
package, illustrating how to track, analyze, and visualize game-related data.

The demonstrations include:
- Basic game statistics (wins, losses, duration).
- Player and game performance metrics.
- ELO rating system for competitive player ranking.
- Replay analysis for pattern detection and strategic insights.
- Heatmap visualization for spatial data analysis.
- Dashboard creation for a high-level overview of key metrics.
- AI difficulty rating based on performance.
"""

from __future__ import annotations

import time

from common.analytics import Dashboard, EloRating, GameStatistics, Heatmap, PerformanceMetrics, ReplayAnalyzer
from common.analytics.rating_systems import calculate_ai_difficulty_rating
from common.analytics.visualization import create_leaderboard_display


def demo_game_statistics() -> None:
    """Demonstrates the tracking of basic game statistics.

    This function simulates a series of games and records the outcomes
    using the `GameStatistics` class. It then displays a summary of the
    collected data, such as win counts, total games, and average duration.
    """
    print("=" * 80)
    print("GAME STATISTICS DEMO")
    print("=" * 80)
    print()

    # Initialize a statistics tracker for a specific game.
    # This allows for separate tracking for different games in the collection.
    stats = GameStatistics(game_name="Tic-Tac-Toe")

    # Simulate several game outcomes to populate the tracker.
    # This includes wins, losses, and draws between different players.
    print("Simulating games...")
    stats.record_game(winner="Alice", players=["Alice", "Bob"], duration=120.0)
    stats.record_game(winner="Alice", players=["Alice", "Bob"], duration=95.0)
    stats.record_game(winner="Bob", players=["Alice", "Bob"], duration=150.0)
    stats.record_game(winner="Alice", players=["Alice", "Charlie"], duration=110.0)
    stats.record_game(winner=None, players=["Bob", "Charlie"], duration=180.0)  # A `None` winner indicates a draw.

    # Display a formatted summary of the statistics.
    print(stats.get_summary())
    print()


def demo_performance_metrics() -> None:
    """Demonstrates the tracking of player and game performance metrics.

    This function uses the `PerformanceMetrics` class to record data
    related to player decision-making and overall game performance.
    """
    print("=" * 80)
    print("PERFORMANCE METRICS DEMO")
    print("=" * 80)
    print()

    # Initialize a performance tracker for a specific game.
    metrics = PerformanceMetrics(game_name="Chess")

    # Record individual player decisions, including the time taken and a quality score.
    # This can be used to analyze player efficiency and skill.
    print("Recording player decisions...")
    metrics.record_decision("Alice", 2.5, quality=0.85)
    metrics.record_decision("Alice", 3.2, quality=0.90)
    metrics.record_decision("Alice", 1.8, quality=0.75)
    metrics.record_decision("Bob", 5.1, quality=0.65)
    metrics.record_decision("Bob", 4.3, quality=0.70)

    # Record the total duration of several games.
    metrics.record_game_duration(1200.0)
    metrics.record_game_duration(1500.0)
    metrics.record_game_duration(900.0)

    # Display a summary of the collected performance data.
    print(metrics.get_summary())
    print()


def demo_elo_rating() -> None:
    """Demonstrates the ELO rating system for player ranking.

    This function simulates a small tournament and updates player ratings
    based on match outcomes using the `EloRating` class. A leaderboard
    is displayed at the end.
    """
    print("=" * 80)
    print("ELO RATING SYSTEM DEMO")
    print("=" * 80)
    print()

    # Initialize the ELO rating system.
    elo = EloRating()

    # Simulate a series of tournament matches.
    # The `update_ratings` method takes the winner and loser, or two players and a score (1.0 for win, 0.5 for draw, 0.0 for loss).
    print("Simulating tournament matches...")

    # Round 1: Alice and Charlie win their matches.
    elo.update_ratings("Alice", "Bob", 1.0)
    elo.update_ratings("Charlie", "Diana", 1.0)

    # Round 2: Alice and Charlie draw, Bob beats Diana.
    elo.update_ratings("Alice", "Charlie", 0.5)
    elo.update_ratings("Bob", "Diana", 1.0)

    # Round 3: Alice and Charlie win again.
    elo.update_ratings("Alice", "Diana", 1.0)
    elo.update_ratings("Charlie", "Bob", 1.0)

    # Retrieve and display the final leaderboard.
    leaderboard = elo.get_leaderboard()
    print(create_leaderboard_display(leaderboard, title="Tournament Leaderboard"))
    print()


def demo_replay_analysis() -> None:
    """Demonstrates the analysis of game replays.

    This function uses the `ReplayAnalyzer` to record a sequence of game
    moves and then performs analysis, such as detecting specific patterns
    and examining opening moves.
    """
    print("=" * 80)
    print("REPLAY ANALYSIS DEMO")
    print("=" * 80)
    print()

    # Initialize a replay analyzer for a strategy game.
    analyzer = ReplayAnalyzer(game_name="Strategy Game")

    # Record a sequence of moves, each with metadata like player, type, and quality.
    print("Recording game moves...")
    moves = [
        {"player_id": "Alice", "type": "attack", "position": (2, 3), "quality": 0.8},
        {"player_id": "Bob", "type": "defend", "position": (2, 4), "quality": 0.7},
        {"player_id": "Alice", "type": "attack", "position": (3, 3), "quality": 0.9},
        {"player_id": "Bob", "type": "move", "position": (1, 1), "quality": 0.6},
        {"player_id": "Alice", "type": "attack", "position": (2, 3), "quality": 0.85},
    ]
    for move in moves:
        analyzer.add_move(move)

    # Define a custom function to detect a specific pattern (e.g., all attack moves).
    def attack_pattern_detector(move_history):
        """Finds all moves of type 'attack'."""
        return [i for i, m in enumerate(move_history) if m["type"] == "attack"]

    # Use the analyzer to find occurrences of the defined pattern.
    pattern = analyzer.detect_pattern(
        "attack_moves",
        "Aggressive attack moves",
        attack_pattern_detector,
    )
    print(f"Pattern '{pattern.description}' detected {pattern.occurrences} times")
    print()

    # Analyze the opening phase of the game.
    opening = analyzer.analyze_opening(num_moves=2)
    print(f"Opening analysis: {opening['num_moves']} moves examined.")
    print()


def demo_heatmap() -> None:
    """Demonstrates the creation and rendering of a heatmap.

    This function uses the `Heatmap` class to visualize spatial data,
    such as the frequency of actions on a game board.
    """
    print("=" * 80)
    print("HEATMAP VISUALIZATION DEMO")
    print("=" * 80)
    print()

    # Create a 5x5 heatmap, representing a small game board.
    heatmap = Heatmap(width=5, height=5)

    # Simulate and record usage of different positions on the board.
    print("Recording position usage...")
    positions = [
        (2, 2, 10),  # Center is the most used position
        (1, 1, 7),
        (3, 3, 7),
        (2, 1, 5),
        (2, 3, 5),
        (1, 2, 4),
        (3, 2, 4),
        (0, 0, 2),
        (4, 4, 2),
    ]
    for x, y, count in positions:
        heatmap.set_value(x, y, count)

    # Normalize the heatmap values to a 0-1 scale for consistent visualization.
    heatmap.normalize()

    # Render the heatmap as an ASCII chart in the console.
    print("Position Frequency Heatmap:")
    print(heatmap.render_ascii())
    print()

    # Identify and display "hotspots" where activity is above a certain threshold.
    hotspots = heatmap.get_hotspots(threshold=0.6)
    print("Hotspots (activity > 60%):")
    for x, y, value in hotspots:
        print(f"  Position ({x}, {y}): {value:.2f}")
    print()


def demo_dashboard() -> None:
    """Demonstrates the creation of a text-based analytics dashboard.

    This function uses the `Dashboard` class to combine various statistics
    and charts into a single, consolidated view.
    """
    print("=" * 80)
    print("DASHBOARD DEMO")
    print("=" * 80)
    print()

    # Initialize a dashboard with a title.
    dashboard = Dashboard(title="Game Analytics Dashboard", width=80)

    # Add key statistics to different sections of the dashboard.
    dashboard.add_stat("Game Statistics", "Total Games", 150)
    dashboard.add_stat("Game Statistics", "Win Rate", 0.653, ".1%")  # Format as percentage
    dashboard.add_stat("Game Statistics", "Average Duration", "12:35")

    dashboard.add_stat("Performance", "Average Decision Time", "3.2s")
    dashboard.add_stat("Performance", "Move Quality", 0.82, ".1%")

    # Add a simple bar chart to the dashboard.
    player_wins = {
        "Alice": 45,
        "Bob": 38,
        "Charlie": 32,
        "Diana": 35,
    }
    dashboard.add_chart("Player Wins", player_wins, max_width=30)

    # Render the complete dashboard to the console.
    print(dashboard.render())


def demo_ai_difficulty() -> None:
    """Demonstrates the rating of AI difficulty levels.

    This function calculates a difficulty score for different AI configurations
    based on their performance metrics.
    """
    print("=" * 80)
    print("AI DIFFICULTY RATING DEMO")
    print("=" * 80)
    print()

    # Define several AI configurations with different performance characteristics.
    ai_configs = [
        # (Name, Win Rate, Average Game Length, Move Quality)
        ("Easy AI", 0.3, 15.0, 0.5),
        ("Medium AI", 0.6, 20.0, 0.75),
        ("Hard AI", 0.85, 25.0, 0.9),
        ("Expert AI", 0.95, 30.0, 0.98),
    ]

    print("AI Difficulty Ratings:")
    # Calculate and display a difficulty rating for each AI.
    for name, win_rate, avg_length, quality in ai_configs:
        difficulty = calculate_ai_difficulty_rating(win_rate, avg_length, quality)
        print(f"  {name:15s}: {difficulty:.1f}/100")
    print()


def main() -> None:
    """Runs all analytics demonstrations in sequence.

    This main function calls each demo function to provide a complete
    overview of the analytics system's features.
    """
    demos = [
        demo_game_statistics,
        demo_performance_metrics,
        demo_elo_rating,
        demo_replay_analysis,
        demo_heatmap,
        demo_dashboard,
        demo_ai_difficulty,
    ]

    # Iterate through and run each demo function.
    for i, demo_func in enumerate(demos):
        demo_func()
        # Pause briefly between demos for better readability.
        if i < len(demos) - 1:
            time.sleep(1)

    print("=" * 80)
    print("Analytics demo complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
