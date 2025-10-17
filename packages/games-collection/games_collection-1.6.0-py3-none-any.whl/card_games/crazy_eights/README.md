# Crazy Eights Card Game

A classic shedding card game similar to Uno but using a standard deck.

## Rules

Crazy Eights is a shedding game where players try to get rid of all their cards:

1. **Setup**: Each player gets 5 cards (2 players) or 7 cards (3+ players)
1. **Gameplay**: Play a card matching the active card's rank OR suit
1. **Eights are wild**: Play an 8 to change the suit to anything you want
1. **Drawing**: If you can't play, draw up to 3 cards (or until you can play)
1. **Passing**: If still unable to play after drawing, pass your turn
1. **Winning**: First player to discard all cards wins the round
1. **Scoring**: Winner gets points for cards left in opponents' hands:
   - Eights: 50 points each
   - Face cards (J, Q, K, A): 10 points each
   - Number cards: Face value

## Running the Game

Launch the GUI (auto-detects PyQt5, then Tkinter):

```bash
python -m card_games.crazy_eights
```

Force the PyQt5 GUI:

```bash
python -m card_games.crazy_eights --gui-framework pyqt5
```

Force the legacy Tkinter GUI:

```bash
python -m card_games.crazy_eights --gui-framework tkinter
```

Run the command-line interface instead of any GUI:

```bash
python -m card_games.crazy_eights --cli
```

Specify players and names:

```bash
python -m card_games.crazy_eights --players 3 --names Alice Bob Charlie
```

Change draw limit:

```bash
python -m card_games.crazy_eights --draw-limit 5
```

Unlimited drawing (draw until you can play):

```bash
python -m card_games.crazy_eights --draw-limit 0
```

Reproducible game with seed:

```bash
python -m card_games.crazy_eights --seed 42
```

> **Note:** The GUI requires Tkinter, which is typically bundled with standard Python installations on Windows and
> macOS. Linux users may need to install `python3-tk` from their package manager. The new PyQt5 interface is preferred
> when `pyqt5` is installed (see `pip install -e ".[gui]"`).

## Features

- Support for 2-6 players
- Automatic deck reshuffling when empty
- Visual indicators for playable cards (✓)
- Hand organized by suit
- Customizable draw limit
- Score tracking across rounds
- Interactive CLI with clear prompts
- Custom player names support
- Deterministic games with seed support

## Strategy Tips

- **Save eights** for when you're stuck or want to switch to your strongest suit
- **Track which suits are being played** to predict what's safe to play
- **Count cards** to know which suits/ranks are still in play
- **Play high-value cards** first to reduce potential penalty if you lose
- **Watch opponents' draws** to guess what they don't have

## Differences from Uno

While similar in concept, Crazy Eights differs from Uno:

- Uses a standard 52-card deck (no special cards except 8s)
- No Skip, Reverse, or Draw action cards
- Only eights are wild (like Wild cards in Uno)
- Simpler rules make it easier to learn
- Traditional card deck makes it more accessible

## Architecture

The implementation follows the repository's architecture patterns:

- `game.py` - Core game engine with player and state management
- `cli.py` - Command-line interface with hand display and input handling
- `__main__.py` - Entry point with argument parsing

## Future Enhancements

Potential additions:

- Enhanced PyQt5 visuals with subtle card animations
- AI opponent with suit tracking
- Multi-round tournament mode
- Statistics tracking (win rates, average game length)
- Network multiplayer
- Custom rules (different wild cards, special actions)
- Hint system for beginners
