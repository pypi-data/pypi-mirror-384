"""Demo of the analytics and metrics system.

This example demonstrates how to use the analytics system to track
game statistics, performance metrics, ratings, and visualizations.
"""

from __future__ import annotations

import time

from common.analytics import Dashboard, EloRating, GameStatistics, Heatmap, PerformanceMetrics, ReplayAnalyzer
from common.analytics.rating_systems import calculate_ai_difficulty_rating
from common.analytics.visualization import create_leaderboard_display


def demo_game_statistics() -> None:
    """Demonstrate game statistics tracking."""
    print("=" * 80)
    print("GAME STATISTICS DEMO")
    print("=" * 80)
    print()

    # Create statistics tracker
    stats = GameStatistics(game_name="Tic-Tac-Toe")

    # Simulate some games
    print("Simulating games...")
    stats.record_game(winner="Alice", players=["Alice", "Bob"], duration=120.0)
    stats.record_game(winner="Alice", players=["Alice", "Bob"], duration=95.0)
    stats.record_game(winner="Bob", players=["Alice", "Bob"], duration=150.0)
    stats.record_game(winner="Alice", players=["Alice", "Charlie"], duration=110.0)
    stats.record_game(winner=None, players=["Bob", "Charlie"], duration=180.0)  # Draw

    # Display summary
    print(stats.get_summary())
    print()


def demo_performance_metrics() -> None:
    """Demonstrate performance metrics tracking."""
    print("=" * 80)
    print("PERFORMANCE METRICS DEMO")
    print("=" * 80)
    print()

    # Create performance tracker
    metrics = PerformanceMetrics(game_name="Chess")

    # Simulate decisions
    print("Recording player decisions...")
    metrics.record_decision("Alice", 2.5, quality=0.85)
    metrics.record_decision("Alice", 3.2, quality=0.90)
    metrics.record_decision("Alice", 1.8, quality=0.75)
    metrics.record_decision("Bob", 5.1, quality=0.65)
    metrics.record_decision("Bob", 4.3, quality=0.70)

    # Record game durations
    metrics.record_game_duration(1200.0)
    metrics.record_game_duration(1500.0)
    metrics.record_game_duration(900.0)

    # Display summary
    print(metrics.get_summary())
    print()


def demo_elo_rating() -> None:
    """Demonstrate ELO rating system."""
    print("=" * 80)
    print("ELO RATING SYSTEM DEMO")
    print("=" * 80)
    print()

    # Create ELO tracker
    elo = EloRating()

    # Simulate tournament
    print("Simulating tournament matches...")

    # Round 1
    elo.update_ratings("Alice", "Bob", 1.0)  # Alice wins
    elo.update_ratings("Charlie", "Diana", 1.0)  # Charlie wins

    # Round 2
    elo.update_ratings("Alice", "Charlie", 0.5)  # Draw
    elo.update_ratings("Bob", "Diana", 1.0)  # Bob wins

    # Round 3
    elo.update_ratings("Alice", "Diana", 1.0)  # Alice wins
    elo.update_ratings("Charlie", "Bob", 1.0)  # Charlie wins

    # Display leaderboard
    leaderboard = elo.get_leaderboard()
    print(create_leaderboard_display(leaderboard, title="Tournament Leaderboard"))
    print()


def demo_replay_analysis() -> None:
    """Demonstrate replay analysis."""
    print("=" * 80)
    print("REPLAY ANALYSIS DEMO")
    print("=" * 80)
    print()

    # Create analyzer
    analyzer = ReplayAnalyzer(game_name="Strategy Game")

    # Add some moves
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

    # Detect patterns
    def attack_pattern_detector(move_history):
        return [i for i, m in enumerate(move_history) if m["type"] == "attack"]

    pattern = analyzer.detect_pattern(
        "attack_moves",
        "Aggressive attack moves",
        attack_pattern_detector,
    )

    print(f"Pattern '{pattern.description}' detected {pattern.occurrences} times")
    print()

    # Analyze opening
    opening = analyzer.analyze_opening(num_moves=2)
    print(f"Opening analysis: {opening['num_moves']} moves")
    print()


def demo_heatmap() -> None:
    """Demonstrate heatmap visualization."""
    print("=" * 80)
    print("HEATMAP VISUALIZATION DEMO")
    print("=" * 80)
    print()

    # Create a 5x5 heatmap
    heatmap = Heatmap(width=5, height=5)

    # Simulate position usage
    print("Recording position usage...")
    positions = [
        (2, 2, 10),  # Center is hottest
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

    # Normalize values
    heatmap.normalize()

    # Display heatmap
    print("Position Frequency Heatmap:")
    print(heatmap.render_ascii())
    print()

    # Show hotspots
    hotspots = heatmap.get_hotspots(threshold=0.6)
    print("Hotspots (threshold 0.6):")
    for x, y, value in hotspots:
        print(f"  Position ({x}, {y}): {value:.2f}")
    print()


def demo_dashboard() -> None:
    """Demonstrate dashboard creation."""
    print("=" * 80)
    print("DASHBOARD DEMO")
    print("=" * 80)
    print()

    # Create dashboard
    dashboard = Dashboard(title="Game Analytics Dashboard", width=80)

    # Add statistics section
    dashboard.add_stat("Game Statistics", "Total Games", 150)
    dashboard.add_stat("Game Statistics", "Win Rate", 0.653, ".1%")
    dashboard.add_stat("Game Statistics", "Average Duration", "12:35")

    # Add performance section
    dashboard.add_stat("Performance", "Average Decision Time", "3.2s")
    dashboard.add_stat("Performance", "Move Quality", 0.82, ".1%")

    # Add chart
    player_wins = {
        "Alice": 45,
        "Bob": 38,
        "Charlie": 32,
        "Diana": 35,
    }
    dashboard.add_chart("Player Wins", player_wins, max_width=30)

    # Render dashboard
    print(dashboard.render())


def demo_ai_difficulty() -> None:
    """Demonstrate AI difficulty rating."""
    print("=" * 80)
    print("AI DIFFICULTY RATING DEMO")
    print("=" * 80)
    print()

    # Calculate difficulty for different AI levels
    ai_configs = [
        ("Easy AI", 0.3, 15.0, 0.5),
        ("Medium AI", 0.6, 20.0, 0.75),
        ("Hard AI", 0.85, 25.0, 0.9),
        ("Expert AI", 0.95, 30.0, 0.98),
    ]

    print("AI Difficulty Ratings:")
    for name, win_rate, avg_length, quality in ai_configs:
        difficulty = calculate_ai_difficulty_rating(win_rate, avg_length, quality)
        print(f"  {name:15s}: {difficulty:.1f}/100")
    print()


def main() -> None:
    """Run all analytics demos."""
    demos = [
        demo_game_statistics,
        demo_performance_metrics,
        demo_elo_rating,
        demo_replay_analysis,
        demo_heatmap,
        demo_dashboard,
        demo_ai_difficulty,
    ]

    for demo_func in demos:
        demo_func()
        time.sleep(1)  # Pause between demos

    print("=" * 80)
    print("Analytics demo complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
