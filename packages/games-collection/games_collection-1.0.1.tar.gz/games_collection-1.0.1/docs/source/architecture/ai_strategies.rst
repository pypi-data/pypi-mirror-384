AI Strategies and Algorithms
=============================

This document provides comprehensive documentation of the AI strategies and algorithms
used across all games in the collection.

Overview
--------

The games collection employs various AI techniques depending on the game type:

* **Perfect Information Games** (Tic-Tac-Toe): Minimax with alpha-beta pruning
* **Imperfect Information Games** (Poker): Monte Carlo simulation
* **Deception Games** (Bluff): Opponent modeling and psychological strategies
* **Pattern Recognition** (Battleship): Probability distributions
* **Mathematical Games** (Nim): Optimal strategy calculation

Minimax Algorithm
-----------------

Used in: Tic-Tac-Toe, Ultimate Tic-Tac-Toe

Theory
~~~~~~

Minimax assumes both players play optimally:

* **Maximizing player**: Wants highest score
* **Minimizing player**: Wants lowest score
* Algorithm explores all possible moves to find optimal play

Implementation
~~~~~~~~~~~~~~

.. code-block:: python

   def minimax(board, depth, is_maximizing, alpha=-inf, beta=inf):
       """Minimax with alpha-beta pruning.

       Args:
           board: Current game state
           depth: Remaining search depth
           is_maximizing: True if maximizing player's turn
           alpha: Best score for maximizer
           beta: Best score for minimizer

       Returns:
           Tuple[int, Optional[Move]]: (score, best_move)
       """
       # Base case: terminal state or depth limit
       if board.is_game_over() or depth == 0:
           return evaluate_board(board), None

       if is_maximizing:
           max_score = float('-inf')
           best_move = None

           for move in board.get_legal_moves():
               # Try this move
               board.make_move(move)
               score, _ = minimax(board, depth - 1, False, alpha, beta)
               board.undo_move(move)

               # Update best score
               if score > max_score:
                   max_score = score
                   best_move = move

               # Alpha-beta pruning
               alpha = max(alpha, score)
               if beta <= alpha:
                   break  # Beta cutoff

           return max_score, best_move

       else:
           min_score = float('inf')
           best_move = None

           for move in board.get_legal_moves():
               board.make_move(move)
               score, _ = minimax(board, depth - 1, True, alpha, beta)
               board.undo_move(move)

               if score < min_score:
                   min_score = score
                   best_move = move

               # Alpha-beta pruning
               beta = min(beta, score)
               if beta <= alpha:
                   break  # Alpha cutoff

           return min_score, best_move

**Complexity:**

* Without pruning: O(b^d) where b = branching factor, d = depth
* With pruning: O(b^(d/2)) in best case
* Space: O(d) for recursion stack

Board Evaluation
~~~~~~~~~~~~~~~~

For terminal states:

.. code-block:: python

   def evaluate_board(board):
       """Evaluate board position.

       Returns:
           +10: AI wins
           -10: Human wins
           0: Draw
       """
       winner = board.get_winner()

       if winner == AI:
           return 10
       elif winner == HUMAN:
           return -10
       else:
           return 0

For non-terminal states (heuristic):

.. code-block:: python

   def heuristic_eval(board):
       """Heuristic evaluation for incomplete games.

       Considers:
       - Number of winning lines available
       - Center control
       - Corner control
       """
       score = 0

       # Center control bonus
       if board.center == AI:
           score += 3
       elif board.center == HUMAN:
           score -= 3

       # Count threats (2-in-a-row with open third)
       ai_threats = count_threats(board, AI)
       human_threats = count_threats(board, HUMAN)
       score += ai_threats * 2
       score -= human_threats * 2

       return score

Alpha-Beta Pruning
~~~~~~~~~~~~~~~~~~

Optimization that eliminates unnecessary branches:

.. code-block:: text

   Maximizer's turn (alpha = -∞, beta = +∞):

   Move 1: Score = 5
   ├─> Update alpha to 5
   └─> Continue searching

   Move 2: Start evaluation
   ├─> Child returns score = 3 (less than alpha=5)
   ├─> Minimizer would choose this or worse
   └─> Maximizer won't choose this branch
       Skip remaining children! (β-cutoff)

   Move 3: Score = 7
   └─> New best move (alpha = 7)

**Pruning Effectiveness:**

* Best case: 50% of nodes pruned
* Average case: 30-40% pruned
* Move ordering crucial for effectiveness

Move Ordering
~~~~~~~~~~~~~

Better pruning with good move order:

.. code-block:: python

   def order_moves(board, moves):
       """Order moves for better alpha-beta pruning.

       Priority:
       1. Winning moves
       2. Blocking opponent wins
       3. Center
       4. Corners
       5. Edges
       """
       def move_priority(move):
           # Check if winning move
           board.make_move(move)
           if board.is_win(AI):
               priority = 1000
           # Check if blocks opponent win
           elif would_block_win(board, move):
               priority = 900
           # Center
           elif is_center(move):
               priority = 800
           # Corners
           elif is_corner(move):
               priority = 700
           # Edges
           else:
               priority = 600
           board.undo_move(move)
           return priority

       return sorted(moves, key=move_priority, reverse=True)

Monte Carlo Simulation
----------------------

Used in: Poker

Theory
~~~~~~

When perfect analysis is impractical, use sampling:

1. Simulate many random game continuations
2. Count favorable outcomes
3. Estimate probability from sample

**Advantages:**

* Works with imperfect information
* Scales to complex games
* Anytime algorithm (more samples = better estimate)

**Disadvantages:**

* Approximate (not exact)
* Requires many simulations
* Quality depends on simulation realism

Implementation
~~~~~~~~~~~~~~

.. code-block:: python

   def monte_carlo_equity(hole_cards, community_cards,
                         num_opponents=3, simulations=1000):
       """Estimate hand equity through Monte Carlo simulation.

       Args:
           hole_cards: Player's private cards
           community_cards: Revealed community cards
           num_opponents: Number of opponents
           simulations: Number of trials to run

       Returns:
           float: Estimated win probability (0.0 to 1.0)
       """
       wins = 0
       ties = 0

       # Create remaining deck
       deck = Deck()
       deck.remove_cards(hole_cards + community_cards)

       for _ in range(simulations):
           # Deal opponent hands
           sim_deck = deck.copy()
           sim_deck.shuffle()

           opponent_hands = []
           for _ in range(num_opponents):
               opponent_hands.append(sim_deck.deal(2))

           # Complete community cards
           remaining_community = 5 - len(community_cards)
           full_community = community_cards + sim_deck.deal(remaining_community)

           # Evaluate all hands
           my_hand = best_hand(hole_cards + full_community)
           opponent_best = max(
               best_hand(opp + full_community)
               for opp in opponent_hands
           )

           # Count results
           if my_hand > opponent_best:
               wins += 1
           elif my_hand == opponent_best:
               ties += 1

       # Return win rate (ties count as half win)
       return (wins + ties * 0.5) / simulations

**Optimization:**

* Use importance sampling for rare events
* Parallelize simulations
* Cache repeated calculations
* Reduce simulation count for fast actions

Variance Reduction
~~~~~~~~~~~~~~~~~~

Techniques to improve accuracy:

.. code-block:: python

   def monte_carlo_with_variance_reduction(hole_cards, community_cards,
                                           simulations=1000):
       """Monte Carlo with variance reduction techniques."""

       # 1. Stratified sampling
       # Divide opponent cards into strata (strong, medium, weak)
       strata_results = []
       for strength in ['strong', 'medium', 'weak']:
           stratum_wins = simulate_stratum(hole_cards, community_cards,
                                          strength, simulations // 3)
           strata_results.append(stratum_wins)

       # Combine strata (weighted by probability)
       win_rate = sum(r * w for r, w in zip(strata_results, [0.2, 0.6, 0.2]))

       # 2. Control variates
       # Use known expected values to reduce variance
       baseline = analytical_preflop_equity(hole_cards)
       simulated = simulate_preflop(hole_cards, simulations)
       correction = baseline - simulated

       return win_rate + correction

Simulation Count Trade-offs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Simulations | Accuracy | Time    | Use Case
   ------------|----------|---------|------------------
   100         | ±5%      | <10ms   | Fast decisions
   500         | ±3%      | ~50ms   | Normal play
   1000        | ±2%      | ~100ms  | Important decisions
   5000        | ±1%      | ~500ms  | Critical analysis
   10000       | ±0.5%    | ~1s     | Post-game analysis

Opponent Modeling
-----------------

Used in: Bluff, Poker

Theory
~~~~~~

Track opponent behavior to predict future actions:

* **Bayesian updating**: Update beliefs based on observations
* **History weighting**: Recent actions more important
* **Exploit patterns**: Adjust strategy based on opponent tendencies

Implementation
~~~~~~~~~~~~~~

.. code-block:: python

   class OpponentModel:
       """Model of opponent's playing style."""

       def __init__(self, player_name):
           self.name = player_name

           # Behavioral statistics
           self.actions_observed = 0
           self.fold_count = 0
           self.call_count = 0
           self.raise_count = 0
           self.bluff_count = 0
           self.showdown_hands = []

           # Derived metrics
           self.vpip = 0.0  # Voluntarily put $ in pot
           self.pfr = 0.0   # Pre-flop raise %
           self.aggression = 0.0  # Raise/call ratio
           self.tightness = 0.0  # Hand selectivity

       def update(self, action, context):
           """Update model based on observed action."""
           self.actions_observed += 1

           if action == 'fold':
               self.fold_count += 1
           elif action == 'call':
               self.call_count += 1
           elif action == 'raise':
               self.raise_count += 1

           # Recalculate derived metrics
           self.calculate_metrics()

       def calculate_metrics(self):
           """Calculate playing style metrics."""
           total = self.actions_observed
           if total == 0:
               return

           # VPIP: % of hands played
           self.vpip = (self.call_count + self.raise_count) / total

           # Aggression: raise vs call ratio
           if self.call_count > 0:
               self.aggression = self.raise_count / self.call_count
           else:
               self.aggression = float('inf')

           # Tightness: fold frequency
           self.tightness = self.fold_count / total

       def predict_action(self, game_state):
           """Predict opponent's likely action.

           Returns:
               Dict[Action, float]: Probability distribution over actions
           """
           # Use observed frequencies as baseline
           probs = {
               'fold': self.fold_count / self.actions_observed,
               'call': self.call_count / self.actions_observed,
               'raise': self.raise_count / self.actions_observed,
           }

           # Adjust based on context
           if game_state.pot_size > game_state.average_pot:
               # Tight players fold more in big pots
               if self.tightness > 0.6:
                   probs['fold'] *= 1.5
                   probs = normalize(probs)

           return probs

Player Archetypes
~~~~~~~~~~~~~~~~~

Common player types to recognize:

.. code-block:: python

   class PlayerArchetype:
       """Standard player archetypes."""

       TIGHT_PASSIVE = {
           'vpip': 0.15,  # Plays few hands
           'aggression': 0.3,  # Rarely raises
           'bluff_freq': 0.05
       }

       TIGHT_AGGRESSIVE = {
           'vpip': 0.20,  # Selective hands
           'aggression': 2.0,  # Raises often when playing
           'bluff_freq': 0.15
       }

       LOOSE_PASSIVE = {
           'vpip': 0.40,  # Plays many hands
           'aggression': 0.4,  # Calls more than raises
           'bluff_freq': 0.10
       }

       LOOSE_AGGRESSIVE = {
           'vpip': 0.35,  # Many hands
           'aggression': 3.0,  # Very aggressive
           'bluff_freq': 0.30
       }

   def classify_opponent(model):
       """Classify opponent into archetype."""
       if model.vpip < 0.25 and model.aggression < 1.0:
           return 'TIGHT_PASSIVE'
       elif model.vpip < 0.25 and model.aggression >= 1.0:
           return 'TIGHT_AGGRESSIVE'
       elif model.vpip >= 0.25 and model.aggression < 1.0:
           return 'LOOSE_PASSIVE'
       else:
           return 'LOOSE_AGGRESSIVE'

Bayesian Belief Updates
~~~~~~~~~~~~~~~~~~~~~~~~

Update beliefs based on new evidence:

.. code-block:: python

   def update_bluff_belief(prior_belief, evidence):
       """Update belief that opponent is bluffing.

       Args:
           prior_belief: Prior probability of bluff
           evidence: Observed action/context

       Returns:
           float: Updated probability (posterior)
       """
       # Likelihood of evidence given bluff
       p_evidence_given_bluff = calculate_likelihood(evidence, is_bluff=True)

       # Likelihood of evidence given honest
       p_evidence_given_honest = calculate_likelihood(evidence, is_bluff=False)

       # Bayes' theorem
       numerator = p_evidence_given_bluff * prior_belief
       denominator = (p_evidence_given_bluff * prior_belief +
                     p_evidence_given_honest * (1 - prior_belief))

       return numerator / denominator

Probability and Heuristics
--------------------------

Used in: Battleship, Dots and Boxes

Probability Distributions
~~~~~~~~~~~~~~~~~~~~~~~~~

In Battleship, track hit probabilities:

.. code-block:: python

   class ProbabilityMap:
       """Track probability of ship presence at each cell."""

       def __init__(self, grid_size, ships):
           self.grid_size = grid_size
           self.ships = ships
           self.prob_map = [[0.0] * grid_size for _ in range(grid_size)]
           self.update_probabilities()

       def update_probabilities(self):
           """Recalculate probabilities based on game state."""
           # Reset map
           self.prob_map = [[0.0] * self.grid_size
                           for _ in range(self.grid_size)]

           # For each ship not yet sunk
           for ship in self.unsunk_ships():
               # For each possible placement
               for placement in self.valid_placements(ship):
                   # Increment probability for each cell
                   for cell in placement:
                       self.prob_map[cell.row][cell.col] += 1

           # Normalize
           total = sum(sum(row) for row in self.prob_map)
           if total > 0:
               self.prob_map = [[cell / total for cell in row]
                               for row in self.prob_map]

       def best_target(self):
           """Return cell with highest probability."""
           max_prob = 0
           best_cell = None

           for row in range(self.grid_size):
               for col in range(self.grid_size):
                   if (not self.already_hit(row, col) and
                       self.prob_map[row][col] > max_prob):
                       max_prob = self.prob_map[row][col]
                       best_cell = (row, col)

           return best_cell

Hunt/Target Mode
~~~~~~~~~~~~~~~~

Two-phase strategy:

.. code-block:: python

   class BattleshipAI:
       """AI with hunt/target modes."""

       def __init__(self):
           self.mode = 'HUNT'
           self.target_stack = []

       def choose_shot(self):
           """Choose next shot based on mode."""
           if self.mode == 'HUNT':
               # No hits to follow up - use probability map
               return self.prob_map.best_target()

           else:  # TARGET mode
               # Following up on a hit
               if self.target_stack:
                   return self.target_stack.pop()
               else:
                   # No more targets, return to hunting
                   self.mode = 'HUNT'
                   return self.choose_shot()

       def process_result(self, shot, result):
           """Process shot result and update strategy."""
           if result == 'HIT':
               # Switch to target mode
               self.mode = 'TARGET'

               # Add adjacent cells to target stack
               for adj in self.adjacent_cells(shot):
                   if self.is_valid_target(adj):
                       self.target_stack.append(adj)

           elif result == 'SUNK':
               # Ship sunk - clear target stack and return to hunt
               self.target_stack.clear()
               self.mode = 'HUNT'
               self.update_probability_map()

Optimal Strategy (Nim)
----------------------

Used in: Nim, Nim Variants

Nim-Sum Calculation
~~~~~~~~~~~~~~~~~~~

The winning strategy for Nim uses XOR:

.. code-block:: python

   def nim_sum(heaps):
       """Calculate Nim-sum (XOR of all heap sizes).

       Nim-sum = 0 → Losing position
       Nim-sum ≠ 0 → Winning position
       """
       result = 0
       for heap in heaps:
           result ^= heap
       return result

   def optimal_move(heaps):
       """Find optimal move in Nim.

       Strategy:
       1. Calculate current Nim-sum
       2. If Nim-sum = 0, position is losing (make any legal move)
       3. If Nim-sum ≠ 0, find move that makes Nim-sum = 0
       """
       current_sum = nim_sum(heaps)

       if current_sum == 0:
           # Losing position - make any legal move
           for i, heap in enumerate(heaps):
               if heap > 0:
                   return (i, 1)  # Remove 1 from first non-empty heap

       # Find move to make Nim-sum = 0
       for i, heap in enumerate(heaps):
           target_size = heap ^ current_sum
           if target_size < heap:
               # Found it! Remove (heap - target_size) from heap i
               return (i, heap - target_size)

**Proof of Optimality:**

1. From Nim-sum = 0 position, any move creates Nim-sum ≠ 0
2. From Nim-sum ≠ 0 position, there exists a move to Nim-sum = 0
3. Therefore, with optimal play from Nim-sum ≠ 0, you can always force a win

Misère Nim
~~~~~~~~~~

In misère (take last object loses):

.. code-block:: python

   def misere_nim_strategy(heaps):
       """Optimal strategy for misère Nim.

       Strategy differs in endgame:
       - If all heaps ≤ 1: Play to leave odd number of heaps
       - Otherwise: Play normal Nim (make Nim-sum = 0)
       """
       if all(h <= 1 for h in heaps):
           # Endgame: count non-empty heaps
           non_empty = sum(1 for h in heaps if h > 0)

           # Want to leave odd number
           if non_empty % 2 == 0:
               # Remove a heap
               for i, h in enumerate(heaps):
                   if h > 0:
                       return (i, h)
           else:
               # Do nothing (pass)
               return None

       else:
           # Normal Nim strategy
           return optimal_move(heaps)

Performance Comparison
----------------------

Algorithm Performance
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Algorithm         | Time Complexity | Space | Accuracy | Use Case
   ------------------|-----------------|-------|----------|----------
   Minimax           | O(b^d)          | O(d)  | Perfect  | Small trees
   Alpha-Beta        | O(b^(d/2))      | O(d)  | Perfect  | Medium trees
   Monte Carlo       | O(s)            | O(1)  | ±ε       | Large/imperfect
   Opponent Model    | O(n)            | O(n)  | Variable | Learning
   Probability Map   | O(n²)           | O(n²) | Heuristic| Battleship
   Nim-Sum           | O(n)            | O(1)  | Perfect  | Nim

   s = simulations, n = game state size, b = branching factor, d = depth

Decision Speed
~~~~~~~~~~~~~~

Typical decision times:

* **Minimax** (3x3 Tic-Tac-Toe): <1ms
* **Alpha-Beta** (Ultimate TTT): 10-100ms
* **Monte Carlo** (1000 sims): 50-200ms
* **Opponent Model Update**: <1ms
* **Probability Map**: 10-50ms

Next Steps
----------

* See specific game architectures:

  * :doc:`poker_architecture` for Monte Carlo details
  * :doc:`bluff_architecture` for opponent modeling

* Explore code examples:

  * :doc:`../examples/ai_examples` for implementation samples

* Read academic papers on game AI for deeper understanding
