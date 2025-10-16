# Mastermind

Code-breaking game with colored pegs and logical deduction.

## How to Play

1. Computer creates a secret code of colored pegs
1. Make guesses to find the code
1. Get feedback: ⚫ black peg (right color, right position), ⚪ white peg (right color, wrong position)
1. Use deduction to crack the code within 10 guesses

**Run the game**: `python -m paper_games.mastermind`

## Features

- 6 colors available
- Configurable code length (2-8)
- Accurate feedback system
- Strategic guessing required

## Strategy

- Start with diverse colors
- Use black pegs to lock in positions
- Eliminate possibilities systematically
