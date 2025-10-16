# War Card Game

A simple implementation of the classic card game War.

## Rules

War is a simple card game typically played between two players:

1. The deck is divided equally between two players (26 cards each)
1. Each round, both players reveal their top card simultaneously
1. The player with the higher card wins both cards and adds them to the bottom of their deck
1. If both cards are equal, a "war" occurs:
   - Each player places 3 cards face down
   - Then reveals 1 card face up
   - The higher face-up card wins all cards in play
   - If those cards are also equal, another war occurs
1. The game continues until one player has all the cards

## Card Values

- Ace is highest (value 14)
- King = 13, Queen = 12, Jack = 11
- Number cards have their face value (2-10)

## Running the Game

### Graphical Interface (GUI)

Launch the animated Tkinter GUI:

```bash
python -m card_games.war --gui
```

Features of the GUI:

- Deck counters for each player and the shared pile
- Animated war sequences that stack facedown cards and flash alerts
- Round log with the face-up cards from each battle
- Buttons for **Play Round** and **Start/Stop Auto Play**
- Slider to adjust auto-play speed (150 ms – 2000 ms between rounds)

Auto-play tips:

- Click **Start Auto Play** to schedule rounds. The slider updates instantly, so you can slow down or speed up play
  mid-game.
- The GUI automatically stops when the game ends and offers to save statistics if the optional analytics package is
  available.

Enable experimental sound effects (requires `pygame` for the shared sound manager):

```bash
python -m card_games.war --gui --enable-sounds
```

### Command-Line Interface (CLI)

Play interactively in the terminal:

```bash
python -m card_games.war
```

Auto-play a full game from the CLI:

```bash
python -m card_games.war --auto
```

Use a specific seed for reproducible games:

```bash
python -m card_games.war --seed 42
```

View leaderboard:

```bash
python -m card_games.war --leaderboard
```

View player statistics:

```bash
python -m card_games.war --show-stats --player "Player 1"
```

Disable statistics tracking:

```bash
python -m card_games.war --no-stats
```

## Features

- Full implementation of War rules including recursive wars
- Automatic detection of insufficient cards during war
- Game statistics tracking (rounds played, wars fought)
- **Win/loss statistics** - Tracks player performance across games
- **Leaderboards** - View top players by wins
- Animated Tkinter GUI with auto-play controls and round log
- Interactive CLI with round-by-round play
- Auto-play mode for quick simulation
- Deterministic games with seed support

## Architecture

The implementation follows the repository's architecture patterns:

- `game.py` - Core game engine with no UI dependencies
- `cli.py` - Command-line interface helpers
- `__main__.py` - Entry point with argument parsing

## Future Enhancements

Potential additions:

- Support for more than 2 players
- Statistics tracking across multiple games
- AI strategy analysis (though War is entirely luck-based)
