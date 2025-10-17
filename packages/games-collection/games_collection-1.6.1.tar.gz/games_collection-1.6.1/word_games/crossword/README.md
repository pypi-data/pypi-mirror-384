# Crossword

This Crossword game allows you to solve puzzles in a simple, command-line interface. The game engine is designed with flexibility in mind, featuring a system for importing and exporting custom crossword packs.

## Gameplay

The game presents a grid of clues, both "across" and "down." Your task is to provide the correct answers for each clue. The game tracks which clues you have successfully solved. The game is won when all clues have been answered correctly.

A default puzzle is included for immediate play.

## Custom Crossword Packs

A key feature of this game is the ability to create, share, and play custom crossword puzzles. The game uses a simple JSON format for defining puzzle packs.

### Pack Format

A crossword pack is a JSON file containing a list of clue objects. Each object must have the following fields:

- `id`: A unique integer identifier for the clue.
- `row`: The starting row (0-indexed) of the word in the grid.
- `column`: The starting column (0-indexed) of the word in the grid.
- `direction`: The direction of the word (`"across"` or `"down"`).
- `answer`: The word that solves the clue.
- `clue`: The text of the clue.

### Example Pack

```json
[
  {
    "id": 1,
    "row": 0,
    "column": 0,
    "direction": "across",
    "answer": "PYTHON",
    "clue": "A popular high-level programming language."
  },
  {
    "id": 2,
    "row": 0,
    "column": 0,
    "direction": "down",
    "answer": "PUZZLE",
    "clue": "A game or problem designed to test ingenuity."
  }
]
```

The game's CLI (Command-Line Interface) provides options for loading custom packs.

## Running the Game

To play the Crossword game, use the following command from the project root:

```bash
python -m word_games.crossword
```