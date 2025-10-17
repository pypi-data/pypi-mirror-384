# Tutorial Catalogue Overview

The tutorial system automatically creates guided learning paths for every game
listed in `docs/source/games_catalog.rst`. When the project starts up the
registry parses the catalogue, locates each package's documentation, and builds
step-by-step lessons that link back to the appropriate README or rulebook.

## Key Features

- **Dynamic discovery** – Adding a game to the catalogue instantly exposes a
  tutorial entry without hand-written boilerplate.
- **Documentation-backed steps** – Each tutorial references the module's
  README or a shared guide so players can cross-check rules while they play.
- **Difficulty and goals** – Learners can pick a difficulty level and focus on
  mechanics, scoring, or strategy topics when launching from the unified
  launcher.
- **Strategy support** – Every tutorial registers a strategy tip provider and a
  lightweight probability calculator that surfaces in the interactive session.

## Using the Tutorials

Launch `python -m scripts.launcher` and choose **Tutorial catalogue** from the
Educational Tools section. The browser lets players:

1. Browse all tutorials grouped by game category.
1. Read a summary that highlights the key documentation for the game.
1. Select a difficulty level and optional learning goal.
1. Start an interactive tutorial session that prints each step, provides hints,
   and performs automatic sample moves when the engine supports it.

For games without an auto-instantiable engine, the launcher prints the ordered
steps so players can follow along while running the normal CLI or GUI.

## Extending the Catalogue

1. Add the new module to `docs/source/games_catalog.rst`.
1. Ensure the package ships with a README or dedicated rules document.
1. Optional: expose a `GameEngine` subclass with sensible defaults so the
   interactive session can run moves automatically.
1. Run the test suite (`pytest tests/test_tutorial_catalog.py`) to confirm the
   registry picked up the new entry and that strategy tips are available.

No additional registration code is required—the system derives metadata and
creates tutorial classes on the fly.
