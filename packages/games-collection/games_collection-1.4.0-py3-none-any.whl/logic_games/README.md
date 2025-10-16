# Logic & Puzzle Games

This directory contains implementations of logic puzzles and brain teasers.

## Planned Games

### Minesweeper

Classic mine detection game with difficulty levels

### Sokoban

Warehouse puzzle with box-pushing mechanics

### Sliding Puzzle (15-puzzle)

Number tile sliding game with solvability check

### Lights Out

Toggle-based puzzle with graph theory solution

### Picross/Nonograms

Picture logic puzzles with row/column hints

## Game Structure

Each game follows the standard structure:

```
game_name/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point (python -m logic_games.game_name)
├── game_name.py         # Core game logic (game engine)
├── cli.py              # Command-line interface (optional)
├── gui.py              # Graphical interface (optional)
├── README.md           # Game-specific documentation
└── tests/              # Tests (or in top-level tests/)
```

## Running Games

Once implemented, games can be run with:

```bash
python -m logic_games.game_name
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on adding new logic and puzzle games.
