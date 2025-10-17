# Battleship

A feature-rich and well-documented implementation of the classic Battleship game, offering multiple gameplay modes, a challenging AI, and two distinct graphical user interfaces (Tkinter and PyQt5).

## Features

### Grid Size Options
Choose between two standard board sizes for different game dynamics:
- **8x8**: Ideal for faster games and quick matches.
- **10x10**: The classic, traditional Battleship experience.

**Usage:**
```bash
# For a 10x10 game (default)
python -m paper_games.battleship

# For an 8x8 game
python -m paper_games.battleship --size 8
```

### Fleet Configurations
Select from three different fleet compositions to vary the challenge:
- **Small Fleet (4 ships)**: Perfect for 8x8 boards.
- **Default Fleet (5 ships)**: The standard Battleship configuration.
- **Extended Fleet (7 ships)**: A more complex game with additional ships.

**Usage:**
```bash
python -m paper_games.battleship --fleet small
```

### AI Difficulty Levels
Face off against an AI with three distinct difficulty levels:
- **Easy**: The AI shoots randomly, offering a more predictable opponent.
- **Medium**: The AI uses its "hunt and target" strategy 70% of the time.
- **Hard**: The AI always uses its optimal hunting strategy, making for a challenging opponent.

**Usage:**
```bash
python -m paper_games.battleship --difficulty hard
```

### 2-Player Hot-Seat Mode
Play against a friend on the same computer in a turn-based "hot-seat" mode. The game prompts players to look away during their opponent's turn to keep ship placements secret.

**Usage:**
```bash
python -m paper_games.battleship --two-player
```

### Salvo Mode
Enable a strategic variant where the number of shots per turn is equal to your number of unsunk ships. As you lose ships, your firepower decreases, adding a new layer of strategy.

**Usage:**
```bash
python -m paper_games.battleship --salvo
```

### Reproducible Games
Use a random seed to ensure reproducible ship placements and AI behavior, perfect for testing strategies or replaying interesting scenarios.

**Usage:**
```bash
python -m paper_games.battleship --seed 12345
```

## Graphical User Interfaces (GUIs)
This project includes two separate, fully-featured GUIs built with different frameworks: **Tkinter** and **PyQt5**. Both provide an intuitive, visual way to play the game.

### GUI Features
- **Interactive Ship Placement**: Visually place your ships with a real-time preview.
- **Orientation Toggle**: Easily switch between horizontal and vertical placement.
- **Random Placement**: Automatically place your ships for a quick start.
- **Dual Board View**: See your fleet and your shots on the enemy's board side-by-side.
- **Clear Visual Feedback**: Instantly see hits, misses, and sunk ships.
- **Full Game Mode Support**: All command-line options (size, fleet, difficulty, etc.) are supported.

### Running the GUIs

**Tkinter GUI (Default):**
```bash
# Run with default settings
python -m paper_games.battleship.gui

# Run with custom options
python -m paper_games.battleship.gui --size 8 --fleet small --salvo
```

**PyQt5 GUI:**
```bash
# Run with default settings
python -m paper_games.battleship.gui_pyqt

# Run with custom options
python -m paper_games.battleship.gui_pyqt --size 8 --fleet small --salvo
```

## Command-Line Options
All game options can be configured via the command line:
```
usage: python -m paper_games.battleship [-h] [--size {8,10}]
                                        [--fleet {small,default,extended}]
                                        [--difficulty {easy,medium,hard}]
                                        [--two-player] [--salvo] [--seed SEED]

options:
  -h, --help            show this help message and exit
  --size {8,10}         The size of the game board (8 for 8x8, 10 for 10x10).
  --fleet {small,default,extended}
                        The fleet configuration to use.
  --difficulty {easy,medium,hard}
                        The AI difficulty level.
  --two-player          Enable two-player hot-seat mode.
  --salvo               Enable salvo mode.
  --seed SEED           A random seed for reproducible games.
```

## Module Structure
The codebase is organized into a set of focused, well-documented modules:
- `battleship.py`: The core game engine, including game state, ship placement, and AI logic.
- `cli.py`: The command-line interface for playing the game in a terminal.
- `gui.py`: The Tkinter-based graphical user interface.
- `gui_pyqt.py`: The PyQt5-based graphical user interface.
