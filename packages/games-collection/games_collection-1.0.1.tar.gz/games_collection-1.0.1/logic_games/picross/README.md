# Picross / Nonogram

Solve a classic picture logic puzzle using the numeric hints that run along the rows and columns. The Picross
implementation in this repository aims to mimic a full handheld experience: you can fill cells, mark them as empty,
cycle through states, and inspect detailed progress for each line while the engine tracks mistakes.

## Features

- 10×10 hand-crafted puzzle that forms a lantern-shaped mosaic
- Accurate hint generation for both rows and columns
- Mistake tracking with the ability to clear or toggle cells
- Line progress inspector to help you reason about the puzzle logically
- Rich CLI with Unicode blocks for a faithful nonogram feel

## Running

```bash
python -m logic_games.picross
```
