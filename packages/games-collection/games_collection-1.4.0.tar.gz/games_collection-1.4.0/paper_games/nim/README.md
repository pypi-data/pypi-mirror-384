# Nim and Variants

A comprehensive implementation of the classic game of Nim and its mathematical variants, featuring educational tools,
multiplayer support, and advanced visualizations.

## Quick Start

```bash
python -m paper_games.nim
```

## Features

### Classic Nim

Play the mathematical game of Nim with an optimal computer opponent. The game includes:

- **Graphical Heap Representation**: Visualize heaps as vertical stacks of blocks
- **Educational Mode**: Get strategy hints and explanations of optimal moves
- **Multiplayer Support**: Play with 3-6 players (human and computer)
- **Custom Rules**: Configure game variations like max-take limits
- **Misère Mode**: Reverse the winning condition (last player loses)

### Game Variants

#### Northcott's Game

A spatial variant where players slide pieces towards each other on parallel rows. The gaps between pieces form Nim
heaps, combining positional play with Nim strategy.

**Features:**

- Configurable board size and number of rows
- Visual board representation
- Optimal computer opponent using Nim-sum analysis

#### Wythoff's Game

A two-heap variant where players can either:

- Remove any number from one heap (standard Nim move)
- Remove the same number from both heaps (diagonal move)

**Features:**

- Based on the golden ratio and Beatty sequences
- "Cold position" analysis (losing positions)
- Optimal strategy using Wythoff pairs

## Usage Examples

### Playing with Graphical Display

```python
from paper_games.nim import NimGame

# Create a game
game = NimGame([4, 6, 8])

# Display with graphical rendering
print(game.render(graphical=True))
```

Output:

```
                ▓▓▓
                ▓▓▓
         ▓▓▓    ▓▓▓
         ▓▓▓    ▓▓▓
  ▓▓▓    ▓▓▓    ▓▓▓
  ▓▓▓    ▓▓▓    ▓▓▓
  ▓▓▓    ▓▓▓    ▓▓▓
  ▓▓▓    ▓▓▓    ▓▓▓
 [  4]  [  6]  [  8]
 Heap1 Heap2 Heap3
```

### Getting Strategy Hints

```python
# Get educational hints about the current position
hint = game.get_strategy_hint()
print(hint)
```

Output shows:

- Binary representation of heaps
- Nim-sum calculation
- Position analysis (winning/losing)
- Suggested winning moves

### Computer Move with Explanation

```python
# Get move with educational explanation
heap_idx, count, explanation = game.computer_move(explain=True)
print(f"Computer removed {count} from heap {heap_idx + 1}")
print(f"Strategy: {explanation}")
```

### Multiplayer Game

```python
# Create a 4-player game
game = NimGame([10, 12, 15], num_players=4)

# Players take turns
game.player_move(0, 3)  # Player 1
print(f"Current player: {game.current_player}")  # Now player 2
```

### Custom Rules

```python
# Limit maximum objects per turn
game = NimGame([10, 15, 20], max_take=5)

# This will raise ValueError
try:
    game.player_move(0, 6)  # Can't take more than 5
except ValueError as e:
    print(e)  # "Cannot take more than 5 objects per turn."
```

### Northcott's Game

```python
from paper_games.nim import NorthcottGame

# Create game with default random setup
game = NorthcottGame()
print(game.render())

# Move white piece in row 1 to position 3
game.make_move(0, 'white', 3)

# Computer makes optimal move
row, piece, pos = game.computer_move()
print(f"Computer moved {piece} in row {row + 1} to position {pos}")
```

### Wythoff's Game

```python
from paper_games.nim import WythoffGame

# Create game with custom heap sizes
game = WythoffGame(heap1=5, heap2=8)
print(game.render())

# Remove 2 from heap 1
game.make_move(2, 0)

# Diagonal move: remove 3 from both
game.make_move(3, 3)

# Computer move
h1, h2 = game.computer_move()
```

