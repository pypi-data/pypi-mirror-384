# Canasta

This implementation models partnership Canasta played with two standard decks and four jokers. It focuses on rules that most directly impact digital play: draw and discard handling, melding restrictions, and team scoring with minimum meld requirements.

## Key Features

- Two-deck shoe with jokers and discard freezing logic
- Partnership scoring with configurable minimum meld requirements
- Validation of meld composition including wild-card limits and canasta bonuses
- Text-based interface plus Tkinter and PyQt GUIs built on the shared framework

## Running the Game

Launch the command line client:

```bash
python -m card_games.canasta.cli
```

Start the Tkinter GUI (if Tk is available):

```bash
python -m card_games.canasta.gui
```

Or the PyQt interface (requires PyQt5):

```bash
python -m card_games.canasta.gui_pyqt
```

## Rules Summary

- Each player is dealt 11 cards; the remaining stock is placed face-down with one card turned face-up to start the discard pile.
- A meld contains at least three cards of the same rank. Jokers and twos are wild but can never outnumber the natural cards.
- The discard pile becomes frozen when a wild card or black three is discarded. Picking up a frozen pile requires two natural cards that match the top discard.
- Partnerships must meet a minimum meld value based on their cumulative score before they may lay down their first meld in a round.
- Going out requires at least one canasta (seven-card meld). Going out concealed grants a larger bonus.

Consult the documentation in `docs/card_games/canasta.md` for a deeper explanation of scoring, meld management, and UI controls.
