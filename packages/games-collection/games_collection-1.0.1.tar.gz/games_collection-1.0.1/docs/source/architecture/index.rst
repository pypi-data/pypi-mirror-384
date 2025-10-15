Architecture & Design
=====================

This section provides in-depth documentation of the architecture and design decisions
for complex games in the collection.

.. toctree::
   :maxdepth: 2

   poker_architecture
   bluff_architecture
   ai_strategies

Overview
--------

The games collection is designed with several key principles:

* **Modularity**: Each game is self-contained with minimal dependencies
* **Extensibility**: Easy to add new games or extend existing ones
* **Clean Separation**: Game logic separated from UI (CLI and GUI)
* **Reusability**: Common utilities shared across games

Project Structure
-----------------

.. code-block:: text

   Games/
   ├── card_games/          # Card game implementations
   │   ├── common/          # Shared card utilities
   │   ├── poker/           # Texas Hold'em and Omaha
   │   ├── bluff/           # Bluff/Cheat game
   │   ├── blackjack/       # Casino blackjack
   │   └── uno/             # Classic Uno
   ├── paper_games/         # Paper-and-pencil games
   │   ├── tic_tac_toe/     # Minimax-powered tic-tac-toe
   │   ├── battleship/      # Naval combat
   │   ├── hangman/         # Word guessing
   │   ├── dots_and_boxes/  # Connect the dots
   │   ├── nim/             # Mathematical strategy
   │   └── unscramble/      # Word unscrambling
   ├── tests/               # Test suite
   └── docs/                # Documentation

Common Patterns
---------------

Game Engine Pattern
~~~~~~~~~~~~~~~~~~~

Each game follows a common pattern:

1. **Game State**: Core class maintaining game state
2. **Player Representation**: Classes for human and AI players
3. **Action System**: Enumerated actions players can take
4. **CLI Module**: Command-line interface
5. **GUI Module**: Optional Tkinter interface

Example structure:

.. code-block:: python

   class GameEngine:
       """Core game logic and state management."""
       def __init__(self):
           self.players = []
           self.current_state = None

       def make_move(self, action):
           """Process a player action."""
           pass

       def get_winner(self):
           """Determine game winner."""
           pass

   class Player:
       """Represents a player (human or AI)."""
       pass

   class AIPlayer(Player):
       """AI opponent with strategy logic."""
       def choose_action(self):
           """Determine best move."""
           pass

UI Separation
~~~~~~~~~~~~~

Game logic is independent of UI:

.. code-block:: python

   # Game engine is UI-agnostic
   game = PokerGame()
   game.deal_cards()

   # CLI uses the same engine
   cli = PokerCLI(game)
   cli.run()

   # GUI uses the same engine
   gui = PokerGUI(game)
   gui.mainloop()

This allows:

* Easy testing of game logic
* Multiple UI implementations
* Headless operation for AI development

Design Principles
-----------------

Composition Over Inheritance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Games use composition for flexibility:

.. code-block:: python

   class PokerTable:
       def __init__(self):
           self.deck = Deck()           # Composition
           self.players = []            # Composition
           self.pot = Pot()             # Composition

This makes it easy to:

* Swap implementations (e.g., different deck types)
* Test components in isolation
* Reuse components across games

Immutable Data Where Possible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Key game elements use immutable data:

.. code-block:: python

   @dataclass(frozen=True)
   class Card:
       rank: str
       suit: Suit

Benefits:

* Thread-safe
* Easier to reason about
* Can be used as dictionary keys
* Prevents accidental modifications

Clear State Transitions
~~~~~~~~~~~~~~~~~~~~~~~

Games use enums for state management:

.. code-block:: python

   class GamePhase(Enum):
       SETUP = auto()
       PLAYING = auto()
       FINISHED = auto()

This ensures:

* Clear state machine
* Type-safe transitions
* Easy debugging

Performance Considerations
--------------------------

AI Decision Making
~~~~~~~~~~~~~~~~~~

AI performance is optimized through:

* **Monte Carlo Sampling**: Limited simulations for practical speed
* **Caching**: Repeated calculations cached
* **Pruning**: Alpha-beta pruning in minimax
* **Heuristics**: Fast evaluation functions

Example from Poker:

.. code-block:: python

   def estimate_win_rate(hole_cards, community_cards, num_simulations=1000):
       """Fast Monte Carlo estimation with limited simulations."""
       wins = 0
       for _ in range(num_simulations):
           # Simulate one possible outcome
           if simulate_hand(hole_cards, community_cards):
               wins += 1
       return wins / num_simulations

Memory Management
~~~~~~~~~~~~~~~~~

* **Lazy Loading**: Game assets loaded only when needed
* **Generator Usage**: Large iterations use generators
* **Cleanup**: Explicit cleanup in GUI close handlers

Testing Strategy
----------------

Each game includes:

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test game flow
3. **AI Tests**: Verify AI behavior
4. **Regression Tests**: Prevent bugs from returning

Example test structure:

.. code-block:: python

   class TestPokerGame(unittest.TestCase):
       def test_deal_cards(self):
           """Test card dealing."""
           game = PokerGame()
           game.deal()
           self.assertEqual(len(game.players[0].hand), 2)

       def test_hand_ranking(self):
           """Test hand evaluation."""
           hand = [Card('A', 'hearts'), ...]
           rank = evaluate_hand(hand)
           self.assertEqual(rank, HandRank.FLUSH)

Next Steps
----------

Explore detailed architecture documentation:

* :doc:`poker_architecture` - Texas Hold'em implementation details
* :doc:`bluff_architecture` - Bluff/Cheat game design
* :doc:`ai_strategies` - AI algorithms and strategies
