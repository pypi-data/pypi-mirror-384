# Unscramble - New Features

This document describes the enhanced features added to the Unscramble word game.

## Features Overview

### 1. Difficulty-Based Word Selection

The game now includes three difficulty levels based on word length:

- **Easy**: 6+ letter words (360 words) - More letters make patterns easier to spot
- **Medium**: 4-5 letter words (360 words) - Balanced challenge
- **Hard**: 3 letter words (360 words) - Very challenging with fewer letters
- **Mixed**: All difficulties combined (1,080 words)

**How to Use:**

```python
from paper_games.unscramble import load_words_by_difficulty, UnscrambleGame

# Load specific difficulty
easy_words = load_words_by_difficulty("easy")
medium_words = load_words_by_difficulty("medium")
hard_words = load_words_by_difficulty("hard")

# Create game with difficulty
game = UnscrambleGame(words=easy_words, difficulty="easy")
```

### 2. Themed Word Packs

Five themed word categories are now available:

- **Technical**: Programming and computer science terms (49 words)
- **Literature**: Literary terms and concepts (48 words)
- **Science**: Scientific terms from various fields (47 words)
- **Geography**: Geographic features and concepts (48 words)
- **Music**: Musical terms and concepts (52 words)

**How to Use:**

```python
from paper_games.unscramble import load_themed_words, UnscrambleGame

# List all themes
from paper_games.unscramble import list_themes
print(list_themes())

# Load specific theme
tech_words = load_themed_words("technical")

# Create game with theme
game = UnscrambleGame(words=tech_words, theme="technical")
```

### 3. Timed Mode

Play with a countdown timer for each word:

- **Easy**: 30 seconds per word
- **Medium**: 20 seconds per word (default)
- **Hard**: 10 seconds per word

Features:

- Real-time countdown
- Automatic timeout detection
- Time tracking for statistics
- Speed-based achievements

**How to Play:** Select "Timed Mode" from the CLI menu and choose your preferred time limit.

### 4. Multiplayer Competitive Mode

Compete with 2-4 players:

- **Turn-based gameplay**: Players take turns guessing each word
- **First to solve wins**: The first player to correctly guess gets the point
- **Optional timer**: Add time pressure with optional per-word timers
- **Score tracking**: Keep track of points across all rounds
- **Winner declaration**: Automatic winner announcement at game end

**How to Play:**

1. Select "Multiplayer Mode" from the CLI menu
1. Enter number of players (2-4)
1. Enter player names
1. Choose number of rounds
1. Select difficulty and theme
1. Optionally enable timer

### 5. Streak Tracking and Achievement System

Comprehensive statistics and achievements:

**Statistics Tracked:**

- Total words attempted
- Words solved
- Current streak (consecutive correct answers)
- Longest streak
- Solve rate percentage
- Fastest solve time
- Average solve time
- Stats by difficulty level
- Stats by theme
- Total games played

**Achievements:**

- **First Solve**: Solve your first word
- **Getting Started**: Solve 10 words
- **Word Master**: Solve 50 words
- **Unscramble Legend**: Solve 100 words
- **Streak Starter**: Achieve a 3-word streak
- **On Fire**: Achieve a 5-word streak
- **Unstoppable**: Achieve a 10-word streak
- **Speed Demon**: Solve a word in under 5 seconds
- **Lightning Fast**: Solve a word in under 3 seconds
- **Marathon Player**: Complete 10 game sessions
- **Dedicated**: Complete 25 game sessions

**How to Use:**

```python
from paper_games.unscramble import GameStats

# Load existing stats
stats = GameStats.load(filepath)

# Record word attempts
stats.record_word(solved=True, difficulty="easy", time_taken=4.5)

# Check for new achievements
new_achievements = stats.check_achievements()

# View statistics
print(stats.summary())

# Save statistics
stats.save(filepath)
```

### 6. Three Game Modes

**Classic Mode:**

- No time limit
- Focus on accuracy
- Choose difficulty and themes
- Track time for statistics

**Timed Mode:**

- Countdown timer per word
- Three difficulty levels (10s/20s/30s)
- High-pressure gameplay
- Speed-based achievements

**Multiplayer Mode:**

- 2-4 players
- Competitive turn-based play
- Optional timer
- Score tracking
- Winner declaration

## API Reference

### Functions

- `load_unscramble_words()` - Load all 1,080 words from all difficulties
- `load_words_by_difficulty(difficulty)` - Load words by difficulty level
- `load_themed_words(theme=None)` - Load themed word lists
- `list_themes()` - Get formatted string listing all themes

