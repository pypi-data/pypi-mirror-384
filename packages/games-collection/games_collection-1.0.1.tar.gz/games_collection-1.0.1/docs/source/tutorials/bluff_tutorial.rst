Bluff (Cheat) Tutorial
======================

Getting Started with Bluff
---------------------------

Bluff (also known as Cheat or "I Doubt It") is a card game of deception where players
must bluff their way to victory by claiming to play cards they may not actually have.

Basic Gameplay
--------------

Starting Your First Game
~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest way to start:

.. code-block:: bash

   python -m card_games.bluff

This starts with default settings:

* Noob difficulty (1 bot opponent)
* 5 rounds
* 1 deck of cards

How to Play
~~~~~~~~~~~

1. **Making a Claim**: On your turn, play a card face-down and claim what rank it is
2. **Challenging**: Other players can challenge your claim if they think you're lying
3. **Resolution**:

   * If the challenge is correct (you lied), you take the pile
   * If the challenge is wrong (you told truth), challenger takes the pile

4. **Winning**: First player to empty their hand wins, or player with fewest cards after all rounds

Difficulty Levels
-----------------

The game offers five difficulty levels that change the number of bots, decks, and AI behavior:

Noob
~~~~

.. code-block:: bash

   python -m card_games.bluff --difficulty Noob

* 1 bot opponent
* 1 deck
* Bots are cautious and rarely bluff
* Good for learning the game

Easy
~~~~

.. code-block:: bash

   python -m card_games.bluff --difficulty Easy

* 2 bot opponents
* 1 deck
* Bots use light deception
* Balanced gameplay

Medium
~~~~~~

.. code-block:: bash

   python -m card_games.bluff --difficulty Medium

* 2 bot opponents
* 2 decks (more cards, more chaos)
* Bots balance bluffing and challenging
* Standard gameplay

Hard
~~~~

.. code-block:: bash

   python -m card_games.bluff --difficulty Hard

* 3 bot opponents
* 2 decks
* Bots bluff boldly and challenge aggressively
* Challenging gameplay

Insane
~~~~~~

.. code-block:: bash

   python -m card_games.bluff --difficulty Insane

* 4 bot opponents
* 3 decks
* Bots lie constantly and police rivals
* Maximum chaos!

Customizing Your Game
---------------------

Number of Rounds
~~~~~~~~~~~~~~~~

Control how many rounds the game lasts:

.. code-block:: bash

   # Short game (3 rounds)
   python -m card_games.bluff --rounds 3

   # Long game (10 rounds)
   python -m card_games.bluff --rounds 10

Random Seeds
~~~~~~~~~~~~

Use seeds for reproducible games:

.. code-block:: bash

   python -m card_games.bluff --seed 42

This ensures the same card distribution every time, useful for testing strategies.

GUI Mode
--------

Starting the GUI
~~~~~~~~~~~~~~~~

For a visual experience, the ``--gui`` flag launches the PyQt5 interface (it
automatically falls back to the classic Tkinter window if PyQt5 is not
installed):

.. code-block:: bash

   python -m card_games.bluff --gui

**PyQt5 GUI Highlights:**

* Rich text log rendered with Qt's ``QTextEdit``
* Interactive card selection powered by button groups
* Scoreboard table that tracks truths, lies, and challenge records
* ``QMessageBox`` prompts for confirming claims and deciding challenges
* Smooth turn transitions handled by ``QTimer.singleShot``

Combining GUI with Options
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # GUI with hard difficulty
   python -m card_games.bluff --gui --difficulty Hard

   # GUI with custom rounds
   python -m card_games.bluff --gui --rounds 8 --seed 123

Understanding the AI
--------------------

Bot Decision Making
~~~~~~~~~~~~~~~~~~~

Bots use several factors to decide:

1. **Hand Composition**: More likely to lie if they don't have the claimed card
2. **Pile Size**: More willing to lie for smaller piles (less risk)
3. **Opponent History**: Track who has been caught lying recently
4. **Challenge Threshold**: Varies by difficulty - harder bots challenge more

Bot Personalities
~~~~~~~~~~~~~~~~~

Each difficulty creates distinct personalities:

* **Cautious** (Noob): Rarely bluffs, only challenges obvious lies
* **Balanced** (Easy/Medium): Mix of honest play and deception
* **Aggressive** (Hard/Insane): Frequent bluffs and challenges

Game Flow
---------

Turn Structure
~~~~~~~~~~~~~~

Each turn follows this sequence:

1. Current player sees their hand
2. Player chooses a card to play
3. Player claims what rank they're playing
4. All other players can choose to challenge
5. If challenged, card is revealed:

   * Liar takes the pile
   * Truthful player gives pile to challenger

6. Play continues to next player

Round Completion
~~~~~~~~~~~~~~~~

A round ends when:

* One player empties their hand (they win immediately)
* All players have had equal turns (player with fewest cards wins)

Match Completion
~~~~~~~~~~~~~~~~

After all rounds:

* Player with most round wins is declared overall winner
* Statistics are displayed for all players

Strategy Tips
-------------

For Beginners
~~~~~~~~~~~~~

1. **Start Honest**: Build credibility before bluffing
2. **Small Bluffs First**: Lie when the pile is small
3. **Track the Deck**: Remember what ranks have been played
4. **Watch Patterns**: Notice when bots are more likely to lie

For Advanced Players
~~~~~~~~~~~~~~~~~~~~

1. **Psychological Warfare**: Mix up your patterns to confuse bots
2. **Pile Management**: Sometimes lie to avoid taking a big pile
3. **Risk Assessment**: Calculate odds based on cards remaining
4. **Adaptive Play**: Adjust strategy based on bot personalities

Advanced Features
-----------------

Challenge Dynamics
~~~~~~~~~~~~~~~~~~

The game supports:

* Multiple challenges per claim
* First challenger gets priority
* Pile goes to the appropriate player based on outcome

Statistics Tracking
~~~~~~~~~~~~~~~~~~~

After each game, see:

* Total claims made
* Successful bluffs
* Caught bluffs
* Challenge accuracy
* Round wins

Event Log
~~~~~~~~~

In GUI mode, the event log shows:

* All player actions
* Challenge outcomes
* Pile transfers
* Round results

Code Examples
-------------

Programmatic Usage
~~~~~~~~~~~~~~~~~~

You can use the Bluff engine in your own code:

.. code-block:: python

   from card_games.bluff.bluff import BluffGame, DifficultyLevel

   # Create a game
   game = BluffGame(
       num_players=4,
       num_decks=2,
       difficulty=DifficultyLevel.MEDIUM,
       rounds=5
   )

   # Start the game
   game.start()

   # Make moves
   game.play_card(card_index=0, claimed_rank='A')

   # Challenge a claim
   game.challenge(challenger_index=1)

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Game feels too easy/hard**
   Try adjusting the difficulty level

**Can't keep track of cards**
   Use the GUI mode for visual feedback

**Want faster games**
   Reduce the number of rounds

**Bots seem predictable**
   Try different difficulty levels - each has unique behavior

Next Steps
----------

* Try the :doc:`poker_tutorial` for a more strategic card game
* Read the :doc:`../architecture/bluff_architecture` for implementation details
* Explore the :doc:`../examples/bluff_examples` for advanced usage
