#!/usr/bin/env python3
"""Demonstration of educational features.

This script demonstrates how to use the educational features including:
- Tutorial modes
- Strategy tips
- Probability calculators
- Game theory explanations
- Challenge packs
"""

from __future__ import annotations

import pathlib
import sys

# Add project root to path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def demo_poker_tutorial():
    """Demonstrate poker tutorial mode."""
    print("=" * 70)
    print("POKER TUTORIAL DEMONSTRATION")
    print("=" * 70)

    from card_games.poker.educational import PokerTutorialMode

    tutorial = PokerTutorialMode()

    # Show first 3 steps
    for i in range(3):
        step = tutorial.get_current_step()
        if step:
            print(f"\n📚 Step {i + 1}: {step.title}")
            print(f"\n{step.description}")
            if step.hint:
                print(f"\n💡 Hint: {step.hint}")
            print("\n" + "-" * 70)
            tutorial.advance_step()


def demo_blackjack_tutorial():
    """Demonstrate blackjack tutorial mode."""
    print("\n" + "=" * 70)
    print("BLACKJACK TUTORIAL DEMONSTRATION")
    print("=" * 70)

    from card_games.blackjack.educational import BlackjackTutorialMode

    tutorial = BlackjackTutorialMode()

    # Show first 2 steps
    for i in range(2):
        step = tutorial.get_current_step()
        if step:
            print(f"\n📚 Step {i + 1}: {step.title}")
            print(f"\n{step.description}")
            if step.hint:
                print(f"\n💡 Hint: {step.hint}")
            print("\n" + "-" * 70)
            tutorial.advance_step()


def demo_probability_calculators():
    """Demonstrate probability calculators."""
    print("\n" + "=" * 70)
    print("PROBABILITY CALCULATOR DEMONSTRATION")
    print("=" * 70)

    from card_games.blackjack.educational import BlackjackProbabilityCalculator
    from card_games.poker.educational import PokerProbabilityCalculator

    # Poker calculator
    print("\n🃏 POKER PROBABILITY CALCULATOR")
    print("-" * 70)
    poker_calc = PokerProbabilityCalculator()

    # Example: Pot odds calculation
    print("\nScenario: $100 pot, $20 to call, 25% win probability")
    comparison = poker_calc.format_pot_odds_comparison(amount_to_call=20, current_pot=100, win_probability=0.25)
    print(comparison)

    # Blackjack calculator
    print("\n\n🃏 BLACKJACK PROBABILITY CALCULATOR")
    print("-" * 70)
    bj_calc = BlackjackProbabilityCalculator()

    # Example: Bust probability
    print("\nBust Probabilities:")
    for total in [12, 14, 16, 18, 20]:
        prob = bj_calc.calculate_bust_probability(total)
        print(f"  Hand total {total}: {bj_calc.format_probability(prob)}")

    # Example: Dealer bust by upcard
    print("\nDealer Bust Probabilities by Upcard:")
    for upcard in [2, 6, 10, 11]:
        prob = bj_calc.calculate_dealer_bust_probability(upcard)
        card_name = "Ace" if upcard == 11 else str(upcard)
        print(f"  Dealer showing {card_name}: {bj_calc.format_probability(prob)}")

    # Example: Basic strategy recommendation
    print("\n\nBasic Strategy Recommendation:")
    print("You have: Hard 16, Dealer shows: 10")
    action = bj_calc.get_basic_strategy_recommendation(player_total=16, dealer_upcard=10, is_soft=False, can_double=False)
    print(f"Recommended: {action}")
    explanation = bj_calc.explain_basic_strategy_decision(player_total=16, dealer_upcard=10, is_soft=False)
    print(f"\n{explanation}")


def demo_game_theory_explanations():
    """Demonstrate game theory explanations."""
    print("\n" + "=" * 70)
    print("GAME THEORY EXPLANATIONS DEMONSTRATION")
    print("=" * 70)

    from common import GameTheoryExplainer

    explainer = GameTheoryExplainer()

    # Show available concepts
    concepts = explainer.list_concepts()
    print(f"\n📖 Available Concepts: {len(concepts)}")
    for concept in concepts[:3]:  # Show first 3
        print(f"  • {concept}")

    # Show detailed explanation
    print("\n" + "-" * 70)
    monte_carlo = explainer.get_explanation("monte_carlo")
    if monte_carlo:
        print(f"\n🎲 {monte_carlo.concept}")
        print(f"\n{monte_carlo.description}")
        if monte_carlo.example:
            print(f"\n📝 Example:\n{monte_carlo.example}")


