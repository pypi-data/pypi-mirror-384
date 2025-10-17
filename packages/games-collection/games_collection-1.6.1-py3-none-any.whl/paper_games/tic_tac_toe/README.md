# Tic-Tac-Toe

A feature-rich and well-documented implementation of Tic-Tac-Toe, offering multiple game modes, extensive customization, and a challenging AI opponent. This project serves as a comprehensive example of game development in Python, with clear, commented code and a modular structure.

## Features

### Multiple Board Sizes
Play on different board sizes with customizable win conditions, providing variety beyond the classic game:
- **3x3** (Classic)
- **4x4**
- **5x5**
- **Configurable Win Length**: Adjust the number of symbols in a row required to win (from 3 up to the board size).

### Game Modes

#### Classic Mode
Challenge an optimal minimax-based AI opponent that is designed to never lose. The AI's difficulty adapts to the board size, providing a consistent challenge.
```bash
python -m paper_games.tic_tac_toe
```

#### Ultimate Tic-Tac-Toe
Experience an advanced "meta-board" variant where the game is played across a 3x3 grid of smaller boards. Winning a small board claims that cell on the larger meta-board, adding a new layer of strategy.
```bash
python -m paper_games.tic_tac_toe --ultimate
# or
python -m paper_games.tic_tac_toe -u
```

#### Network Multiplayer
Play against another human over a local network. Host a game and have a friend connect to your machine for a head-to-head match.
```bash
# Host a game (Server)
python -m paper_games.tic_tac_toe --network
# Choose option 1 to host

# Join a game (Client)
python -m paper_games.tic_tac_toe --network
# Choose option 2 to join
```

### Themed Boards
Customize your game with a wide variety of themed symbol sets, including:
- **Classic**: X and O
- **Hearts**: ♥ and ♡
- **Stars**: ★ and ☆
- **Chess**: ♔ and ♚
- **Emojis**: 😀 and 😎
- **Holiday**: 🎄 and 🎁
- And many more, including animals, food, and abstract symbols!

### Game Statistics
Your performance is automatically tracked across all game modes, providing insights into your play style:
- **Overall Stats**: Total wins, losses, and draws.
- **Win Rate**: A percentage-based calculation of your success.
- **Stats by Board Size**: A detailed breakdown of your performance on different board sizes.
- **Persistent Storage**: All statistics are saved to `~/.games/tic_tac_toe_stats.json`.

### Undo Functionality
Made a mistake? The classic game mode includes an "undo" feature that lets you take back your last move, giving you a chance to rethink your strategy.

## Usage Examples

### Standard 3x3 Game
To start a standard game, run the following command and follow the on-screen prompts:
```bash
python -m paper_games.tic_tac_toe
```
You will be prompted to:
1. View your statistics.
2. Choose the board size (default: 3).
3. Choose the win length (default: same as board size).
4. Select your symbol (X or O) or choose a theme.
5. Decide who goes first.

### 4x4 Board with Custom Win Length
For a different challenge, you can play on a larger board with a shorter win condition:
- At the prompts, set **Board size** to `4` and **Win length** to `3`.

### Using Themed Boards
To play with a themed board:
- When asked "Use a themed board?", enter `y` to see the list of available themes.
- Choose a theme, such as `emoji`, to play with 😀 vs. 😎.

### Playing Ultimate Tic-Tac-Toe
To play the ultimate variant, use the `--ultimate` flag:
```bash
python -m paper_games.tic_tac_toe --ultimate
```
In this mode:
- The game is played on a 3x3 grid of smaller tic-tac-toe boards.
- Your move on a small board determines which board your opponent must play on next.
- To win, you must get three in a row on the main "meta-board."

### Network Multiplayer Setup
**Server (Host):**
```bash
python -m paper_games.tic_tac_toe --network
# 1. Choose option 1 to "Host a game".
# 2. Set the port (default: 5555).
# 3. Set the board size (default: 3).
```

**Client (Join):**
```bash
python -m paper_games.tic_tac_toe --network
# 1. Choose option 2 to "Join a game".
# 2. Enter the server's address (default: localhost).
# 3. Enter the server's port (default: 5555).
```

## Board Coordinates
The game uses a standard letter-number coordinate system for moves:
- **Rows** are labeled with letters (A, B, C, ...).
- **Columns** are labeled with numbers (1, 2, 3, ...).
- **Example Moves**: `A1` for the top-left, `B2` for the center, etc.

## Algorithm Details

### Minimax AI
The AI for the classic game mode is powered by the minimax algorithm, with optimizations for different board sizes:
- **3x3 boards**: A complete game tree search ensures perfect play.
- **4x4 boards**: A depth-limited search (up to depth 6) provides a strong opponent.
- **5x5 boards**: A depth-limited search (up to depth 4) balances performance and difficulty.

### Ultimate Tic-Tac-Toe AI
The AI for the ultimate variant uses a heuristic-based strategy that prioritizes:
1. Taking the center cell of the center board.
2. Taking the center cell of any available board.
3. Making strategic moves based on board availability.

## Module Structure
The codebase is organized into a set of focused, well-documented modules:
- `tic_tac_toe.py`: Core game logic, state management, and the minimax AI.
- `cli.py`: The command-line interface for the classic game mode.
- `ultimate.py`: The implementation of the Ultimate Tic-Tac-Toe game rules.
- `ultimate_cli.py`: The CLI for the Ultimate Tic-Tac-Toe variant.
- `network.py`: Server and client classes for network multiplayer.
- `network_cli.py`: The CLI for setting up and playing network games.
- `stats.py`: Game statistics tracking and persistence.
- `themes.py`: Themed symbol sets and management.

## Statistics File
Game statistics are automatically saved to `~/.games/tic_tac_toe_stats.json`. You can view your stats at the start of each game or inspect this file directly.

## Testing
The project includes a comprehensive test suite to ensure correctness and stability. To run the tests, execute the following command:
```bash
python tests/test_tic_tac_toe.py
```
The test suite covers:
- Board size and win condition variations.
- Coordinate parsing and move validation.
- Statistics tracking and calculation.
- Theme functionality.
- Ultimate Tic-Tac-Toe and network game logic.

## Requirements
- **Python 3.7+**
- No external dependencies are required for the core functionality.
- Network play uses the standard library `socket` module.
