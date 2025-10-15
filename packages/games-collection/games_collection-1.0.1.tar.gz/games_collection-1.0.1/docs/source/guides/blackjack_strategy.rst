Blackjack Strategy Guide
========================

Master the game of blackjack with basic strategy, card counting, and bankroll management.

Basic Strategy
--------------

Basic strategy is the mathematically optimal way to play every hand in blackjack.

Hard Hands (No Ace or Ace counts as 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Always Stand:**
* 17 or higher

**Always Hit:**
* 8 or lower

**Dealer Shows 2-6 (Dealer Bust Zone):**
* Stand on 12-16 (let dealer bust)
* Exception: Hit 12 vs dealer 2 or 3

**Dealer Shows 7-Ace (Dealer Strong):**
* Hit on 12-16
* Dealer likely has 17+, so you need 17+

Soft Hands (Ace counted as 11)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Soft 19-20:**
* Always stand

**Soft 18:**
* Stand vs dealer 2, 7, 8
* Double vs dealer 3-6 (if allowed)
* Hit vs dealer 9, 10, Ace

**Soft 17 or lower:**
* Always hit
* Double on soft 13-18 vs dealer 4-6

Doubling Down
~~~~~~~~~~~~~

Double down when you have the advantage:

**Always Double:**
* 11 vs dealer 2-10
* 10 vs dealer 2-9

**Sometimes Double:**
* 9 vs dealer 3-6
* Soft 13-18 vs dealer 4-6

Splitting Pairs
~~~~~~~~~~~~~~~

**Always Split:**
* Aces - But only get one card per Ace
* 8s - Two 16s is bad, two hands from 8 is good

**Never Split:**
* 10s - 20 is too strong to break up
* 5s - 10 is perfect for doubling
* 4s - 8 is better than two 4s

**Conditional Splits:**
* 2s, 3s: Split vs dealer 4-7
* 6s: Split vs dealer 2-6
* 7s: Split vs dealer 2-7
* 9s: Split vs dealer 2-9 except 7

Understanding the Dealer
------------------------

Dealer Bust Probabilities
~~~~~~~~~~~~~~~~~~~~~~~~~~

The dealer must follow strict rules (hit on 16, stand on 17+):

**Dealer Upcard → Bust Probability:**

* 2 → 35%
* 3 → 37%
* 4 → 40%
* 5 → 42%
* 6 → 42%
* 7 → 26%
* 8 → 24%
* 9 → 23%
* 10 → 21%
* Ace → 17%

When dealer shows 5 or 6, they bust most often!

Card Counting (Hi-Lo System)
-----------------------------

Card counting tracks the ratio of high to low cards.

The Hi-Lo System
~~~~~~~~~~~~~~~~

**Assign Values:**

* 2, 3, 4, 5, 6: +1 (low cards favor dealer)
* 7, 8, 9: 0 (neutral)
* 10, J, Q, K, A: -1 (high cards favor player)

**Running Count:**

Keep a mental tally as cards are revealed:

.. code-block:: text

   Cards: 5, K, 3, 7, Q, 2, A
   Count: +1, 0, +1, +1, 0, +1, 0 = +3

**True Count:**

Divide running count by decks remaining:

.. code-block:: text

   Running Count: +8
   Decks Remaining: 4
   True Count: +8 ÷ 4 = +2

**Using the Count:**

* True count < 0: Deck favors dealer, bet minimum
* True count = 0 to +1: Neutral, standard bet
* True count ≥ +2: Deck favors player, increase bet
* True count ≥ +3: Strong advantage, max bet

Strategy Deviations
~~~~~~~~~~~~~~~~~~~

Adjust basic strategy based on true count:

**True Count +3 or Higher:**

* Stand on 16 vs dealer 10
* Stand on 15 vs dealer 10
* Take insurance on blackjack

**True Count +2:**

* Stand on 12 vs dealer 3

**True Count 0 or Lower:**

* Hit on 16 vs dealer 10 (normal play)

Bankroll Management
-------------------

Proper bankroll management is essential for long-term success.

Betting Strategy
~~~~~~~~~~~~~~~~

**Conservative (Recommended):**

* Bet 1-1.5% of total bankroll per hand
* Example: $1,000 bankroll → $10-15 per hand

**Aggressive:**

* Bet 2-5% of total bankroll
* Higher risk, higher variance
* Example: $1,000 bankroll → $20-50 per hand

**Card Counting Spread:**

* True count ≤ 0: 1 unit (minimum)
* True count +1: 2 units
* True count +2: 4 units
* True count +3: 8 units
* True count +4 or higher: 12 units

Loss Limits
~~~~~~~~~~~

Set and stick to loss limits:

* **Session limit:** 20-30% of total bankroll
* **Daily limit:** 50% of total bankroll
* **Stop when:** You lose predetermined amount
* **Never chase:** Don't increase bets to recover losses

Win Goals
~~~~~~~~~

Consider taking profits:

* **Session goal:** 50-100% profit
* **Lock in:** Set aside original bankroll after doubling
* **Play with profits:** Use only winnings for subsequent bets

House Edge
----------

Understanding the House Edge
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Basic Strategy:**

* Single deck: ~0.5% house edge
* Six decks: ~0.6% house edge
* Eight decks: ~0.65% house edge

**Poor Play:**

* Playing hunches: ~2-4% house edge
* Ignoring basic strategy: ~3-5% house edge

**Card Counting:**

* True count +3: ~1% player advantage
* True count +4: ~2% player advantage

**Factors Affecting Edge:**

* Dealer hits soft 17: +0.2% house edge
* Blackjack pays 6:5 instead of 3:2: +1.4% house edge
* Late surrender allowed: -0.06% house edge
* Double after split allowed: -0.15% house edge

Common Mistakes
---------------

**1. Taking Insurance**
   Never take insurance unless counting and true count ≥ +3

**2. Playing Hunches**
   Stick to basic strategy, don't "feel" what's coming

**3. Not Splitting Aces and 8s**
   These are mathematically correct splits

**4. Splitting 10s**
   20 is too strong to break up

**5. Standing on Soft 18 vs 9, 10, Ace**
   You must improve this hand

**6. Poor Bankroll Management**
   Betting too much leads to ruin

**7. Chasing Losses**
   Increasing bets when losing is recipe for disaster

**8. Not Learning Basic Strategy**
   Basic strategy reduces house edge significantly

Practice Drills
---------------

**Drill 1: Hard Hands**

What's the correct play?

1. You have 16, dealer shows 7
2. You have 12, dealer shows 3
3. You have 11, dealer shows 6

**Answers:** 1. Hit, 2. Hit, 3. Double

**Drill 2: Soft Hands**

What's the correct play?

1. You have A-7 (soft 18), dealer shows 4
2. You have A-6 (soft 17), dealer shows 8
3. You have A-8 (soft 19), dealer shows 10

**Answers:** 1. Double, 2. Hit, 3. Stand

**Drill 3: Pairs**

Should you split?

1. Pair of 8s vs dealer 10
2. Pair of 10s vs dealer 6
3. Pair of 9s vs dealer 7

**Answers:** 1. Yes, 2. No, 3. No

**Drill 4: Card Counting**

Calculate the running count:

.. code-block:: text

   Cards dealt: K, 5, 3, J, 2, 8, A, 6, Q

   K: -1
   5: +1
   3: +1
   J: -1
   2: +1
   8: 0
   A: -1
   6: +1
   Q: -1

   Running Count: 0

Advanced Topics
---------------

Shuffle Tracking
~~~~~~~~~~~~~~~~

Advanced technique to track clusters of high cards through shuffle.

Team Play
~~~~~~~~~

Multiple counters working together to maximize advantage.

Camouflage
~~~~~~~~~~

Techniques to avoid detection:

* Vary bet sizes with non-count factors
* Make occasional basic strategy "errors"
* Act like recreational player
* Tip dealers appropriately

Further Reading
---------------

* **Books:**
  * "Beat the Dealer" by Edward O. Thorp
  * "Professional Blackjack" by Stanford Wong
  * "Blackjack Attack" by Don Schlesinger

* **Practice:**
  * Use our educational mode with card counting hints
  * Practice basic strategy until automatic
  * Start counting with single deck, then progress
