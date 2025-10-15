Paper Games Tutorial
====================

Getting Started with Paper & Pencil Games
------------------------------------------

This tutorial covers all the classic paper-and-pencil games included in the collection.
Each game is quick to learn and fun to play!

Tic-Tac-Toe
-----------

Classic noughts and crosses with perfect minimax AI.

Starting the Game
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -m paper_games.tic_tac_toe

**Features:**

* Multiple board sizes (3x3, 4x4, 5x5, etc.)
* Custom win lengths
* Perfect AI opponent (minimax algorithm)
* Themed boards (emoji, ASCII art, etc.)
* Statistics tracking

Coordinate System
~~~~~~~~~~~~~~~~~

Use coordinates like chess:

* Columns: A, B, C (left to right)
* Rows: 1, 2, 3 (top to bottom)
* Example: ``A1`` is top-left, ``C3`` is bottom-right

Custom Board Sizes
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # When prompted, enter custom size
   Board size: 4
   Win length: 3  # Get 3 in a row on a 4x4 board

Ultimate Tic-Tac-Toe
~~~~~~~~~~~~~~~~~~~~

Play the advanced variant:

.. code-block:: bash

   python -m paper_games.tic_tac_toe --ultimate

9 small boards form a meta-board. Win small boards to claim cells on the meta-board!

Battleship
----------

Naval combat game with ship placement and strategic guessing.

Starting the Game
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -m paper_games.battleship

**Features:**

* Multiple grid sizes (6x6, 8x8, 10x10)
* Various ship types and sizes
* Difficulty levels for AI
* GUI with drag-and-drop placement
* Salvo mode (multiple shots per turn)

Placing Ships
~~~~~~~~~~~~~

In CLI mode:

1. Enter coordinates (e.g., ``A1``)
2. Choose orientation (H for horizontal, V for vertical)
3. Ships are placed automatically in GUI

Making Attacks
~~~~~~~~~~~~~~

* Enter coordinates to attack
* Hit/Miss feedback provided
* Track opponent's board
* First to sink all ships wins

GUI Mode
~~~~~~~~

.. code-block:: bash

   python -m paper_games.battleship --gui

**GUI Features:**

* Visual ship placement with mouse
* Click to attack
* Color-coded hit/miss markers
* Ship status display

Hangman
-------

Classic word-guessing game with ASCII art gallows.

Starting the Game
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -m paper_games.hangman

**Features:**

* Curated word list with thousands of words
* Configurable mistake limits
* ASCII art gallows that fills in
* Full-word guess option
* Difficulty levels

How to Play
~~~~~~~~~~~

1. Computer selects a random word
2. You see blanks for each letter
3. Guess letters one at a time
4. Wrong guesses add to the gallows
5. Complete the word before gallows is complete!

Strategy Tips
~~~~~~~~~~~~~

* Start with common letters: E, T, A, O, I, N
* Look for common patterns
* Use full-word guess when you're confident
* Avoid uncommon letters early

Dots and Boxes
--------------

Connect dots to complete boxes and score points.

Starting the Game
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -m paper_games.dots_and_boxes

**Features:**

* Multiple board sizes (2x2, 3x3, 4x4, 5x5, 6x6)
* Chain detection and highlighting
* Move hints for learning
* Tournament mode with statistics
* Network multiplayer

How to Play
~~~~~~~~~~~

1. Players take turns drawing lines between dots
2. Complete a box to score a point
3. Get a bonus turn when you complete a box
4. Player with most boxes wins

Coordinate System
~~~~~~~~~~~~~~~~~

Enter two dots to connect:

* Example: ``A0-A1`` draws a line from A0 to A1
* Format: ``[col][row]-[col][row]``

Advanced Features
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Enable hints
   python -m paper_games.dots_and_boxes --gui --hints

   # Tournament mode
   python -m paper_games.dots_and_boxes --tournament --games 5

Nim
---

