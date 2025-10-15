Poker Tutorial
==============

Getting Started with Texas Hold'em
-----------------------------------

This tutorial will guide you through playing poker in this collection, from basic
gameplay to advanced features like tournaments and statistics tracking.

Basic Gameplay
--------------

Starting Your First Game
~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest way to start a poker game is:

.. code-block:: bash

   python -m card_games.poker

This starts a game with default settings:

* Medium difficulty AI opponents
* 5 rounds
* No-limit betting
* Texas Hold'em variant

Customizing Your Game
~~~~~~~~~~~~~~~~~~~~~

You can customize many aspects of the game:

.. code-block:: bash

   # Change difficulty level
   python -m card_games.poker --difficulty Hard

   # Play more rounds
   python -m card_games.poker --rounds 10

   # Use a specific random seed for reproducibility
   python -m card_games.poker --seed 12345

Understanding Difficulty Levels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The game offers five difficulty levels:

* **Very Easy**: Bots make frequent mistakes and play passively
* **Easy**: Bots play loosely with moderate mistakes
* **Medium**: Balanced gameplay with occasional mistakes
* **Hard**: Tight, aggressive play with few mistakes
* **Insane**: Near-perfect play with maximum aggression

Game Variants
-------------

Texas Hold'em (Default)
~~~~~~~~~~~~~~~~~~~~~~~

Classic poker where each player receives 2 hole cards:

.. code-block:: bash

   python -m card_games.poker --variant texas-holdem

**Key Rules:**

* Each player gets 2 private hole cards
* 5 community cards are dealt (3 on flop, 1 on turn, 1 on river)
* Make the best 5-card hand using any combination of hole and community cards
* Four betting rounds: pre-flop, flop, turn, river

Omaha Hold'em
~~~~~~~~~~~~~

A variant where players receive 4 hole cards:

.. code-block:: bash

   python -m card_games.poker --variant omaha

**Key Rules:**

* Each player gets 4 private hole cards
* Must use exactly 2 hole cards and 3 community cards
* More action and bigger pots due to stronger hands

Betting Structures
------------------

No-Limit (Default)
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -m card_games.poker --limit no-limit

Players can bet any amount up to their entire chip stack.

Pot-Limit
~~~~~~~~~

.. code-block:: bash

   python -m card_games.poker --limit pot-limit

Maximum bet is the current pot size. Popular in Omaha.

Fixed-Limit
~~~~~~~~~~~

.. code-block:: bash

   python -m card_games.poker --limit fixed-limit

Bets are fixed at predetermined amounts. Good for beginners.

Tournament Mode
---------------

Playing a Tournament
~~~~~~~~~~~~~~~~~~~~

Tournament mode features increasing blinds:

.. code-block:: bash

   python -m card_games.poker --tournament --rounds 20

**Tournament Features:**

* Blinds automatically increase every few hands
* More strategic depth as stack sizes change
* Elimination when players run out of chips
* Winner takes all

Configuring Blind Increases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Customize how often blinds increase:

.. code-block:: bash

   python -m card_games.poker --tournament --blind-schedule 5

This increases blinds every 5 hands instead of the default.

Statistics and Analysis
-----------------------

Viewing Statistics
~~~~~~~~~~~~~~~~~~

After each game, you can review comprehensive statistics:

* Hands won and lost
* Showdown win rate
* Fold frequency
* Net profit/loss
* Aggression metrics

Statistics are automatically saved to JSON files in your game directory for later analysis.

Hand History
~~~~~~~~~~~~

Every game creates a detailed hand history file with:

* Complete action sequences
* Community cards dealt
* Final showdowns
* Pot distributions

These files are saved in the ``hand_histories/`` directory.

GUI Mode
--------

Starting the GUI
~~~~~~~~~~~~~~~~

For a visual poker experience:

.. code-block:: bash

   python -m card_games.poker --gui

**GUI Features:**

* Visual card representations
* Click-based betting controls
* Action log showing all moves
* Player chip stacks and pot display
* Animated card dealing

Combining Options
~~~~~~~~~~~~~~~~~

You can combine GUI with other options:

.. code-block:: bash

   # GUI with tournament mode
   python -m card_games.poker --gui --tournament

   # GUI with Omaha variant
   python -m card_games.poker --gui --variant omaha --difficulty Hard

Understanding the AI
--------------------

How Bots Make Decisions
~~~~~~~~~~~~~~~~~~~~~~~~

The poker bots use a combination of:

1. **Monte Carlo Simulation**: Estimates win probability by simulating random outcomes
2. **Position Awareness**: Adjusts strategy based on dealer button position
3. **Opponent Modeling**: Tracks betting patterns to detect bluffs
4. **Pot Odds**: Calculates whether calls are mathematically justified

Bot Personalities
~~~~~~~~~~~~~~~~~

Each difficulty level creates distinct playing styles:

* **Loose-Passive**: Calls often, rarely raises (Easy)
* **Tight-Aggressive**: Selective starting hands, aggressive betting (Hard)
* **Loose-Aggressive**: Plays many hands with heavy betting (Insane)

Advanced Topics
---------------

Hand Evaluation
~~~~~~~~~~~~~~~

The engine uses a sophisticated hand ranking system that correctly handles:

* High card
* One pair
* Two pair
* Three of a kind
* Straight
* Flush
* Full house
* Four of a kind
* Straight flush
* Royal flush

You can test hand evaluation directly:

.. code-block:: bash

   python -m card_games.poker.poker_hand_evaluator As Kh Qd Jc Ts

Tips and Strategy
-----------------

For Beginners
~~~~~~~~~~~~~

1. **Start with Fixed-Limit**: Easier to manage your bankroll
2. **Play Tight**: Only play strong starting hands
3. **Watch Your Position**: Play more hands when dealer button is close
4. **Learn Pot Odds**: Understand when calls are profitable

For Advanced Players
~~~~~~~~~~~~~~~~~~~~

1. **Study the AI**: Note how bots adjust to your play style
2. **Use Tournament Mode**: Tests your ability to adjust to changing dynamics
3. **Try Different Variants**: Omaha requires different strategy than Hold'em
4. **Analyze Hand Histories**: Review your decisions to improve

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Game runs too slowly**
   Try reducing the number of Monte Carlo simulations the AI uses

**GUI doesn't start**
   Ensure tkinter is installed (``python -m tkinter`` should open a window)

**Bots seem too easy/hard**
   Adjust the difficulty level or try tournament mode for more challenge

Next Steps
----------

* Try the :doc:`bluff_tutorial` for a different card game
* Read the :doc:`../architecture/poker_architecture` for implementation details
* Explore the :doc:`../examples/poker_examples` for code samples
