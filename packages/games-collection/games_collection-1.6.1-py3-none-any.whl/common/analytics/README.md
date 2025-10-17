# Analytics & Metrics System

The analytics module provides comprehensive tools for tracking, analyzing, and visualizing game statistics and player
performance.

## Features

- **Game Statistics**: Track wins, losses, draws, and streaks
- **Performance Metrics**: Monitor game duration, decision time, and move quality
- **Rating Systems**: ELO and Glicko-2 implementations for skill rating
- **Replay Analysis**: Analyze game replays to detect patterns and strategies
- **Visualizations**: Dashboards, heatmaps, and charts for data presentation
- **AI Difficulty Rating**: Calculate and track AI opponent difficulty

## Installation

The analytics module is included in the `common` package. No additional dependencies required.

## Quick Start

### Game Statistics

Track wins, losses, and player statistics:

```python
from common.analytics import GameStatistics

# Create statistics tracker
stats = GameStatistics(game_name="Tic-Tac-Toe")

# Record games
stats.record_game(
    winner="Alice",
    players=["Alice", "Bob"],
    duration=120.0,
)

# View leaderboard
leaderboard = stats.get_leaderboard("win_rate")
for player in leaderboard:
    print(f"{player.player_id}: {player.win_rate():.1f}% win rate")

# Save/load statistics
stats.save(Path("stats.json"))
loaded = GameStatistics.load(Path("stats.json"))
```

### Performance Metrics

Track decision times and move quality:

```python
from common.analytics import PerformanceMetrics

# Create metrics tracker
metrics = PerformanceMetrics(game_name="Chess")

# Record decisions
metrics.record_decision(
    player_id="Alice",
    decision_time=2.5,
    quality=0.85,
)

# Record game duration
metrics.record_game_duration(1200.0)

# View summary
print(metrics.get_summary())
```

### ELO Rating System

Track player skill with ELO ratings:

```python
from common.analytics import EloRating

# Create ELO tracker
elo = EloRating()

# Update ratings after a game
new_rating_a, new_rating_b = elo.update_ratings(
    player_a="Alice",
    player_b="Bob",
    score_a=1.0,  # 1=win, 0.5=draw, 0=loss
)

# View leaderboard
leaderboard = elo.get_leaderboard()
```

### Glicko-2 Rating System

More sophisticated rating with uncertainty:

```python
from common.analytics import GlickoRating

# Create Glicko tracker
glicko = GlickoRating()

# Update ratings
new_a, new_b = glicko.update_ratings(
    player_a="Alice",
    player_b="Bob",
    score_a=1.0,
)

# View rating details
rating = glicko.get_rating("Alice")
print(f"Rating: {rating['rating']:.0f}")
print(f"RD: {rating['rd']:.0f}")
print(f"Volatility: {rating['volatility']:.3f}")
```

### Replay Analysis

Analyze game replays for patterns:

```python
from common.analytics import ReplayAnalyzer

# Create analyzer
analyzer = ReplayAnalyzer(game_name="Strategy Game")

# Add moves
analyzer.add_move({
    "player_id": "Alice",
    "type": "attack",
    "position": (2, 3),
    "quality": 0.85,
})

# Detect patterns
def pattern_detector(moves):
    return [i for i, m in enumerate(moves) if m["type"] == "attack"]

pattern = analyzer.detect_pattern(
    "aggressive_play",
    "Aggressive attack pattern",
    pattern_detector,
)

# Get heatmap data
heatmap_data = analyzer.get_position_heatmap_data()
```

### Heatmaps

Visualize position frequency and strategy:

```python
from common.analytics import Heatmap

# Create heatmap
heatmap = Heatmap(width=8, height=8)

# Record position usage
heatmap.increment(3, 4)
heatmap.increment(3, 4)
heatmap.increment(2, 5)

# Normalize and display
heatmap.normalize()
print(heatmap.render_ascii())

# Find hotspots
hotspots = heatmap.get_hotspots(threshold=0.7)
```

### Dashboards

Create visual analytics dashboards:

```python
from common.analytics import Dashboard

# Create dashboard
dashboard = Dashboard(title="Game Analytics")

# Add statistics
dashboard.add_stat("Overview", "Total Games", 150)
dashboard.add_stat("Overview", "Win Rate", 0.653, ".1%")

# Add chart
player_data = {
    "Alice": 45,
    "Bob": 38,
    "Charlie": 32,
}
dashboard.add_chart("Player Wins", player_data)

# Render
print(dashboard.render())
```

### AI Difficulty Rating

Calculate AI opponent difficulty:

```python
from common.analytics.rating_systems import calculate_ai_difficulty_rating

difficulty = calculate_ai_difficulty_rating(
    win_rate=0.85,
    average_game_length=25.0,
    move_quality=0.9,
)

print(f"AI Difficulty: {difficulty:.1f}/100")
```

## Complete Example

