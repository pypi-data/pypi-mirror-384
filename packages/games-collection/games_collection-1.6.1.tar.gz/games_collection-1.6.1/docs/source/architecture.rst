Architecture
============

The codebase is intentionally modular so that new games can lean on a shared set
of abstractions. This section summarises the most important components.

Package layout
--------------

- ``card_games/``
- ``paper_games/``
- ``dice_games/``
- ``logic_games/``
- ``word_games/``

  Genre-specific packages. Each game lives in its own subpackage that exposes a
  ``main`` function for CLI play and, when available, GUI launchers.

- ``common/`` – Cross-cutting utilities shared by every game. Highlights
  include:

  * ``common.game_engine.GameEngine`` – Base class that standardises turn
    management, win detection, and state transitions.
  * ``common.ai_strategy`` – Strategy interfaces and heuristics used by AI
    opponents. Games can plug in their own subclasses to tailor behaviour.
  * ``common.gui_base``, ``common.gui_base_pyqt``, and ``common.gui_frameworks`` – Foundations for Tkinter, PyQt, and other graphical front ends.
  * ``common.educational`` – Helper classes for hint systems and explanatory
    overlays.
  * ``common.cli_utils`` – Utilities for creating enhanced command-line interfaces.
  * ``common.sound_manager`` – A centralized manager for in-game audio.
  * ``common.themes`` – Manages visual themes for GUI components.
  * ``common.i18n`` – Internationalization and localization utilities.
  * ``common.analytics`` and ``common.crash_reporter`` – Services for analytics and crash reporting.
  * ``common.profile`` and ``common.profile_service`` – User profile management.
  * ``common.leaderboard_service`` – A service for managing leaderboards.
  * ``common.achievements`` and ``common.achievements_registry`` – Systems for managing and tracking player achievements.
  * ``common.daily_challenges`` and ``common.challenges`` – Infrastructure for daily challenges and other game challenges.
  * ``common.tutorial_registry`` and ``common.tutorial_session`` – Systems for managing and displaying tutorials.
  * ``common.recommendation_service`` – A service for recommending games to players.
  * ``common.keyboard_shortcuts`` – A system for managing keyboard shortcuts.
  * ``common.animations`` – Utilities for creating animations.


- ``common/architecture/`` – Core infrastructure for the game engine.

  * ``events`` – A lightweight event dispatcher.
  * ``persistence`` – Helpers for saving and loading game state.
  * ``replay`` – A system for recording and replaying games.
  * ``plugin`` – A plugin system for discovering third-party games.
  * ``settings`` – A centralized manager for user preferences.
  * ``observer`` – An implementation of the observer pattern for synchronizing GUI views with engine state.

- ``scripts/`` – Entry points that glue the packages together for distribution.
  The ``games-collection`` launcher offers a curated menu of installed games.

Architectural patterns
----------------------

* **Event-driven state updates** – ``common.architecture.events`` defines a
  lightweight dispatcher so interfaces can subscribe to gameplay events without
  directly coupling to the engine.
* **Persistence and replay** – ``common.architecture.persistence`` and
  ``common.architecture.replay`` provide serialisation helpers. Games opt in by
  implementing ``to_dict``/``from_dict`` hooks or by defining command objects.
* **Plugin support** – ``common.architecture.plugin`` discovers third-party
  game packages at runtime. This keeps the main menu extendable without
  modifying the core repository.
* **Settings management** – ``common.architecture.settings`` centralises user
  preferences such as sound, difficulty, and interface layout. Games read these
  values instead of implementing their own configuration files.
* **Observer pattern** – ``common.architecture.observer`` synchronises GUI views
  with engine state changes, ensuring that board redraws react instantly to
  moves.

Extending the system
--------------------

When building a new game:

1. Create a new package under the appropriate genre directory.
2. Subclass :class:`common.game_engine.GameEngine` to model state and turns.
3. Implement CLI entry points (``__main__.py`` or ``cli.py``) and register an
   optional console script in ``pyproject.toml``.
4. Reuse the shared architecture modules instead of reinventing persistence or
   event handling.
5. Add documentation and tests that describe rules, AI behaviour, and any new
   assets required.