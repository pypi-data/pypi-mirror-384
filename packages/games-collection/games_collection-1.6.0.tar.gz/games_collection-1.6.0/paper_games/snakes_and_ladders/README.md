# Snakes and Ladders

A classic board game where players race to the finish by rolling dice, climbing ladders, and avoiding snakes.

## How to Play

**Objective**: Be the first player to reach square 100 (or the configured board size).

**Gameplay**:

1. Players take turns rolling a single die (1-6)
1. Move your token forward by the number rolled
1. If you land on a ladder, climb up to the top
1. If you land on a snake's head, slide down to its tail
1. First player to reach or pass the final square wins

**Run the game**:

```bash
python -m paper_games.snakes_and_ladders
```

## Features

- 2-4 player support
- Standard 100-square board
- Configurable snakes and ladders
- Classic game rules
- Turn-based CLI interface

## Game Rules

- Players start at position 0
- Dice rolls are 1-6
- Ladders provide shortcuts forward
- Snakes send you backward
- Must reach exactly or beyond the final square to win
- No special rules for exact landing in this implementation

## Implementation Notes

- Extends `GameEngine` for consistent game logic
- Type hints and docstrings for code quality
- Configurable board size and snake/ladder positions
- Simple but complete implementation

## Example Snakes and Ladders

**Default Ladders** (shortcuts):

- 1 → 38, 4 → 14, 9 → 31, 21 → 42, 28 → 84, 36 → 44, 51 → 67, 71 → 91, 80 → 100

**Default Snakes** (setbacks):

- 16 → 6, 47 → 26, 49 → 11, 56 → 53, 62 → 19, 64 → 60, 87 → 24, 93 → 73, 95 → 75, 98 → 78
