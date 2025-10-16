Player Guide
============

This chapter explains how to install the Games Collection, explore the catalogue,
and launch matches. No Python knowledge is required for the basics—only a recent
Python interpreter or a packaged release.

Installation options
--------------------

1. **Install from PyPI** (recommended for most players)::

       pip install games-collection

   This installs console entry points such as ``games-blackjack`` and
   ``games-tic-tac-toe`` that start games immediately.

2. **Run from a source checkout** (handy when tracking the latest commits)::

       git clone https://github.com/saint2706/Games.git
       cd Games
       pip install -e .

   The editable installation exposes the same entry points while allowing you to
   modify the code locally.

3. **Optional GUI extras** – install PyQt5 and pygame for richer graphical
   interfaces::

       pip install games-collection[gui]

Launching a game
----------------

*From the command line*
    Every packaged game registers a console script. Example commands:

    * ``games-blackjack`` – launch the Blackjack card table
    * ``games-tic-tac-toe`` – start a quick board duel
    * ``games-farkle`` – roll the dice from your terminal

*Using Python modules*
    Prefer explicit module execution or want to inspect command-line options?
    Run games with ``python -m``::

       python -m card_games.blackjack --help
       python -m paper_games.connect_four --mode ai
       python -m dice_games.craps

GUI support
-----------

Most titles ship with a Tkinter-based GUI that can be triggered with a flag::

    python -m card_games.blackjack --gui

PyQt5 implementations are gradually rolling out. When available they can be
selected explicitly::

    python -m paper_games.dots_and_boxes --gui-framework pyqt5

Not every game features a GUI yet; consult the :doc:`games_catalog` for the
latest status.

Personalised recommendations
----------------------------

When you open the launcher or finish a match you will see a shortlist of new
games to explore. The system analyses your playtime, favourite mechanics, and
community challenge trends to surface relevant suggestions. Each entry includes
a short explanation such as ``You enjoy trick-taking games; try Spades`` so you
understand why it appears. Accepting a suggestion sharpens future picks, while
dismissing it quietly moves that title further down the queue.

Double-deck Pinochle
--------------------

The new :mod:`card_games.pinochle` package models the classic partnership
variant with a full double-deck shoe. Launch it from the terminal (it will try
the PyQt GUI, then Tk, before falling back to text mode)::

    python -m card_games.pinochle

Prefer the command line immediately? Use the ``--cli`` flag. The interface
guides all four players through three distinct phases:

* **Bidding** – Each seat commits to a value (minimum 250) or passes. The
  interface enforces incremental bidding so the auction escalates cleanly.
* **Meld** – The winning bidder picks the trump suit and the program tallies
  runs, marriages, pinochles, arounds, and dix bonuses using the printed
  breakdown.
* **Trick play** – Players follow suit by choosing cards from an enumerated
  list; trick summaries reveal the winning card combination after every round.

Graphical front-ends mirror the same flow. Force a specific backend with
``--gui-framework tk`` or ``--gui-framework pyqt`` when you want to skip the
auto-detection logic.

Both GUIs share the enhanced theme, sound hooks, and keyboard shortcuts common
to the card table interfaces while surfacing dedicated panels for bids, melds,
and trick history.

Saving progress
---------------

Games that support persistence expose a ``--save`` flag (or prompt from within
the interface). Save files are stored in the ``~/.games_collection`` directory
by default. Load them later with ``--load`` or through the in-game menus. The
shared persistence helpers live in :mod:`common.persistence` for developers who
want to add support to new titles.

Multiplayer and AI
------------------

* **Local multiplayer** – Pass-and-play modes are available in titles such as
  Connect Four, Checkers, and Uno.
* **AI opponents** – Many games ship with multiple difficulty settings. Use the
  ``--difficulty`` option (when supported) to adjust the challenge curve. The
  AI engines typically rely on heuristics or minimax search depending on game
  complexity.

Next steps
----------

Browse the :doc:`games_catalog` for the full list of experiences or continue to
:doc:`developer_guide` if you plan to tinker with the codebase.