## Game Theory Background

### Classic Nim

Nim is a solved game using the **Nim-sum** (XOR of all heap sizes):

- If Nim-sum = 0: current player is in a **losing position**
- If Nim-sum ≠ 0: current player can force a win

The optimal strategy is to make moves that result in a Nim-sum of 0.

### Misère Nim

In misère rules, the player who takes the last object **loses**. The strategy is similar to normal Nim, except when all
remaining heaps have size 1.

### Northcott's Game

This is equivalent to Nim where the "heap" is the gap between pieces. The game demonstrates that many spatial games can
be analyzed using Nim theory.

### Wythoff's Game

Uses the **golden ratio** (φ ≈ 1.618) to define losing positions. The losing positions form pairs:

- (0, 0), (1, 2), (3, 5), (4, 7), (6, 10), ...
- These follow the Beatty sequences: aₖ = ⌊k·φ⌋ and bₖ = ⌊k·φ²⌋

## CLI Features

When you run `python -m paper_games.nim`, you can:

1. **Choose a game variant**: Classic Nim, Northcott, or Wythoff
1. **Configure rules**: Misère mode, max-take limits, heap sizes
1. **Enable features**:
   - Graphical heap display
   - Educational mode with strategy hints
   - Multiplayer mode (3-6 players)
1. **Learn as you play**: Request hints and explanations at any time

## API Reference

### NimGame

```python
class NimGame:
    def __init__(
        self,
        heaps: List[int] = [3, 4, 5],
        misere: bool = False,
        num_players: int = 2,
        max_take: int | None = None,
    )
```

**Methods:**

- `render(graphical: bool = False) -> str`: Display game state
- `get_strategy_hint() -> str`: Get educational analysis
- `computer_move(explain: bool = False)`: AI move with optional explanation
- `player_move(heap_index: int, count: int)`: Make a move
- `nim_sum() -> int`: Calculate current Nim-sum
- `is_over() -> bool`: Check if game is finished

### NorthcottGame

```python
class NorthcottGame:
    def __init__(
        self,
        board_size: int = 8,
        num_rows: int = 3,
        rows: List[Tuple[int, int]] = None,
    )
```

**Methods:**

- `render() -> str`: Display board state
- `make_move(row_index: int, piece: str, new_position: int)`: Move a piece
- `computer_move() -> Tuple[int, str, int]`: AI move
- `get_gaps() -> List[int]`: Get gap sizes (Nim heap values)
- `nim_sum() -> int`: Calculate Nim-sum of gaps

### WythoffGame

```python
class WythoffGame:
    def __init__(self, heap1: int = 5, heap2: int = 8)
```

**Methods:**

- `render() -> str`: Display heap state
- `make_move(from_heap1: int, from_heap2: int)`: Remove from heaps
- `computer_move() -> Tuple[int, int]`: AI move
- `is_over() -> bool`: Check if game is finished

## Testing

Run the test suite:

```bash
python tests/test_nim.py
python tests/test_nim_enhancements.py
```

## Educational Value

This implementation is designed for learning:

1. **Combinatorial Game Theory**: Understand Nim-sum and winning strategies
1. **Mathematical Patterns**: Explore golden ratio in Wythoff's Game
1. **Algorithm Design**: See how optimal AI opponents are implemented
1. **Code Quality**: Well-documented, type-hinted Python code

## Future Enhancements

Potential additions:

- GUI implementation with animations
- Network multiplayer mode
- Additional variants (Dawson's Chess, Kayles, etc.)
- Tournament mode with multiple games
- Save/load game state
- Move history and replay

## References

- **Nim**: Bouton, C. L. (1901). "Nim, A Game with a Complete Mathematical Theory"
- **Wythoff's Game**: Wythoff, W. A. (1907). "A Modification of the Game of Nim"
- **Combinatorial Game Theory**: Berlekamp, Conway, and Guy. "Winning Ways for Your Mathematical Plays"
