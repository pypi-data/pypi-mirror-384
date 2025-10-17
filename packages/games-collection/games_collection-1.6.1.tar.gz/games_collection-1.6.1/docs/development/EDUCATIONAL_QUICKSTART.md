# Educational Features - Quick Start Guide

Get started with the educational features in 5 minutes!

## Try the Demo

The fastest way to see what's available:

```bash
python examples/educational_demo.py
```

This interactive demo showcases all educational features.

## Use Tutorial Mode

### Poker Tutorial

```python
from card_games.poker.educational import PokerTutorialMode

tutorial = PokerTutorialMode()

while not tutorial.completed:
    step = tutorial.get_current_step()
    print(f"\n{step.title}")
    print(step.description)

    input("Press Enter to continue...")
    tutorial.advance_step()

print("\nTutorial completed!")
```

### Blackjack Tutorial

```python
from card_games.blackjack.educational import BlackjackTutorialMode

tutorial = BlackjackTutorialMode()
step = tutorial.get_current_step()

print(step.title)
print(step.description)
print(f"Hint: {step.hint}")
```

## Calculate Probabilities

### Poker Pot Odds

```python
from card_games.poker.educational import PokerProbabilityCalculator

calc = PokerProbabilityCalculator()

# Should I call?
result = calc.format_pot_odds_comparison(
    amount_to_call=20,  # $20 to call
    current_pot=100,     # $100 in pot
    win_probability=0.25 # 25% chance to win
)
print(result)
# Output: ✓ PROFITABLE CALL (+8.3% edge)
```

### Blackjack Bust Odds

```python
from card_games.blackjack.educational import BlackjackProbabilityCalculator

calc = BlackjackProbabilityCalculator()

# What's my bust chance with 16?
bust_prob = calc.calculate_bust_probability(16)
print(f"Bust probability: {calc.format_probability(bust_prob)}")
# Output: Bust probability: 61.5%

# What should I do?
action = calc.get_basic_strategy_recommendation(
    player_total=16,
    dealer_upcard=10,
    is_soft=False,
    can_double=False
)
print(f"Recommended: {action}")
# Output: Recommended: Hit
```

## Learn Game Theory

```python
from common import GameTheoryExplainer

explainer = GameTheoryExplainer()

# What's Monte Carlo?
mc = explainer.get_explanation("monte_carlo")
print(mc.concept)
print(mc.description)
print(mc.example)
```

## Try Challenges

```python
from common import get_default_challenge_manager

manager = get_default_challenge_manager()

# Get poker challenges
poker_pack = manager.get_pack("Poker Fundamentals")

# Try the first challenge
challenge = poker_pack.challenges[0]
print(f"Challenge: {challenge.title}")
print(f"Difficulty: {challenge.difficulty.value}")
print(challenge.description)

# Try to solve it...

# Check solution
print(f"\nSolution:\n{challenge.solution}")
```

## Use with Games

### Blackjack with Educational Mode

```bash
# Enable card counting hints
python -m card_games.blackjack.cli --educational
```

### Nim with Explanations

```python
from paper_games.nim import NimGame

game = NimGame([3, 5, 7])

# Get strategy hint
hint = game.get_strategy_hint()
print(hint)

# AI explains its move
heap, count, explanation = game.computer_move(explain=True)
print(f"AI: {explanation}")
```

## Read Strategy Guides

Open these files in any text editor:

- `docs/source/guides/poker_strategy.rst` - Complete poker strategy
- `docs/source/guides/blackjack_strategy.rst` - Complete blackjack strategy
- `docs/source/guides/game_theory.rst` - Game theory concepts

Or build the documentation:

```bash
cd docs
make html
open build/html/guides/index.html
```

## Next Steps

1. **Complete Documentation**: Read `EDUCATIONAL_FEATURES.md` (same directory)
1. **Code Examples**: Check `tests/test_educational_features.py`
1. **Strategy Guides**: Study `docs/source/guides/`
1. **Practice**: Try the challenge packs
1. **Integrate**: Add educational features to your game

## Quick Reference

| Feature | Module | Description |
| -------------------- | ---------------------------------- | ---------------------- |
| Tutorial Mode | `common.TutorialMode` | Step-by-step learning |
| Strategy Tips | `common.StrategyTipProvider` | Contextual advice |
| Probability Calc | `common.ProbabilityCalculator` | Odds calculation |
| Game Theory | `common.GameTheoryExplainer` | Algorithm explanations |
| Challenges | `common.ChallengeManager` | Practice puzzles |
| Poker Tutorial | `card_games.poker.educational` | Poker learning |
| Poker Calculator | `card_games.poker.educational` | Poker odds |
| Blackjack Tutorial | `card_games.blackjack.educational` | Blackjack learning |
| Blackjack Calculator | `card_games.blackjack.educational` | Blackjack odds |

## Help

- Questions? Check `EDUCATIONAL_FEATURES.md` (same directory)
- Bugs? Open an issue on GitHub
- Contributions? See `CONTRIBUTING.md`

Happy learning! 🎓
