# Yahtzee

A classic dice game where players roll five dice trying to achieve specific combinations for points.

## How to Play

**Objective**: Score the highest total by filling in all 13 categories on your scorecard.

**Gameplay**:

1. Roll five dice up to three times per turn
1. After each roll, choose which dice to keep
1. After your rolls, choose a category to score
1. Each category can only be used once
1. Game ends when all players have scored all 13 categories

**Run the game**:

```bash
python -m paper_games.yahtzee
```

## Scoring Categories

**Upper Section** (score sum of matching dice):

- Ones, Twos, Threes, Fours, Fives, Sixes
- Bonus: 35 points if upper section totals 63 or more

**Lower Section**:

- **Three of a Kind**: Sum of all dice (if at least 3 match)
- **Four of a Kind**: Sum of all dice (if at least 4 match)
- **Full House**: 25 points (3 of one number, 2 of another)
- **Small Straight**: 30 points (sequence of 4)
- **Large Straight**: 40 points (sequence of 5)
- **Yahtzee**: 50 points (all 5 dice match)
- **Chance**: Sum of all dice (any combination)

## Features

- 1-4 player support
- Standard Yahtzee scoring rules
- Up to 3 rolls per turn
- Strategy-based dice keeping
- Bonus for upper section
- Complete scorecard display

## Strategy Tips

- Try to get the upper section bonus (63+ points)
- Save Chance for when you have bad rolls
- Yahtzee is worth the most at 50 points
- Straights require planning across rolls
- Sometimes it's better to take a zero than waste a good category

## Implementation Notes

- Extends `GameEngine` for consistent game logic
- Enum-based category system
- Type hints and comprehensive docstrings
- Proper score calculation for all categories
