#!/usr/bin/env python3
"""This script demonstrates the various educational features available in the Games Collection.

It showcases how different components can be used to create an enriching learning
experience for players, helping them understand game mechanics, strategy, and
underlying mathematical concepts.

The demonstrations cover:
- Step-by-step tutorial modes for specific games (Poker, Blackjack).
- Probability calculators to analyze game situations (e.g., pot odds, bust probability).
- A game theory explainer for core concepts like Minimax and Monte Carlo.
- A dynamic strategy tip system.
- Curated challenge packs to test and improve player skills.
- Integration of educational features within a game (Nim).
"""

from __future__ import annotations

import pathlib
import sys

# Ensure the project root is in the Python path to allow for module imports.
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def demo_poker_tutorial():
    """Demonstrates the step-by-step tutorial mode for Poker.

    This function initializes the `PokerTutorialMode` and walks through the
    first few steps, printing the title, description, and any hints provided.
    """
    print("=" * 70)
    print("POKER TUTORIAL DEMONSTRATION")
    print("=" * 70)

    from card_games.poker.educational import PokerTutorialMode

    tutorial = PokerTutorialMode()
    print("\nInitializing the Poker tutorial...")

    # Display the first 3 steps of the tutorial to show how it progresses.
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
    """Demonstrates the step-by-step tutorial mode for Blackjack."""
    print("\n" + "=" * 70)
    print("BLACKJACK TUTORIAL DEMONSTRATION")
    print("=" * 70)

    from card_games.blackjack.educational import BlackjackTutorialMode

    tutorial = BlackjackTutorialMode()
    print("\nInitializing the Blackjack tutorial...")

    # Display the first 2 steps.
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
    """Demonstrates the probability calculators for Poker and Blackjack."""
    print("\n" + "=" * 70)
    print("PROBABILITY CALCULATOR DEMONSTRATION")
    print("=" * 70)

    from card_games.blackjack.educational import BlackjackProbabilityCalculator
    from card_games.poker.educational import PokerProbabilityCalculator

    # --- Poker Probability Calculator ---
    print("\n🃏 POKER PROBABILITY CALCULATOR")
    print("-" * 70)
    poker_calc = PokerProbabilityCalculator()

    # Example: Calculate and explain pot odds.
    print("\nScenario: Pot is $100, it costs $20 to call, and you estimate a 25% chance to win.")
    comparison = poker_calc.format_pot_odds_comparison(amount_to_call=20, current_pot=100, win_probability=0.25)
    print(comparison)

    # --- Blackjack Probability Calculator ---
    print("\n\n🃏 BLACKJACK PROBABILITY CALCULATOR")
    print("-" * 70)
    bj_calc = BlackjackProbabilityCalculator()

    # Example: Calculate the probability of busting with a given hand total.
    print("\nBust Probabilities on Next Hit:")
    for total in [12, 14, 16, 18, 20]:
        prob = bj_calc.calculate_bust_probability(total)
        print(f"  - Hand total of {total}: {bj_calc.format_probability(prob)}")

    # Example: Calculate the dealer's bust probability based on their upcard.
    print("\nDealer Bust Probabilities by Upcard:")
    for upcard in [2, 6, 10, 11]:  # Using 11 for Ace
        prob = bj_calc.calculate_dealer_bust_probability(upcard)
        card_name = "Ace" if upcard == 11 else str(upcard)
        print(f"  - Dealer showing {card_name}: {bj_calc.format_probability(prob)}")

    # Example: Get a basic strategy recommendation and its explanation.
    print("\n\nBasic Strategy Recommendation:")
    print("Scenario: Your hand is a Hard 16, and the Dealer's upcard is a 10.")
    action = bj_calc.get_basic_strategy_recommendation(player_total=16, dealer_upcard=10, is_soft=False, can_double=False)
    print(f"Recommended Action: {action}")
    explanation = bj_calc.explain_basic_strategy_decision(player_total=16, dealer_upcard=10, is_soft=False)
    print(f"\nExplanation:\n{explanation}")


def demo_game_theory_explanations():
    """Demonstrates the GameTheoryExplainer for fundamental AI concepts."""
    print("\n" + "=" * 70)
    print("GAME THEORY EXPLANATIONS DEMONSTRATION")
    print("=" * 70)

    from common import GameTheoryExplainer

    explainer = GameTheoryExplainer()

    # List the first few available concepts.
    concepts = explainer.list_concepts()
    print(f"\n📖 Found {len(concepts)} available concepts in the explainer. Showing first 3:")
    for concept in concepts[:3]:
        print(f"  • {concept}")

    # Display a detailed explanation for a specific concept.
    print("\n" + "-" * 70)
    monte_carlo_explanation = explainer.get_explanation("monte_carlo")
    if monte_carlo_explanation:
        print(f"\n🎲 Concept: {monte_carlo_explanation.concept}")
        print(f"\n{monte_carlo_explanation.description}")
        if monte_carlo_explanation.example:
            print(f"\n📝 Example:\n{monte_carlo_explanation.example}")


