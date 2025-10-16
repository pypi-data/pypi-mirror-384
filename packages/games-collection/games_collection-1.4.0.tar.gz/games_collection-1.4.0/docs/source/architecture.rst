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
  * ``common.gui_base`` and ``common.gui_base_pyqt`` – Foundations for Tkinter
    and PyQt graphical front ends.
  * ``common.architecture`` – Infrastructure for events, persistence, replay
    capture, plugin discovery, and user settings.
  * ``common.educational`` – Helper classes for hint systems and explanatory
    overlays.

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
