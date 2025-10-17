# Farkle

Farkle is a risk-based dice game where players roll six dice and try to accumulate points by banking scoring
combinations, with the risk of "farkling" (rolling no scoring dice) and losing all points for that turn.

## Rules

### Objective

Be the first player to reach 10,000 points.

### Scoring

- **Single 1**: 100 points
- **Single 5**: 50 points
- **Three of a kind**: number × 100 (except three 1s = 1000)
- **Four of a kind**: (three of a kind) × 2
- **Five of a kind**: (four of a kind) × 2
- **Six of a kind**: (five of a kind) × 2
- **Straight (1-2-3-4-5-6)**: 1500 points
- **Three pairs**: 1500 points

### Gameplay

1. On your turn, roll all 6 dice
1. Set aside scoring dice and add to your turn score
1. Choose to:
   - **Bank and continue**: Roll remaining dice to score more (risk farkling)
   - **Bank and end turn**: Add turn score to your total score
1. If you use all 6 dice ("hot dice"), you get all 6 back
1. If you roll with no scoring dice, you "farkle" and lose all turn points

## Running the Game

```bash
python -m dice_games.farkle
```

## Features

- 2-6 players
- Push-your-luck mechanics
- Hot dice bonus
- Strategic risk/reward decisions

## Strategy Tips

- Early in the game, take more risks to build your score
- Near 10,000 points, play more conservatively
- Hot dice are powerful - try to use all 6 dice when possible
- Banking 300-500 points is often safer than risking a farkle
