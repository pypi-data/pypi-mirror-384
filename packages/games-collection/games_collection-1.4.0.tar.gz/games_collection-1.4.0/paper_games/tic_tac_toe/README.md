# Tic-Tac-Toe

A feature-rich implementation of Tic-Tac-Toe with multiple game modes and variants.

## Features

### Multiple Board Sizes

Play on different board sizes with customizable win conditions:

- **3x3** (classic)
- **4x4**
- **5x5**
- Configurable win length (3 to board size)

### Game Modes

#### Classic Mode

Play against an optimal minimax-based AI opponent that never loses.

```bash
python -m paper_games.tic_tac_toe
```

#### Ultimate Tic-Tac-Toe

Play the advanced meta-board variant where you must win small boards to claim cells on a larger board.

```bash
python -m paper_games.tic_tac_toe --ultimate
# or
python -m paper_games.tic_tac_toe -u
```

#### Network Multiplayer

Play against another human player over the network.

```bash
# Host a game (server)
python -m paper_games.tic_tac_toe --network
# Choose option 1

# Join a game (client)
python -m paper_games.tic_tac_toe --network
# Choose option 2
```

### Themed Boards

Choose from various themed symbol sets:

- Classic (X and O)
- Hearts (♥ and ♡)
- Stars (★ and ☆)
- Circles (● and ○)
- Squares (■ and □)
- Chess pieces (♔ and ♚)
- Emojis (😀 and 😎)
- Holiday themes (🎄 and 🎁)
- Halloween (🎃 and 👻)
- Animals (🐱 and 🐶)
- Numbers, arrows, music notes, weather, food, and more!

### Game Statistics

Automatically tracks your performance across games:

- Total wins, losses, and draws
- Win rate calculation
- Statistics by board size
- Persistent storage (saved to `~/.games/tic_tac_toe_stats.json`)

## Usage Examples

### Standard 3x3 Game

```bash
python -m paper_games.tic_tac_toe
```

Follow the prompts to:

1. View your statistics (if available)
1. Choose board size (default: 3)
1. Choose win length (default: same as board size)
1. Choose your symbol (X or O)
1. Choose who goes first

### 4x4 Board with Custom Win Length

When prompted during game setup:

- Board size: `4`
- Win length: `3` (get 3 in a row to win on a 4x4 board)

### Using Themed Boards

When asked "Use a themed board?", enter `y` to see all available themes. Choose a theme like `emoji` to play with 😀 vs
😎.

### Playing Ultimate Tic-Tac-Toe

```bash
python -m paper_games.tic_tac_toe --ultimate
```

In Ultimate Tic-Tac-Toe:

- The board consists of 9 small tic-tac-toe boards arranged in a 3x3 grid
- Win small boards to claim cells on the meta-board
- Your move determines which board your opponent must play on next
- Get 3 in a row on the meta-board to win!

### Network Multiplayer

**Server (Host):**

```bash
python -m paper_games.tic_tac_toe --network
# Choose option 1: Host a game
# Choose port (default: 5555)
# Choose board size (default: 3)
```

**Client (Join):**

```bash
python -m paper_games.tic_tac_toe --network
# Choose option 2: Join a game
# Enter server address (default: localhost)
# Enter port (default: 5555)
```

## Board Coordinates

Boards use letter-number coordinates:

- Rows are labeled with letters (A, B, C, ...)
- Columns are labeled with numbers (1, 2, 3, ...)
- Example moves: `A1` (top-left), `B2` (center), `C3` (bottom-right)

For larger boards (4x4, 5x5), the coordinate system extends accordingly:

- 4x4: A1-D4
- 5x5: A1-E5

## Algorithm Details

### Minimax AI

The classic game mode uses the minimax algorithm with alpha-beta pruning concepts:

- For 3x3 boards: Complete game tree exploration (perfect play)
- For 4x4 boards: Depth-limited search (depth 6)
- For 5x5 boards: Depth-limited search (depth 4)

### Ultimate Tic-Tac-Toe AI

The ultimate variant uses a simplified strategy:

1. Prefer center positions
1. Prioritize the center board
1. Make strategic moves based on board availability

## Module Structure

- `tic_tac_toe.py` - Core game logic and AI
- `cli.py` - Command-line interface for classic mode
- `ultimate.py` - Ultimate Tic-Tac-Toe implementation
- `ultimate_cli.py` - CLI for ultimate variant
- `network.py` - Network multiplayer support
- `network_cli.py` - CLI for network play
- `stats.py` - Game statistics tracking
- `themes.py` - Themed symbol sets

## Statistics File

Game statistics are saved to: `~/.games/tic_tac_toe_stats.json`

You can view your stats at the start of each game or by checking this file directly.

## Testing

Run the test suite:

```bash
python tests/test_tic_tac_toe.py
```

The test suite covers:

- Board size variations
- Win condition detection
- Coordinate parsing
- Statistics tracking
- Theme functionality
- Ultimate Tic-Tac-Toe logic
- Network configuration

## Requirements

- Python 3.7+
- No external dependencies for core functionality
- Network play requires standard library `socket` module
