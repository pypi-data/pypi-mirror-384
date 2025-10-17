# Games Collection

The Games Collection brings together more than forty classic games implemented
in Python. Card tables, pen-and-paper puzzles, dice showdowns, word challenges,
and logic brainteasers all live in a single repository with shared engines,
artificial intelligence opponents, and optional graphical interfaces.

The project targets players who want quick access to familiar favourites and
contributors who enjoy extending game mechanics or experimenting with strategy
algorithms.

## Highlights

- **Broad catalogue** – 49 playable games spanning card, paper, dice, logic, and
  word genres. See the [Games Catalogue](docs/source/games_catalog.rst) for the
  full list.
- **Multiple interfaces** – Launch titles from the command line, via the
  `games-collection` menu, or with Tkinter/PyQt graphical front ends where
  available.
- **Reusable infrastructure** – Common modules provide AI strategies, save/load
  support, event dispatch, replay recording, accessibility helpers, and more.
- **Educational tooling** – Several games ship with hint systems, tutorials, and
  probability calculators that make the collection a useful teaching aid.

## Installation

### From PyPI

Install the published package to get the latest stable release:

```bash
pip install games-collection
```

Optional extras install the GUI stack and developer tooling:

```bash
pip install games-collection[gui]
pip install games-collection[dev]
```

### From Source

Working on the codebase or trying unreleased features? Clone the repository and
perform an editable install:

```bash
git clone https://github.com/saint2706/Games.git
cd Games
pip install -e .[dev]
```

## Running games

After installation you have several options:

- **Interactive menu** – Run `games-collection` to browse all installed titles.

- **Console scripts** – Call commands such as `games-blackjack`,
  `games-tic-tac-toe`, or `games-farkle` directly.

- **Module execution** – Use Python’s module runner when you want additional
  flags or to inspect help text:

  ```bash
  python -m card_games.blackjack --help
  python -m paper_games.connect_four --gui
  python -m dice_games.craps
  ```

Many games accept a `--gui` flag to launch graphical interfaces. PyQt5 is the primary GUI framework, with Tkinter available as a fallback. You can select a specific framework with `--gui-framework pyqt5` or `--gui-framework tkinter`.

## Repository layout

```text
card_games/      Card-based titles such as Blackjack, Poker, Uno, and Hearts
paper_games/     Board and pencil games including Chess, Sudoku, and Yahtzee
dice_games/      Dice-driven experiences like Craps and Farkle
logic_games/     Puzzle boxes such as Sokoban and Minesweeper
word_games/      Vocabulary challenges including Crossword and Trivia
common/          Shared engines, AI strategies, GUIs, persistence, accessibility
scripts/         Launchers registered as console entry points
docs/            Sphinx documentation (rewritten from scratch)
examples/        Sample integrations and automation snippets
tests/           Automated test suite mirroring the package structure
```

## Development workflow

1. Install dependencies with `pip install -e .[dev]`.
1. Format code with `black .` and `ruff check --fix .` (line length 160).
1. Run static analysis using `mypy .` and, optionally, `radon cc ...`.
1. Execute the full test suite: `pytest` or `pytest --cov`. Fixtures live under
   `tests/fixtures`.
1. Update documentation in `docs/` and add entries to `CHANGELOG.md` for notable
   changes.

Pre-commit hooks (`pre-commit install`) help keep commits consistent.

## Documentation

This README provides a high-level summary. Detailed user and developer guides
live in the [Sphinx documentation](docs/README.md). Build the HTML site with:

```bash
cd docs
pip install -r requirements.txt
make html
```

Generated pages will be available in `docs/build/html/index.html`.

## Contributing

Contributions are welcome! Please open an issue or discussion to propose new
ideas, then follow the steps in [CONTRIBUTING.md](CONTRIBUTING.md). Remember to
include tests and documentation updates alongside code changes.

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for full
terms.