```python
from pathlib import Path
from common.analytics import (
    GameStatistics,
    PerformanceMetrics,
    EloRating,
    Dashboard,
)

# Track statistics
stats = GameStatistics(game_name="Chess")
metrics = PerformanceMetrics(game_name="Chess")
elo = EloRating()

# Play games
for _ in range(10):
    # Record game
    stats.record_game("Alice", ["Alice", "Bob"], 1200.0)
    metrics.record_game_duration(1200.0)

    # Record decisions
    metrics.record_decision("Alice", 3.2, quality=0.85)
    metrics.record_decision("Bob", 4.5, quality=0.75)

    # Update ratings
    elo.update_ratings("Alice", "Bob", 1.0)

# Create dashboard
dashboard = Dashboard(title="Chess Analytics")
dashboard.add_stat("Games", "Total", len(stats.game_history))
dashboard.add_stat("Games", "Avg Duration", f"{metrics.average_game_duration():.0f}s")

# Add leaderboard
leaderboard = elo.get_leaderboard()
dashboard.add_section(
    "Ratings",
    [f"{pid}: {rating:.0f}" for pid, rating in leaderboard[:5]],
)

print(dashboard.render())

# Save data
stats.save(Path("stats.json"))
metrics.save(Path("metrics.json"))
elo.save(Path("ratings.json"))
```

## API Reference

### GameStatistics

- `record_game(winner, players, duration, metadata)` - Record a game result
- `get_or_create_player(player_id)` - Get or create player stats
- `get_leaderboard(sort_by)` - Get sorted leaderboard
- `get_summary()` - Generate statistics summary
- `save(filepath)` / `load(filepath)` - Persist statistics

### PerformanceMetrics

- `record_decision(player_id, decision_time, quality)` - Record a decision
- `record_game_duration(duration)` - Record game duration
- `average_game_duration()` - Get average game time
- `get_summary()` - Generate performance summary
- `save(filepath)` / `load(filepath)` - Persist metrics

### EloRating

- `get_rating(player_id)` - Get player's rating
- `expected_score(rating_a, rating_b)` - Calculate expected outcome
- `update_ratings(player_a, player_b, score_a)` - Update after game
- `get_leaderboard()` - Get sorted ratings
- `save(filepath)` / `load(filepath)` - Persist ratings

### GlickoRating

- `get_rating(player_id)` - Get rating, RD, and volatility
- `update_ratings(player_a, player_b, score_a)` - Update after game
- `get_leaderboard()` - Get sorted ratings
- `save(filepath)` / `load(filepath)` - Persist ratings

### ReplayAnalyzer

- `add_move(move_data)` - Add move to history
- `detect_pattern(pattern_id, description, detector)` - Detect pattern
- `analyze_opening(num_moves)` - Analyze opening moves
- `analyze_endgame(num_moves)` - Analyze endgame
- `get_move_frequency(player_id)` - Get move frequency
- `get_position_heatmap_data()` - Get heatmap data
- `save_analysis(filepath)` / `load_analysis(filepath)` - Persist analysis

### Heatmap

- `set_value(x, y, value)` - Set cell value
- `get_value(x, y)` - Get cell value
- `increment(x, y, amount)` - Increment cell
- `normalize()` - Normalize to 0-1 range
- `render_ascii()` - Render as ASCII art
- `get_hotspots(threshold)` - Find high-value positions

### Dashboard

- `add_section(title, content, style)` - Add section
- `add_stat(section_title, stat_name, value, format_spec)` - Add statistic
- `add_chart(section_title, data, max_width)` - Add bar chart
- `render()` - Render dashboard
- `clear()` - Clear all sections

## Integration with Games

To integrate analytics into your game:

1. Create statistics and metrics trackers at game start
1. Record decisions and moves during gameplay
1. Update statistics and ratings after each game
1. Save analytics data periodically
1. Display dashboards and summaries to players

Example integration:

```python
class MyGame:
    def __init__(self):
        self.stats = GameStatistics(game_name="MyGame")
        self.metrics = PerformanceMetrics(game_name="MyGame")
        self.elo = EloRating()

    def play_game(self, player1, player2):
        # Game logic here...

        # Record analytics
        self.stats.record_game(winner, [player1, player2], duration)
        self.metrics.record_game_duration(duration)

        # Update ratings
        score = 1.0 if winner == player1 else 0.0
        self.elo.update_ratings(player1, player2, score)

    def show_stats(self):
        print(self.stats.get_summary())
        print(self.metrics.get_summary())
```

## Best Practices

1. **Save Regularly**: Persist analytics data after each game or session
1. **Use Appropriate Metrics**: Choose metrics relevant to your game type
1. **Normalize Data**: Use normalize() for heatmaps before visualization
1. **Handle Edge Cases**: Check for zero-division in rate calculations
1. **Privacy**: Consider player privacy when storing and displaying data
1. **Performance**: For large datasets, consider batching operations

## Examples

See `examples/analytics_demo.py` for a comprehensive demonstration of all features.

## Testing

Run the test suite:

```bash
pytest tests/test_analytics.py -v
```

## Future Enhancements

- Export to CSV/Excel formats
- Web-based dashboards
- Advanced statistical analysis
- Machine learning integration
- Real-time analytics streaming
- Multi-game aggregation

## License

Part of the Games repository. See main LICENSE file.
