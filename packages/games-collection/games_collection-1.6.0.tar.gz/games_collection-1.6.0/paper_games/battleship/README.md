# Battleship Game

A feature-rich implementation of the classic Battleship game with multiple gameplay modes and configurations.

## Features

### Grid Size Options

Play on different board sizes:

- **8x8**: Faster games, ideal for quick matches
- **10x10**: Classic Battleship size

```bash
python -m paper_games.battleship --size 8
python -m paper_games.battleship --size 10
```

### Fleet Configurations

Choose from three fleet types:

#### Small Fleet (4 ships)

Perfect for 8x8 boards:

- Battleship (4 cells)
- Cruiser (3 cells)
- Submarine (3 cells)
- Destroyer (2 cells)

#### Default Fleet (5 ships)

Classic Battleship configuration:

- Carrier (5 cells)
- Battleship (4 cells)
- Cruiser (3 cells)
- Submarine (3 cells)
- Destroyer (2 cells)

#### Extended Fleet (7 ships)

More challenging with additional ships:

- Carrier (5 cells)
- Battleship (4 cells)
- Cruiser (3 cells)
- Submarine (3 cells)
- Destroyer (2 cells)
- Patrol Boat (2 cells)
- Frigate (3 cells)

```bash
python -m paper_games.battleship --fleet small
python -m paper_games.battleship --fleet default
python -m paper_games.battleship --fleet extended
```

### AI Difficulty Levels

Three difficulty levels with distinct strategies:

- **Easy**: AI shoots randomly without strategy
- **Medium**: AI uses hunting strategy 70% of the time
- **Hard**: AI always uses optimal hunting strategy (targets adjacent cells after hits)

```bash
python -m paper_games.battleship --difficulty easy
python -m paper_games.battleship --difficulty medium
python -m paper_games.battleship --difficulty hard
```

### 2-Player Hot-Seat Mode

Play against a friend on the same computer:

- Each player sets up their own fleet
- Turn-based gameplay with screen hiding
- No AI opponent

```bash
python -m paper_games.battleship --two-player
```

### Salvo Mode

A strategic variant where you get multiple shots per turn:

- Number of shots equals your number of unsunk ships
- As your ships sink, you get fewer shots
- Adds strategic depth to gameplay

```bash
python -m paper_games.battleship --salvo
```

### Reproducible Games

Set a random seed for reproducible ship placement and AI behavior:

```bash
python -m paper_games.battleship --seed 12345
```

## Usage Examples

### Quick 8x8 Game

```bash
python -m paper_games.battleship --size 8 --fleet small --difficulty easy
```

### Challenging Solo Game

```bash
python -m paper_games.battleship --difficulty hard --salvo
```

### 2-Player Match with Salvo

```bash
python -m paper_games.battleship --two-player --salvo
```

### Extended Fleet on Large Board

```bash
python -m paper_games.battleship --size 10 --fleet extended --difficulty hard
```

## Command-Line Options

```
usage: python -m paper_games.battleship [-h] [--size {8,10}]
                                        [--fleet {small,default,extended}]
                                        [--difficulty {easy,medium,hard}]
                                        [--two-player] [--salvo] [--seed SEED]

Play Battleship with configurable options

options:
  -h, --help            show this help message and exit
  --size {8,10}         Board size (8x8 or 10x10)
  --fleet {small,default,extended}
                        Fleet configuration
  --difficulty {easy,medium,hard}
                        AI difficulty level
  --two-player          Enable 2-player hot-seat mode (no AI)
  --salvo               Enable salvo mode (shots per turn = unsunk ships)
  --seed SEED           Random seed for reproducible games
```

## Gameplay

### Ship Placement

- Choose manual placement to position each ship
- Or use automatic random placement for quick setup

### Shooting

- Enter coordinates as "row col" (e.g., "3 5")
- In salvo mode, you'll make multiple shots per turn

### Winning

- Sink all opponent ships to win
- In salvo mode, protect your ships to maintain firepower

## API Usage

```python
from paper_games.battleship import (
    BattleshipGame,
    DEFAULT_FLEET,
    EXTENDED_FLEET,
    SMALL_FLEET,
)

# Create a game with custom configuration
game = BattleshipGame(
    size=10,
    fleet=EXTENDED_FLEET,
    difficulty="hard",
    salvo_mode=True,
)

# Setup ships
game.setup_random()

# Make moves
result, ship_name = game.player_shoot((3, 5))
coord, result, ship_name = game.ai_shoot()

# Check win conditions
if game.opponent_has_lost():
    print("You win!")
```

## Testing

Run the test suite:

```bash
python tests/test_battleship.py
```

All tests validate:

- Board size configurations
- Fleet variations
- AI difficulty behaviors
- Game mode flags
- Salvo shot counting

## GUI Mode

The game includes a graphical user interface with interactive ship placement.

### Features

#### Ship Placement Phase

- **Interactive placement**: Click on the board to place ships
- **Orientation toggle**: Switch between horizontal and vertical with a button
- **Visual preview**: Green highlight shows valid placement before clicking
- **Random placement**: "Place Randomly" button for quick setup
- **Real-time validation**: Invalid placements won't show a preview

#### Gameplay Phase

- **Dual board view**: Your fleet (left) and enemy waters (right)
- **Visual feedback**:
  - Gray squares show your ships
  - Blue circles (○) indicate misses
  - Red X marks (✗) indicate hits
- **Status updates**: Clear messages about whose turn and shot results
- **All game modes supported**: Board sizes, fleets, AI difficulties, 2-player, salvo mode

### Usage

Run the GUI with default settings (10x10 board, default fleet, medium AI):

```bash
python -m paper_games.battleship.gui
```

Or with custom options:

```bash
python -m paper_games.battleship.gui --size 8 --fleet small --difficulty hard --salvo
```

### From Python Code

```python
from paper_games.battleship import run_gui

# Run with default settings
run_gui()

# Run with custom settings
run_gui(size=8, fleet="small", difficulty="hard", salvo=True)
```

### Screenshots

The GUI provides an intuitive visual interface with two main screens:

1. **Ship Placement**: Interactive board with ship placement controls (see `../../docs/images/battleship_gui_setup.png`)
1. **Active Gameplay**: Dual-board view showing your fleet and enemy waters (see `../../docs/images/battleship_gui_game.png`)
