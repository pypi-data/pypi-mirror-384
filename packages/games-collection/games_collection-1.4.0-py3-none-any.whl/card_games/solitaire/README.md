# Solitaire (Klondike)

Classic single-player patience game where the goal is to build four foundation piles from Ace to King, one for each
suit. This implementation mirrors modern Klondike variants, including draw-one/draw-three styles, realistic redeal
limits, Windows-style scoring, and the Vegas casino option.

## How to Play

```bash
python -m card_games.solitaire [--draw-count {1,3}] [--max-recycles N] [--scoring {standard,vegas}] [--seed SEED] [--cli]
```

By default the module launches the PyQt5 GUI when the dependency is available. Pass `--cli` to stay in the original
command-line interface; all gameplay options apply to every mode. The launcher automatically falls back to the
legacy Tkinter GUI or CLI if graphical dependencies are missing.

### GUI Highlights

- Toolbar buttons for drawing, auto-moving to the foundations, recycling the waste, and starting a fresh deal.
- Visual tableau with highlighted drop targets whenever a card or run is selected.
- Scoreboard showing score, move counts, and recycle usage in real time.

### Launch Options

- `--draw-count` – choose between drawing 1 or 3 cards from the stock (default: 3).
- `--max-recycles` – cap how many times the waste may be recycled back to the stock (defaults to `None` for draw-one and
  `3` for draw-three).
- `--scoring` – `standard` (Windows scoring with flip bonuses) or `vegas` (buy-in of -52, +5 per foundation card).
- `--seed` – provide a random seed for reproducible shuffles.
- `--cli` – force the text-mode experience when Tkinter is not desired or available.

> **GUI dependencies:** Install `pip install games-collection[gui]` (or `pip install pyqt5`) for the PyQt5 interface.
> Systems without Tkinter should install `python3-tk` (Debian/Ubuntu) or the equivalent package. macOS users should
> ensure they are running the framework build of Python.

## Game Rules

- **Tableau**: Seven piles where cards can be moved in descending order with alternating colors
- **Foundation**: Four piles (one per suit) built from Ace to King
- **Stock**: Draw pile from which you can draw cards
- **Waste**: Discard pile where drawn cards are placed

### Commands

| Command | Description |
| ------------------ | ------------------------------------------------------------------------------------------ |
| `d`, `draw` | Draw from stock into the waste (obeys draw-one/draw-three setting). |
| `r`, `reset` | Recycle the entire waste back to the stock when redeals remain. |
| `a`, `auto` | Auto-play all currently legal foundation moves (does not count towards manual move tally). |
| `s`, `stats` | Display score, move counts, and redeal usage in-line. |
| `w <dest>` | Move the top waste card (e.g., `w 0` moves to tableau column 0). |
| `<src> f` | Move the top tableau card to the matching foundation (e.g., `0 f`). |
| `<src> <dest> [n]` | Move a face-up run of `n` cards between tableau columns (e.g., `0 1 3`). |
| `h`, `help` | Show contextual help including scoring reminders. |
| `q`, `quit` | Exit the current game. |

## Features

- Draw-one and draw-three game styles with realistic redeal limits (three passes by default for draw-three).
- Standard scoring (+10 to foundations, +5 tableau flips, -15 for withdrawing from foundations) and Vegas (-52 buy-in,
  +5 per foundation card).
- Automatic foundation moves, move counting, and state summaries for CLI overlays or analytics.
- Full tableau face-up tracking so revealing a new card immediately awards the appropriate flip bonus.
- Comprehensive win detection and stock recycling logic that mirrors the behaviour of digital Klondike clients.
