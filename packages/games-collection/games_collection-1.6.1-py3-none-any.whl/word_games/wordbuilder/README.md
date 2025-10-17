# WordBuilder

WordBuilder is a tile-based game that challenges players to form words from a hand of lettered tiles, similar to the classic game Scrabble.

## Gameplay

Players are given a hand of seven tiles, each with a letter and a point value. The objective is to create valid words from these tiles. Each time a word is formed, its points are added to the player's score, and the used tiles are replenished from a central "tile bag."

The game ends after a fixed number of turns (10) or when the tile bag is empty and the player's hand is exhausted.

## Features

### Dictionary Validation

All words played are validated against a built-in dictionary to ensure they are legitimate. The dictionary is stored in a simple text file, making it easy to view or extend.

### Tile Distribution and Scoring

The game uses a standard Scrabble-like tile distribution and scoring system. The tile bag is pre-configured with a specific count for each letter of the alphabet. The point value of each letter is also based on its frequency in the English language.

### Customization

The game engine is designed to be configurable. You can create an instance of the game with:
- A custom dictionary file.
- A different tile bag configuration, allowing for variations in gameplay.

## Running the Game

To play WordBuilder, execute the following command from the project's root directory:

```bash
python -m word_games.wordbuilder
```