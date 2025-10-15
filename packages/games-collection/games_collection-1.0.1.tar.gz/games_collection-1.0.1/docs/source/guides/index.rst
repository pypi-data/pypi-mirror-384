Strategy Guides
===============

Comprehensive strategy guides and educational resources for mastering the games.

.. toctree::
   :maxdepth: 2
   :caption: Game Strategy Guides:

   poker_strategy
   blackjack_strategy
   game_theory

Poker Strategy
--------------

Learn fundamental poker strategy including:

* Hand selection and position play
* Pot odds and expected value
* Betting strategy and bluffing
* Tournament considerations

:doc:`poker_strategy`

Blackjack Strategy
------------------

Master blackjack with:

* Complete basic strategy charts
* Card counting (Hi-Lo system)
* Bankroll management
* Common mistakes to avoid

:doc:`blackjack_strategy`

Game Theory Concepts
--------------------

Understand the mathematics behind the games:

* Minimax algorithm
* Monte Carlo simulation
* Nim-sum (XOR strategy)
* Expected value calculations
* Nash equilibrium

:doc:`game_theory`

Educational Features
--------------------

The games collection includes built-in educational features:

Tutorial Modes
~~~~~~~~~~~~~~

Step-by-step tutorials for learning each game:

.. code-block:: python

    from card_games.poker.educational import PokerTutorialMode

    tutorial = PokerTutorialMode()
    step = tutorial.get_current_step()
    print(step.title)
    print(step.description)

AI Move Explanations
~~~~~~~~~~~~~~~~~~~~

Have the AI explain its decisions:

.. code-block:: python

    # Nim with explanations
    heap_idx, count, explanation = game.computer_move(explain=True)
    print(explanation)
    # "Nim-sum is 2 (winning position). Removing 1 from heap 3 to achieve nim-sum of 0."

Probability Calculators
~~~~~~~~~~~~~~~~~~~~~~~

Calculate odds during gameplay:

.. code-block:: python

    from card_games.poker.educational import PokerProbabilityCalculator

    calc = PokerProbabilityCalculator()
    win_prob = calc.calculate_win_probability(table_state)
    pot_odds_analysis = calc.format_pot_odds_comparison(20, 100, win_prob)
    print(pot_odds_analysis)

Strategy Tips
~~~~~~~~~~~~~

Get context-aware strategy advice:

.. code-block:: python

    from common import StrategyTipProvider, StrategyTip

    tip_provider = StrategyTipProvider()
    tip = tip_provider.get_random_tip()
    print(f"{tip.title}: {tip.description}")

Game Theory Explanations
~~~~~~~~~~~~~~~~~~~~~~~~~

Learn about the algorithms:

.. code-block:: python

    from common import GameTheoryExplainer

    explainer = GameTheoryExplainer()
    monte_carlo = explainer.get_explanation("monte_carlo")
    print(monte_carlo.description)
    print(monte_carlo.example)

Practice and Improvement
-------------------------

Tips for Improving
~~~~~~~~~~~~~~~~~~

1. **Start with basics:** Master fundamental strategy before advanced techniques
2. **Use educational mode:** Enable tutorials and hints when learning
3. **Analyze decisions:** Review why certain plays are optimal
4. **Practice regularly:** Consistent practice builds intuition
5. **Learn from mistakes:** Pay attention to suboptimal decisions
6. **Study theory:** Understanding the math improves decision-making
7. **Adjust to opponents:** Observe patterns and adapt strategy

Recommended Learning Path
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Beginners:**

1. Complete tutorial mode for chosen game
2. Read basic strategy guide
3. Practice with hints enabled
4. Focus on avoiding common mistakes

**Intermediate:**

1. Study probability calculations
2. Learn game theory concepts
3. Practice without hints
4. Experiment with different strategies

**Advanced:**

1. Master optimal play (minimax, GTO)
2. Understand opponent exploitation
3. Study advanced concepts (Nash equilibrium, etc.)
4. Compete in tournament modes

Additional Resources
--------------------

In-Game Help
~~~~~~~~~~~~

All games include:

* Interactive tutorials
* Strategy hints during play
* AI move explanations
* Probability calculators (where applicable)

Documentation
~~~~~~~~~~~~~

* :doc:`../tutorials/index` - Getting started guides
* :doc:`../architecture/index` - How the games work
* :doc:`../examples/index` - Code examples

External Resources
~~~~~~~~~~~~~~~~~~

**Poker:**

* Books: "The Theory of Poker," "Harrington on Hold'em"
* Websites: Upswing Poker, Run It Once

**Blackjack:**

* Books: "Beat the Dealer," "Professional Blackjack"
* Practice: Blackjack trainers, card counting apps

**Game Theory:**

* Courses: Khan Academy Game Theory, MIT OCW
* Books: "The Art of Strategy," "Game Theory 101"
