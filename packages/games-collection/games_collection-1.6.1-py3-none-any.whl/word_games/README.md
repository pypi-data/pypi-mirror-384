# Word Games Collection

Welcome to the Word Games collection! This directory features a variety of word-based and trivia games, each designed with a clean architecture and a focus on enjoyable gameplay.

## Games Included

### [Anagrams](./anagrams/README.md)

A classic word puzzle game where you unscramble letters to form words. It's a test of vocabulary and quick thinking, set over a series of timed or untimed rounds.

### [Crossword](./crossword/README.md)

Solve crossword puzzles with a simple and intuitive interface. This game includes a flexible system for importing and exporting custom puzzle packs, allowing you to create and share your own crosswords.

### [Trivia Quiz](./trivia/README.md)

Test your knowledge with this multiple-choice trivia game. It dynamically fetches questions from an online database for a virtually endless supply of questions. It also features a robust caching system for offline play.

### [WordBuilder](./wordbuilder/README.md)

A tile-based word-building game inspired by Scrabble. Use your hand of lettered tiles to form high-scoring words, validated against a comprehensive dictionary.

## Game Structure

Each game is a self-contained package with its own game engine, command-line interface (CLI), and documentation. They are built upon a common framework that ensures consistency and allows for easy extension.

## Running the Games

Each game can be run as a Python module from the root of the repository. For example, to play the Anagrams game, use the following command:

```bash
python -m word_games.anagrams
```

For more detailed instructions, please see the `README.md` file within each game's directory.

## Contributing

If you're interested in adding a new game to the collection, please refer to the main [CONTRIBUTING.md](../CONTRIBUTING.md) file for guidelines.