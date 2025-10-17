# Contributing to Card & Paper Games

Thank you for your interest in contributing! This document provides guidelines for contributing to the games collection.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Adding a New Game](#adding-a-new-game)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

This project aims to be welcoming and inclusive. Please:

- Be respectful and considerate
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Be patient with questions and discussions

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Basic understanding of Python and game development

### Fork and Clone

1. Fork the repository on GitHub
1. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/Games.git
cd Games
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/saint2706/Games.git
```

## Development Setup

### Install Dependencies

You have two options for setting up your development environment:

#### Option 1: Install from PyPI (Recommended for testing)

```bash
# Install with all development dependencies
pip install games-collection[dev]

# Or with GUI support
pip install games-collection[gui,dev]
```

#### Option 2: Install from Source (For active development)

```bash
# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Or with GUI support
pip install -e ".[gui,dev]"
```

#### Optional System Dependencies

For GUI support on Linux:

```bash
# On Ubuntu/Debian:
sudo apt-get install python3-tk
```

### Set Up Pre-commit Hooks

The repository uses [pre-commit](https://pre-commit.com/) to run Black, Ruff, Mdformat, and the Radon-based complexity checks.
After installing the development dependencies, enable the hooks locally so that the same tooling runs before every commit:

```bash
pre-commit install

# Run on demand across the entire codebase
pre-commit run --all-files
```

### Verify Installation

Run existing tests to ensure everything is working:

```bash
pytest tests/
```

## How to Contribute

### Types of Contributions

We welcome:

- **Bug fixes**: Fix issues in existing games
- **New games**: Add new card or paper games
- **Features**: Add features to existing games (new variants, difficulty levels, etc.)
- **Documentation**: Improve docs, tutorials, or code comments
- **Tests**: Increase test coverage
- **Performance**: Optimize slow code
- **UI/UX**: Improve CLI or GUI interfaces

### Finding Issues to Work On

- Check the [Issues](https://github.com/saint2706/Games/issues) page
- Look for issues labeled `good-first-issue` or `help-wanted`
- Review `docs/planning/TODO.md` for planned features
- Propose your own ideas by opening an issue first

## Adding a New Game

### Game Structure

Each game should follow this structure:

```
game_name/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point (python -m package.game_name)
├── game_name.py         # Core game logic
├── cli.py              # Command-line interface (optional)
├── gui.py              # Graphical interface (optional)
├── README.md           # Game-specific documentation
└── tests/              # Game-specific tests (or in top-level tests/)
    └── test_game_name.py
```

### Required Components

Every game must include:

1. **Game Engine**: Core logic independent of UI
1. **Documentation**: Module docstrings, function docstrings, README
1. **CLI Interface**: At minimum, a playable command-line version
1. **Tests**: Unit tests for game logic
1. **Entry Point**: Runnable via `python -m package.game_name`

### Game Engine Template

```python
"""Game Name - Brief description.

Detailed module docstring explaining:
- Game rules
- How the code is organized
- Key classes and their responsibilities
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

class GamePhase(Enum):
    """Game lifecycle phases."""
    SETUP = auto()
    PLAYING = auto()
    FINISHED = auto()

@dataclass
class Player:
    """Player state."""
    name: str
    score: int = 0
    is_bot: bool = False

class GameEngine:
    """Core game logic.

    This class manages game state and rules, independent of UI.
    """

    def __init__(self, num_players: int = 2):
        """Initialize game.

        Args:
            num_players: Number of players (2-4)
        """
        self.players = [Player(f"Player {i+1}") for i in range(num_players)]
        self.phase = GamePhase.SETUP
        self.current_player = 0

    def start(self):
        """Start the game."""
        self.phase = GamePhase.PLAYING
        # Setup game state

    def make_move(self, move):
        """Process a player move.

        Args:
            move: The move to make

        Returns:
            bool: True if move was valid
        """
        if not self.is_valid_move(move):
            return False

        # Apply move
        # Update state
        # Check for game end

        if self.is_game_over():
            self.phase = GamePhase.FINISHED
        else:
            self.next_player()

        return True

    def is_valid_move(self, move) -> bool:
        """Check if move is legal."""
        # Implement validation
        return True

    def is_game_over(self) -> bool:
        """Check if game has ended."""
        # Implement end condition
        return False

    def get_winner(self) -> Optional[Player]:
        """Get game winner, if any."""
        # Implement winner determination
        return None

    def next_player(self):
        """Advance to next player."""
        self.current_player = (self.current_player + 1) % len(self.players)

# CLI interface
def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(description='Game Name')
    parser.add_argument('--players', type=int, default=2,
                       help='Number of players')
    parser.add_argument('--seed', type=int, help='Random seed')

    args = parser.parse_args()

    # Create and run game
    game = GameEngine(num_players=args.players)
    game.start()

    # Game loop
    while not game.is_game_over():
        # Display state
        # Get player input
        # Make move
        pass

    # Show results
    winner = game.get_winner()
    print(f"Winner: {winner.name if winner else 'Draw'}")

if __name__ == '__main__':
    main()
```

### **main**.py Template

```python
"""Entry point for game_name module."""

from .game_name import main

if __name__ == '__main__':
    main()
```

### Adding AI Opponents

If your game includes AI:

1. **Separate AI Logic**: Keep AI in separate class/module
1. **Difficulty Levels**: Provide at least 2-3 difficulty levels
1. **Explain Strategy**: Document how AI makes decisions
1. **Reasonable Speed**: AI should respond in \<1 second typically

Example AI structure:

```python
class AIPlayer:
    """AI opponent for game.

    Uses [algorithm name] to make decisions.
    """

    def __init__(self, difficulty: str = 'medium'):
        self.difficulty = difficulty

    def choose_move(self, game_state):
        """Choose best move.

        Args:
            game_state: Current game state

        Returns:
            Best move according to AI strategy
        """
        if self.difficulty == 'easy':
            return self.random_move(game_state)
        elif self.difficulty == 'medium':
            return self.heuristic_move(game_state)
        else:  # hard
            return self.optimal_move(game_state)
```

## Code Style Guidelines

### General Principles

- **Readability**: Code should be self-documenting
- **Simplicity**: Prefer simple solutions over clever ones
- **Consistency**: Follow existing patterns in the codebase
- **Documentation**: Explain _why_, not just _what_

### Python Style

Follow [PEP 8](https://pep8.org/) with these specifics:

```python
# Naming conventions
class MyGameEngine:         # PascalCase for classes
    pass

def calculate_score():      # snake_case for functions
    pass

CONSTANT_VALUE = 42         # UPPER_CASE for constants

my_variable = 10            # snake_case for variables

# Line length: 88 characters (Black formatter default)

# Imports: standard library, third-party, local
import json
import random
from typing import List

import tkinter as tk

from .cards import Deck
from ..common.utils import format_output

# Type hints encouraged
def deal_cards(num_cards: int) -> List[Card]:
    """Deal cards from deck."""
    pass

# Docstrings: Google style
def my_function(param1: int, param2: str) -> bool:
    """Short description.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When params are invalid
    """
    pass
```

### Documentation Style

All modules, classes, and public functions must have docstrings:

```python
"""Module docstring.

Comprehensive explanation of the module, including:
- Purpose and overview
- Key components
- Usage examples
- References to related modules
"""

class GameEngine:
    """Brief description.

    Detailed description of the class, its purpose,
    and how it fits into the larger system.

    Attributes:
        players: List of players in the game
        current_player: Index of active player
    """

    def __init__(self, num_players: int):
        """Initialize game engine.

        Args:
            num_players: Number of players (2-4)

        Raises:
            ValueError: If num_players is out of range
        """
        pass
```

### Git Commit Messages

Follow conventional commits format:

```
type(scope): brief description

Longer explanation if needed

Fixes #123
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `style`: Formatting changes
- `perf`: Performance improvements

Examples:

```
feat(poker): add Omaha variant

Implements Omaha Hold'em with 4 hole cards and 2+3 hand evaluation.

Fixes #42

---

fix(bluff): correct pile transfer logic

Pile was not clearing after successful challenge.
Now properly clears pile and updates statistics.

Fixes #56

---

docs: add tutorial for blackjack

Comprehensive guide covering basic play, strategy, and advanced features.
```

## Testing Requirements

### Test Coverage

- All new games must include tests
- Aim for >80% code coverage
- Test both normal and edge cases

### Test Structure

```python
import unittest
from game_package.game_name import GameEngine, Player

class TestGameEngine(unittest.TestCase):
    """Tests for GameEngine class."""

    def setUp(self):
        """Set up test fixtures."""
        self.game = GameEngine(num_players=2)

    def test_initialization(self):
        """Test game initializes correctly."""
        self.assertEqual(len(self.game.players), 2)
        self.assertEqual(self.game.current_player, 0)

    def test_valid_move(self):
        """Test valid move is accepted."""
        self.game.start()
        result = self.game.make_move(valid_move)
        self.assertTrue(result)

    def test_invalid_move(self):
        """Test invalid move is rejected."""
        self.game.start()
        result = self.game.make_move(invalid_move)
        self.assertFalse(result)

    def test_game_end(self):
        """Test game ends correctly."""
        # Set up winning condition
        self.assertTrue(self.game.is_game_over())
        self.assertIsNotNone(self.game.get_winner())

    def test_edge_cases(self):
        """Test edge cases."""
        # Test boundary conditions
        # Test empty states
        # Test maximum values
        pass

if __name__ == '__main__':
    unittest.main()
```

### Running Tests

```bash
# Run all tests
python -m unittest discover -s tests -p "test_*.py"

# Run specific test file
python tests/test_game_name.py

# Run specific test
python -m unittest tests.test_game_name.TestGameEngine.test_valid_move
```

## Documentation

### Required Documentation

For each game, provide:

1. **Module Docstrings**: Explain overall architecture
1. **Function Docstrings**: Explain purpose, parameters, returns
1. **README.md**: User-facing documentation with:
   - Game overview
   - How to play
   - Command-line options
   - Examples
   - Strategy tips (optional)
1. **Update Main README**: Add your game to the main README.md

### Documentation Template

See `docs/source/tutorials/` for tutorial templates.

### Building Sphinx Docs

```bash
cd docs
pip install sphinx sphinx_rtd_theme
make html
# Open docs/build/html/index.html
```

## Submitting Changes

### Before Submitting

1. **Run Tests**: Ensure all tests pass

   ```bash
   python -m unittest discover -s tests
   ```

1. **Check Style**: Code follows style guidelines

1. **Update Docs**: Documentation is complete and accurate

1. **Test Manually**: Play your game to ensure it works

1. **Update docs/planning/TODO.md**: If completing a TODO item, mark it done

### Pull Request Process

1. **Create Branch**: Create a feature branch

   ```bash
   git checkout -b feature/my-new-game
   ```

1. **Make Changes**: Implement your feature/fix

1. **Commit**: Make clear, logical commits

   ```bash
   git add .
   git commit -m "feat(game): add new game"
   ```

1. **Update**: Sync with upstream

   ```bash
   git fetch upstream
   git rebase upstream/master
   ```

1. **Push**: Push to your fork

   ```bash
   git push origin feature/my-new-game
   ```

1. **Open PR**: Open Pull Request on GitHub

   - Use clear title following commit conventions
   - Describe changes comprehensively
   - Reference related issues
   - Include screenshots for UI changes

### PR Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Checklist

- [ ] Tests pass locally
- [ ] Added tests for new code
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] No breaking changes (or documented)

## Related Issues

Fixes #123

## Screenshots

(If applicable)
```

## Review Process

### What Reviewers Look For

- Code quality and style
- Test coverage
- Documentation completeness
- Performance considerations
- Security issues
- Edge cases handled

### Responding to Feedback

- Be receptive to suggestions
- Ask questions if unclear
- Make requested changes promptly
- Re-request review after updates

## Additional Guidelines

### Security

- Never commit secrets or API keys
- Validate all user input
- Be careful with `eval()` or `exec()`
- Use secure random number generation for games

### Performance

- Profile slow code
- Optimize hot paths
- Consider memory usage
- Keep AI response time reasonable (\<1s typically)

### Compatibility

- Test on Python 3.9, 3.10, 3.11, 3.12
- Ensure cross-platform compatibility
- Handle missing optional dependencies gracefully
- Use pathlib for file paths

### Accessibility

- Provide both CLI and GUI where possible
- Use clear, descriptive text
- Support keyboard navigation in GUIs
- Consider colorblind-friendly color schemes

## Getting Help

### Resources

- **Documentation**: Check `docs/` directory
- **Examples**: Review existing games for patterns
- **Issues**: Search existing issues for similar problems
- **Discussions**: Use GitHub Discussions for questions

### Contact

- Open an issue for bugs or feature requests
- Use discussions for general questions
- Tag maintainers if urgent

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Recognition

Contributors are recognized in:

- Git commit history
- Release notes
- Main README.md (for significant contributions)

Thank you for contributing! 🎮
