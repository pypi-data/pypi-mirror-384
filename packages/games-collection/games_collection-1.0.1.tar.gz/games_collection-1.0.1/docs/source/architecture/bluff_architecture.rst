Bluff Architecture
==================

This document describes the architecture and design of the Bluff (Cheat) card game
implementation, focusing on game mechanics, AI psychology, and challenge resolution.

Overview
--------

The Bluff module implements a complete card game of deception where players must
claim card ranks while playing cards face-down. The implementation features:

* Full hand management for all players (bots and human)
* Psychological AI that tracks opponent behavior
* Dynamic difficulty levels with distinct bot personalities
* Challenge resolution system
* Support for multiple decks
* Both CLI and GUI interfaces

Architecture Diagram
--------------------

.. code-block:: text

   ┌─────────────────────────────────────────────────┐
   │              User Interfaces                    │
   │  ┌──────────────┐      ┌──────────────┐        │
   │  │ CLI          │      │ GUI (Tkinter)│        │
   │  │ (__main__)   │      │ (gui.py)     │        │
   │  └──────┬───────┘      └──────┬───────┘        │
   └─────────┼────────────────────┼─────────────────┘
             │                    │
             └────────┬───────────┘
                      │
   ┌──────────────────▼──────────────────────┐
   │          BluffGame (Engine)             │
   │  ┌────────────────────────────────┐    │
   │  │ Game State Management          │    │
   │  │ - Current phase (Turn/Challenge)│   │
   │  │ - Pile of claimed cards        │    │
   │  │ - Round tracking               │    │
   │  └────────────────────────────────┘    │
   │                                         │
   │  ┌────────────────────────────────┐    │
   │  │ Challenge Resolution           │    │
   │  │ - Verify claims                │    │
   │  │ - Determine outcomes           │    │
   │  │ - Transfer piles               │    │
   │  └────────────────────────────────┘    │
   └──────────────┬──────────────────────────┘
                  │
      ┌───────────┼────────────┐
      │           │            │
   ┌──▼────┐  ┌──▼─────┐  ┌──▼───┐
   │Player │  │Bot AI  │  │ Pile │
   │State  │  │Logic   │  │      │
   └───────┘  └────────┘  └──────┘
                  │
           ┌──────┴───────┐
           │              │
      ┌────▼────┐   ┌─────▼──────┐
      │Suspicion│   │ Bluff      │
      │Tracking │   │ Strategy   │
      └─────────┘   └────────────┘

Core Components
---------------

Game Phases
~~~~~~~~~~~

The game operates in distinct phases:

.. code-block:: python

   class Phase(Enum):
       """Game lifecycle phases."""
       TURN = auto()       # Player making a claim
       CHALLENGE = auto()  # Others can challenge
       COMPLETE = auto()   # Game ended

   class BluffGame:
       def __init__(self):
           self.phase = Phase.TURN
           self.current_player_idx = 0
           self.pending_claim = None

**Phase Transitions:**

.. code-block:: text

   TURN → Player plays card and makes claim
     ↓
   CHALLENGE → Other players can challenge
     ↓
   If challenged → Resolve → Return to TURN
   If not challenged → Add to pile → Next player's TURN
     ↓
   When hand empty or rounds complete → COMPLETE

Player State
~~~~~~~~~~~~

Each player maintains comprehensive state:

.. code-block:: python

   @dataclass
   class PlayerState:
       """Complete player state."""
       name: str
       hand: List[Card]
       is_bot: bool

       # Statistics for AI decision making
       total_claims: int = 0
       caught_lying: int = 0
       successful_bluffs: int = 0
       challenges_made: int = 0
       successful_challenges: int = 0

       # Bot personality (if bot)
       personality: Optional[BotPersonality] = None

**Why Track Statistics:**

* AI uses opponent history to inform decisions
* Detect patterns (frequent liars vs honest players)
* Adjust challenge threshold dynamically
* Inform bluffing strategy

The Pile
~~~~~~~~

The discard pile is central to gameplay:

