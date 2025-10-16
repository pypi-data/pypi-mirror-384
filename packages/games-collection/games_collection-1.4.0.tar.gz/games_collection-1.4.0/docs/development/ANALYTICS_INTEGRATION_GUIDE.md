# Analytics Integration Guide

This guide shows how to integrate the analytics system into your games to track statistics, performance, and player
ratings.

## Table of Contents

1. [Quick Start](#quick-start)
1. [Core Concepts](#core-concepts)
1. [Step-by-Step Integration](#step-by-step-integration)
1. [Advanced Features](#advanced-features)
1. [Best Practices](#best-practices)
1. [Examples](#examples)

## Quick Start

Minimal integration example:

```python
from common.analytics import GameStatistics, PerformanceMetrics, EloRating

class MyGame:
    def __init__(self):
        self.stats = GameStatistics(game_name="MyGame")
        self.metrics = PerformanceMetrics(game_name="MyGame")
        self.elo = EloRating()

    def play_game(self, player1, player2):
        start_time = time.time()

        # Your game logic here...
        winner = self.run_game_loop()

        duration = time.time() - start_time

        # Record results
        self.stats.record_game(winner, [player1, player2], duration)
        self.metrics.record_game_duration(duration)

        score = 1.0 if winner == player1 else 0.0
        self.elo.update_ratings(player1, player2, score)
```

## Core Concepts

### Game Statistics

Tracks overall game outcomes:

- Wins, losses, draws per player
- Win/loss streaks
- Total playtime
- Game history

### Performance Metrics

Tracks timing and quality:

- Decision time per move
- Game duration
- Move quality (optional)
- Speed trends

### Rating Systems

Tracks player skill:

- **ELO**: Classic rating system (simpler)
- **Glicko-2**: Advanced system with uncertainty (more accurate)

### Replay Analysis

Analyzes gameplay:

- Move patterns
- Position frequency
- Strategy analysis

### Visualizations

Presents data:

- Dashboards for statistics
- Heatmaps for position analysis
- Charts and graphs

## Step-by-Step Integration

### Step 1: Initialize Analytics

Add analytics trackers to your game class:

```python
from pathlib import Path
from common.analytics import (
    GameStatistics,
    PerformanceMetrics,
    EloRating,
    Heatmap,
)

class MyGame:
    def __init__(self, stats_dir: Path = None):
        self.stats_dir = stats_dir or Path("game_data")
        self.stats_dir.mkdir(exist_ok=True)

        # Initialize trackers
        self.stats = self._load_or_create_stats()
        self.metrics = self._load_or_create_metrics()
        self.elo = self._load_or_create_ratings()

        # Optional: Position heatmap for board games
        self.heatmap = Heatmap(width=8, height=8)

    def _load_or_create_stats(self):
        stats_file = self.stats_dir / "stats.json"
        try:
            return GameStatistics.load(stats_file)
        except FileNotFoundError:
            return GameStatistics(game_name="MyGame")
```

### Step 2: Track Moves and Decisions

Record each move with timing:

```python
def make_move(self, player_id, move):
    start_time = time.time()

    # Validate and execute move
    if self.is_valid_move(move):
        self.execute_move(move)

        # Calculate decision time
        decision_time = time.time() - start_time

        # Record decision
        self.metrics.record_decision(
            player_id=player_id,
            decision_time=decision_time,
            quality=self.evaluate_move_quality(move),  # Optional
        )

        # Update heatmap for board games
        if hasattr(move, 'position'):
            x, y = move.position
            self.heatmap.increment(x, y)

        return True
    return False
```

### Step 3: Record Game Results

After each game, record the outcome:

```python
def finish_game(self, winner, players, game_duration):
    # Record in statistics
    self.stats.record_game(
        winner=winner,
        players=players,
        duration=game_duration,
        metadata={
            "board_size": self.board_size,
            "difficulty": self.difficulty,
        },
    )

    # Record game duration
    self.metrics.record_game_duration(game_duration)

    # Update ratings
    if len(players) == 2:
        if winner == players[0]:
            score = 1.0
        elif winner == players[1]:
            score = 0.0
        else:
            score = 0.5  # Draw

        self.elo.update_ratings(players[0], players[1], score)

    # Save analytics
    self.save_analytics()
```

### Step 4: Save Analytics Data

Persist analytics after games:

```python
def save_analytics(self):
    """Save all analytics data to disk."""
    self.stats.save(self.stats_dir / "stats.json")
    self.metrics.save(self.stats_dir / "metrics.json")
    self.elo.save(self.stats_dir / "elo.json")
```

### Step 5: Display Analytics

Show statistics to players:

```python
from common.analytics import Dashboard

def show_statistics(self):
    # Create dashboard
    dashboard = Dashboard(title=f"{self.game_name} Statistics")

    # Add game stats
    total_games = len(self.stats.game_history)
    dashboard.add_stat("Overview", "Total Games", total_games)

    # Add leaderboard
    leaderboard = self.stats.get_leaderboard("win_rate")[:5]
    dashboard.add_section(
        "Top Players",
        [
            f"{i+1}. {p.player_id}: {p.wins}W-{p.losses}L "
            f"({p.win_rate():.1f}%)"
            for i, p in enumerate(leaderboard)
        ],
    )

    # Add performance metrics
    if self.metrics.game_durations:
        avg_duration = self.metrics.average_game_duration()
        dashboard.add_stat("Performance", "Avg Duration", f"{avg_duration:.1f}s")

    # Add ratings chart
    ratings = dict(self.elo.get_leaderboard()[:5])
    dashboard.add_chart("ELO Ratings", ratings)

    # Display
    print(dashboard.render())
```

## Advanced Features

### Move Quality Tracking

Implement move quality evaluation:

```python
def evaluate_move_quality(self, move, game_state):
    """Evaluate move quality (0-1 scale).

    Returns:
        Quality score where 1.0 is optimal.
    """
    # Compare with best possible move
    best_move = self.get_best_move(game_state)

    if move == best_move:
        return 1.0

    # Calculate similarity or value difference
    move_value = self.evaluate_position(move)
    best_value = self.evaluate_position(best_move)

    # Normalize to 0-1 range
    quality = move_value / best_value if best_value > 0 else 0.5

    return max(0.0, min(1.0, quality))
```

### Replay Analysis

Analyze completed games:

```python
from common.analytics import ReplayAnalyzer

def analyze_game(self, game_history):
    analyzer = ReplayAnalyzer(game_name=self.game_name)

    # Add all moves
    for move in game_history:
        analyzer.add_move(move)

    # Detect patterns
    def aggressive_detector(moves):
        return [i for i, m in enumerate(moves) if m.get('type') == 'attack']

    pattern = analyzer.detect_pattern(
        "aggressive_play",
        "Aggressive attack pattern",
        aggressive_detector,
    )

    # Analyze phases
    opening = analyzer.analyze_opening(num_moves=5)
    endgame = analyzer.analyze_endgame(num_moves=5)

    return analyzer
```

### Position Heatmaps

Visualize popular board positions:

```python
def show_position_heatmap(self):
    """Display position frequency heatmap."""
    self.heatmap.normalize()

    print("Position Frequency Heatmap:")
    print(self.heatmap.render_ascii())

    # Show hotspots
    hotspots = self.heatmap.get_hotspots(threshold=0.7)
    print("\nMost Popular Positions:")
    for x, y, value in hotspots[:5]:
        print(f"  ({x}, {y}): {value:.1%}")
```

### AI Difficulty Rating

Track and display AI difficulty:

```python
from common.analytics.rating_systems import calculate_ai_difficulty_rating

def evaluate_ai_difficulty(self, ai_player):
    """Calculate AI opponent difficulty rating."""
    # Get AI statistics
    player_stats = self.stats.get_or_create_player(ai_player)

    # Calculate metrics
    total_games = player_stats.total_games
    if total_games == 0:
        return 50.0  # Default neutral difficulty

    win_rate = player_stats.wins / total_games

    # Get performance data
    ai_metrics = self.metrics.get_or_create_player(ai_player)
    avg_quality = ai_metrics.average_move_quality() if ai_metrics.move_qualities else 0.7

    # Estimate game length (could track this separately)
    avg_length = 20.0

    # Calculate difficulty
    difficulty = calculate_ai_difficulty_rating(
        win_rate=win_rate,
        average_game_length=avg_length,
        move_quality=avg_quality,
    )

    return difficulty
```

## Best Practices

### 1. Save Frequently

Save analytics data regularly:

```python
def save_analytics_periodically(self, every_n_games=5):
    """Save after every N games."""
    if len(self.stats.game_history) % every_n_games == 0:
        self.save_analytics()
```

### 2. Handle Errors Gracefully

Protect against data corruption:

```python
def _load_or_create_stats(self):
    try:
        return GameStatistics.load(self.stats_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load stats: {e}")
        return GameStatistics(game_name=self.game_name)
```

### 3. Provide Privacy Options

Let players control their data:

```python
def __init__(self, enable_analytics=True, anonymous=False):
    self.enable_analytics = enable_analytics
    self.anonymous = anonymous

    if enable_analytics:
        self.stats = GameStatistics(game_name=self.game_name)
    else:
        self.stats = None

def record_game(self, winner, players, duration):
    if not self.enable_analytics:
        return

    # Anonymize if requested
    if self.anonymous:
        players = [f"Player{i+1}" for i in range(len(players))]
        winner = f"Player1" if winner == players[0] else None

    self.stats.record_game(winner, players, duration)
```

### 4. Optimize for Performance

Batch operations for large datasets:

```python
def record_batch_games(self, game_results):
    """Record multiple games efficiently."""
    for result in game_results:
        self.stats.record_game(
            winner=result['winner'],
            players=result['players'],
            duration=result['duration'],
        )

    # Save once at the end
    self.save_analytics()
```

### 5. Version Your Data

Include version info for compatibility:

```python
def save_analytics(self):
    """Save with version information."""
    self.stats.save(self.stats_dir / "stats.json")

    # Save version info
    version_file = self.stats_dir / "version.txt"
    with open(version_file, 'w') as f:
        f.write("1.0.0")
```

## Examples

### Example 1: Simple Card Game

```python
from common.analytics import GameStatistics, EloRating

class CardGame:
    def __init__(self):
        self.stats = GameStatistics(game_name="Cards")
        self.elo = EloRating()

    def play_round(self, players):
        start = time.time()
        winner = self.determine_winner(players)
        duration = time.time() - start

        self.stats.record_game(winner, players, duration)

        # Update all pairwise ratings
        for i, p1 in enumerate(players):
            for p2 in players[i+1:]:
                if winner == p1:
                    self.elo.update_ratings(p1, p2, 1.0)
                elif winner == p2:
                    self.elo.update_ratings(p1, p2, 0.0)
```

### Example 2: Board Game with Position Tracking

```python
from common.analytics import GameStatistics, Heatmap

class BoardGame:
    def __init__(self, board_size=8):
        self.stats = GameStatistics(game_name="Board")
        self.heatmap = Heatmap(board_size, board_size)

    def make_move(self, player, position):
        x, y = position

        if self.is_valid_move(position):
            self.execute_move(player, position)
            self.heatmap.increment(x, y)
            return True
        return False

    def show_popular_moves(self):
        self.heatmap.normalize()
        print(self.heatmap.render_ascii())
```

### Example 3: Real-time Strategy Game

```python
from common.analytics import PerformanceMetrics, ReplayAnalyzer

class RTSGame:
    def __init__(self):
        self.metrics = PerformanceMetrics(game_name="RTS")
        self.analyzer = ReplayAnalyzer(game_name="RTS")

    def execute_action(self, player, action):
        start = time.time()

        result = self.process_action(action)

        decision_time = time.time() - start
        quality = self.evaluate_action(action)

        self.metrics.record_decision(player, decision_time, quality)
        self.analyzer.add_move({
            'player': player,
            'action': action,
            'quality': quality,
            'timestamp': time.time(),
        })
```

## Testing Analytics Integration

Add tests for your analytics integration:

```python
import pytest
from pathlib import Path
import tempfile

def test_analytics_integration():
    with tempfile.TemporaryDirectory() as tmpdir:
        game = MyGame(stats_dir=Path(tmpdir))

        # Play test games
        game.play_game("Player1", "Player2")

        # Verify analytics recorded
        assert len(game.stats.game_history) == 1
        assert "Player1" in game.stats.players
        assert "Player2" in game.stats.players

        # Verify data saved
        assert (Path(tmpdir) / "stats.json").exists()
```

## Troubleshooting

### Analytics not saving

Check directory permissions and ensure `save_analytics()` is called:

```python
def save_analytics(self):
    try:
        self.stats_dir.mkdir(parents=True, exist_ok=True)
        self.stats.save(self.stats_dir / "stats.json")
    except Exception as e:
        print(f"Error saving analytics: {e}")
```

### Performance issues with large datasets

Limit history size or use database:

```python
def record_game(self, *args, **kwargs):
    super().record_game(*args, **kwargs)

    # Keep only recent history
    if len(self.game_history) > 1000:
        self.game_history = self.game_history[-1000:]
```

### Rating inflation/deflation

Reset ratings periodically or use decay:

```python
def decay_ratings(self, decay_factor=0.95):
    """Apply decay to pull ratings toward default."""
    for player_id in self.elo.player_ratings:
        current = self.elo.player_ratings[player_id]
        default = self.elo.default_rating
        self.elo.player_ratings[player_id] = (
            current * decay_factor + default * (1 - decay_factor)
        )
```

## Further Resources

- See `examples/analytics_demo.py` for comprehensive demonstrations
- See `examples/tic_tac_toe_with_analytics.py` for real integration
- Check `common/analytics/README.md` for API documentation
- Run tests: `pytest tests/test_analytics.py -v`

## Support

For questions or issues:

1. Check existing game integrations for examples
1. Review test cases for usage patterns
1. Create an issue on GitHub with details
