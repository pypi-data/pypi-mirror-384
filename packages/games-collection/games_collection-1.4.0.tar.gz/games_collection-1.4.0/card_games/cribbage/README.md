# Cribbage

A classic two-player card game featuring the pegging board, strategic discarding, and complex scoring.

## Game Overview

Cribbage is a strategy card game where players try to be the first to reach 121 points. Points are earned through
combinations of cards played during "The Play" (pegging) phase and scored in "The Show" phase.

## Rules

### Setup

- Standard 52-card deck
- Two players
- Each player starts at 0 points
- Goal: First to 121 points wins

### Gameplay Phases

1. **The Deal**: Each player receives 6 cards

1. **The Discard**: Each player discards 2 cards to the "crib" (dealer's extra hand)

1. **The Cut**: Top card is cut as the "starter"

1. **The Play (Pegging)**:

   - Players alternate playing cards
   - Running count must not exceed 31
   - Score points for:
     - Reaching exactly 15: 2 points
     - Pairs: 2 points (3 of a kind: 6 points, 4 of a kind: 12 points)
     - Runs of 3+: 1 point per card in run
     - Reaching exactly 31: 2 points
     - Last card: 1 point

1. **The Show (Scoring Hands)**:

   - Non-dealer scores their hand first
   - Dealer scores their hand
   - Dealer scores the crib
   - Score combinations for:
     - Fifteens (any cards that sum to 15): 2 points each
     - Pairs: 2 points each
     - Runs of 3+ cards: 1 point per card
     - Flush (4 cards same suit): 4 points (5 with starter: 5 points)
     - Nobs (Jack of same suit as starter): 1 point

### Card Values

- Ace: 1
- 2-10: Face value
- Jack, Queen, King: 10

## Features

- Two-player gameplay
- Pegging phase with running count
- Complex scoring system
- The Show with hand evaluation
- Crib scoring
- First to 121 wins

## Usage

```bash
# Play interactively
python -m card_games.cribbage

# With seed for reproducibility
python -m card_games.cribbage --seed 42
```

## Strategy Tips

1. **Discarding**: Keep cards that work well together (pairs, 15s, runs)
1. **The Play**: Try to avoid giving your opponent easy scoring opportunities
1. **Pegging**: Remember cards played to anticipate runs and pairs
1. **The Crib**: If you're the dealer, discard cards that might score well together

## Scoring Examples

### Fifteens

- 7 + 8 = 15 → 2 points
- 5 + 10 = 15 → 2 points
- 5 + 5 + 5 = 15 → 2 points

### Pairs

- Two 7s → 2 points
- Three 7s → 6 points (three pairs)
- Four 7s → 12 points (six pairs)

### Runs

- 3-4-5 → 3 points
- 4-5-6 → 3 points
- 2-3-4-5 → 4 points

### Complex Hand

Hand: 5-5-6-7-8 with Starter: 4

- Fifteens: 5+6+4=15, 5+6+4=15, 7+8=15 → 6 points
- Pairs: 5-5 → 2 points
- Runs: 4-5-6-7-8 (twice due to pair of 5s) → 10 points
- **Total: 18 points**

## Implementation Notes

This implementation includes:

- ✅ Full game engine with all phases
- ✅ Pegging phase with scoring
- ✅ The Show with complete hand evaluation
- ✅ Crib scoring
- ✅ Interactive CLI
- ⏳ GUI (planned)
- ⏳ AI opponent (planned)

## References

- [Cribbage Rules](https://en.wikipedia.org/wiki/Cribbage)
- [Official American Cribbage Congress Rules](https://www.cribbage.org/)
