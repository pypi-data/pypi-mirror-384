# Spades

Partnership trick-taking game where spades are always trump. Players bid on tricks and partnerships work together to
make their combined bid.

## Launching the Game

- **Graphical interface (default):**

  ```bash
  python -m card_games.spades [--name "Your Name"]
  ```

  The GUI opens with a dark theme and high-contrast accessibility aids enabled. Use the spinner in the bidding panel to
  enter your bid, click **Submit bid**, and then play highlighted cards from your hand when it is your turn. Keyboard
  shortcuts are available for quick navigation:

  - `Ctrl+N`: Start the next round after reviewing the breakdown screen.
  - `Ctrl+L`: Move keyboard focus to the round log for screen readers.
  - `F1`: Display an overview of all shortcuts managed by the shared GUI framework.

  The layout includes:

  - A bidding panel that records human and AI bids in order and disables invalid actions automatically.
  - Partnership score and bag trackers that update as soon as a round finishes.
  - A trick display that lists the cards currently on the table so you can track suit order and trump plays.
  - A detailed round log plus a breakdown pane summarising bids, tricks, and scoring once a hand is complete.

- **Command-line interface:**

  ```bash
  python -m card_games.spades --cli
  ```

  The CLI is also selected automatically if Tkinter is unavailable. It provides the same AI behaviour but requires you
  to type bids and card codes directly.

## Game Rules

- Four players in two partnerships (North-South vs East-West)
- Each player is dealt 13 cards
- **Opening lead**: The player holding the 2♣ leads the first trick of the rubber
- **Bidding phase**: Each player bids 0-13 tricks (0 is "nil", blind nil is supported for higher stakes)
- Spades are always trump and cannot be led until broken (unless a player has nothing but spades)
- Must follow suit if possible
- Partnerships combine the bids of their non-nil players and total tricks won
- Making the combined bid scores 10 points per trick bid
- Overtricks (bags) give 1 point each but 10 bags incur a 100-point penalty
- Nil bid: +100 if successful, -100 if failed (blind nil doubles these values)
- First partnership to 500 points wins, with ties broken by the higher score

## Features

- Partnership mechanics (0&2 vs 1&3) with persistent team scores and bag tracking
- Nil and blind-nil bid handling with automatic logging of bidding history
- Trick history preserved for post-hand analysis and next-round leader selection
- Enforced opening 2♣ lead and authentic spade-breaking restrictions
- AI bidding and play heuristics that respect the new rule set
- CLI walkthrough showing bids, trick transcripts, and cumulative scores after every round
