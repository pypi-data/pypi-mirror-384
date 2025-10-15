Poker Architecture
==================

This document describes the architecture and design of the Texas Hold'em poker
implementation, including game flow, AI strategy, and extensibility.

Overview
--------

The poker module implements a complete Texas Hold'em poker game with:

* Multiple game variants (Texas Hold'em, Omaha)
* Betting structures (No-limit, Pot-limit, Fixed-limit)
* Tournament mode with increasing blinds
* AI opponents with Monte Carlo decision making
* Statistics tracking and hand history
* Both CLI and GUI interfaces

Architecture Diagram
--------------------

.. code-block:: text

   ┌─────────────────────────────────────────────────────────┐
   │                    User Interfaces                       │
   │  ┌──────────────────┐        ┌──────────────────┐      │
   │  │   CLI Interface  │        │   GUI Interface  │      │
   │  │  (poker/__main__)│        │   (poker/gui.py) │      │
   │  └────────┬─────────┘        └────────┬─────────┘      │
   └───────────┼────────────────────────────┼────────────────┘
               │                            │
               │        ┌───────────────────┘
               │        │
   ┌───────────▼────────▼─────────────────────────────────┐
   │               Game Orchestration                      │
   │  ┌──────────────────────────────────────────────┐    │
   │  │         PokerMatch                            │    │
   │  │  - Manages multiple hands                     │    │
   │  │  - Tracks player statistics                   │    │
   │  │  - Handles tournament blind increases         │    │
   │  └────────────────┬─────────────────────────────┘    │
   │                   │                                    │
   │  ┌────────────────▼─────────────────────────────┐    │
   │  │         PokerTable                            │    │
   │  │  - Manages single hand                        │    │
   │  │  - Coordinates betting rounds                 │    │
   │  │  - Handles pot distribution                   │    │
   │  └────────────────┬─────────────────────────────┘    │
   └───────────────────┼──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐
   │ Player  │   │ PokerBot  │  │  Deck   │
   │         │   │ (AI)      │  │         │
   │ State   │   │ Strategy  │  │ Cards   │
   └─────────┘   └───────────┘  └─────────┘
                       │
                 ┌─────▼──────┐
                 │  Poker     │
                 │  Core      │
                 │  (Hand     │
                 │  Eval)     │
                 └────────────┘

Core Components
---------------

PokerMatch Class
~~~~~~~~~~~~~~~~

Orchestrates multiple hands and manages the overall game:

.. code-block:: python

   class PokerMatch:
       """Manages a complete poker match with multiple hands.

       Responsibilities:
       - Track player statistics across hands
       - Manage tournament blind increases
       - Handle player elimination
       - Save hand history
       """

       def __init__(self, variant, limit_type, tournament_mode):
           self.players = []
           self.hands_played = 0
           self.statistics = {}
           self.tournament_mode = tournament_mode

       def play_hand(self):
           """Play a single hand."""
           table = PokerTable(self.players, self.blinds)
           table.play()
           self.update_statistics(table.results)

**Key Features:**

* Statistics tracking for all players
* Hand history logging to JSON
* Tournament blind escalation
* Player elimination handling

PokerTable Class
~~~~~~~~~~~~~~~~

Manages a single hand from deal to showdown:

.. code-block:: python

   class PokerTable:
       """Manages a single poker hand.

       Responsibilities:
       - Deal cards (hole cards and community cards)
       - Coordinate betting rounds
       - Calculate pots and side pots
       - Determine winners
       """

       def __init__(self, players, blinds):
           self.players = players
           self.deck = Deck()
           self.community_cards = []
           self.pot = 0
           self.current_bet = 0

       def play(self):
           """Execute complete hand."""
           self.post_blinds()
           self.deal_hole_cards()
           self.betting_round()  # Pre-flop
           self.deal_flop()
           self.betting_round()
           self.deal_turn()
           self.betting_round()
           self.deal_river()
           self.betting_round()
           self.showdown()

**Betting Round Flow:**

1. Start with player after big blind (pre-flop) or dealer (other rounds)
2. Each player can: fold, call, raise, check (if no bet)
3. Round continues until all active players have matched the bet
4. Handle all-in situations and side pots

Player and PokerBot
~~~~~~~~~~~~~~~~~~~

Player state and AI decision making:

.. code-block:: python

   @dataclass
   class Player:
       """Player state."""
       name: str
       chips: int
       hole_cards: List[Card]
       folded: bool
       current_bet: int
       is_bot: bool

   class PokerBot:
       """AI opponent with configurable skill level.

       Decision making uses:
       - Monte Carlo simulation for win rate estimation
       - Position awareness
       - Pot odds calculation
       - Opponent modeling
       """

       def __init__(self, skill_level: BotSkill):
           self.skill = skill_level
           self.opponent_model = {}

       def decide_action(self, game_state) -> Action:
           """Choose action based on game state."""
           win_rate = self.estimate_equity(game_state)
           pot_odds = self.calculate_pot_odds(game_state)

           # Apply skill-based adjustments
           if self.skill.mistake_rate > random.random():
               return self.make_mistake()

           return self.optimal_action(win_rate, pot_odds)

Hand Evaluation
~~~~~~~~~~~~~~~

Fast and accurate hand ranking:

.. code-block:: python

   def best_hand(cards: List[Card]) -> Tuple[HandRank, List[int]]:
       """Evaluate best 5-card poker hand.

       Returns:
           (hand_rank, tiebreaker_values)

       Example:
           best_hand([As, Ks, Qs, Js, Ts])
           -> (HandRank.STRAIGHT_FLUSH, [14])
       """
       # Check for each hand type in descending order
       if is_straight_flush(cards):
           return (HandRank.STRAIGHT_FLUSH, get_high_cards(cards))
       elif is_four_of_kind(cards):
           return (HandRank.FOUR_OF_KIND, get_quad_kickers(cards))
       # ... etc

**Performance:**

* Evaluates hands in microseconds
* Handles all edge cases (wheel straights, etc.)
* Correct tiebreaker ordering

Game Flow
---------

Complete Hand Sequence
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   1. POST BLINDS
      │
      ├─> Small blind posts (e.g., $5)
      └─> Big blind posts (e.g., $10)

   2. DEAL HOLE CARDS
      │
      ├─> Each player receives 2 cards (Texas) or 4 cards (Omaha)
      └─> Cards are private to each player

   3. PRE-FLOP BETTING
      │
      ├─> Starts with player after big blind
      ├─> Players can: Fold, Call, Raise
      └─> Round ends when all players match the bet

   4. DEAL FLOP (3 community cards)
      │
      └─> Burn one card, deal 3 face up

   5. FLOP BETTING
      │
      ├─> Starts with player after dealer
      ├─> Players can: Check, Bet, Fold, Call, Raise
      └─> Round ends when all players match

   6. DEAL TURN (1 community card)
      │
      └─> Burn one card, deal 1 face up

   7. TURN BETTING
      │
      └─> Same as flop betting

   8. DEAL RIVER (1 community card)
      │
      └─> Burn one card, deal 1 face up

   9. RIVER BETTING
      │
      └─> Final betting round

   10. SHOWDOWN
       │
       ├─> Remaining players reveal cards
       ├─> Best hand wins
       ├─> Handle side pots if players all-in
       └─> Distribute chips

Betting Round Details
~~~~~~~~~~~~~~~~~~~~~

Each betting round follows these rules:

1. **Action Order**: Clockwise from designated starting position
2. **Valid Actions**:

   * **Fold**: Forfeit hand (can't win pot)
   * **Check**: Pass action if no bet (not allowed if bet exists)
   * **Call**: Match current bet
   * **Bet/Raise**: Increase the current bet
   * **All-in**: Bet all remaining chips

3. **Completion**: Round ends when all active players have equal bets
4. **Side Pots**: Created when player(s) go all-in with less than current bet

AI Strategy
-----------

Monte Carlo Simulation
~~~~~~~~~~~~~~~~~~~~~~

The AI estimates hand strength through simulation:

.. code-block:: python

   def estimate_win_rate(hole_cards, community_cards,
                         num_opponents=3, simulations=1000):
       """Estimate probability of winning through simulation.

       Process:
       1. Deal random opponent hands
       2. Deal remaining community cards
       3. Evaluate all hands
       4. Count wins
       5. Return win rate
       """
       wins = 0

       for _ in range(simulations):
           # Simulate one possible outcome
           deck = Deck()
           deck.remove_cards(hole_cards + community_cards)

           # Deal opponent hands
           opponent_hands = [deck.deal(2) for _ in range(num_opponents)]

           # Complete community cards
           remaining = 5 - len(community_cards)
           simulated_community = community_cards + deck.deal(remaining)

           # Evaluate hands
           my_hand = best_hand(hole_cards + simulated_community)
           opponent_best = max(
               best_hand(opp + simulated_community)
               for opp in opponent_hands
           )

           if my_hand > opponent_best:
               wins += 1

       return wins / simulations

**Parameters:**

* ``simulations``: More = accurate but slower (default: 1000)
* Adjusts based on difficulty level
* Pre-flop uses different strategy than post-flop

Position Awareness
~~~~~~~~~~~~~~~~~~

AI adjusts strategy based on position:

.. code-block:: python

   def position_factor(position, num_players):
       """Calculate position advantage.

       Returns:
           float: Multiplier for hand strength
                 (1.0 = neutral, >1.0 = advantage)
       """
       # Early position (first to act)
       if position <= num_players // 3:
           return 0.85  # Play tighter

       # Middle position
       elif position <= 2 * num_players // 3:
           return 1.0  # Standard play

       # Late position (dealer button nearby)
       else:
           return 1.15  # Play looser, more aggressive

**Why Position Matters:**

* Late position sees opponents' actions first
* Can play more hands profitably
* Better bluffing opportunities
* More information for decisions

Skill Levels
~~~~~~~~~~~~

Different skill levels create distinct behaviors:

.. code-block:: python

   @dataclass
   class BotSkill:
       """AI skill parameters."""
       name: str
       mistake_rate: float      # Probability of sub-optimal play
       aggression: float        # Tendency to bet/raise vs check/call
       bluff_frequency: float   # How often to bluff
       hand_tightness: float    # Starting hand requirements
       simulations: int         # Monte Carlo iterations

   DIFFICULTY_LEVELS = {
       'Very Easy': BotSkill(
           mistake_rate=0.35,
           aggression=0.3,
           bluff_frequency=0.1,
           hand_tightness=0.4,
           simulations=500
       ),
       'Hard': BotSkill(
           mistake_rate=0.05,
           aggression=0.7,
           bluff_frequency=0.25,
           hand_tightness=0.7,
           simulations=2000
       ),
       # ... other levels
   }

Pot Odds Calculation
~~~~~~~~~~~~~~~~~~~~

AI uses pot odds for call/fold decisions:

.. code-block:: python

   def should_call(pot_size, call_amount, win_rate):
       """Determine if calling is profitable.

       Args:
           pot_size: Current pot size
           call_amount: Amount to call
           win_rate: Estimated probability of winning

       Returns:
           bool: True if call is +EV
       """
       pot_odds = call_amount / (pot_size + call_amount)
       return win_rate > pot_odds

**Example:**

* Pot: $100
* Call: $20
* Pot odds: 20 / (100 + 20) = 16.7%
* Need >16.7% equity to call profitably

Extensibility
-------------

Adding New Variants
~~~~~~~~~~~~~~~~~~~

The architecture supports adding new poker variants:

.. code-block:: python

   class GameVariant(Enum):
       TEXAS_HOLDEM = "texas-holdem"
       OMAHA = "omaha"
       # Add new variants here

   def deal_hole_cards(variant, deck):
       """Deal appropriate hole cards for variant."""
       if variant == GameVariant.TEXAS_HOLDEM:
           return deck.deal(2)
       elif variant == GameVariant.OMAHA:
           return deck.deal(4)
       # Add new variant logic here

Custom Betting Structures
~~~~~~~~~~~~~~~~~~~~~~~~~~

Easy to add new betting structures:

.. code-block:: python

   class BettingLimit(Enum):
       NO_LIMIT = "no-limit"
       POT_LIMIT = "pot-limit"
       FIXED_LIMIT = "fixed-limit"

   def max_raise(limit_type, pot_size, current_bet):
       """Calculate maximum raise for betting structure."""
       if limit_type == BettingLimit.NO_LIMIT:
           return float('inf')  # No maximum
       elif limit_type == BettingLimit.POT_LIMIT:
           return pot_size
       elif limit_type == BettingLimit.FIXED_LIMIT:
           return current_bet * 2

Statistics and Analytics
------------------------

Hand History
~~~~~~~~~~~~

Every hand is logged to JSON:

.. code-block:: json

   {
       "hand_id": "2024-01-15-001",
       "variant": "texas-holdem",
       "players": [...],
       "actions": [
           {"player": "Alice", "action": "raise", "amount": 20},
           {"player": "Bot1", "action": "call", "amount": 20}
       ],
       "community_cards": ["As", "Kh", "Qd", "Jc", "Ts"],
       "showdown": {...},
       "winner": "Alice",
       "pot": 120
   }

Player Statistics
~~~~~~~~~~~~~~~~~

Comprehensive stats tracked:

* Hands played
* Win rate
* Showdown win rate
* Fold frequency
* Average bet size
* Net profit/loss
* Hands won by type (pair, flush, etc.)

Tournament Features
-------------------

Blind Schedule
~~~~~~~~~~~~~~

Blinds increase on schedule:

.. code-block:: python

   def get_blinds(hands_played, schedule_interval=10):
       """Calculate current blinds based on hands played.

       Example schedule:
           Hands 1-10:   $5/$10
           Hands 11-20:  $10/$20
           Hands 21-30:  $15/$30
           etc.
       """
       level = hands_played // schedule_interval
       base = 5
       return (base * (level + 1), base * 2 * (level + 1))

Player Elimination
~~~~~~~~~~~~~~~~~~

When a player runs out of chips:

1. Player is marked as eliminated
2. Remaining players continue
3. Tournament ends when one player remains
4. Winner is declared

Testing
-------

The poker module includes comprehensive tests:

.. code-block:: python

   class TestPokerGame(unittest.TestCase):
       def test_hand_evaluation(self):
           """Test hand ranking."""
           # Royal flush beats everything
           royal = [Card('A','♠'), Card('K','♠'), ...]
           pair = [Card('A','♥'), Card('A','♦'), ...]
           self.assertGreater(best_hand(royal), best_hand(pair))

       def test_pot_calculation(self):
           """Test pot and side pot calculation."""
           # Player 1: $100 all-in
           # Player 2: $200 bet
           # Player 3: $200 call
           table = PokerTable([...])
           table.process_bets()
           self.assertEqual(table.main_pot, 300)
           self.assertEqual(table.side_pots[0], 400)

       def test_ai_decision(self):
           """Test AI makes reasonable decisions."""
           bot = PokerBot(skill_level='Medium')
           # With strong hand, bot should raise
           action = bot.decide_action(strong_hand_state)
           self.assertIn(action.type, [ActionType.RAISE, ActionType.CALL])

Performance Optimization
------------------------

The implementation is optimized for smooth gameplay:

* Hand evaluation: O(1) with lookup tables
* Monte Carlo: Parallelizable (future enhancement)
* Memory: Efficient card representation
* GUI: Smooth animations without blocking

Next Steps
----------

* Review :doc:`bluff_architecture` for another card game architecture
* See :doc:`ai_strategies` for AI algorithm details
* Check :doc:`../examples/poker_examples` for code samples
