# Educational Features

This document describes the educational features available in the games collection, designed to help players learn game
strategies, understand game theory concepts, and improve their skills.

## Overview

The educational features include:

1. **Tutorial Modes** - Step-by-step guidance for learning each game
1. **Strategy Tips** - Context-aware advice during gameplay
1. **AI Move Explanations** - Understanding why the AI made certain decisions
1. **Probability Calculators** - Calculate odds and probabilities in real-time
1. **Game Theory Explanations** - Learn about algorithms like minimax and Monte Carlo
1. **Strategy Guides** - Comprehensive documentation on optimal play
1. **Challenge Packs** - Practice scenarios and puzzles

## Tutorial Modes

Tutorial modes provide step-by-step guidance for learning games from scratch.

### Available Tutorials

- **Poker** - Learn Texas Hold'em basics, hand rankings, betting strategy
- **Blackjack** - Master card values, basic strategy, and card counting
- **Nim** - Understand the nim-sum and optimal play (existing)

### Usage

```python
from card_games.poker.educational import PokerTutorialMode

# Create tutorial
tutorial = PokerTutorialMode()

# Get current step
step = tutorial.get_current_step()
print(f"{step.title}")
print(f"{step.description}")
if step.hint:
    print(f"Hint: {step.hint}")

# Advance to next step
if tutorial.advance_step():
    print("Moved to next step")
else:
    print("Tutorial completed!")
```

### Creating Custom Tutorials

```python
from common import TutorialMode, TutorialStep

class MyGameTutorial(TutorialMode):
    def _create_tutorial_steps(self):
        return [
            TutorialStep(
                title="Welcome",
                description="Welcome to my game!",
                hint="This is just the beginning"
            ),
            TutorialStep(
                title="How to Play",
                description="Here's how to play...",
            ),
            # Add more steps...
        ]

tutorial = MyGameTutorial()
```

## Strategy Tips

Strategy tips provide context-aware advice during gameplay.

### Usage

```python
from common import StrategyTipProvider, StrategyTip

# Create provider and add tips
provider = StrategyTipProvider()
provider.add_tip(StrategyTip(
    title="Position Matters",
    description="Play more hands from late position",
    applies_to="Pre-flop decision-making",
    difficulty="beginner"
))

# Get random tip
tip = provider.get_random_tip()
print(f"{tip.title}: {tip.description}")

# Get tips by difficulty
beginner_tips = provider.get_tips_by_difficulty("beginner")
```

## AI Move Explanations

Get explanations for why the AI made specific moves.

### Nim (Existing Feature)

```python
from paper_games.nim import NimGame

game = NimGame([3, 5, 7])
heap_idx, count, explanation = game.computer_move(explain=True)
print(explanation)
# Output: "Nim-sum is 1 (winning position). Removing 2 from heap 3 to achieve nim-sum of 0."
```

### Extending to Other Games

```python
from common import AIExplainer

class MyGameAIExplainer(AIExplainer):
    def explain_move(self, state, move):
        # Analyze the state and move
        if is_strong_position(state):
            return f"Played {move} because position is strong"
        else:
            return f"Played {move} to improve position"
```

## Probability Calculators

Calculate odds and probabilities during gameplay.

### Poker Probability Calculator

```python
from card_games.poker.educational import PokerProbabilityCalculator

calc = PokerProbabilityCalculator()

# Calculate win probability (requires game state)
win_prob = calc.calculate_win_probability(table_state)
print(f"Win probability: {calc.format_probability(win_prob)}")

# Calculate pot odds
pot_odds = calc.calculate_pot_odds(amount_to_call=20, current_pot=100)
print(f"Pot odds: {calc.format_probability(pot_odds)}")

# Compare pot odds to equity
comparison = calc.format_pot_odds_comparison(
    amount_to_call=20,
    current_pot=100,
    win_probability=0.25
)
print(comparison)
# Output:
# Pot Odds: 16.7% (need to win 16.7% of the time to break even)
# Win Probability: 25.0%
# ✓ PROFITABLE CALL (+8.3% edge)
```

### Blackjack Probability Calculator

```python
from card_games.blackjack.educational import BlackjackProbabilityCalculator

calc = BlackjackProbabilityCalculator()

# Calculate bust probability
bust_prob = calc.calculate_bust_probability(hand_total=16)
print(f"Bust probability: {calc.format_probability(bust_prob)}")

# Get dealer bust probability
dealer_bust = calc.calculate_dealer_bust_probability(dealer_upcard_value=6)
print(f"Dealer bust probability: {calc.format_probability(dealer_bust)}")

# Get basic strategy recommendation
action = calc.get_basic_strategy_recommendation(
    player_total=16,
    dealer_upcard=10,
    is_soft=False,
    can_double=False
)
print(f"Recommended action: {action}")

# Get explanation
explanation = calc.explain_basic_strategy_decision(
    player_total=16,
    dealer_upcard=10,
    is_soft=False
)
print(explanation)
```

