Code Examples
=============

This section provides practical code examples for using and extending the games collection.

.. toctree::
   :maxdepth: 2

   basic_usage
   custom_games
   ai_integration

Quick Start Examples
--------------------

Playing a Game Programmatically
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instead of using the CLI, you can use the game engines directly in your code:

.. code-block:: python

   from card_games.poker.poker import PokerMatch, GameVariant, BettingLimit

   # Create a poker match
   match = PokerMatch(
       variant=GameVariant.TEXAS_HOLDEM,
       limit_type=BettingLimit.NO_LIMIT,
       num_rounds=5,
       difficulty='Medium'
   )

   # Play the match
   match.play()

   # Access results
   print(f"Winner: {match.get_winner()}")
   print(f"Statistics: {match.get_statistics()}")

Customizing Game Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from card_games.bluff.bluff import BluffGame, DifficultyLevel

   # Create custom difficulty
   custom_difficulty = DifficultyLevel(
       name="Expert",
       num_bots=3,
       num_decks=2,
       bluff_frequency=0.45,
       challenge_frequency=0.40,
       suspicion_memory=12
   )

   # Create game with custom settings
   game = BluffGame(
       num_players=4,
       difficulty=custom_difficulty,
       rounds=7,
       seed=12345
   )

   # Play the game
   game.start()

Using Game Components
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from card_games.common.cards import Deck, Card
   from card_games.poker.poker_core import best_hand, HandRank

   # Create and shuffle a deck
   deck = Deck()
   deck.shuffle()

   # Deal some cards
   hand = deck.deal(5)

   # Evaluate the hand
   rank, kickers = best_hand(hand)
   print(f"Hand: {rank.name}")

   # Compare hands
   hand2 = deck.deal(5)
   rank2, kickers2 = best_hand(hand2)

   if (rank, kickers) > (rank2, kickers2):
       print("Hand 1 wins!")

Integrating with GUI
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import tkinter as tk
   from card_games.poker.gui import PokerGUI
   from card_games.poker.poker import PokerMatch

   # Create game engine
   match = PokerMatch(
       variant='texas-holdem',
       difficulty='Hard',
       num_rounds=10
   )

   # Create GUI
   root = tk.Tk()
   gui = PokerGUI(root, match)

   # Start game
   root.mainloop()

Testing Game Logic
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import unittest
   from paper_games.tic_tac_toe.tic_tac_toe import TicTacToe

   class TestMyGame(unittest.TestCase):
       def setUp(self):
           self.game = TicTacToe(board_size=3)

       def test_win_condition(self):
           """Test winning with three in a row."""
           # X plays three in a row
           self.game.make_move(0, 0)  # X
           self.game.make_move(1, 0)  # O
           self.game.make_move(0, 1)  # X
           self.game.make_move(1, 1)  # O
           self.game.make_move(0, 2)  # X

           self.assertTrue(self.game.is_game_over())
           self.assertEqual(self.game.get_winner(), 'X')

       def test_draw(self):
           """Test draw condition."""
           # Fill board with no winner
           moves = [(0,0), (0,1), (0,2),
                   (1,1), (1,0), (1,2),
                   (2,1), (2,2), (2,0)]

           for i, move in enumerate(moves):
               self.game.make_move(*move)

           self.assertTrue(self.game.is_game_over())
           self.assertIsNone(self.game.get_winner())

   if __name__ == '__main__':
       unittest.main()

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   from card_games.poker.poker import PokerMatch
   import json

   def run_tournament(num_games=100):
       """Run multiple games and collect statistics."""
       results = []

       for i in range(num_games):
           match = PokerMatch(
               variant='texas-holdem',
               difficulty='Hard',
               num_rounds=5,
               seed=i  # Different seed for each game
           )

           match.play()

           results.append({
               'game_id': i,
               'winner': match.get_winner(),
               'hands_played': match.hands_played,
               'statistics': match.get_statistics()
           })

       # Save results
       with open('tournament_results.json', 'w') as f:
           json.dump(results, f, indent=2)

       return results

   # Run tournament
   results = run_tournament(100)

   # Analyze results
   bot_wins = sum(1 for r in results if r['winner'].startswith('Bot'))
   print(f"Bot win rate: {bot_wins / len(results) * 100:.1f}%")

Common Patterns
---------------