def demo_strategy_tips():
    """Demonstrate strategy tip system."""
    print("\n" + "=" * 70)
    print("STRATEGY TIPS DEMONSTRATION")
    print("=" * 70)

    from common import StrategyTip, StrategyTipProvider

    provider = StrategyTipProvider()

    # Add some poker tips
    provider.add_tip(
        StrategyTip(
            title="Position is Power",
            description=(
                "Playing in late position (button or cutoff) allows you to see "
                "what other players do before making your decision. Play more hands "
                "from late position and fewer from early position."
            ),
            applies_to="Pre-flop strategy",
            difficulty="beginner",
        )
    )

    provider.add_tip(
        StrategyTip(
            title="Pot Odds > Equity = Call",
            description=(
                "If your pot odds (amount to call / total pot) are smaller than "
                "your estimated win probability, calling is profitable. For example, "
                "if pot odds are 20% and you have 30% equity, call!"
            ),
            applies_to="Calling decisions",
            difficulty="intermediate",
        )
    )

    # Show tips
    print("\n💡 Strategy Tips:\n")
    for difficulty in ["beginner", "intermediate"]:
        tips = provider.get_tips_by_difficulty(difficulty)
        for tip in tips:
            print(f"[{tip.difficulty.upper()}] {tip.title}")
            print(f"  {tip.description}")
            if tip.applies_to:
                print(f"  Applies to: {tip.applies_to}")
            print()


def demo_challenges():
    """Demonstrate challenge pack system."""
    print("\n" + "=" * 70)
    print("CHALLENGE PACKS DEMONSTRATION")
    print("=" * 70)

    from common import get_default_challenge_manager

    manager = get_default_challenge_manager()

    # List available packs
    packs = manager.list_packs()
    print(f"\n📦 Available Challenge Packs: {len(packs)}")
    for pack_name in packs:
        pack = manager.get_pack(pack_name)
        print(f"\n  • {pack.name}")
        print(f"    {pack.description}")
        print(f"    Challenges: {len(pack)}")

    # Show a specific challenge
    print("\n" + "-" * 70)
    poker_pack = manager.get_pack("Poker Fundamentals")
    if poker_pack:
        challenge = poker_pack.get_challenge("poker_pot_odds_1")
        if challenge:
            print(f"\n🎯 Sample Challenge: {challenge.title}")
            print(f"Difficulty: {challenge.difficulty.value}")
            print(f"\n{challenge.description}")
            print(f"\n🎯 Goal: {challenge.goal}")
            print(f"\n✅ Solution:\n{challenge.solution}")


def demo_nim_explanations():
    """Demonstrate Nim's existing educational features."""
    print("\n" + "=" * 70)
    print("NIM EDUCATIONAL FEATURES DEMONSTRATION")
    print("=" * 70)

    try:
        from paper_games.nim import NimGame

        # Create a game
        game = NimGame([3, 5, 7])

        print("\n🎮 Initial State:")
        print(f"Heaps: {game.heaps}")

        # Get strategy hint
        print("\n" + "-" * 70)
        print("\n📊 Strategy Hint:")
        hint = game.get_strategy_hint()
        print(hint)

        # Computer move with explanation
        print("\n" + "-" * 70)
        print("\n🤖 Computer Move with Explanation:")
        heap_idx, count, explanation = game.computer_move(explain=True)
        print(f"Move: Remove {count} from heap {heap_idx + 1}")
        print(f"Explanation: {explanation}")
        print(f"New heaps: {game.heaps}")
    except ImportError:
        print("\n⚠️  Nim demo skipped (tkinter not available)")
        print("   Nim has built-in educational features:")
        print("   • get_strategy_hint() - Explains current position")
        print("   • computer_move(explain=True) - Explains AI's move")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("EDUCATIONAL FEATURES DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo showcases the educational features available in the")
    print("games collection. Each section demonstrates different capabilities.")
    print("\nPress Enter to continue through each demo...")

    input("\n▶ Press Enter to start...")

    # Run demonstrations
    demo_poker_tutorial()
    input("\n▶ Press Enter to continue...")

    demo_blackjack_tutorial()
    input("\n▶ Press Enter to continue...")

    demo_probability_calculators()
    input("\n▶ Press Enter to continue...")

    demo_game_theory_explanations()
    input("\n▶ Press Enter to continue...")

    demo_strategy_tips()
    input("\n▶ Press Enter to continue...")

    demo_challenges()
    input("\n▶ Press Enter to continue...")

    demo_nim_explanations()

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\n✨ Features demonstrated:")
    print("  • Tutorial modes for Poker and Blackjack")
    print("  • Probability calculators with real examples")
    print("  • Game theory explanations (Minimax, Monte Carlo, etc.)")
    print("  • Strategy tip system")
    print("  • Challenge packs with solutions")
    print("  • Nim's existing educational features")
    print("\n📚 For more information:")
    print("  • Read docs/EDUCATIONAL_FEATURES.md")
    print("  • Check docs/source/guides/ for strategy guides")
    print("  • Review tests/test_educational_features.py for usage examples")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
