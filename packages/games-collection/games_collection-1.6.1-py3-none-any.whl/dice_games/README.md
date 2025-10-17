# Dice Games

This directory contains implementations of dice-based games.

## Planned Games

### Craps

Casino dice game with pass/don't pass betting

### Farkle

Risk-based scoring with push-your-luck mechanics

### Liar's Dice

Bluffing game similar to Bluff but with dice

### Bunco

Party dice game with rounds and team scoring

## Game Structure

Each game follows the standard structure:

```
game_name/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point (python -m dice_games.game_name)
├── game_name.py         # Core game logic (game engine)
├── cli.py              # Command-line interface (optional)
├── gui.py              # Graphical interface (optional)
├── README.md           # Game-specific documentation
└── tests/              # Tests (or in top-level tests/)
```

## Running Games

Once implemented, games can be run with:

```bash
python -m dice_games.game_name
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on adding new dice games.
