# Rummy 500

A variant of rummy featuring melding, laying off, and scoring that includes negative points for cards left in hand.

## Game Overview

Rummy 500 is a card game where players try to form melds (sets and runs) and be the first to reach 500 points.

## Rules

### Setup

- Standard 52-card deck
- 2-4 players
- 7 cards dealt to each player
- First player to 500 points wins

### Gameplay

1. **Draw**: Take a card from deck or discard pile
1. **Meld**: Lay down sets (3+ same rank) or runs (3+ consecutive same suit)
1. **Lay Off**: Add cards to existing melds
1. **Discard**: Discard one card to end turn

### Scoring

**Melds** (positive points):

- Ace: 15 points
- Face cards (J, Q, K): 10 points each
- Number cards: Face value

**Cards in Hand** (negative points):

- Same values as above, but subtracted from score

### Winning

- First player to reach 500 points wins
- Round ends when a player goes out (empties hand)

### Special Rules

- Can take multiple cards from discard pile
- All discarded cards are visible
- Must meld immediately if taking from discard

## Features

- 2-4 player support
- Meld validation (sets and runs)
- Visible discard pile
- Score tracking
- First to 500 wins

## Usage

```bash
# Play with 2 players
python -m card_games.rummy500

# With 3 players
python -m card_games.rummy500 --players 3

# With seed for reproducibility
python -m card_games.rummy500 --seed 42
```

## Strategy Tips

1. **Melding**: Form melds early to reduce hand penalty
1. **Discard Pile**: Watch what others take
1. **Card Values**: Keep low-value cards if can't meld
1. **Going Out**: Time your going out to maximize points

## Examples

### Valid Melds

**Sets** (same rank):

- 7♣ 7♦ 7♥
- K♠ K♣ K♥ K♦

**Runs** (consecutive, same suit):

- 3♠ 4♠ 5♠
- 9♥ T♥ J♥ Q♥

### Scoring Example

**Player goes out with:**

- Meld 1: 7-7-7 = 21 points
- Meld 2: 3♠-4♠-5♠ = 12 points
- Total: 33 points

**Opponent has in hand:**

- K♥ Q♦ 5♣ = -25 points
- Current score: 100
- New score: 75

## Implementation Notes

This implementation includes:

- ✅ Full game engine
- ✅ Meld validation
- ✅ Score tracking
- ✅ Interactive CLI
- ⏳ Lay off mechanics (simplified)
- ⏳ GUI (planned)
- ⏳ Advanced AI (planned)

## References

- [Rummy 500 Rules](https://en.wikipedia.org/wiki/500_rum)
- [Official Card Game Rules](https://www.pagat.com/rummy/500rum.html)
