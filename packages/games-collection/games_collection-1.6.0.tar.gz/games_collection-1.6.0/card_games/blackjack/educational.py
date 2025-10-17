"""Educational features for blackjack.

This module provides tutorial mode, probability calculators, and strategy
explanations for blackjack.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from common.educational import ProbabilityCalculator, TutorialMode, TutorialStep

if TYPE_CHECKING:
    from .game import BlackjackGame


class BlackjackProbabilityCalculator(ProbabilityCalculator):
    """Calculates probabilities for blackjack situations."""

    def calculate_win_probability(self, state: BlackjackGame) -> float:
        """Calculate probability of winning current hand.

        Args:
            state: Current blackjack game state.

        Returns:
            Estimated win probability (0.0 to 1.0).
        """
        # Simplified - would need full simulation for accuracy
        return 0.5

    def calculate_bust_probability(self, hand_total: int) -> float:
        """Calculate probability of busting if hitting.

        Args:
            hand_total: Current hand total.

        Returns:
            Probability of busting (0.0 to 1.0).
        """
        if hand_total >= 21:
            return 1.0 if hand_total > 21 else 0.0

        # Calculate based on cards that would bust
        cards_that_bust = max(0, 13 - (21 - hand_total))
        return cards_that_bust / 13.0

    def calculate_dealer_bust_probability(self, dealer_upcard_value: int) -> float:
        """Calculate probability of dealer busting based on upcard.

        Args:
            dealer_upcard_value: Value of dealer's visible card.

        Returns:
            Approximate probability of dealer busting.
        """
        # Empirical probabilities based on dealer upcard
        bust_probabilities = {
            2: 0.35,
            3: 0.37,
            4: 0.40,
            5: 0.42,
            6: 0.42,
            7: 0.26,
            8: 0.24,
            9: 0.23,
            10: 0.21,
            11: 0.17,  # Ace
        }
        return bust_probabilities.get(dealer_upcard_value, 0.25)

    def calculate_dealer_final_totals(self, dealer_upcard_value: int) -> dict[int, float]:
        """Calculate probability distribution of dealer's final hand.

        Args:
            dealer_upcard_value: Value of dealer's visible card.

        Returns:
            Dictionary mapping final totals to their probabilities.
        """
        # Simplified - these are approximate empirical probabilities
        if dealer_upcard_value == 11:  # Ace
            return {17: 0.13, 18: 0.13, 19: 0.13, 20: 0.35, 21: 0.09, 0: 0.17}  # 0 = bust
        elif dealer_upcard_value == 10:
            return {17: 0.37, 18: 0.14, 19: 0.14, 20: 0.14, 21: 0.00, 0: 0.21}
        elif dealer_upcard_value in (7, 8, 9):
            return {17: 0.37, 18: 0.14, 19: 0.13, 20: 0.12, 21: 0.01, 0: 0.23}
        else:  # 2-6
            return {17: 0.14, 18: 0.11, 19: 0.11, 20: 0.11, 21: 0.13, 0: 0.40}

    def get_basic_strategy_recommendation(self, player_total: int, dealer_upcard: int, is_soft: bool, can_double: bool, can_split: bool = False) -> str:
        """Get basic strategy recommendation for a hand.

        Args:
            player_total: Player's hand total.
            dealer_upcard: Dealer's upcard value (2-11, where 11 is Ace).
            is_soft: Whether player has a soft hand (Ace counted as 11).
            can_double: Whether doubling down is allowed.
            can_split: Whether splitting is an option.

        Returns:
            Recommended action (Hit, Stand, Double, Split).
        """
        # Simplified basic strategy
        if is_soft:
            # Soft hands (Ace + X)
            if player_total >= 19:
                return "Stand"
            elif player_total == 18:
                return "Stand" if dealer_upcard in (2, 7, 8) else ("Double" if can_double else "Hit")
            elif player_total == 17 and can_double and dealer_upcard in (3, 4, 5, 6):
                return "Double"
            else:
                return "Hit"
        else:
            # Hard hands
            if player_total >= 17:
                return "Stand"
            elif player_total <= 11:
                return "Double" if can_double and player_total in (10, 11) else "Hit"
            elif player_total == 16:
                return "Stand" if dealer_upcard <= 6 else "Hit"
            elif player_total == 15:
                return "Stand" if dealer_upcard <= 6 else "Hit"
            elif player_total == 14 or player_total == 13:
                return "Stand" if dealer_upcard <= 6 else "Hit"
            elif player_total == 12:
                return "Stand" if 4 <= dealer_upcard <= 6 else "Hit"
            else:
                return "Hit"

    def explain_basic_strategy_decision(self, player_total: int, dealer_upcard: int, is_soft: bool) -> str:
        """Explain why basic strategy recommends a particular action.

        Args:
            player_total: Player's hand total.
            dealer_upcard: Dealer's upcard value.
            is_soft: Whether player has a soft hand.

        Returns:
            Explanation of the basic strategy decision.
        """
        action = self.get_basic_strategy_recommendation(player_total, dealer_upcard, is_soft, True, False)

        explanation = f"Basic Strategy recommends: {action}\n\n"

        if action == "Stand":
            explanation += "Your hand is strong enough, or the dealer is likely to bust."
        elif action == "Hit":
            bust_prob = self.calculate_bust_probability(player_total)
            explanation += f"Risk of busting: {self.format_probability(bust_prob)}\n"
            explanation += "Your hand needs improvement and the risk is acceptable."
        elif action == "Double":
            explanation += "This is a favorable situation to double your bet."

        dealer_bust = self.calculate_dealer_bust_probability(dealer_upcard)
        explanation += f"\nDealer bust probability (upcard {dealer_upcard}): {self.format_probability(dealer_bust)}"

        return explanation


class BlackjackTutorialMode(TutorialMode):
    """Tutorial mode for learning blackjack."""

    def _create_tutorial_steps(self) -> List[TutorialStep]:
        """Create blackjack tutorial steps.

        Returns:
            List of tutorial steps for learning blackjack.
        """
        return [
            TutorialStep(
                title="Welcome to Blackjack",
                description=(
                    "Blackjack (also called 21) is a card game where you compete against the dealer. "
                    "The goal is to get a hand value as close to 21 as possible without going over (busting). "
                    "You win if your hand is closer to 21 than the dealer's, or if the dealer busts."
                ),
                hint="Number cards count as their value, face cards count as 10, and Aces count as 1 or 11.",
            ),
            TutorialStep(
                title="Card Values",
                description=(
                    "Understanding card values is essential:\n\n"
                    "• Number cards (2-10): Face value\n"
                    "• Face cards (J, Q, K): Worth 10\n"
                    "• Ace (A): Worth 1 or 11 (whichever is better)\n\n"
                    "A hand with an Ace counted as 11 is called a 'soft' hand. "
                    "For example, Ace-6 is 'soft 17' (can't bust on next card)."
                ),
                hint="Soft hands give you flexibility because you can't bust on the next card!",
            ),
            TutorialStep(
                title="How to Play",
                description=(
                    "1. Place your bet before cards are dealt\n"
                    "2. You receive 2 cards face-up; dealer gets 1 up, 1 down\n"
                    "3. Decide to Hit (take a card), Stand (keep your hand), "
                    "Double Down (double bet and take 1 card), or Split (if you have a pair)\n"
                    "4. After you finish, dealer reveals their hidden card\n"
                    "5. Dealer must hit on 16 or less, stand on 17 or more\n"
                    "6. Compare hands - closer to 21 wins!"
                ),
                hint="If your first 2 cards total 21, that's a Blackjack and pays 3:2!",
            ),
            TutorialStep(
                title="Basic Strategy - When to Hit or Stand",
                description=(
                    "Basic strategy is mathematically optimal play:\n\n"
                    "ALWAYS HIT:\n"
                    "• Hard 8 or less\n"
                    "• Soft 17 or less\n\n"
                    "ALWAYS STAND:\n"
                    "• Hard 17 or more\n"
                    "• Soft 19 or more\n\n"
                    "CONDITIONAL (depends on dealer's upcard):\n"
                    "• Hard 12-16: Stand if dealer shows 2-6, otherwise hit\n"
                    "• Soft 18: Stand vs 2, 7, 8; Hit vs 9, 10, A"
                ),
                hint="When dealer shows 2-6, they're more likely to bust - so stand on weaker hands!",
            ),
            TutorialStep(
                title="Doubling Down",
                description=(
                    "Doubling down lets you double your bet in exchange for receiving exactly one more card. "
                    "Do this when you have a strong chance of winning:\n\n"
                    "ALWAYS DOUBLE:\n"
                    "• 11 vs dealer 2-10\n"
                    "• 10 vs dealer 2-9\n\n"
                    "SOMETIMES DOUBLE:\n"
                    "• 9 vs dealer 3-6\n"
                    "• Soft 16-18 vs dealer 4-6"
                ),
                hint="Doubling down increases your bet when you have the advantage!",
            ),
            TutorialStep(
                title="Splitting Pairs",
                description=(
                    "When dealt a pair, you can split them into two separate hands:\n\n"
                    "ALWAYS SPLIT:\n"
                    "• Aces (but you only get one card per Ace)\n"
                    "• 8s (two 16s is bad, but two hands starting with 8 is good)\n\n"
                    "NEVER SPLIT:\n"
                    "• 10s (20 is too good to break up)\n"
                    "• 5s (10 is great for doubling down)\n\n"
                    "CONDITIONAL:\n"
                    "• Split 2s, 3s, 6s, 7s, 9s based on dealer's upcard"
                ),
                hint="Splitting Aces and 8s is almost always correct!",
            ),
            TutorialStep(
                title="Understanding the Dealer",
                description=(
                    "The dealer has strict rules they must follow:\n"
                    "• Must hit on 16 or less\n"
                    "• Must stand on 17 or more\n"
                    "• No choices - dealer plays mechanically\n\n"
                    "Dealer bust rates by upcard:\n"
                    "• 2-6: ~35-42% (high bust rate)\n"
                    "• 7-9: ~23-26% (medium)\n"
                    "• 10, A: ~17-21% (low)\n\n"
                    "This is why you play more conservatively when dealer shows 2-6!"
                ),
                hint="Dealer showing 5 or 6 is best for you - they bust most often!",
            ),
            TutorialStep(
                title="Card Counting Basics (Educational)",
                description=(
                    "Card counting tracks the ratio of high to low cards:\n\n"
                    "Hi-Lo System:\n"
                    "• 2-6: +1 (good for dealer, bad for player)\n"
                    "• 7-9: 0 (neutral)\n"
                    "• 10-A: -1 (good for player, bad for dealer)\n\n"
                    "Running Count: Keep a mental tally\n"
                    "True Count: Running count ÷ decks remaining\n\n"
                    "When true count is +2 or higher, the deck favors the player!"
                ),
                hint="This is for educational purposes - casinos don't like card counters!",
            ),
            TutorialStep(
                title="Bankroll Management",
                description=(
                    "Smart bankroll management is crucial:\n\n"
                    "• Don't bet more than 1-2% of your total bankroll per hand\n"
                    "• Set a loss limit and stick to it\n"
                    "• Don't chase losses by increasing bets\n"
                    "• Take breaks when losing\n"
                    "• Remember: the house always has an edge\n\n"
                    "Example: With $500 bankroll, bet $5-10 per hand"
                ),
                hint="Proper bankroll management helps you play longer and have more fun!",
            ),
            TutorialStep(
                title="Ready to Play!",
                description=(
                    "Congratulations! You now understand:\n"
                    "• Card values and hand totals\n"
                    "• When to hit, stand, double, and split\n"
                    "• Basic strategy for optimal play\n"
                    "• How the dealer plays\n"
                    "• Card counting basics\n"
                    "• Bankroll management\n\n"
                    "Start playing and practice making the right decisions. "
                    "Good luck at the tables!"
                ),
                hint="Focus on learning basic strategy first - it's the foundation of good blackjack play!",
            ),
        ]
