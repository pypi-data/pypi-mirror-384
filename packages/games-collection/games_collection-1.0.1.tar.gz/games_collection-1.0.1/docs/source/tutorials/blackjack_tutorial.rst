Blackjack Tutorial
==================

Getting Started with Blackjack
-------------------------------

Experience casino-style blackjack with realistic rules, including splits, doubles,
insurance, and dealer AI that follows standard casino protocols.

Basic Gameplay
--------------

Starting Your First Game
~~~~~~~~~~~~~~~~~~~~~~~~~

Launch the GUI version (recommended):

.. code-block:: bash

   python -m card_games.blackjack

Or start with CLI mode:

.. code-block:: bash

   python -m card_games.blackjack --cli

Default settings:

* $1000 starting bankroll
* $10 minimum bet
* 6 decks in the shoe
* Standard blackjack rules

How to Play
~~~~~~~~~~~

1. **Place Your Bet**: Enter bet amount (must be at least minimum bet)
2. **Receive Cards**: You and dealer each get 2 cards (one dealer card hidden)
3. **Make Decisions**:

   * **Hit**: Take another card
   * **Stand**: Keep your current hand
   * **Double**: Double your bet and take exactly one more card
   * **Split**: If you have a pair, split into two hands

4. **Dealer Plays**: Dealer reveals hidden card and plays by fixed rules
5. **Payouts**: Win (1:1), lose your bet, or push (tie - bet returned)

Customizing Your Game
---------------------

CLI Options
~~~~~~~~~~~

.. code-block:: bash

   # Custom starting bankroll
   python -m card_games.blackjack --cli --bankroll 500

   # Higher minimum bet
   python -m card_games.blackjack --cli --min-bet 25

   # More decks in shoe
   python -m card_games.blackjack --cli --decks 8

**Available Options:**

* ``--bankroll``: Starting money (default: $1000)
* ``--min-bet``: Minimum bet amount (default: $10)
* ``--decks``: Number of decks in shoe (default: 6)

GUI Mode Features
-----------------

Visual Interface
~~~~~~~~~~~~~~~~

The GUI provides:

* High-quality card graphics
* Animated card dealing
* Visual chip stack and pot display
* Click-based controls
* Action history log

Starting the GUI
~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -m card_games.blackjack

The GUI starts automatically unless you use ``--cli`` flag.

Game Rules
----------

Basic Rules
~~~~~~~~~~~

* **Goal**: Get closer to 21 than the dealer without going over
* **Card Values**:

  * Number cards: Face value
  * Face cards (J, Q, K): 10 points
  * Aces: 1 or 11 points (whichever is better)

* **Blackjack**: Ace + 10-value card = 21, pays 3:2
* **Bust**: Going over 21 = automatic loss

Dealer Rules
~~~~~~~~~~~~

The dealer must:

* Hit on 16 or less
* Stand on 17 or more
* Hit on soft 17 (A-6)

These are standard casino rules.

Advanced Actions
----------------

Splitting Pairs
~~~~~~~~~~~~~~~

When you have a pair (two cards of same rank):

1. You can split into two separate hands
2. Each hand gets an additional card
3. Place an equal bet on the second hand
4. Play each hand independently

**Strategy Tips:**

* Always split Aces and 8s
* Never split 5s or 10s
* Split 2s, 3s, 6s, 7s, 9s against weak dealer cards

Doubling Down
~~~~~~~~~~~~~

When you have a good hand:

1. Double your original bet
2. Receive exactly one more card
3. Cannot hit again after doubling

**Strategy Tips:**

* Double on 11 against any dealer card except Ace
* Double on 10 against dealer 2-9
* Double on 9 against dealer 3-6

Insurance
~~~~~~~~~

When dealer shows an Ace:

1. You can buy insurance (costs half your bet)
2. If dealer has blackjack, insurance pays 2:1
3. Otherwise, insurance bet is lost

**Strategy Tips:**

* Insurance is generally not recommended
* Only consider if you're counting cards (advanced)

Shoe Management
---------------

Multi-Deck Shoe
~~~~~~~~~~~~~~~

The game uses a shoe (multiple decks shuffled together):