Mathematical strategy game with multiple variants.

Starting the Game
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -m paper_games.nim

**Features:**

* Classic Nim with multiple heaps
* Northcott's Game variant
* Wythoff's Game variant
* Educational mode with strategy explanations
* Optimal AI opponent
* Multiplayer support (3+ players)

How to Play Classic Nim
~~~~~~~~~~~~~~~~~~~~~~~~

1. Start with heaps of objects (e.g., 3 heaps: 3, 5, 7 objects)
2. On your turn, remove any number of objects from one heap
3. Player who takes the last object wins (normal play)
   OR loses (misère play)

Strategy
~~~~~~~~

The game has a mathematical winning strategy based on "Nim-sum":

* XOR all heap sizes together
* If result is 0, current player is in losing position
* Educational mode explains optimal moves

Variants
~~~~~~~~

**Northcott's Game**: Move checkers on rows, can't pass opponent's checker

**Wythoff's Game**: Two heaps, can remove from one or equal amounts from both

Unscramble
----------

Word unscrambling game with scoring and multiple rounds.

Starting the Game
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -m paper_games.unscramble

**Features:**

* Curated word list (same as Hangman)
* Multiple rounds
* Score tracking
* Time pressure (optional)
* Difficulty levels

How to Play
~~~~~~~~~~~

1. See a scrambled word
2. Unscramble it
3. Enter your answer
4. Earn points for correct answers
5. Play multiple rounds

Strategy Tips
~~~~~~~~~~~~~

* Look for common prefixes/suffixes
* Rearrange vowels and consonants
* Think of word categories
* Use pen and paper for difficult ones

General Tips for All Games
---------------------------

Statistics
~~~~~~~~~~

Most games track statistics:

* Win/loss records
* Games played
* Success rates
* Saved to ``~/.games/`` directory

Network Play
~~~~~~~~~~~~

Some games support network multiplayer:

.. code-block:: bash

   # Host a game
   python -m paper_games.tic_tac_toe --network
   # Choose option 1: Host

   # Join a game
   python -m paper_games.tic_tac_toe --network
   # Choose option 2: Join
   # Enter host address

Seeded Games
~~~~~~~~~~~~

Use seeds for reproducible gameplay:

.. code-block:: bash

   python -m paper_games.battleship --seed 12345

Useful for:

* Testing strategies
* Sharing interesting games
* Debugging

Quick Reference
---------------

Starting Each Game
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Tic-Tac-Toe
   python -m paper_games.tic_tac_toe

   # Battleship
   python -m paper_games.battleship

   # Hangman
   python -m paper_games.hangman

   # Dots and Boxes
   python -m paper_games.dots_and_boxes

   # Nim
   python -m paper_games.nim

   # Unscramble
   python -m paper_games.unscramble

Getting Help
~~~~~~~~~~~~

Most games support ``--help``:

.. code-block:: bash

   python -m paper_games.tic_tac_toe --help

Code Examples
-------------

Programmatic Usage
~~~~~~~~~~~~~~~~~~

Use any game engine in your code:

.. code-block:: python

   from paper_games.tic_tac_toe.tic_tac_toe import TicTacToe

   # Create a game
   game = TicTacToe(board_size=3)

   # Make moves
   game.make_move(0, 0)  # X plays top-left
   game.make_move(1, 1)  # O plays center

   # Check winner
   winner = game.get_winner()

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Import errors**
   Ensure you're running from the repository root

**Statistics not saving**
   Check permissions for ``~/.games/`` directory

**GUI doesn't start**
   Install tkinter: ``sudo apt-get install python3-tk`` (Linux)

**AI too difficult**
   Try lower difficulty settings where available

Next Steps
----------

* Try the :doc:`poker_tutorial` for more complex games
* Read game-specific architecture docs in :doc:`../architecture/index`
* Explore :doc:`../examples/index` for code samples
* Check individual game README files for detailed features