Game State Management
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from dataclasses import dataclass
   from enum import Enum, auto

   class GamePhase(Enum):
       """Game phases."""
       SETUP = auto()
       PLAYING = auto()
       FINISHED = auto()

   @dataclass
   class GameState:
       """Immutable game state."""
       phase: GamePhase
       current_player: int
       scores: tuple
       move_history: tuple

       def make_move(self, move):
           """Return new state with move applied."""
           new_history = self.move_history + (move,)
           new_scores = self.calculate_scores(move)
           next_player = (self.current_player + 1) % len(self.scores)

           return GameState(
               phase=self.check_game_end(),
               current_player=next_player,
               scores=new_scores,
               move_history=new_history
           )

Event-Driven Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class GameEngine:
       """Game engine with event system."""

       def __init__(self):
           self.listeners = []

       def add_listener(self, listener):
           """Register event listener."""
           self.listeners.append(listener)

       def notify(self, event_type, data):
           """Notify all listeners of event."""
           for listener in self.listeners:
               if hasattr(listener, f'on_{event_type}'):
                   getattr(listener, f'on_{event_type}')(data)

       def make_move(self, move):
           """Make a move and notify listeners."""
           # Process move
           result = self.process_move(move)

           # Notify listeners
           self.notify('move_made', {
               'move': move,
               'result': result,
               'game_state': self.get_state()
           })

   class GUIListener:
       """GUI that listens to game events."""

       def on_move_made(self, data):
           """Update GUI when move is made."""
           self.update_board(data['game_state'])
           self.log_move(data['move'])

Plugin System
~~~~~~~~~~~~~

.. code-block:: python

   from abc import ABC, abstractmethod

   class GamePlugin(ABC):
       """Base class for game plugins."""

       @abstractmethod
       def get_name(self):
           """Return plugin name."""
           pass

       @abstractmethod
       def on_game_start(self, game):
           """Called when game starts."""
           pass

       @abstractmethod
       def on_move(self, move, game):
           """Called after each move."""
           pass

       @abstractmethod
       def on_game_end(self, game):
           """Called when game ends."""
           pass

   class StatisticsPlugin(GamePlugin):
       """Plugin that tracks statistics."""

       def __init__(self):
           self.stats = {}

       def get_name(self):
           return "Statistics Tracker"

       def on_game_start(self, game):
           self.stats = {
               'moves': 0,
               'start_time': time.time()
           }

       def on_move(self, move, game):
           self.stats['moves'] += 1

       def on_game_end(self, game):
           self.stats['duration'] = time.time() - self.stats['start_time']
           self.save_stats()

   # Usage
   game = GameEngine()
   game.add_plugin(StatisticsPlugin())
   game.add_plugin(LoggingPlugin())

Advanced Topics
---------------

Custom AI Opponents
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from card_games.poker.poker import PokerBot, BotSkill

   class CustomPokerBot(PokerBot):
       """Custom bot with unique strategy."""

       def __init__(self, name, skill_level):
           super().__init__(name, skill_level)
           self.hand_history = []

       def decide_action(self, game_state):
           """Custom decision making."""
           # Use custom strategy
           equity = self.calculate_custom_equity(game_state)
           pot_odds = self.calculate_pot_odds(game_state)

           # Adjust based on hand history
           if self.has_been_bluffed_recently():
               # Play more aggressively
               equity *= 1.2

           # Make decision
           if equity > pot_odds * 1.5:
               return self.make_raise(game_state)
           elif equity > pot_odds:
               return self.make_call(game_state)
           else:
               return self.make_fold()

Save/Load Game State
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import json
   import pickle
   from pathlib import Path

   class SaveableGame:
       """Game that can be saved and loaded."""

       def save_game(self, filepath):
           """Save game state to file."""
           state = {
               'version': '1.0',
               'game_type': self.__class__.__name__,
               'players': [p.to_dict() for p in self.players],
               'board': self.board.to_dict(),
               'current_player': self.current_player,
               'move_history': self.move_history,
               'timestamp': time.time()
           }

           with open(filepath, 'w') as f:
               json.dump(state, f, indent=2)

       @classmethod
       def load_game(cls, filepath):
           """Load game state from file."""
           with open(filepath) as f:
               state = json.load(f)

           # Validate version
           if state['version'] != '1.0':
               raise ValueError(f"Unsupported version: {state['version']}")

           # Reconstruct game
           game = cls()
           game.players = [Player.from_dict(p) for p in state['players']]
           game.board = Board.from_dict(state['board'])
           game.current_player = state['current_player']
           game.move_history = state['move_history']

           return game

Next Steps
----------

* See :doc:`basic_usage` for more introductory examples
* Check :doc:`custom_games` for creating your own games
* Review :doc:`ai_integration` for advanced AI techniques
* Read the :doc:`../architecture/index` for design patterns
