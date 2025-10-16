# Canasta Gameplay Guide

This guide summarises the rules and controls implemented by the Canasta package. It complements the in-repo README and serves as a quick reference while playing via the CLI or GUI front ends.

## Rules Overview

- **Players and teams**: Four players compete in two partnerships (North/South vs East/West). Teammates share melds and scores.
- **Deck**: Two standard decks plus four jokers (108 cards total). Jokers and twos are wild.
- **Dealing**: Each player receives 11 cards. One card starts the discard pile; the remainder forms the stock.
- **Melds**: Melds contain at least three cards of the same rank. Wild cards can never outnumber natural cards and no meld may contain more than three wilds. A meld with seven cards is a canasta; pure canastas (no wilds) award an extra 500 points, mixed canastas award 300.
- **Minimum meld values**: Before laying their first meld in a round, a partnership must meet a point threshold based on cumulative score: 50 (0–1495), 90 (1500–2995), 120 (3000–4995), 150 (5000+).
- **Frozen discard pile**: Discarding a wild card or black three freezes the pile. To take a frozen pile, a player must hold two natural cards that match the top discard and immediately meld that rank.
- **Going out**: A partnership may go out only after forming at least one canasta and clearing both hands. Going out yields a 100 point bonus (200 if concealed).
- **Scoring**: Count the values of melded cards, add bonuses, and subtract any cards left in hand. Jokers and twos are worth 50 and 20 points respectively; aces are 20, eights through kings are 10, and fours through sevens are 5.

## CLI Controls

1. Start the game with `python -m card_games.canasta.cli`.
2. On your turn choose whether to draw from the stock or discard pile.
3. Enter card indices to lay melds; blank input skips melding.
4. Choose a card to discard. If your team has a canasta and both hands are empty, you may elect to go out.

## GUI Controls

### Tkinter

- Launch with `python -m card_games.canasta.gui`.
- Buttons drive the flow: **Draw Stock**, **Take Discard**, **Lay Meld**, **Discard**, **Go Out**, and **Next Turn**.
- Use the hand list to select cards for melding or discarding. Melds appear in the "Team Melds" pane and the log tracks draw/discard events.

### PyQt

- Launch with `python -m card_games.canasta.gui_pyqt` (requires PyQt5).
- Functionality mirrors the Tkinter GUI with the same action buttons and selection workflow.
- A log pane records actions and scoring breakdowns when the round ends.

Enjoy strategising your way to 5000 points!
