# Bluff Game - New Features Documentation

This document describes the new features added to the Bluff (Cheat) card game.

## Table of Contents

- [Replay System](#replay-system)
- [Variable Deck Types](#variable-deck-types)
- [Tournament Mode](#tournament-mode)
- [Team Play Variant](#team-play-variant)
- [Challenge Reveal Animations](#challenge-reveal-animations)
- [Advanced AI with Pattern Learning](#advanced-ai-with-pattern-learning)

______________________________________________________________________

## Replay System

Record and review your games to analyze strategies and improve your play.

### Features

- **Automatic Recording**: Games are recorded when `--record-replay` flag is used
- **JSON Storage**: Replays saved to `~/.bluff_replays/` in JSON format
- **Complete History**: Records all claims, challenges, and outcomes
- **Playback**: Watch recorded games with `--replay <file>` option

### Usage

```bash
# Record a game
python -m card_games.bluff --record-replay

# Watch a replay
python -m card_games.bluff --replay ~/.bluff_replays/bluff_replay_20231010_123456.json
```

### Replay Data Structure

Each replay includes:

- Game difficulty and configuration
- Random seed (if used) for reproducibility
- All player actions (claims, challenges, passes)
- Final game state and winner

______________________________________________________________________

## Variable Deck Types

Choose from different deck configurations to vary gameplay difficulty and strategy.

### Available Deck Types

| Deck Type | Description | Cards | Best For |
| ----------------- | ------------------------ | ----- | --------------------------- |
| **Standard** | Traditional 52-card deck | 52 | Classic gameplay |
| **FaceCardsOnly** | Only J, Q, K, A | 16 | Fast-paced games |
| **NumbersOnly** | Only 2-10 | 36 | Beginner practice |
| **DoubleDown** | Two copies of each card | 104 | More bluffing opportunities |
| **HighLow** | Only 2-6 and 9-A | 44 | Strategic variety |

### Usage

```bash
# Use Face Cards Only deck
python -m card_games.bluff --deck-type FaceCardsOnly

# Combine with other options
python -m card_games.bluff --deck-type DoubleDown --difficulty Hard --gui
```

### Implementation Details

- Each deck type specifies valid ranks and suits
- Game engine validates claims against the active deck type
- AI bots adapt their strategies to the available ranks

______________________________________________________________________

## Tournament Mode

Compete in an 8-player single-elimination tournament.

### Features

- **8-Player Bracket**: Face 7 opponents in elimination matches
- **Progressive Rounds**: Win to advance (Quarter-finals → Semi-finals → Finals)
- **Match-Based**: Each matchup is a complete game
- **Champion Tracking**: Statistics tracked throughout tournament

### Usage

```bash
# Start a tournament
python -m card_games.bluff --tournament

# Tournament with custom settings
python -m card_games.bluff --tournament --difficulty Hard --rounds 5
```

### Tournament Structure

1. **Round 1**: 8 players → 4 matches → 4 winners
1. **Round 2**: 4 players → 2 matches → 2 winners
1. **Round 3**: 2 players → 1 match → 1 champion

### How It Works

- Players are randomly seeded into bracket positions
- Each match is a complete Bluff game
- Match winner advances, loser is eliminated
- Final standings show all players ranked by wins

______________________________________________________________________

## Team Play Variant

Players are divided into teams that compete for collective victory.

### Features

- **Two Teams**: Team Alpha vs Team Bravo
- **Shared Goal**: Team wins when all members have no cards
- **Team Scoreboard**: Shows combined statistics
- **Strategic Depth**: Coordinate with teammates

### Usage

```bash
# Enable team play
python -m card_games.bluff --team-play

# Team play with custom difficulty
python -m card_games.bluff --team-play --difficulty Medium
```

### Team Mechanics

- Players automatically divided into two teams
- Individual plays still made independently
- Team totals displayed in scoreboard
- Victory requires all team members to empty hands

### Scoreboard Example

```
Team Alpha (Total: 15 cards):
  - You: 8 cards | Truths: 3 | Lies: 2 | Calls: 1/2
  - Bot 1 (Team Alpha): 7 cards | Truths: 2 | Lies: 1 | Calls: 0/1

Team Bravo (Total: 12 cards):
  - Bot 2 (Team Bravo): 6 cards | Truths: 4 | Lies: 0 | Calls: 1/1
  - Bot 3 (Team Bravo): 6 cards | Truths: 1 | Lies: 3 | Calls: 2/3
```

______________________________________________________________________

## Challenge Reveal Animations

Enhanced GUI with visual effects for challenge outcomes.

### Features

- **Fade-In Animation**: Smooth reveal of challenge results
- **Color-Coded**: Green for truth, red for bluff
- **Visual Feedback**: Large text overlay during reveal
- **Timing**: Brief pause to highlight important moments

### Animation States

1. **"REVEALING..."** (Green): Claim was truthful, challenger takes pile
1. **"CAUGHT!"** (Red): Claim was a bluff, claimant caught

### Technical Details

- Implemented using Tkinter's `after()` method
- Non-blocking animation that doesn't interrupt gameplay
- Automatically saves replays when recording is enabled

______________________________________________________________________

## Advanced AI with Pattern Learning

Bots now learn from player behavior to make smarter challenges.

### Learning Mechanisms

#### 1. Bluff Rate Tracking

- **By Pile Size**: Learns how often players bluff at different pile sizes
- **By Card Count**: Tracks bluffing patterns based on hand size
- **Bucketed Data**: Groups similar situations for pattern recognition

#### 2. Behavioral Analysis

- **Recent Behavior**: Remembers last 10 claims (truth vs bluff)
- **Preferred Ranks**: Identifies which ranks player tends to bluff about
- **Moving Averages**: Updates patterns gradually for accuracy

#### 3. Pattern-Based Challenges

High-memory bots (memory > 0.5) use learned patterns:

```python
# Estimated bluff probability influences challenge decision
suspected_bluff_prob = pattern.get_suspected_bluff_probability(
    pile_size, card_count, claimed_rank
)
tendency += (suspected_bluff_prob - 0.5) * bot.profile.memory
```

### Learning in Action

**Scenario**: A player has made 5 claims

- 3 bluffs when pile size was 5-10
- 2 truths when pile size was 0-4
- Preferred bluff rank: Ace

**Result**: When this player claims an Ace with pile size 8:

- AI calculates high bluff probability (~70%)
- High-memory bots more likely to challenge
- Low-memory bots less affected by patterns

### Configuration

Pattern learning is automatic and based on bot profiles:

- **High Memory (0.7-0.95)**: Strong pattern recognition
- **Medium Memory (0.4-0.7)**: Moderate pattern use
- **Low Memory (0.2-0.4)**: Minimal pattern influence

______________________________________________________________________

## Combining Features

All features can be combined for maximum variety:

```bash
# Epic tournament with custom deck and replay
python -m card_games.bluff --tournament --deck-type DoubleDown --record-replay

# Team play with face cards in GUI
python -m card_games.bluff --team-play --deck-type FaceCardsOnly --gui

# Practice against learning AI with recording
python -m card_games.bluff --difficulty Insane --record-replay --seed 42
```

______________________________________________________________________

## Implementation Summary

### Files Modified

- `card_games/bluff/bluff.py`: Core game engine with all new features
- `card_games/bluff/gui.py`: GUI enhancements and animations
- `TODO.md`: Updated with completed features

### Classes Added

- `DeckType`: Defines card deck configurations
- `GameAction`: Records individual game actions
- `GameReplay`: Complete game recording for playback
- `TournamentPlayer`: Player representation in tournaments
- `TournamentRound`: Single round of tournament matches
- `BluffTournament`: Manages tournament structure
- `Team`: Team play functionality
- `PlayerPattern`: AI learning and pattern recognition

### Key Features

- 5 new deck types with varying strategies
- Complete replay system with JSON storage
- 8-player tournament with bracket progression
- Team-based gameplay variant
- Animated challenge reveals in GUI
- Advanced AI that learns player patterns

### Testing

All features have been tested with:

- Unit tests in `tests/test_bluff.py`
- Integration testing via demo script
- Syntax validation and import checks

______________________________________________________________________

## Future Enhancements

Potential additions for future versions:

- Online multiplayer support
- Custom deck designer
- Tournament bracket visualization
- Team communication features
- Machine learning model for advanced AI
- Statistics dashboard
- Achievement system