* Default: 6 decks (312 cards)
* Shuffle indicator appears when running low
* Automatic reshuffle between hands when needed

This simulates real casino conditions.

Card Counting
~~~~~~~~~~~~~

While the game doesn't prevent counting:

* No visual count display
* Must track mentally
* Useful for learning counting systems
* True count adjusts for remaining decks

Bankroll Management
-------------------

Starting Bankroll
~~~~~~~~~~~~~~~~~

Manage your money wisely:

.. code-block:: bash

   # Conservative start
   python -m card_games.blackjack --cli --bankroll 500 --min-bet 5

   # High roller
   python -m card_games.blackjack --cli --bankroll 5000 --min-bet 100

Going Broke
~~~~~~~~~~~

When your bankroll drops below minimum bet:

* Game ends
* Final statistics displayed
* Option to start a new game

Strategy Guide
--------------

Basic Strategy
~~~~~~~~~~~~~~

Follow this basic strategy chart:

**Your Hand vs Dealer Upcard:**

* **Hard 8 or less**: Always hit
* **Hard 9**: Double on dealer 3-6, otherwise hit
* **Hard 10**: Double on dealer 2-9, otherwise hit
* **Hard 11**: Double on dealer 2-10, otherwise hit
* **Hard 12**: Stand on dealer 4-6, otherwise hit
* **Hard 13-16**: Stand on dealer 2-6, otherwise hit
* **Hard 17+**: Always stand

**Soft Hands:**

* **Soft 13-17**: Hit
* **Soft 18**: Stand on dealer 2-8, hit on 9-A
* **Soft 19+**: Always stand

Understanding Soft Hands
~~~~~~~~~~~~~~~~~~~~~~~~~

A soft hand contains an Ace counted as 11:

* A-6 = Soft 17
* Can't bust by hitting
* Becomes "hard" if Ace must count as 1

Statistics and Analysis
-----------------------

Post-Game Stats
~~~~~~~~~~~~~~~

After playing, review:

* Total hands played
* Win/loss record
* Blackjacks dealt
* Highest bankroll reached
* Final profit/loss

Learning from Results
~~~~~~~~~~~~~~~~~~~~~

Track your performance:

* Identify weak decision points
* Compare against basic strategy
* Adjust bet sizing strategy

Advanced Topics
---------------

Surrender (Not Implemented)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Standard blackjack includes surrender, where you can forfeit half your bet.
This feature may be added in future versions.

Side Bets (Not Implemented)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Common side bets like "Perfect Pairs" or "21+3" are not currently available
but could be added.

Code Examples
-------------

Programmatic Usage
~~~~~~~~~~~~~~~~~~

Use the blackjack engine in your code:

.. code-block:: python

   from card_games.blackjack.blackjack import BlackjackGame

   # Create a game
   game = BlackjackGame(
       bankroll=1000,
       min_bet=10,
       num_decks=6
   )

   # Place a bet
   game.place_bet(25)

   # Deal initial cards
   game.deal()

   # Make decisions
   game.hit()
   game.stand()
   game.double()
   game.split()

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**GUI doesn't open**
   Ensure tkinter is installed: ``python -m tkinter``

**Cards not displaying properly**
   The game uses Unicode card symbols - ensure your terminal supports UTF-8

**Minimum bet too high**
   Adjust with ``--min-bet`` flag to a lower amount

**Running out of money quickly**
   Start with higher bankroll or lower minimum bet

Tips for Success
----------------

Money Management
~~~~~~~~~~~~~~~~

1. Never bet more than 5% of bankroll per hand
2. Set win/loss limits
3. Take breaks when losing
4. Don't chase losses

Game Strategy
~~~~~~~~~~~~~

1. Learn basic strategy thoroughly
2. Avoid insurance bets
3. Always split Aces and 8s
4. Stand on 17 or higher
5. Don't make decisions based on "hunches"

Next Steps
----------

* Try the :doc:`poker_tutorial` for a game with more player interaction
* Read the :doc:`../architecture/blackjack_architecture` for implementation details
* Explore the :doc:`../examples/blackjack_examples` for code samples
