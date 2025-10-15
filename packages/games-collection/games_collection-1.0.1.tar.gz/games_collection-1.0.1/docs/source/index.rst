Card & Paper Games Documentation
=================================

Welcome to the comprehensive documentation for the Card & Paper Games project!
This collection includes implementations of classic card games (Poker, Blackjack,
Bluff/Cheat, Uno) and paper-and-pencil games (Tic-Tac-Toe, Hangman, Battleship,
Dots and Boxes, and more).

.. toctree::
   :maxdepth: 2
   :caption: Getting Started:

   tutorials/index

.. toctree::
   :maxdepth: 2
   :caption: Architecture & Design:

   architecture/index

.. toctree::
   :maxdepth: 2
   :caption: Code Examples:

   examples/index

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api/card_games
   api/paper_games

.. toctree::
   :maxdepth: 1
   :caption: Contributing:

   contributing

Quick Start
-----------

Install the games package:

.. code-block:: bash

   git clone https://github.com/saint2706/Games.git
   cd Games
   pip install -r requirements.txt

Play your first game:

.. code-block:: bash

   # Play Poker
   python -m card_games.poker --difficulty Medium --rounds 5

   # Play Bluff with GUI
   python -m card_games.bluff --gui

   # Play Tic-Tac-Toe
   python -m paper_games.tic_tac_toe

Features
--------

* **Card Games**: Texas Hold'em Poker, Blackjack, Bluff/Cheat, Uno
* **Paper Games**: Tic-Tac-Toe, Battleship, Hangman, Dots and Boxes, Nim, Unscramble
* **AI Opponents**: Multiple difficulty levels with different personalities
* **GUI Support**: PyQt5 interfaces (with Tkinter fallbacks during migration)
* **CLI Support**: Rich command-line interfaces with colorful output
* **Extensible**: Well-documented code makes it easy to add new games

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
