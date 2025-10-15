Game Theory in Games
====================

This guide explains the game theory concepts and algorithms used in the games collection.

Minimax Algorithm
-----------------

What is Minimax?
~~~~~~~~~~~~~~~~

Minimax is a decision-making algorithm for two-player zero-sum games. It assumes both players play optimally:

* **Maximizer:** Tries to maximize their score
* **Minimizer:** Tries to minimize the maximizer's score

The algorithm recursively explores all possible game states to find the best move.

How It Works
~~~~~~~~~~~~

1. **Build game tree:** Explore all possible moves from current state
2. **Evaluate leaf nodes:** Assign scores to terminal states
3. **Propagate scores up:**

   * Max player chooses maximum score
   * Min player chooses minimum score

4. **Select best move:** Choose move leading to best score at current level

Example: Tic-Tac-Toe
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

           Current State (X to move)
                  |
        /---------+---------\
       /          |          \
    Move A     Move B     Move C
   (Score 0)  (Score 1)  (Score -1)

   X chooses Move B (highest score = 1)

Python Implementation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def minimax(state, depth, is_maximizing):
        """Minimax algorithm for optimal play."""
        # Base case: game over or max depth
        if state.is_terminal() or depth == 0:
            return state.evaluate()

        if is_maximizing:
            # Maximizer: choose highest value
            best_value = float('-inf')
            for move in state.get_valid_moves():
                new_state = state.make_move(move)
                value = minimax(new_state, depth - 1, False)
                best_value = max(best_value, value)
            return best_value
        else:
            # Minimizer: choose lowest value
            best_value = float('inf')
            for move in state.get_valid_moves():
                new_state = state.make_move(move)
                value = minimax(new_state, depth - 1, True)
                best_value = min(best_value, value)
            return best_value

Alpha-Beta Pruning
~~~~~~~~~~~~~~~~~~

Optimization that prunes branches that won't affect the final decision:

.. code-block:: python

    def minimax_ab(state, depth, alpha, beta, is_maximizing):
        """Minimax with alpha-beta pruning."""
        if state.is_terminal() or depth == 0:
            return state.evaluate()

        if is_maximizing:
            best_value = float('-inf')
            for move in state.get_valid_moves():
                new_state = state.make_move(move)
                value = minimax_ab(new_state, depth - 1, alpha, beta, False)
                best_value = max(best_value, value)
                alpha = max(alpha, best_value)
                if beta <= alpha:
                    break  # Beta cutoff
            return best_value
        else:
            best_value = float('inf')
            for move in state.get_valid_moves():
                new_state = state.make_move(move)
                value = minimax_ab(new_state, depth - 1, alpha, beta, True)
                best_value = min(best_value, value)
                beta = min(beta, best_value)
                if beta <= alpha:
                    break  # Alpha cutoff
            return best_value

Used In:
~~~~~~~~

* **Tic-Tac-Toe:** Perfect play with full game tree
* **Connect Four:** Limited depth due to branching factor
* **Checkers:** With evaluation heuristics

Monte Carlo Simulation
----------------------

What is Monte Carlo?
~~~~~~~~~~~~~~~~~~~~

Monte Carlo methods use random sampling to estimate outcomes when exact calculation is too complex.

How It Works
~~~~~~~~~~~~

1. **Run many simulations:** Play out random scenarios
2. **Track outcomes:** Record wins, losses, draws
3. **Calculate statistics:** Win rate approximates true probability
4. **Make decision:** Choose move with highest simulated win rate

Example: Poker Hand Strength
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Your hand: A♠ K♠
   Board: Q♠ J♠ 2♣

   Simulation 1: Deal random river/turn → You win
   Simulation 2: Deal random river/turn → You lose
   Simulation 3: Deal random river/turn → You win
   ...
   Simulation 1000: Deal random river/turn → You win

   Results: Won 682/1000 = 68.2% win rate

Python Implementation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def monte_carlo_estimate(state, move, simulations=1000):
        """Estimate win probability using Monte Carlo."""
        wins = 0

        for _ in range(simulations):
            # Make a copy and apply move
            sim_state = state.copy()
            sim_state.make_move(move)

            # Play out randomly to end
            while not sim_state.is_terminal():
                random_move = random.choice(sim_state.get_valid_moves())
                sim_state.make_move(random_move)

            # Check if we won
            if sim_state.winner() == state.current_player:
                wins += 1

        return wins / simulations