## Game Theory Explanations

Learn about the algorithms and concepts used in games.

### Usage

```python
from common import GameTheoryExplainer

explainer = GameTheoryExplainer()

# List available concepts
concepts = explainer.list_concepts()
print("Available concepts:", concepts)

# Get specific explanation
minimax = explainer.get_explanation("minimax")
print(f"Concept: {minimax.concept}")
print(f"Description: {minimax.description}")
if minimax.example:
    print(f"Example: {minimax.example}")

# Available explanations:
# - minimax: Minimax algorithm for optimal play
# - monte_carlo: Monte Carlo simulation for probability estimation
# - nim_sum: XOR strategy for Nim-like games
# - expected_value: EV calculations for decision-making
# - card_counting: Hi-Lo card counting system
```

### Adding Custom Explanations

```python
from common import GameTheoryExplanation

explanation = GameTheoryExplanation(
    concept="Alpha-Beta Pruning",
    description="Optimization of minimax that prunes unnecessary branches...",
    example="In a game tree with 1000 positions, alpha-beta can reduce this to 100...",
    code_snippet="def minimax_ab(state, alpha, beta): ..."
)

explainer.add_explanation(explanation)
```

## Strategy Guides

Comprehensive strategy documentation is available in the `docs/source/guides/` directory:

### Available Guides

1. **Poker Strategy** (`docs/source/guides/poker_strategy.rst`)

   - Pre-flop hand selection
   - Position strategy
   - Pot odds and EV
   - Betting strategy
   - Common mistakes

1. **Blackjack Strategy** (`docs/source/guides/blackjack_strategy.rst`)

   - Complete basic strategy
   - Card counting (Hi-Lo system)
   - Bankroll management
   - House edge analysis
   - Practice drills

1. **Game Theory** (`docs/source/guides/game_theory.rst`)

   - Minimax algorithm with code examples
   - Monte Carlo simulation
   - Nim-sum (XOR strategy)
   - Expected value calculations
   - Nash equilibrium concepts

### Viewing Guides

The guides are in reStructuredText format and can be:

1. Read directly as text files
1. Rendered with Sphinx documentation system
1. Converted to HTML, PDF, or other formats

## Challenge Packs

Practice your skills with pre-defined scenarios and puzzles.

### Available Challenge Packs

1. **Poker Fundamentals** - Practice pot odds, position play, and decision-making
1. **Blackjack Mastery** - Basic strategy scenarios and card counting situations
1. **Nim Puzzles** - Solve Nim positions using game theory

### Usage

```python
from common import get_default_challenge_manager, DifficultyLevel

# Get challenge manager with default packs
manager = get_default_challenge_manager()

# List available packs
packs = manager.list_packs()
print("Available packs:", packs)

# Get a specific pack
poker_pack = manager.get_pack("Poker Fundamentals")
print(f"Pack: {poker_pack.name}")
print(f"Description: {poker_pack.description}")
print(f"Challenges: {len(poker_pack)}")

# Get a specific challenge
challenge = poker_pack.get_challenge("poker_pot_odds_1")
print(f"\nChallenge: {challenge.title}")
print(f"Difficulty: {challenge.difficulty.value}")
print(f"Description: {challenge.description}")
print(f"Goal: {challenge.goal}")

# Show solution (after attempting)
print(f"\nSolution:\n{challenge.solution}")

# Filter by difficulty
beginner_challenges = poker_pack.get_challenges_by_difficulty(DifficultyLevel.BEGINNER)
print(f"\nBeginner challenges: {len(beginner_challenges)}")
```

### Creating Custom Challenges

```python
from common import Challenge, ChallengePack, DifficultyLevel

# Create a custom challenge
challenge = Challenge(
    id="my_challenge_1",
    title="Difficult Decision",
    description="You have 16, dealer shows 10. What do you do?",
    difficulty=DifficultyLevel.INTERMEDIATE,
    initial_state={"player": 16, "dealer": 10},
    goal="Make the optimal decision",
    solution="Hit. Hard 16 vs 10 requires hitting for optimal play.",
)

# Create a custom pack
pack = ChallengePack(
    name="My Custom Pack",
    description="Custom challenges for practice"
)
pack.add_challenge(challenge)

# Register with manager
manager.register_pack(pack)
```

## Integration Examples

### Adding Tutorial to a Game

```python
from common import TutorialMode, TutorialStep

class MyGameWithTutorial:
    def __init__(self, tutorial_mode=False):
        self.tutorial_mode = tutorial_mode
        if tutorial_mode:
            self.tutorial = MyGameTutorial()

    def play_turn(self):
        if self.tutorial_mode:
            step = self.tutorial.get_current_step()
            if step:
                print(f"\n📚 Tutorial: {step.title}")
                print(f"{step.description}")
                if step.hint:
                    print(f"💡 Hint: {step.hint}")

        # Regular game logic...
        self.make_move()

        if self.tutorial_mode and self.tutorial.validate_current_step(self):
            self.tutorial.advance_step()
```