### UnscrambleGame Parameters

- `words` - Iterable of words to use
- `rng` - Random number generator (default: random.Random())
- `difficulty` - Optional difficulty name to display (default: None)
- `theme` - Optional theme name to display (default: None)

### GameStats Methods

- `record_word(solved, difficulty, theme, time_taken)` - Record word attempt
- `record_game()` - Record game session completion
- `check_achievements()` - Check and return newly unlocked achievements
- `solve_rate()` - Calculate solve percentage
- `average_solve_time()` - Calculate average time per solved word
- `summary()` - Generate formatted statistics summary
- `save(filepath)` - Save statistics to JSON file
- `load(filepath)` - Load statistics from JSON file

## Examples

### Classic Mode with Difficulty

```python
from paper_games.unscramble import UnscrambleGame, load_words_by_difficulty

hard_words = load_words_by_difficulty("hard")
game = UnscrambleGame(words=hard_words, difficulty="hard")

# Play rounds
for round_num in range(5):
    scrambled = game.new_round()
    print(f"Round {round_num + 1}: {scrambled}")
    guess = input("Your guess: ")
    if game.guess(guess):
        print("Correct!")
    else:
        print(f"Wrong! It was '{game.secret_word}'")
```

### Themed Game with Statistics

```python
from paper_games.unscramble import (
    UnscrambleGame,
    GameStats,
    load_themed_words
)
from pathlib import Path
import time

# Load stats and theme
stats = GameStats.load(Path.home() / ".games" / "unscramble_stats.json")
tech_words = load_themed_words("technical")
game = UnscrambleGame(words=tech_words, theme="technical")

# Play with time tracking
scrambled = game.new_round()
start_time = time.time()
guess = input(f"Unscramble: {scrambled} > ")
time_taken = time.time() - start_time

solved = game.guess(guess)
stats.record_word(
    solved=solved,
    theme="technical",
    time_taken=time_taken
)

# Check achievements
new_achievements = stats.check_achievements()
if new_achievements:
    print(f"New achievements: {', '.join(new_achievements)}")

# Save stats
stats.save(Path.home() / ".games" / "unscramble_stats.json")
```

### Multiplayer Game

```python
from paper_games.unscramble import UnscrambleGame

players = [
    {"name": "Alice", "score": 0},
    {"name": "Bob", "score": 0}
]

game = UnscrambleGame()

for round_num in range(5):
    game.new_round()
    print(f"\nRound {round_num + 1}: {game.scrambled}")

    for player in players:
        print(f"\n{player['name']}'s turn:")
        guess = input("Your guess: ")
        if game.guess(guess):
            print("Correct!")
            player["score"] += 1
            break
    else:
        print(f"No one got it! It was '{game.secret_word}'")

# Show results
winner = max(players, key=lambda p: p["score"])
print(f"\n{winner['name']} wins with {winner['score']} points!")
```

## Statistics File Location

Statistics are automatically saved to:

```
~/.games/unscramble_stats.json
```

This file contains:

- All word attempt history (aggregated)
- Streak information
- Achievements unlocked
- Time tracking data
- Stats by difficulty and theme

## Command Line Interface

When running the game via CLI:

```bash
python -m paper_games.unscramble
```

You'll be presented with:

1. Option to view existing statistics
1. Game mode selection (Classic/Timed/Multiplayer)
1. Difficulty selection
1. Theme selection (optional)
1. Game-specific options (rounds, timer duration, player count)
1. Achievement notifications
1. Final statistics summary

## Implementation Notes

### Word Selection

Words are selected randomly from the chosen difficulty or theme. Each word is scrambled by shuffling its letters,
ensuring the scrambled version is different from the original word.

### Time Tracking

Time is tracked using Python's `time.time()` for precise measurements. Times are recorded in seconds with decimal
precision.

### Statistics Persistence

Statistics are saved as JSON files with human-readable formatting. The file is created automatically on first use.

### Achievements

Achievements are checked after each game session. Once unlocked, achievements persist permanently in the statistics
file.

## Future Enhancements

Potential features for future versions:

- Hint system (reveal one letter)
- Hint penalties (time or point deduction)
- Online multiplayer with real-time competition
- Leaderboards
- Daily challenges
- Custom word pack creation
- Progressive difficulty (words get harder as you progress)
- Combo multipliers for consecutive fast solves
- Power-ups (extra time, letter reveal, shuffle)