Monte Carlo Tree Search (MCTS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Advanced variant that builds a search tree:

1. **Selection:** Choose promising node to explore
2. **Expansion:** Add new child nodes
3. **Simulation:** Play out random game from new node
4. **Backpropagation:** Update statistics up the tree

Used In:
~~~~~~~~

* **Poker:** Estimate hand strength and win probability
* **Complex games:** When exact calculation is infeasible
* **AlphaGo:** Combined with deep learning

Nim-Sum (XOR Strategy)
----------------------

What is Nim-Sum?
~~~~~~~~~~~~~~~~

The nim-sum is the bitwise XOR of all heap sizes. It determines winning/losing positions.

The Bouton's Theorem
~~~~~~~~~~~~~~~~~~~~

**Winning Position:** Nim-sum ≠ 0 (there exists a winning move)

**Losing Position:** Nim-sum = 0 (all moves lead to losing position)

How It Works
~~~~~~~~~~~~

.. code-block:: text

   Heaps: [3, 4, 5]

   Binary representation:
   3 = 011
   4 = 100
   5 = 101
   ------
   XOR = 010 = 2 (non-zero = winning position!)

Finding Winning Move
~~~~~~~~~~~~~~~~~~~~

To win, make a move that results in nim-sum = 0:

.. code-block:: text

   Current: [3, 4, 5], nim-sum = 2

   Try removing from heap of 5:
   - Remove 3: [3, 4, 2], nim-sum = 5 ✗
   - Remove 4: [3, 4, 1], nim-sum = 6 ✗
   - Remove 5: [3, 4, 0], nim-sum = 7 ✗

   Winning move: Change 5 to 4 → [3, 4, 4], nim-sum = 3 ✓

Python Implementation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def calculate_nim_sum(heaps):
        """Calculate nim-sum using XOR."""
        nim_sum = 0
        for heap in heaps:
            nim_sum ^= heap
        return nim_sum

    def find_winning_move(heaps):
        """Find move that results in nim-sum = 0."""
        current_nim_sum = calculate_nim_sum(heaps)

        if current_nim_sum == 0:
            return None  # Already losing position

        for i, heap in enumerate(heaps):
            # Calculate target heap size
            target = heap ^ current_nim_sum
            if target < heap:
                # Remove (heap - target) objects from heap i
                return (i, heap - target)

        return None

Used In:
~~~~~~~~

* **Nim:** Classic combinatorial game
* **Nimble:** Movement variant
* **Similar games:** Any impartial game with XOR strategy

Expected Value
--------------

What is EV?
~~~~~~~~~~~

Expected Value is the average outcome if a decision were repeated many times.

Formula
~~~~~~~

.. code-block:: text

   EV = Σ (Probability_i × Outcome_i)

   Where:
   - Probability_i = chance of outcome i
   - Outcome_i = value of outcome i

Example: Poker Bet
~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Pot: $100
   Bet to call: $20
   Win probability: 30%

   EV = (0.30 × $100) - (0.70 × $20)
      = $30 - $14
      = +$16

   Positive EV = profitable call!

Example: Blackjack Insurance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Dealer shows Ace
   Insurance costs $10 (half original bet)
   Pays 2:1 if dealer has blackjack

   Probability dealer has blackjack ≈ 30.8%

   EV = (0.308 × $20) - (0.692 × $10)
      = $6.16 - $6.92
      = -$0.76

   Negative EV = don't take insurance!

Python Implementation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def calculate_ev(outcomes, probabilities, costs):
        """Calculate expected value of a decision."""
        if len(outcomes) != len(probabilities):
            raise ValueError("Outcomes and probabilities must match")

        ev = 0
        for outcome, prob in zip(outcomes, probabilities):
            ev += outcome * prob

        # Subtract costs
        for cost, prob in zip(costs, probabilities):
            ev -= cost * prob

        return ev

Decision Making
~~~~~~~~~~~~~~~

* **Positive EV:** Take this action (long-term profit)
* **Zero EV:** Neutral (break-even)
* **Negative EV:** Avoid this action (long-term loss)

Used In:
~~~~~~~~

* **Poker:** Bet sizing and calling decisions
* **Blackjack:** Insurance and side bet evaluation
* **All gambling games:** Understanding house edge

Nash Equilibrium
----------------

What is Nash Equilibrium?
~~~~~~~~~~~~~~~~~~~~~~~~~

A state where no player can improve by changing strategy if others don't change.

Example: Rock-Paper-Scissors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Optimal strategy: Play each move 1/3 of the time

   If opponent plays rock 50% of time:
   - You should play paper more often

   At equilibrium:
   - Both play each move 1/3 of time
   - No one can improve unilaterally

Game Theory Optimal (GTO)
~~~~~~~~~~~~~~~~~~~~~~~~~~

In poker, GTO is an unexploitable strategy:

* Play balanced ranges
* Can't be exploited by opponent
* May not be maximally profitable against specific opponents

Used In:
~~~~~~~~

* **Poker:** Balancing bluff/value ratios
* **Competitive games:** Preventing exploitation
* **Multi-player games:** Strategic balance

Practical Applications
----------------------

Combining Strategies
~~~~~~~~~~~~~~~~~~~~

Real AI opponents combine multiple techniques:

.. code-block:: python

    class HybridAI:
        def choose_move(self, state):
            if state.depth() < 4:
                # Use minimax for simple endgames
                return self.minimax(state)
            elif state.has_randomness():
                # Use Monte Carlo for probabilistic games
                return self.monte_carlo(state)
            else:
                # Use heuristic evaluation
                return self.heuristic_search(state)

Difficulty Levels
~~~~~~~~~~~~~~~~~

Adjust AI strength by varying parameters:

* **Easy:** Random moves or shallow search
* **Medium:** Limited Monte Carlo simulations
* **Hard:** Deep minimax or many simulations
* **Expert:** Perfect play with complete search

Learning and Adaptation
~~~~~~~~~~~~~~~~~~~~~~~~

Advanced AIs can adapt:

* Track opponent patterns
* Exploit weaknesses
* Adjust strategy based on history

Further Reading
---------------

**Books:**

* "The Art of Strategy" by Avinash Dixit
* "Game Theory 101" by William Spaniel
* "AI: A Modern Approach" by Russell & Norvig

**Online Resources:**

* Khan Academy - Game Theory
* MIT OpenCourseWare - Game Theory
* Chess programming wiki (for minimax)

**Papers:**

* Bouton's paper on Nim (1901)
* Shannon's paper on chess (1950)
* AlphaGo papers (DeepMind)