.. code-block:: python

   class BluffGame:
       def __init__(self):
           self.pile: Deque[Card] = deque()
           self.pile_claims: List[Tuple[str, str]] = []

       def add_to_pile(self, card: Card, claimed_rank: str, player: str):
           """Add card to pile with claim."""
           self.pile.append(card)
           self.pile_claims.append((claimed_rank, player))

       def resolve_challenge(self, challenger_idx: int):
           """Resolve challenge and transfer pile."""
           last_card = self.pile[-1]
           claimed_rank = self.pile_claims[-1][0]

           if last_card.rank == claimed_rank:
               # Truth - challenger takes pile
               return self.transfer_pile_to(challenger_idx)
           else:
               # Lie - claimer takes pile
               return self.transfer_pile_to(self.current_player_idx)

Game Flow
---------

Complete Turn Sequence
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   1. PLAYER'S TURN
      │
      ├─> Player views their hand
      ├─> Player selects a card to play
      └─> Player claims a rank for that card

   2. CHALLENGE WINDOW
      │
      ├─> All other players see the claim
      ├─> Each player decides: Challenge or Pass
      └─> First challenger gets to challenge

   3. CHALLENGE RESOLUTION (if challenged)
      │
      ├─> Reveal the played card
      ├─> Compare to claim
      │
      ├──> MATCH (truth)
      │    ├─> Challenger takes entire pile
      │    └─> Claimer continues playing
      │
      └──> MISMATCH (lie)
           ├─> Claimer takes entire pile
           └─> Challenger continues playing

   4. NO CHALLENGE
      │
      ├─> Card added to pile (remains face-down)
      └─> Next player's turn

   5. ROUND/GAME END CHECK
      │
      ├─> Player emptied hand? → Win round
      ├─> All rounds complete? → End game
      └─> Continue to next player

Round Completion
~~~~~~~~~~~~~~~~

A round ends when:

1. **Winner by Elimination**: One player empties their hand completely
2. **Winner by Count**: After all turns, player with fewest cards wins

.. code-block:: python

   def check_round_end(self) -> Optional[int]:
       """Check if round has ended.

       Returns:
           int: Winner index, or None if round continues
       """
       # Check for empty hand
       for idx, player in enumerate(self.players):
           if len(player.hand) == 0:
               return idx

       # Check if all players had equal turns
       if self.turns_this_round >= len(self.players) * self.max_turns:
           # Find player with fewest cards
           return min(enumerate(self.players),
                     key=lambda x: len(x[1].hand))[0]

       return None

AI Strategy
-----------

Bot Decision Making
~~~~~~~~~~~~~~~~~~~

Bots make two key decisions: when to lie and when to challenge.

**Deciding Whether to Lie:**

.. code-block:: python

   def should_bot_lie(bot: PlayerState, claimed_rank: str,
                      pile_size: int, difficulty: DifficultyLevel) -> bool:
       """Determine if bot should lie about a card.

       Factors:
       - Bot personality (from difficulty level)
       - Pile size (lower risk for small piles)
       - Opponent history (less likely to be challenged)
       - Current hand composition
       """
       # Has the card - usually tell truth
       has_rank = any(c.rank == claimed_rank for c in bot.hand)
       if has_rank and random.random() > difficulty.bluff_frequency:
           return False

       # Risk assessment based on pile size
       pile_risk = min(1.0, pile_size / 20)  # Larger pile = more risk

       # Historical success rate
       if bot.total_claims > 0:
           success_rate = bot.successful_bluffs / bot.total_claims
       else:
           success_rate = 0.5

       # Decide based on personality
       lie_threshold = difficulty.bluff_frequency * (1 - pile_risk)
       lie_threshold *= (1 + success_rate)

       return random.random() < lie_threshold

**Deciding Whether to Challenge:**

.. code-block:: python

   def should_bot_challenge(bot: PlayerState, claimer: PlayerState,
                           claimed_rank: str, difficulty: DifficultyLevel) -> bool:
       """Determine if bot should challenge a claim.

       Factors:
       - Claimer's history (frequent liar?)
       - Bot's hand (do we have many of claimed rank?)
       - Bot personality (aggression level)
       - Pile size (worth the risk?)
       """
       # Check claimer's history
       if claimer.total_claims > 3:
           liar_rate = claimer.caught_lying / claimer.total_claims
       else:
           liar_rate = 0.3  # Assume moderate lying

       # Do we have many of the claimed rank?
       # More we have, less likely they have it
       we_have_count = sum(1 for c in bot.hand if c.rank == claimed_rank)
       suspicion = we_have_count * 0.15

       # Personality factor
       challenge_threshold = difficulty.challenge_frequency
       challenge_threshold += suspicion
       challenge_threshold += liar_rate * 0.5

       return random.random() < challenge_threshold