### Adding Probability Display

```python
from card_games.poker.educational import PokerProbabilityCalculator

class PokerGameWithProbabilities:
    def __init__(self, show_probabilities=False):
        self.show_probabilities = show_probabilities
        if show_probabilities:
            self.calc = PokerProbabilityCalculator()

    def display_decision(self):
        if self.show_probabilities:
            win_prob = self.calc.calculate_win_probability(self.table)
            print(f"💹 Win Probability: {self.calc.format_probability(win_prob)}")

            if self.facing_bet:
                analysis = self.calc.format_pot_odds_comparison(
                    self.amount_to_call,
                    self.pot,
                    win_prob
                )
                print(f"\n{analysis}")
```

### Adding AI Explanations

```python
class GameWithAIExplanations:
    def __init__(self, explain_ai=False):
        self.explain_ai = explain_ai

    def ai_move(self):
        move = self.calculate_best_move()

        if self.explain_ai:
            explanation = self.explain_move(self.state, move)
            print(f"\n🤖 AI Explanation: {explanation}")

        self.apply_move(move)
```

## Best Practices

### For Game Developers

1. **Modular Design**: Keep educational features optional and toggleable
1. **Clear Explanations**: Write explanations in plain language
1. **Progressive Learning**: Start with basics, gradually introduce advanced concepts
1. **Interactive**: Let players practice with immediate feedback
1. **Consistent UI**: Use similar patterns across games

### For Players

1. **Start with Tutorials**: Complete the tutorial mode before playing
1. **Enable Hints**: Use strategy tips when learning
1. **Study Strategy Guides**: Read the comprehensive guides
1. **Practice Challenges**: Work through challenge packs
1. **Learn Theory**: Understand the math behind the games
1. **Disable Gradually**: Turn off hints as you improve

## Command-Line Usage

Many games support educational features via command-line flags:

### Blackjack Educational Mode

```bash
# Enable card counting hints
python -m card_games.blackjack.cli --educational

# See available options
python -m card_games.blackjack.cli --help
```

### Nim with Explanations

The Nim game's educational features are demonstrated in the CLI when the AI explains its moves.

## Daily Challenge Rotation

The collection now includes a rotating **daily challenge** system that surfaces curated scenarios across games.

- Use `common.daily_challenges.DailyChallengeScheduler` to deterministically select a challenge for a given date.
- Selections are persisted to `~/.games/daily_challenges.json` (or the profile directory you pass in) so all launchers
  display the same rotation for that day.
- Challenge metadata exposes builder callbacks (for example Sudoku boards) that allow CLIs to load bespoke states and run
  automated validation.

Example:

```python
from datetime import date

from common import DailyChallengeScheduler, get_default_challenge_manager

manager = get_default_challenge_manager()
scheduler = DailyChallengeScheduler(manager)

selection = scheduler.get_challenge_for_date(date.today())
print(selection.summary())
```

### Launcher integration

The main CLI launcher (`scripts/launcher.py`) now exposes a **D. Daily Challenge** menu entry. Selecting it shows the current
challenge description, launches specialised experiences (for example an auto-configured Sudoku board), and records
completion through `ProfileService.record_daily_challenge_completion` so streaks are preserved across sessions.

### Persistence and streak tracking

- `PlayerProfile` stores challenge history in `daily_challenge_progress` and unlocks new achievements for first completion
  and multi-day streaks.
- Achievements are registered under the virtual game id `daily_challenge`, making it easy to surface new milestones in
  dashboards or GUIs.

## Future Enhancements

Potential additions to educational features:

- [ ] Interactive quizzes after tutorial completion
- [ ] Achievement system for completing challenges
- [ ] Adaptive difficulty based on player performance
- [ ] Hand history analysis with improvement suggestions
- [ ] Video tutorials and animated explanations
- [ ] Multiplayer cooperative learning modes
- [ ] Progress tracking and statistics

## Contributing

To add educational features to a game:

1. Create a tutorial mode inheriting from `TutorialMode`
1. Implement game-specific probability calculator
1. Add AI explanation capability
1. Create challenge pack for the game
1. Write strategy guide documentation
1. Add tests for new features

See `CONTRIBUTING.md` for more details.

## Resources

- **Code Examples**: `examples/` directory
- **API Documentation**: `docs/source/api/`
- **Strategy Guides**: `docs/source/guides/`
- **Tutorials**: `docs/source/tutorials/`
- **Tests**: `tests/test_educational_features.py`

## License

Educational features are part of the main repository and follow the same license.
