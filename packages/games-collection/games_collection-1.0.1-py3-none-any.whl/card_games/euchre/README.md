# Euchre

A trump-based trick-taking card game with unique "going alone" mechanics and a 24-card deck.

## Game Overview

Euchre is a four-player partnership trick-taking game played with a 24-card deck. The goal is to be the first team to
reach 10 points by winning tricks.

## Rules

### Setup

- 24-card deck (9, T, J, Q, K, A of each suit)
- Four players in two partnerships:
  - Team 1: Players 0 & 2
  - Team 2: Players 1 & 3
- Five cards dealt to each player
- First team to 10 points wins

### Trump Selection

- Dealer turns up top card
- Players can accept or pass
- If all pass, can name any suit as trump
- Maker's team must win at least 3 tricks

### Card Rankings

In trump suit (high to low):

1. Right Bower (Jack of trump)
1. Left Bower (Jack of same color)
1. Ace
1. King
1. Queen
1. 10
1. 9

Non-trump suits follow standard ranking.

### Gameplay

- Player to dealer's left leads first trick
- Must follow suit if able
- Highest trump wins, or highest card of led suit
- Winner of trick leads next trick

### Scoring

- **Made it**: Maker's team wins 3-4 tricks → 1 point
- **March**: Maker's team wins all 5 tricks → 2 points
- **Euchred**: Defenders win 3+ tricks → 2 points
- **Going Alone March**: Alone player wins all 5 tricks → 4 points
- **Going Alone Made it**: Alone player wins 3-4 tricks → 2 points

### Going Alone

- Maker can choose to "go alone"
- Partner sits out the hand
- Higher scoring potential

## Features

- Four-player partnership gameplay
- Trump suit selection
- Bower system (right and left)
- Going alone mechanic
- First to 10 points wins

## Usage

```bash
# Play interactively
python -m card_games.euchre

# With seed for reproducibility
python -m card_games.euchre --seed 42
```

## Strategy Tips

1. **Trump Selection**: Choose trump when you have strong cards
1. **Leading**: Lead trump early to draw out opponents' trump
1. **Going Alone**: Only go alone with very strong hands
1. **Following Suit**: Track which suits are exhausted

## Implementation Notes

This implementation includes:

- ✅ Full game engine
- ✅ Trump selection
- ✅ Bower system
- ✅ Partnership scoring
- ✅ Interactive CLI
- ⏳ Going alone mechanics (simplified)
- ⏳ GUI (planned)
- ⏳ Advanced AI (planned)

## References

- [Euchre Rules](https://en.wikipedia.org/wiki/Euchre)
- [Official Euchre Tournament Rules](https://www.euchre.com/rules.htm)
