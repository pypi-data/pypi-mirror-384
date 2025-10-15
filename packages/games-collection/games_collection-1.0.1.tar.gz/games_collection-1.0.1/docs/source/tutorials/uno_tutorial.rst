Uno Tutorial
============

Getting Started with Uno
-------------------------

Play the classic card game Uno with AI opponents featuring different personalities
and strategies. Includes authentic rules, wild cards, stacking, and more.

Basic Gameplay
--------------

Starting Your First Game
~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest way to start:

.. code-block:: bash

   python -m card_games.uno

Default settings:

* 4 total players (you + 3 bots)
* Balanced bot difficulty
* Standard Uno rules

How to Play
~~~~~~~~~~~

1. **Starting Hand**: Each player receives 7 cards
2. **Taking Turns**: Play a card that matches the color or number of the top card
3. **Special Cards**:

   * **Skip**: Next player loses their turn
   * **Reverse**: Direction of play reverses
   * **Draw Two**: Next player draws 2 cards
   * **Wild**: Change the active color
   * **Wild Draw Four**: Change color and next player draws 4 cards

4. **UNO Call**: When you have one card left, you must call "UNO"
5. **Winning**: First player to empty their hand wins

Customizing Your Game
---------------------

Number of Players
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Play with 2-8 total players
   python -m card_games.uno --players 6 --bots 5

   # Just you and one bot
   python -m card_games.uno --players 2 --bots 1

Bot Difficulty
~~~~~~~~~~~~~~

Choose from different bot personalities:

.. code-block:: bash

   # Easy bots
   python -m card_games.uno --bot-skill easy

   # Balanced bots (default)
   python -m card_games.uno --bot-skill balanced

   # Aggressive bots
   python -m card_games.uno --bot-skill aggressive

**Bot Personalities:**

* **Easy**: Play conservatively, rarely use special cards strategically
* **Balanced**: Mix of strategy and random play
* **Aggressive**: Maximize use of action cards and Wild +4s

Random Seeds
~~~~~~~~~~~~

For reproducible games:

.. code-block:: bash

   python -m card_games.uno --seed 2024

GUI Mode
--------

Starting the GUI
~~~~~~~~~~~~~~~~

For a visual experience:

.. code-block:: bash

   python -m card_games.uno --gui

**GUI Features:**

* Color-coded card display
* Click-based card selection
* UNO button for declarations
* Event log showing all actions
* Card counts for all players

Combining Options
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # GUI with aggressive bots
   python -m card_games.uno --gui --bot-skill aggressive

   # GUI with more players
   python -m card_games.uno --gui --players 6 --bots 5

Game Rules
----------

Card Types
~~~~~~~~~~

**Number Cards (0-9)**: Four colors - Red, Blue, Green, Yellow

**Action Cards:**

* **Skip**: Next player loses their turn
* **Reverse**: Reverses play direction (clockwise ↔ counterclockwise)
* **Draw Two (+2)**: Next player draws 2 cards and loses their turn

**Wild Cards:**

* **Wild**: Play on any card, choose the next color
* **Wild Draw Four (+4)**: Play on any card, choose color, next player draws 4

Card Stacking
~~~~~~~~~~~~~

The game supports stacking Draw cards:

* If someone plays a Draw Two, you can play another Draw Two
* Penalty accumulates and passes to next player
* Same with Wild Draw Four cards
* Must match card type (can't stack +2 on +4)

Wild Draw Four Challenge
~~~~~~~~~~~~~~~~~~~~~~~~

When someone plays Wild Draw Four:

* You can challenge if you think they had a legal play
* If challenge succeeds: They draw 4 cards instead
* If challenge fails: You draw 6 cards instead
* Challenges add strategy and risk

UNO Declaration
~~~~~~~~~~~~~~~

**Critical Rule:**

* When you play your second-to-last card, you must declare "UNO"
* If you forget, any player can call you out
* Penalty: Draw 2 cards
* In GUI mode, click the "UNO" button

Strategy Guide
--------------

For Beginners
~~~~~~~~~~~~~

1. **Save Wild Cards**: Use them when you really need them
2. **Match Colors First**: Try to play number cards before action cards
3. **Watch Opponents**: Note when they're low on cards
4. **Call UNO**: Never forget to call UNO when you have one card!
5. **Color Choice**: Choose colors you have multiple cards of

For Advanced Players
~~~~~~~~~~~~~~~~~~~~

1. **Action Card Timing**: Save Skips and Reverses to protect your UNO
2. **Wild Draw Four**: Only use when you have no legal plays (or you risk a challenge)
3. **Card Counting**: Track which colors have been played heavily
4. **Bluffing**: Sometimes playing a Wild Draw Four illegally can work
5. **Defensive Play**: Use Reverses to skip multiple players in direction changes

Bot Behavior
------------

Understanding AI
~~~~~~~~~~~~~~~~

Bots use different strategies based on skill level:

**Easy Bots:**

* Play first legal card
* Random color choices on Wilds
* Rarely challenge Wild Draw Fours
* Don't strategically use action cards

**Balanced Bots:**

* Consider card colors before playing
* Sometimes save action cards
* Occasionally challenge suspicious Wild Draw Fours
* Mix of strategic and random play

**Aggressive Bots:**

* Maximize action card usage
* Strategic color choices (based on hand composition)
* Frequently challenge Wild Draw Fours
* Play to disrupt opponents

Special Features
----------------

Sound Effects (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~

With pygame installed:

.. code-block:: bash

   pip install pygame
   python -m card_games.uno --gui

Add your own sound files to ``card_games/uno/sounds/`` for:

* Card play sounds
* Wild card sounds
* Draw card sounds
* UNO call sounds
* Win/loss sounds

See ``card_games/uno/sounds/README.md`` for details.

Statistics Tracking
~~~~~~~~~~~~~~~~~~~

After each game:

* Rounds won
* Cards played
* Special cards used
* UNO penalties incurred
* Challenge success rate

Code Examples
-------------

Programmatic Usage
~~~~~~~~~~~~~~~~~~

Use the Uno engine in your code:

.. code-block:: python

   from card_games.uno.uno import UnoGame

   # Create a game
   game = UnoGame(
       num_players=4,
       bot_skill='balanced'
   )

   # Start the game
   game.start()

   # Play a card
   game.play_card(card_index=0, chosen_color='red')

   # Draw a card
   game.draw_card()

   # Call UNO
   game.call_uno()

Creating Custom Bots
~~~~~~~~~~~~~~~~~~~~

Extend the bot AI:

.. code-block:: python

   from card_games.uno.uno import UnoBot

   class MyCustomBot(UnoBot):
       def choose_card(self, valid_cards):
           # Your custom logic here
           return self.choose_best_card(valid_cards)

       def choose_wild_color(self):
           # Your color selection logic
           return self.count_colors_in_hand().most_common(1)[0][0]

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Forgot to call UNO**
   Be more vigilant! Set a reminder, or use GUI mode with the UNO button

**Wild Draw Four challenges**
   Only play +4 when you have no legal plays to avoid challenges

**Too many players**
   Game can slow with 8 players - try 4-5 for optimal pace

**GUI cards too small**
   The GUI adapts to screen size, but many players means smaller cards

**Bots too predictable**
   Try different difficulty levels for varied gameplay

Advanced Topics
---------------

House Rules (Not Implemented)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Common house rules not yet supported:

* Jump-in (play same card out of turn)
* Seven-O (7 swaps hands, 0 rotates hands)
* Progressive Uno (play multiple cards of same number)

These may be added in future versions.

Tournament Mode
~~~~~~~~~~~~~~~

For competitive play:

1. Play multiple games
2. Track overall wins
3. Maintain statistics across games
4. Determine ultimate champion

Team Play
~~~~~~~~~

Not currently supported but possible future feature:

* 2v2 or 3v3 teams
* Partners sit across from each other
* Combined scoring

Next Steps
----------

* Try the :doc:`bluff_tutorial` for another deception-based card game
* Read the :doc:`../architecture/uno_architecture` for implementation details
* Explore the :doc:`../examples/uno_examples` for advanced usage
* Check out ``card_games/uno/FEATURES.md`` for complete feature list