Difficulty Levels
~~~~~~~~~~~~~~~~~

Each difficulty creates a distinct personality:

.. code-block:: python

   @dataclass
   class DifficultyLevel:
       """Bot personality parameters."""
       name: str
       num_bots: int
       num_decks: int
       bluff_frequency: float      # How often to lie
       challenge_frequency: float  # How often to challenge
       suspicion_memory: int       # How many turns to remember

   DIFFICULTY_LEVELS = {
       'Noob': DifficultyLevel(
           num_bots=1,
           num_decks=1,
           bluff_frequency=0.15,      # Rarely bluffs
           challenge_frequency=0.2,   # Rarely challenges
           suspicion_memory=3         # Short memory
       ),
       'Insane': DifficultyLevel(
           num_bots=4,
           num_decks=3,
           bluff_frequency=0.55,      # Lies often!
           challenge_frequency=0.45,  # Challenges aggressively
           suspicion_memory=15        # Long memory
       ),
       # ... other levels
   }

**Personality Differences:**

* **Noob**: Cautious, honest, forgetful
* **Easy**: Slightly deceptive, moderate challenges
* **Medium**: Balanced bluffing and detecting
* **Hard**: Bold lies, sharp detection
* **Insane**: Constant deception, aggressive policing

Opponent Modeling
~~~~~~~~~~~~~~~~~

Bots track opponent behavior:

.. code-block:: python

   class OpponentModel:
       """Track opponent patterns."""

       def __init__(self, player_name: str):
           self.name = player_name
           self.recent_claims = deque(maxlen=10)
           self.lie_history = []
           self.challenge_history = []

       def update_claim(self, rank: str, was_truthful: bool):
           """Record a claim result."""
           self.recent_claims.append((rank, was_truthful))
           if not was_truthful:
               self.lie_history.append(rank)

       def get_trust_score(self) -> float:
           """Calculate trust score (0.0 = always lies, 1.0 = always honest)."""
           if not self.recent_claims:
               return 0.5  # Neutral

           truthful_count = sum(1 for _, truth in self.recent_claims if truth)
           return truthful_count / len(self.recent_claims)

       def is_suspicious(self, claimed_rank: str) -> bool:
           """Check if this claim is suspicious."""
           # Recently lied about this rank?
           recent_lies = [r for r in self.lie_history[-5:]]
           if claimed_rank in recent_lies:
               return True

           # Low trust score?
           if self.get_trust_score() < 0.3:
               return True

           return False

Challenge Dynamics
------------------

Multiple Challengers
~~~~~~~~~~~~~~~~~~~~

Multiple players can attempt to challenge:

.. code-block:: python

   def collect_challenges(self, claimer_idx: int) -> List[int]:
       """Collect challenges from all players except claimer.

       Returns:
           List of player indices who want to challenge
       """
       challengers = []

       for idx, player in enumerate(self.players):
           if idx == claimer_idx:
               continue

           if player.is_bot:
               if self.bot_should_challenge(player, claimer_idx):
                   challengers.append(idx)
           else:
               # Ask human player
               if self.prompt_for_challenge(player):
                   challengers.append(idx)

       return challengers

**Priority System:**

1. First player to challenge gets priority
2. If multiple bots challenge simultaneously, random selection
3. Other challengers lose their opportunity

Pile Transfer Logic
~~~~~~~~~~~~~~~~~~~

When a challenge is resolved:

.. code-block:: python

   def transfer_pile_to(self, player_idx: int):
       """Transfer entire pile to a player.

       Args:
           player_idx: Player receiving the pile
       """
       player = self.players[player_idx]

       # Add all cards to player's hand
       player.hand.extend(self.pile)

       # Log the transfer
       self.log_event(f"{player.name} takes pile of {len(self.pile)} cards")

       # Clear pile
       self.pile.clear()
       self.pile_claims.clear()

       # Update statistics
       if player_idx == self.current_player_idx:
           # They lied and were caught
           player.caught_lying += 1
       else:
           # They challenged successfully
           player.successful_challenges += 1

Edge Cases
----------

Empty Hand During Turn
~~~~~~~~~~~~~~~~~~~~~~

If a player empties their hand:

