# Boggle

A complete and well-documented implementation of the classic word search game, Boggle. This version features official dice layouts, a robust dictionary backend, and a flexible engine that supports multiplayer games and custom time limits.

## How to Play
The goal of Boggle is to find as many words as possible in a grid of random letters within a set time limit.

1. **Start the Game**: Run the game from your terminal:
   ```bash
   python -m paper_games.boggle
   ```
2. **View the Board**: A grid of letters (typically 4x4 or 5x5) will be displayed.
3. **Find Words**: Form words by connecting adjacent letters (horizontally, vertically, or diagonally). You cannot use the same letter tile more than once in a single word.
4. **Submit Words**: Enter the words you find. For multiplayer games, prefix your submission with your player name (e.g., "Player1 hello").
5. **Scoring**: Points are awarded based on word length. In multiplayer, duplicate words submitted by multiple players are not scored.

## Features

- **Official Dice Layouts**: The game uses the official Boggle dice layouts for both 4x4 and 5x5 boards to ensure an authentic gameplay experience.
- **Trie-Based Dictionary**: A highly efficient Trie data structure is used for word validation, allowing for instant lookups and prefix searching.
- **Multiplayer Support**: Play with multiple friends. The game automatically handles duplicate word submissions, only awarding points to unique finds.
- **Configurable Game Rules**:
  - **Board Size**: Choose between different board sizes (e.g., 4 for classic, 5 for "Big Boggle").
  - **Time Limit**: Set the duration of the round in seconds.
- **Command-Line Interface**: A clean and interactive CLI guides players through the game, from setup to final scoring.

## Usage
To run the game, simply execute the module from your terminal:
```bash
python -m paper_games.boggle
```
You will be prompted to configure the game:
- **Board Size**: Enter the desired grid size (e.g., 4 or 5).
- **Time Limit**: Set the round duration in seconds (e.g., 180 for 3 minutes).
- **Number of Players**: Specify how many people are playing.
- **Player Names**: Enter a name for each player.

During the game, submit words as `<player_name> <word>`. If playing solo, you can just enter the word. Type `done` to end the game early.

## Scoring System
Points are awarded according to the official Boggle rules:
- **3-4 letters**: 1 point
- **5 letters**: 2 points
- **6 letters**: 3 points
- **7 letters**: 5 points
- **8+ letters**: 11 points

## Module Structure
The Boggle game is organized into two main, well-documented modules:
- `boggle.py`: Contains the core game engine (`BoggleGame`) and the command-line interface (`BoggleCLI`). It manages the game state, board generation, word validation, and scoring.
- `dictionary.py`: Implements the `BoggleDictionary` class, which uses a Trie data structure to efficiently load and query word lists.
