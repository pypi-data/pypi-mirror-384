# Hangman - New Features

This document describes the enhanced features added to the Hangman game.

## Features Overview

### 1. Themed Word Lists

The game now includes five themed word categories:

- **Movies**: Popular films and movie titles (50 words)
- **Countries**: Nations from around the world (50 words)
- **Sports**: Various athletic activities (47 words)
- **Animals**: Common and exotic creatures (46 words)
- **Food**: Delicious dishes and ingredients (47 words)

**How to Use:**

```python
from paper_games.hangman import load_themed_words, HangmanGame

# Load all themes
themes = load_themed_words()

# Load specific theme
movies = load_themed_words("movies")

# Create game with theme
game = HangmanGame(movies, theme="movies")
```

### 2. Difficulty Selector

Words are categorized by difficulty based on length:

- **Easy**: 6+ letter words (360 words)
- **Medium**: 4-5 letter words (360 words)
- **Hard**: 3 letter words (360 words)

**How to Use:**

```python
from paper_games.hangman import load_words_by_difficulty, HangmanGame

# Load words by difficulty
easy_words = load_words_by_difficulty("easy")
medium_words = load_words_by_difficulty("medium")
hard_words = load_words_by_difficulty("hard")
all_words = load_words_by_difficulty("all")

# Create game with difficulty
game = HangmanGame(hard_words)
```

### 3. Multiplayer Mode

Players can take turns choosing secret words for others to guess.

**Features:**

- Support for 2-4 players
- Configurable number of rounds per player
- Score tracking
- Winner announcement

**How to Use:** In the CLI, select option 2 "Multiplayer" when prompted for game mode.

### 4. Hint System

Players can request hints to reveal unguessed letters.

**Features:**

- 3 hints available per game (configurable)
- Hints reveal one random unguessed letter
- Hint usage tracked in game status
- Can be disabled if desired

**How to Use:**

```python
from paper_games.hangman import HangmanGame

# Create game with hints enabled (default)
game = HangmanGame(["example"], hints_enabled=True, max_hints=3)

# Get a hint
revealed_letter = game.get_hint()

# Disable hints
game_no_hints = HangmanGame(["example"], hints_enabled=False)
```

In the CLI, type `hint` when prompted for a guess.

### 5. ASCII Art Variations

Three different ASCII art styles are available:

- **Classic**: Traditional hangman gallows
- **Simple**: Clean, straightforward design
- **Minimal**: Ultra-minimalist style

**How to Use:**

```python
from paper_games.hangman import HangmanGame, HANGMAN_ART_STYLES

# View available styles
print(HANGMAN_ART_STYLES.keys())

# Create game with art style
game = HangmanGame(["test"], art_style="simple")
```

## CLI Interface

When you run `python -m paper_games.hangman`, you'll see an interactive menu:

1. **Game Mode Selection**: Single player or multiplayer
1. **Difficulty Selection**: Easy, medium, hard, or all
1. **Theme Selection**: Choose a theme or use standard words
1. **Art Style Selection**: Choose your preferred ASCII art style

During gameplay:

- Type a letter to guess
- Type `hint` to get a hint
- Type the full word to guess the entire word

## Backward Compatibility

All new features are optional and maintain backward compatibility:

```python
# Old API still works
from paper_games.hangman import play, HangmanGame, load_default_words

# Traditional usage
words = load_default_words()
game = HangmanGame(words, max_attempts=6)

# CLI with no options
play(words)
```

## API Reference

### Functions

- `load_default_words()` - Load all 1,080 words from all difficulties
- `load_words_by_difficulty(difficulty)` - Load words by difficulty level
- `load_themed_words(theme=None)` - Load themed word lists

### HangmanGame Parameters

- `words` - Iterable of words to use
- `max_attempts` - Number of wrong guesses allowed (default: 6)
- `theme` - Optional theme name to display (default: None)
- `hints_enabled` - Enable hint system (default: True)
- `max_hints` - Maximum hints per game (default: 3)
- `art_style` - ASCII art style to use (default: "classic")

### New Methods

- `get_hint()` - Reveal a random unguessed letter (returns letter or None)

## Examples

### Themed Game with Hints

```python
from paper_games.hangman import load_themed_words, HangmanGame

movies = load_themed_words("movies")
game = HangmanGame(
    movies,
    theme="movies",
    hints_enabled=True,
    max_hints=3,
    art_style="simple"
)

# Play the game
while not (game.is_won() or game.is_lost()):
    print(game.stage)
    print(f"Word: {game.obscured_word}")

    choice = input("Guess or 'hint': ")
    if choice == "hint":
        hint = game.get_hint()
        if hint:
            print(f"Revealed: {hint}")
    else:
        game.guess(choice)
```

### Hard Difficulty Game

```python
from paper_games.hangman import load_words_by_difficulty, HangmanGame

hard_words = load_words_by_difficulty("hard")  # 3-letter words
game = HangmanGame(hard_words, max_attempts=4, hints_enabled=False)
```

## Testing

Comprehensive tests are available in `tests/test_hangman_features.py`:

```bash
pytest tests/test_hangman_features.py -v
```

All 23 feature tests pass, ensuring reliability of the new functionality.