.. code-block:: python

   def play_card(self, card_idx: int, claimed_rank: str):
       """Play a card and make a claim."""
       card = self.current_player.hand.pop(card_idx)
       self.add_to_pile(card, claimed_rank, self.current_player.name)

       # Check for immediate win
       if len(self.current_player.hand) == 0:
           self.phase = Phase.COMPLETE
           self.declare_winner(self.current_player_idx)
       else:
           self.phase = Phase.CHALLENGE

All Players Folded
~~~~~~~~~~~~~~~~~~

In rare cases where all players fold (pile becomes too large):

* Game continues with smaller pile
* Players can't skip turns
* Eventually someone must take the pile

Multiple Decks
~~~~~~~~~~~~~~

With multiple decks, card counting becomes complex:

* More cards of each rank available
* Harder to detect lies based on hand composition
* Increases game chaos and unpredictability

Statistics and Analytics
------------------------

Tracked Metrics
~~~~~~~~~~~~~~~

For each player:

.. code-block:: python

   @dataclass
   class PlayerStats:
       """Comprehensive player statistics."""
       games_played: int = 0
       games_won: int = 0

       total_claims: int = 0
       truthful_claims: int = 0
       bluff_claims: int = 0

       times_challenged: int = 0
       caught_lying: int = 0
       falsely_accused: int = 0

       challenges_made: int = 0
       successful_challenges: int = 0
       failed_challenges: int = 0

       cards_collected: int = 0  # From taking piles

       @property
       def bluff_rate(self) -> float:
           """Percentage of claims that were bluffs."""
           if self.total_claims == 0:
               return 0.0
           return self.bluff_claims / self.total_claims

       @property
       def challenge_accuracy(self) -> float:
           """Percentage of challenges that were correct."""
           if self.challenges_made == 0:
               return 0.0
           return self.successful_challenges / self.challenges_made

Post-Game Analysis
~~~~~~~~~~~~~~~~~~

After each game:

* Display player statistics
* Show bluff success rates
* Highlight most deceptive player
* Show challenge accuracy

Extensibility
-------------

Adding New Bot Personalities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Easy to create custom personalities:

.. code-block:: python

   CUSTOM_LEVEL = DifficultyLevel(
       name="Paranoid",
       num_bots=2,
       num_decks=2,
       bluff_frequency=0.25,      # Moderate bluffing
       challenge_frequency=0.70,  # Challenge everything!
       suspicion_memory=20        # Never forget
   )

Custom Game Modes
~~~~~~~~~~~~~~~~~

The architecture supports variants:

* **Truth Mode**: No bluffing allowed (must play claimed card)
* **Chaos Mode**: Multiple cards can be played per turn
* **Team Mode**: Players form teams, share knowledge

Testing
-------

Comprehensive test coverage:

.. code-block:: python

   class TestBluffGame(unittest.TestCase):
       def test_challenge_resolution(self):
           """Test challenge outcomes."""
           game = BluffGame(num_players=3)

           # Bot lies about card
           game.play_card(0, claimed_rank='A')
           initial_pile = len(game.pile)

           # Human challenges
           game.challenge(challenger_idx=1)

           # Pile should transfer to liar
           self.assertEqual(len(game.players[0].hand),
                          initial_hand_size + initial_pile)

       def test_bot_decision_making(self):
           """Test AI makes reasonable decisions."""
           bot = PlayerState(name="Bot", hand=[...], is_bot=True)

           # With card in hand, should usually tell truth
           decisions = [should_bot_lie(bot, 'A', pile_size=5, ...)
                       for _ in range(100)]
           truth_rate = sum(1 for d in decisions if not d) / 100
           self.assertGreater(truth_rate, 0.7)

Performance Considerations
--------------------------

The implementation is optimized for smooth gameplay:

* **O(1)** pile transfers using deques
* **O(n)** challenge resolution (n = number of players)
* Efficient hand management
* Minimal memory footprint

GUI Updates
~~~~~~~~~~~

The GUI efficiently updates:

.. code-block:: python

   def update_display(self):
       """Update GUI without full redraw."""
       # Only update changed elements
       self.update_card_counts()
       self.update_pile_display()
       self.append_to_log(latest_event)
       # Don't redraw entire window

Next Steps
----------

* Review :doc:`poker_architecture` for comparison with poker
* See :doc:`ai_strategies` for detailed AI algorithms
* Check :doc:`../examples/bluff_examples` for code samples
