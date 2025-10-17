# Trivia Quiz

The Trivia Quiz is a multiple-choice question game that can source questions from an online database, providing a vast and varied quiz experience. It also includes robust offline capabilities, ensuring the game is always playable.

## Gameplay

The game presents a series of multiple-choice questions. For each question, you must select the correct answer from a list of options. Your score is based on the number of correct answers.

## Features

### Online Question Fetching

When an internet connection is available, the game fetches questions from the Open Trivia Database API. This allows for a dynamic and extensive range of questions across various categories and difficulty levels.

### Caching and Offline Mode

To ensure a seamless experience, the game caches questions retrieved from the online API. If the API is unreachable, or if you are offline, the game will draw from this local cache.

As a final fallback, a small set of default questions is included within the game itself, guaranteeing that you can always play.

### Configuration

The game can be configured to:
- Specify the number of questions per game.
- Select a specific category of questions.
- Choose a difficulty level (easy, medium, or hard).

## Running the Game

To start the Trivia Quiz, run the following command from the repository's root directory:

```bash
python -m word_games.trivia
```