def demo_strategy_tips():
    """Demonstrates the system for providing contextual strategy tips."""
    print("\n" + "=" * 70)
    print("STRATEGY TIPS DEMONSTRATION")
    print("=" * 70)

    from common import StrategyTip, StrategyTipProvider

    provider = StrategyTipProvider()

    # Add some example tips for Poker.
    provider.add_tip(
        StrategyTip(
            title="Position is Power",
            description=(
                "In Poker, acting last is a significant advantage. "
                "Play more hands from late positions (like the button) and be more selective from early positions."
            ),
            applies_to="Pre-flop strategy",
            difficulty="beginner",
        )
    )
    provider.add_tip(
        StrategyTip(
            title="Understand Pot Odds",
            description=(
                "Compare the pot odds to your hand's equity. "
                "If your chance of winning is higher than the odds the pot is giving you, "
                "a call is mathematically profitable in the long run."
            ),
            applies_to="Calling decisions",
            difficulty="intermediate",
        )
    )

    # Retrieve and display the tips, organized by difficulty.
    print("\n💡 Available Strategy Tips:\n")
    for difficulty in ["beginner", "intermediate"]:
        tips = provider.get_tips_by_difficulty(difficulty)
        for tip in tips:
            print(f"[{tip.difficulty.upper()}] {tip.title}")
            print(f"  {tip.description}")
            if tip.applies_to:
                print(f"  Applies to: {tip.applies_to}")
            print()


def demo_challenges():
    """Demonstrates the challenge pack system for skill development."""
    print("\n" + "=" * 70)
    print("CHALLENGE PACKS DEMONSTRATION")
    print("=" * 70)

    from common import get_default_challenge_manager

    manager = get_default_challenge_manager()

    # List all available challenge packs.
    packs = manager.list_packs()
    print(f"\n📦 Found {len(packs)} available challenge packs:")
    for pack_name in packs:
        pack = manager.get_pack(pack_name)
        print(f"\n  • {pack.name}")
        print(f"    {pack.description}")
        print(f"    Contains {len(pack)} challenges.")

    # Display a specific challenge from a pack.
    print("\n" + "-" * 70)
    poker_pack = manager.get_pack("Poker Fundamentals")
    if poker_pack:
        challenge = poker_pack.get_challenge("poker_pot_odds_1")
        if challenge:
            print(f"\n🎯 Sample Challenge: {challenge.title}")
            print(f"   Difficulty: {challenge.difficulty.value}")
            print(f"\n{challenge.description}")
            print(f"\nGoal: {challenge.goal}")
            print(f"\nSolution:\n{challenge.solution}")


def demo_nim_explanations():
    """Demonstrates the educational features built directly into the Nim game."""
    print("\n" + "=" * 70)
    print("NIM GAME'S BUILT-IN EDUCATIONAL FEATURES")
    print("=" * 70)

    try:
        from paper_games.nim import NimGame

        game = NimGame(initial_heaps=[3, 5, 7])
        print("\n🎮 Initial Game State:")
        print(f"Heaps: {game.heaps}")

        # Demonstrate getting a strategic hint.
        print("\n" + "-" * 70)
        print("\n📊 Requesting a strategy hint:")
        hint = game.get_strategy_hint()
        print(hint)

        # Demonstrate the computer's move with a detailed explanation.
        print("\n" + "-" * 70)
        print("\n🤖 Computer's turn (with explanation):")
        heap_idx, count, explanation = game.computer_move(explain=True)
        print(f"Computer's move: Remove {count} from heap {heap_idx + 1}.")
        print(f"Explanation: {explanation}")
        print(f"Resulting heaps: {game.heaps}")
    except ImportError:
        print("\n⚠️ Nim demo skipped: Could not import the NimGame class.")
        print("   This can happen if dependencies like `tkinter` are not available.")
        print("   Nim's educational features include:")
        print("   • `get_strategy_hint()`: Explains the current game position (winning/losing).")
        print("   • `computer_move(explain=True)`: Explains the AI's optimal move.")


def main():
    """Main function to run all educational feature demonstrations."""
    print("\n" + "=" * 70)
    print("EDUCATIONAL FEATURES DEMONSTRATION")
    print("=" * 70)
    print("\nThis script showcases the educational features designed to help players learn.")
    print("Each section will demonstrate a different capability.")

    demos = {
        "Poker Tutorial": demo_poker_tutorial,
        "Blackjack Tutorial": demo_blackjack_tutorial,
        "Probability Calculators": demo_probability_calculators,
        "Game Theory Explanations": demo_game_theory_explanations,
        "Strategy Tips": demo_strategy_tips,
        "Challenge Packs": demo_challenges,
        "Nim's Built-in Features": demo_nim_explanations,
    }

    for name, demo_func in demos.items():
        input(f"\n▶ Press Enter to run the '{name}' demonstration...")
        demo_func()

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\n✨ All educational features have been demonstrated.")
    print("These tools can be integrated into games to provide a richer, more")
    print("informative experience for players of all skill levels.")
    print("\nFor more details, please refer to the project documentation.")
    print("=" * 70)


if __name__ == "__main__":
    main()
