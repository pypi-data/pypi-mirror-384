# Blackjack - New Features Guide

This document describes the new features added to the Blackjack game.

## Features Overview

### 1. Progressive Side Bets

Two popular casino side bets have been implemented:

#### Perfect Pairs

Pays out when your first two cards form a pair:

- **Perfect Pair** (same rank and suit): 25:1
- **Colored Pair** (same rank, same color): 12:1
- **Mixed Pair** (same rank, different color): 6:1

#### 21+3

Creates a poker hand from your two cards and the dealer's up card:

- **Suited Trips**: 100:1
- **Straight Flush**: 40:1
- **Three of a Kind**: 30:1
- **Straight**: 10:1
- **Flush**: 5:1

**Usage in CLI:**

```bash
python -m card_games.blackjack.cli
# When prompted:
# Place side bets? (p=Perfect Pairs, t=21+3, n=none): pt
# Perfect Pairs bet (max 950): 5
# 21+3 bet (max 945): 10
```

**Usage in Code:**

```python
from card_games.blackjack.game import BlackjackGame, SideBetType

game = BlackjackGame(bankroll=1000, min_bet=10)
side_bets = {
    SideBetType.PERFECT_PAIRS: 5,
    SideBetType.TWENTY_ONE_PLUS_THREE: 10,
}
game.start_round(50, side_bets=side_bets)
```

### 2. Card Counting Hint System

Educational mode enables a Hi-Lo card counting system with helpful hints:

- **Running Count**: Tracks low cards (+1 for 2-6) vs high cards (-1 for T-A)
- **True Count**: Running count divided by decks remaining
- **Strategy Hints**: Basic strategy deviations based on the count
- **Penetration Indicator**: Shows % of shoe dealt

**Usage in CLI:**

```bash
python -m card_games.blackjack.cli --educational
```

**Usage in Code:**

```python
game = BlackjackGame(bankroll=1000, min_bet=10, educational_mode=True)
game.start_round(50)

# Get hint for current hand
hint = game.get_counting_hint(game.player.hands[0])
print(hint)
# Output: "Running Count: 5 | True Count: 1.2 | Count is favorable - consider increasing bet"

# Check penetration
print(f"Penetration: {game.shoe.penetration():.1f}%")
```

### 3. Surrender Option

Players can surrender their hand to get back half their bet:

- Available on initial two-card hands only
- Late surrender (after dealer checks for blackjack)
- Can be disabled via table rules

**Usage in CLI:**

```bash
# When prompted for action:
# Choose action [H/S/D/R]: r  # Press 'r' to surrender
```

**Usage in Code:**

```python
game = BlackjackGame(bankroll=1000, min_bet=10)
game.start_round(100)
hand = game.player.hands[0]

if hand.can_surrender():
    game.surrender(hand)  # Returns $50 to player
```

### 4. Multiplayer Mode

Support for up to 7 players at a single table:

- Each player manages their own bankroll
- Cards dealt in proper casino order
- All players play against the dealer
- Backward compatible with single-player mode

**Usage in Code:**

```python
# Create a 3-player game
game = BlackjackGame(bankroll=1000, min_bet=10, num_players=3)

# All players place bets
bets = {
    game.players[0]: 50,
    game.players[1]: 25,
    game.players[2]: 100,
}
game.start_multiplayer_round(bets)

# Add/remove players dynamically
new_player = game.add_player("Bob", 500)
game.remove_player(new_player)
```

### 5. Shoe Penetration Indicator

Visual indicator showing how far through the shoe you are:

- Displayed as percentage (0-100%)
- Tracks cards dealt since last shuffle
- Useful for card counters
- Shoe reshuffles at ~75% penetration

**Usage:**

```python
game = BlackjackGame(bankroll=1000, min_bet=10, decks=6)
game.start_round(50)

print(f"Penetration: {game.shoe.penetration():.1f}%")
print(f"Cards remaining: {len(game.shoe.cards)}")
```

### 6. Casino Mode with Multiple Table Options

Three predefined table configurations:

#### Standard Table

- Blackjack pays 3:2
- Dealer stands on soft 17
- Surrender allowed
- Double after split allowed
- Up to 3 splits

#### Liberal Table

- Blackjack pays 3:2
- Dealer stands on soft 17
- Surrender allowed
- Double after split allowed
- Resplit aces allowed
- Up to 4 splits

#### Conservative Table (House favorable)

- Blackjack pays 6:5
- Dealer hits soft 17
- Surrender NOT allowed
- Double after split NOT allowed
- Up to 2 splits

**Usage:**

```python
from card_games.blackjack.game import BlackjackGame, TABLE_CONFIGS

# Use a predefined configuration
game = BlackjackGame(
    bankroll=1000,
    min_bet=10,
    table_rules=TABLE_CONFIGS["Liberal"]
)

# Or create custom rules
from card_games.blackjack.game import TableRules

custom_rules = TableRules(
    blackjack_payout=1.5,
    dealer_hits_soft_17=False,
    surrender_allowed=True,
    max_splits=2,
)
game = BlackjackGame(bankroll=1000, min_bet=10, table_rules=custom_rules)
```

## Complete Example

```python
from card_games.blackjack.game import (
    BlackjackGame,
    SideBetType,
    TABLE_CONFIGS,
)

# Create a multiplayer game with educational mode
game = BlackjackGame(
    bankroll=1000,
    min_bet=10,
    max_bet=500,
    decks=6,
    num_players=2,
    educational_mode=True,
    table_rules=TABLE_CONFIGS["Liberal"]
)

# Start a round with side bets
bets = {game.players[0]: 100, game.players[1]: 50}
side_bets = {
    game.players[0]: {
        SideBetType.PERFECT_PAIRS: 10,
        SideBetType.TWENTY_ONE_PLUS_THREE: 10,
    }
}
game.start_multiplayer_round(bets, side_bets)

# Check card counting info
print(f"Running count: {game.shoe.running_count}")
print(f"True count: {game.shoe.true_count():.2f}")
print(f"Penetration: {game.shoe.penetration():.1f}%")

# Get hint
hint = game.get_counting_hint(game.players[0].hands[0])
print(f"Hint: {hint}")

# Play hands
for player in game.players:
    for hand in player.hands:
        if hand.can_surrender():
            # Surrender bad hands
            if hand.best_total() <= 15:
                game.surrender(hand, player)
        else:
            # Stand on 17+
            if hand.best_total() >= 17:
                game.stand(hand)

# Dealer plays and resolve
game.dealer_play()
results = game.settle_round()

for player, outcomes in results.items():
    print(f"{player.name}: {outcomes}")
```

## CLI Usage

The command-line interface has been updated to support all new features:

```bash
# Basic game
python -m card_games.blackjack.cli

# Educational mode with card counting
python -m card_games.blackjack.cli --educational

# Custom settings
python -m card_games.blackjack.cli --bankroll 2000 --min-bet 25 --decks 8

# See all options
python -m card_games.blackjack.cli --help
```

## Testing

Comprehensive tests are included in `tests/test_blackjack.py`:

```bash
# Run tests (if pytest is installed)
pytest tests/test_blackjack.py -v

# Or run directly with Python
python -m tests.test_blackjack
```

## Notes

- All features maintain backward compatibility with existing code
- Side bets are resolved immediately after the deal
- Card counting is for educational purposes only
- Multiplayer mode uses separate bankrolls for each player
- Table rules affect gameplay (e.g., surrender may not be allowed)
- The shoe automatically reshuffles when penetration reaches ~75%
