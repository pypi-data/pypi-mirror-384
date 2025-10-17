# Minesweeper

Classic mine detection puzzle game where players reveal squares on a grid, using number clues to identify and avoid mine
locations.

## Rules

### Objective

Reveal all non-mine cells without detonating any mines.

### Gameplay

1. Click a cell to reveal it
1. Numbers indicate how many mines are in adjacent cells (including diagonals)
1. Use flags to mark suspected mine locations
1. Revealing a cell with 0 adjacent mines will cascade reveal neighbors
1. Game is won when all non-mine cells are revealed
1. Game is lost if you reveal a mine

### Difficulty Levels

- **Beginner**: 9×9 grid with 10 mines
- **Intermediate**: 16×16 grid with 40 mines
- **Expert**: 16×30 grid with 99 mines

## Running the Game

```bash
python -m logic_games.minesweeper
```

## Features

- Three difficulty levels
- Flag, question mark, and clear mark mechanics
- Chording to reveal around completed numbers
- Automatic cascade reveal for zero cells
- Safe first click (never a mine or immediate neighbor)
- Mine reveal and misflag indicators when the game ends

## Strategy Tips

- Start with corners and edges
- Look for patterns (e.g., 1-2-1 often indicates mines on ends)
- Use flags to mark certain mines
- Work from revealed numbers to deduce mine locations
- When stuck, make educated guesses in areas with lower mine probability
