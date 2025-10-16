# Dots and Boxes

A feature-rich implementation of the classic Dots and Boxes game with AI opponent, GUI, tournament mode, and multiplayer
support.

## Features

- **Multiple Board Sizes**: Play on 2x2, 3x3, 4x4, 5x5, or 6x6 boards
- **Chain-Aware AI**: Computer opponent that understands chain strategies
- **Graphical Interface**: Interactive GUI with visual feedback (requires tkinter)
- **Chain Highlighting**: See chain information when hovering over edges in GUI
- **Move Hints**: Get suggestions for good moves (learning mode)
- **Tournament Mode**: Play multiple games and track statistics
- **Network Multiplayer**: Play against friends over the network

## Usage

### Command Line Interface (CLI)

Play a standard game with default 2x2 board:

```bash
python -m paper_games.dots_and_boxes
```

Play with a larger board (3x3, 4x4, 5x5, or 6x6):

```bash
python -m paper_games.dots_and_boxes --size 4
```

### Graphical Interface (GUI)

Launch the GUI (requires tkinter):

```bash
python -m paper_games.dots_and_boxes --gui --size 3
```

Enable move hints in GUI:

```bash
python -m paper_games.dots_and_boxes --gui --hints
```

### Tournament Mode

Play a tournament of 5 games:

```bash
python -m paper_games.dots_and_boxes --tournament 5 --size 3
```

The tournament tracks:

- Total games played
- Win/loss/tie statistics
- Total scores
- Win percentage
- Average score difference

### Network Multiplayer

Host a multiplayer game:

```bash
python -m paper_games.dots_and_boxes --host --size 3 --name "Alice"
```

Join a multiplayer game:

```bash
python -m paper_games.dots_and_boxes --join localhost --name "Bob"
```

Join a game on a different computer:

```bash
python -m paper_games.dots_and_boxes --join 192.168.1.100 --port 5555 --name "Bob"
```

## Game Rules

Dots and Boxes is played on a grid of dots. Players take turns drawing horizontal or vertical lines between adjacent
dots. When a player completes the fourth side of a box, they claim it and get another turn. The game ends when all boxes
are claimed, and the player with the most boxes wins.

## Strategy Tips

The GUI provides real-time feedback:

- ✅ **Safe move**: Doesn't create a chain opportunity for opponent
- ⚠️ **Warning**: Creates a chain - opponent could capture multiple boxes
- ⭐ **Scoring move**: Completes a box!

### Chain Strategy

A "chain" is created when you give your opponent the opportunity to claim multiple boxes in sequence. The AI is aware of
chains and tries to minimize them. You should too!

## Programming Interface

You can also use the game programmatically:

```python
from paper_games.dots_and_boxes import DotsAndBoxes, play, run_gui, play_tournament

# Create a game
game = DotsAndBoxes(size=3)

# Play in CLI
play(size=4)

# Play in GUI (requires tkinter)
run_gui(size=3, show_hints=True)

# Run a tournament
play_tournament(size=3, num_games=5)

# Host/join multiplayer
from paper_games.dots_and_boxes import host_game, join_game
host_game(size=3, port=5555, player_name="Alice")
join_game(host="localhost", port=5555, player_name="Bob")
```

## Requirements

- Python 3.8+
- tkinter (optional, for GUI - usually included with Python)
- No external dependencies for CLI mode

## Implementation Details

### AI Strategy

- Uses chain analysis to make strategic decisions
- Chain length calculation simulates opponent's optimal play
- Prioritizes safe moves and avoids creating chains for the opponent
- Supports multiple difficulty levels through chain-awareness tuning

### GUI Features

- Real-time chain analysis when hovering over edges
- Visual feedback system:
  - ✅ **Safe move**: No chain created
  - ⚠️ **Warning**: Creates a chain (shows box count)
  - ⭐ **Scoring move**: Completes a box
- Color-coded edge highlighting
- Interactive learning tool for strategy improvement

### Network Protocol

- TCP socket-based communication using JSON protocol
- Host/client architecture for peer-to-peer play
- Real-time move synchronization
- Connection error handling and recovery
- Works over local network or internet

### Tournament System

- Supports both interactive and automated play
- Tracks comprehensive statistics across multiple games
- Records win/loss ratios and score differences
- Suitable for AI evaluation and player skill assessment

### Supported Board Sizes

Board dimensions scale correctly for all sizes:

- 2x2: 4 boxes, 12 edges
- 3x3: 9 boxes, 24 edges
- 4x4: 16 boxes, 40 edges
- 5x5: 25 boxes, 60 edges
- 6x6: 36 boxes, 84 edges
