# Games Collection

A comprehensive collection of games implemented in Python, organized by category. The project includes 49 playable games
(15 card games + 21 paper games + 4 dice games + 4 word games + 5 logic games) ranging from casino classics like Texas
Hold'em and Blackjack to strategy games like Checkers and Chess, word puzzles, dice games, and logic challenges.

**📖 See [GAMES.md](GAMES.md) for a complete catalog of all available games.**

## Installation

### From PyPI (Recommended)

The easiest way to install the Games Collection is via pip:

```bash
# Standard installation
pip install games-collection

# With GUI support
pip install games-collection[gui]

# For development
pip install games-collection[dev]
```

After installation, you can run games using the `games-*` commands:

```bash
# Card games
games-poker
games-blackjack
games-uno
games-war

# Paper games
games-tic-tac-toe
games-battleship
games-checkers

# Dice games
games-craps
games-bunco

# See all available games
pip show games-collection
```

### From Source

For development or testing the latest changes:

```bash
git clone https://github.com/saint2706/Games.git
cd Games

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Run games using Python module syntax
python -m card_games.war
python -m paper_games.tic_tac_toe
```

### Other Options

- **Docker**: See [docs/deployment/DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md#docker-deployment)
- **Standalone Executables**: Download from [Releases](https://github.com/saint2706/Games/releases)
- **Complete Guide**: See [docs/deployment/DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md)

## GUI Frameworks

The Games Collection supports both **Tkinter** and **PyQt5** for graphical interfaces. We are in the process of migrating all GUIs to PyQt5 for better cross-platform support and reliability.

### Current Status

- **Tkinter**: 14 games with full GUI support
- **PyQt5**: 2 games migrated (Dots and Boxes, Blackjack), 12 remaining
- **PyQt5**: 3 games migrated (Dots and Boxes, Go Fish, Bluff), 11 remaining
- **PyQt5**: 3 games migrated (Dots and Boxes, Go Fish, Crazy Eights), 11 remaining
- **PyQt5**: 3 games migrated (Dots and Boxes, Go Fish, Hearts), 11 remaining
- **PyQt5**: 3 games migrated (Dots and Boxes, Go Fish, Solitaire), 11 remaining
- **PyQt5**: 3 games migrated (Dots and Boxes, Go Fish, Uno), 11 remaining

See **[GUI Migration Status](docs/status/GUI_MIGRATION_STATUS.md)** for detailed progress tracking.

### Using GUIs

Most games support a `--gui` flag to launch the graphical interface:

```bash
# Tkinter GUIs (current)
python -m card_games.blackjack --gui
python -m paper_games.battleship --gui

# PyQt5 GUIs (new)
python -m paper_games.dots_and_boxes --gui-framework pyqt5
python -m card_games.blackjack --gui-framework pyqt5
python -m card_games.go_fish --gui-framework pyqt5
python -m card_games.bluff --gui
python -m card_games.crazy_eights --gui-framework pyqt5
python -m card_games.hearts --backend pyqt
```

For more information, see:

- [GUI Migration Guide](docs/gui/MIGRATION_GUIDE.md) - How to migrate a game to PyQt5
- [GUI Frameworks Documentation](docs/gui/FRAMEWORKS.md) - Framework comparison and usage
- [PyQt5 Implementation Summary](docs/gui/PYQT5_IMPLEMENTATION.md) - Technical details
- [GUI Documentation Hub](docs/gui/README.md) - Complete GUI documentation

## Repository layout

```text
card_games/
├── common/           # Shared card representations
├── poker/            # Texas Hold'em and Omaha with tournament mode
├── blackjack/        # Casino-style blackjack with splits, doubles, and GUI
├── bluff/            # Cheat/Bluff card game with AI personalities
├── uno/              # Classic Uno with house rules and team mode
├── hearts/           # Trick-taking with shooting the moon
├── spades/           # Partnership bidding with nil bids
├── gin_rummy/        # Two-player melding game
├── bridge/           # Contract bridge with simplified bidding
├── solitaire/        # Klondike patience game
├── cribbage/         # Pegging and crib scoring to 121 points
├── euchre/           # Trump-based trick-taking with bowers
├── rummy500/         # Melding variant with negative scoring
├── go_fish/          # Classic card matching game
├── war/              # Simple comparison card game
└── crazy_eights/     # Discard matching with action cards
paper_games/
├── tic_tac_toe/      # Minimax AI with ultimate variant
├── battleship/       # Naval combat with strategic AI
├── hangman/          # Word guessing with themed categories
├── dots_and_boxes/   # Connect edges to capture boxes
├── nim/              # Mathematical strategy with variants
├── unscramble/       # Word unscrambling with timed mode
├── connect_four/     # Vertical grid with gravity mechanics
├── checkers/         # Jump mechanics with king promotion
├── mancala/          # Stone distribution game
├── othello/          # Disc flipping with positional strategy
├── sudoku/           # Number puzzle with difficulty levels
├── chess/            # Classic chess with move validation
├── backgammon/       # Race game with dice and strategy
├── mastermind/       # Code-breaking deduction game
├── boggle/           # Word search in letter grid
├── pentago/          # Tic-tac-toe with board rotation
├── sprouts/          # Topological connection game
├── snakes_and_ladders/ # Classic board game with dice
├── yahtzee/          # Dice combination scoring game
├── twenty_questions/ # Deductive guessing game
└── four_square_writing/ # Creative writing game
dice_games/
├── farkle/           # Risk-based dice scoring with hot dice
├── craps/            # Casino dice game with betting
├── liars_dice/       # Bluffing game with hidden dice
└── bunco/            # Social dice game with rounds
word_games/
├── trivia/           # Question and answer trivia game
├── crossword/        # Crossword puzzle generation and solving
├── anagrams/         # Word rearrangement challenge
└── wordbuilder/      # Build words from letter sets
logic_games/
├── minesweeper/      # Classic mine detection puzzle
├── lights_out/       # Toggle puzzle with pattern solving
├── sliding_puzzle/   # Number tile sliding game
├── picross/          # Nonogram picture logic puzzle
└── sokoban/          # Warehouse box-pushing puzzle
common/
├── architecture/     # Architectural patterns (plugin, events, persistence)
├── analytics/        # Game analytics and statistics
├── cli_utils.py      # Enhanced CLI utilities
└── gui_base.py       # Common GUI components
```

## Documentation roadmap

Every game module now opens with an extensive module-level docstring that introduces the contained classes and explains
how they collaborate. Class and function docstrings are deliberately verbose so that you can treat the source as an
executable design document. To dive in:

- Start with `card_games/bluff/bluff.py` for a guided tour of the Cheat/Bluff engine, including commentary on turn
  structure and challenge resolution.
- Explore `card_games/poker/poker.py` and `card_games/poker/gui.py` to see how the Texas hold'em mechanics feed into
  both a CLI and Tkinter front-end.
- Browse `card_games/bluff/gui.py` to learn how the GUI keeps its widgets in sync with the engine state using richly
  annotated helper methods.

Each module's docstrings provide inline references to supporting utilities so you can jump between files without losing
context.

## Paper and pencil classics

Looking for lighter fare? The `paper_games` package recreates a handful of classroom staples:

- `python -m paper_games.hangman` drops you into a word-guessing showdown with configurable mistake limits, gallows art
  that fills in piece by piece, and a curated vocabulary sourced from the
  [The Hangman Wordlist](https://github.com/TheBiemGamer/The-Hangman-Wordlist) project. Go letter by letter or gamble on
  a full-word reveal.
- `python -m paper_games.tic_tac_toe` pits you against a perfect minimax AI that respects coin tosses for the opening
  move, supports X-or-O selection, and uses coordinate input (A1 through C3) so the board feels like the
  pencil-and-paper classic.
- `python -m paper_games.dots_and_boxes` lets you outline squares on a 2×2 board, while the computer now reads chains,
  takes bonus turns, and prints coordinate guides so you can follow along with precision.
- `python -m paper_games.battleship` challenges you to sink a trio of hidden ships spread across a 6×6 ocean.
- `python -m paper_games.unscramble` serves up scrambled words over multiple rounds and keeps score of your successes,
  drawing from the same curated word list as hangman for consistency.
- `python -m paper_games.nim` offers a comprehensive exploration of combinatorial game theory with classic Nim plus
  variants (Northcott's Game and Wythoff's Game). Features include graphical heap visualization, educational mode with
  strategy explanations, multiplayer support (3+ players), and custom rule variations. The optimal AI opponent teaches
  winning strategies while you play.

## Blackjack

Take a seat at a richly detailed blackjack table that recreates the flow of a casino shoe. The Tkinter interface renders
premium card art, highlights the active hand, animates the dealer's draw, and keeps your bankroll front and centre while
you decide when to hit, stand, double, or split.

```bash
python -m card_games.blackjack
```

Prefer the original text-mode experience? Launch it with:

```bash
python -m card_games.blackjack --cli --bankroll 300 --min-bet 15 --decks 4
```

Highlights:

- Shoe management with automatic shuffling as the cards run low.
- Animated dealer reveals, natural blackjack detection, and soft-17 behaviour.
- Support for doubling down, splitting pairs, and per-hand outcome summaries that update your bankroll instantly in both
  the GUI and CLI.

## Poker

Sit at a four-player poker table and battle three computer-controlled opponents across full betting rounds. Each
difficulty level tunes the bots' Monte Carlo-backed decision making—higher settings reduce mistakes, tighten the hands
they play, and increase their aggression when they sense strength.

The poker module now supports multiple game variants, betting structures, and tournament play with comprehensive
statistics tracking.

```bash
# Classic Texas Hold'em
python -m card_games.poker --difficulty Medium --rounds 5 --seed 123

# Omaha Hold'em with 4 hole cards
python -m card_games.poker --variant omaha --rounds 5

# Tournament mode with increasing blinds
python -m card_games.poker --tournament --rounds 10

# Pot-limit betting
python -m card_games.poker --limit pot-limit --rounds 5
```

Gameplay features:

- **Game Variants**: Texas Hold'em (2 hole cards) and Omaha (4 hole cards with exact 2+3 hand evaluation)
- **Betting Limits**: No-limit, pot-limit, and fixed-limit structures
- **Tournament Mode**: Blinds increase automatically based on configurable schedule
- **Statistics Tracking**: Hands won, fold frequency, showdown performance, and net profit tracked for all players
- **Hand History**: Complete game logs saved to JSON files for post-session review
- **Showdown Animations**: Visual card reveals and hand ranking explanations in GUI
- Rotating dealer button with blinds, betting rounds (pre-flop through river), and side-pot aware chip accounting
- Skill profiles that estimate equity against unknown hands to guide calls, bluffs, and value raises
- Detailed action narration in the CLI plus a live-updating graphical table for players who prefer a visual experience

Launch the GUI to play the same match with card visuals, action buttons, and a running log of the hand:

```bash
python -m card_games.poker --gui --difficulty Hard --rounds 3
python -m card_games.poker --gui --variant omaha --tournament
```

Evaluate an arbitrary set of cards via the helper utility:

```bash
python -m card_games.poker.poker_hand_evaluator As Kd Qh Jc Tc
```

## Bluff

Play a full game of Cheat/Bluff where every participant—bots included—handles a hand of cards. Each turn a player
discards a card face down and claims its rank. If the claim is challenged, the entire pile swings to the truthful
player; otherwise it keeps growing until someone is caught. First to shed every card, or whoever holds the fewest cards
after the configured number of table rotations, wins the match.

Difficulty levels tune the number of opponents, deck count, and AI personalities:

| Difficulty | Bots | Decks | Personality |
| ---------- | ---- | ----- | --------------------------------------------- |
| Noob | 1 | 1 | Cautious, rarely bluffs |
| Easy | 2 | 1 | Even tempered with light deception |
| Medium | 2 | 2 | Balanced mix of bluffing and scrutiny |
| Hard | 3 | 2 | Bolder bluffs and sharper challenges |
| Insane | 4 | 3 | Aggressive liars who constantly police rivals |

Fire up a five-rotation match on the default "Noob" setting from the terminal:

```bash
python -m card_games.bluff
```

Add variety with seeds, longer tables, or the graphical interface:

```bash
python -m card_games.bluff --difficulty Hard --rounds 7 --seed 42
python -m card_games.bluff --gui --difficulty Medium
```

### Gameplay highlights

- Bots manage full hands, weigh whether to lie based on the pot size, and keep memory of who was recently caught
  stretching the truth.
- Suspicion travels around the table. Other bots (and you) can challenge any claim, so expect lively AI-versus-AI
  skirmishes when a rival seems shady.
- The Tkinter interface offers card buttons, challenge controls, and a running event log alongside live card counts for
  every player.

## Uno

Enjoy a fast-paced game of Uno that recreates the classic 108-card deck, supports stacking draw cards, and lets you
battle an assortment of AI personalities. The rebuilt engine adds authentic Wild +4 challenges, automatic penalties when
someone forgets to shout UNO, and smarter bots that weigh risks before bluffing with a draw card. The terminal interface
highlights the active colour, tracks draw penalties, and prompts for wild-card colour selections while bots
automatically choose colours based on the makeup of their hands.

```bash
python -m card_games.uno --players 4 --bots 3 --bot-skill balanced --seed 2024
```

Highlights:

- Authentic card distribution with skips, reverses, draw-twos, and wild draw fours that support stacking and optional
  challenges when a rival might be bluffing.
- Adjustable bot aggression so you can face easy-going opponents or relentless action-card junkies that decide when to
  risk a Wild +4 challenge.
- Automatic UNO call enforcement: fail to declare in time and the table hands you a two-card penalty.
- Launch `python -m card_games.uno --gui` to enjoy a Tkinter interface with colour-coded cards, UNO toggles, penalty
  prompts, and a scrolling event log that mirrors each turn.

## Development and Code Quality

This project follows high code quality standards with automated tooling:

### For Contributors

- **Base Classes:** Common game engine and GUI interfaces in `common/` module
- **AI Strategies:** Reusable AI patterns for computer opponents
- **Pre-commit Hooks:** Automated code formatting and linting
- **Type Hints:** Comprehensive type annotations throughout
- **Testing:** 90%+ test coverage target with pytest
- **Complexity Analysis:** Code complexity monitoring and enforcement
- **Copilot Instructions:** Custom instructions for GitHub Copilot coding agent in `.github/copilot-instructions.md` and
  `.github/instructions/`

### Documentation

- **[GAMES.md](GAMES.md)** - Complete catalog of all available games
- **[docs/status/GUI_MIGRATION_STATUS.md](docs/status/GUI_MIGRATION_STATUS.md)** - GUI migration status (Tkinter →
  PyQt5)
- **[docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)** - Architecture patterns and base class
  usage
- **[docs/development/CODE_QUALITY.md](docs/development/CODE_QUALITY.md)** - Code standards, tools, and guidelines
- **[docs/development/TESTING.md](docs/development/TESTING.md)** - Testing guide and best practices
- **[docs/development/IMPLEMENTATION_NOTES.md](docs/development/IMPLEMENTATION_NOTES.md)** - Detailed implementation
  notes
- **[docs/planning/TODO.md](docs/planning/TODO.md)** - Roadmap and future plans
- **[docs/gui/README.md](docs/gui/README.md)** - GUI framework documentation hub
- **[docs/workflows/README.md](docs/workflows/README.md)** - GitHub Actions workflow documentation
- **[common/README.md](common/README.md)** - Common module documentation
- **[examples/](examples/)** - Example implementations using base classes
- **[.github/COPILOT_INSTRUCTIONS_GUIDE.md](.github/COPILOT_INSTRUCTIONS_GUIDE.md)** - GitHub Copilot instructions
  setup guide

### Quick Start for Development

```bash
# Install the package in editable mode with development dependencies
pip install -e ".[dev]"

# Or install from PyPI for testing
pip install games-collection[dev]

# Install pre-commit hooks
pre-commit install

# Run the full test suite (includes performance benchmarks)
pytest

# Run a quicker subset that skips performance benchmarks
pytest -m "not performance"

# Check code quality
pre-commit run --all-files
./scripts/check_complexity.sh

# Run GitHub Actions workflows locally (requires Docker)
make setup-act          # Install act for local workflow testing
make workflow-ci        # Test CI workflow locally
make workflow-list      # List all workflows
```

See [docs/development/CODE_QUALITY.md](docs/development/CODE_QUALITY.md) for detailed guidelines.

### Testing Workflows Locally

You can run and debug GitHub Actions workflows locally before pushing to GitHub:

```bash
# Install act (GitHub Actions local runner)
./scripts/setup_act.sh

# Run the CI workflow locally
./scripts/run_workflow.sh ci

# Run specific jobs
./scripts/run_workflow.sh ci --job lint
./scripts/run_workflow.sh ci --job test

# List all available workflows
./scripts/run_workflow.sh all
```

This allows you to:

- Test workflow changes without pushing to GitHub
- Debug failed jobs locally with faster iteration
- Save CI/CD minutes by testing locally first
- Work offline while developing workflows

See [docs/development/LOCAL_WORKFLOWS.md](docs/development/LOCAL_WORKFLOWS.md) for complete documentation.
