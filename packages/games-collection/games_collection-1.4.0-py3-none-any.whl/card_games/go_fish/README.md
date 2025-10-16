# Go Fish Card Game

A classic implementation of the Go Fish card game for 2-6 players.

## Rules

Go Fish is a card game where players try to collect sets of four cards of the same rank:

1. **Setup**: Each player gets 7 cards (5 for 3+ players), remaining cards form the draw pile
1. **Gameplay**: On your turn, ask another player for cards of a specific rank you have in your hand
1. **If they have it**: They give you all cards of that rank, and you get another turn
1. **If they don't**: They say "Go Fish!" and you draw a card from the pile
1. **Lucky draw**: If you draw the rank you asked for, you get another turn
1. **Making books**: When you collect all 4 cards of a rank, you lay them down (make a "book")
1. **Winning**: Player with the most books when all cards are collected wins

## Running the Game

Launch the animated GUI (default):

```bash
python -m card_games.go_fish
```

Use the classic CLI instead:

```bash
python -m card_games.go_fish --cli
```

Explicitly request the GUI (useful after testing the CLI):

```bash
python -m card_games.go_fish --gui
```

Play with more players:

```bash
python -m card_games.go_fish --players 4
```

Use custom names:

```bash
python -m card_games.go_fish --players 3 --names Alice Bob Charlie
```

Reproducible game with seed:

```bash
python -m card_games.go_fish --seed 42
```

## Features

- Support for 2-6 players
- Automatic book detection and scoring
- Hand organized by rank for easy viewing
- Turn continuation on successful asks and lucky draws
- Comprehensive game state tracking
- Interactive CLI with clear prompts
- Polished GUI with scoreboard, grouped-hand view, and celebratory book animations
- Custom player names support
- Deterministic games with seed support

## Strategy Tips

- **Remember what other players ask for** - this tells you what they have
- **Ask for ranks you have multiple of** - increases chance of making a book
- **Pay attention to successful asks** - indicates which players have which ranks
- **Track books made** - focus on ranks still in play

## Architecture

The implementation follows the repository's architecture patterns:

- `game.py` - Core game engine with player and game state management
- `cli.py` - Command-line interface with hand display and input handling
- `gui.py` - Tkinter GUI with scoreboard, controls, and animated book celebrations
- `__main__.py` - Entry point with argument parsing and CLI/GUI launcher

## Future Enhancements

Potential additions:

- AI opponent with memory and strategy
- Statistics tracking (win rates, average books per game)
- Multiplayer network play
- Hint system for beginners
- Animation of card transfers
