"""Educational features for blackjack, including tutorials and probability tools.

This module provides a ``BlackjackTutorialMode`` for new players to learn the
game, and a ``BlackjackProbabilityCalculator`` for analyzing game situations.
These tools are designed to help players understand optimal strategy and the
likelihood of various outcomes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from common.educational import ProbabilityCalculator, TutorialMode, TutorialStep

if TYPE_CHECKING:
    from .game import BlackjackGame


class BlackjackProbabilityCalculator(ProbabilityCalculator):
    """Calculates probabilities for various blackjack situations.

    This class provides methods to estimate the probability of winning, busting,
    and other game events. It also includes functions to get basic strategy
    recommendations based on the current game state.
    """

    def calculate_win_probability(self, state: BlackjackGame) -> float:
        """Calculate the probability of winning the current hand.

        Note: This is a simplified estimation. Accurate calculation would require
        a full simulation of the remaining shoe.

        Args:
            state: The current blackjack game state.

        Returns:
            An estimated win probability from 0.0 to 1.0.
        """
        # A more complex implementation would simulate the rest of the game
        # thousands of times to get an accurate probability.
        return 0.5

    def calculate_bust_probability(self, hand_total: int) -> float:
        """Calculate the probability of busting if the player hits.

        This assumes a standard, infinite deck for simplification.

        Args:
            hand_total: The current total of the player's hand.

        Returns:
            The probability of busting on the next card.
        """
        if hand_total >= 21:
            return 1.0 if hand_total > 21 else 0.0

        # Calculate how many card ranks would cause a bust.
        cards_that_bust = max(0, 13 - (21 - hand_total))
        return cards_that_bust / 13.0

    def calculate_dealer_bust_probability(self, dealer_upcard_value: int) -> float:
        """Calculate the probability of the dealer busting based on their upcard.

        Args:
            dealer_upcard_value: The value of the dealer's visible card.

        Returns:
            The approximate probability of the dealer busting.
        """
        # These are empirical probabilities based on millions of simulated hands.
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
        """Calculate the probability distribution of the dealer's final hand total.

        Args:
            dealer_upcard_value: The value of the dealer's visible card.

        Returns:
            A dictionary mapping final totals to their approximate probabilities.
            A total of 0 represents a bust.
        """
        # These are simplified empirical probabilities.
        if dealer_upcard_value == 11:  # Ace
            return {17: 0.13, 18: 0.13, 19: 0.13, 20: 0.35, 21: 0.09, 0: 0.17}
        elif dealer_upcard_value == 10:
            return {17: 0.37, 18: 0.14, 19: 0.14, 20: 0.14, 21: 0.00, 0: 0.21}
        elif dealer_upcard_value in (7, 8, 9):
            return {17: 0.37, 18: 0.14, 19: 0.13, 20: 0.12, 21: 0.01, 0: 0.23}
        else:  # 2-6
            return {17: 0.14, 18: 0.11, 19: 0.11, 20: 0.11, 21: 0.13, 0: 0.40}

    def get_basic_strategy_recommendation(
        self,
        player_total: int,
        dealer_upcard: int,
        is_soft: bool,
        can_double: bool,
        can_split: bool = False,
    ) -> str:
        """Get a basic strategy recommendation for a given hand.

        Args:
            player_total: The player's current hand total.
            dealer_upcard: The dealer's upcard value (2-11, where 11 is Ace).
            is_soft: Whether the player has a soft hand (an Ace counted as 11).
            can_double: Whether doubling down is currently allowed.
            can_split: Whether splitting is currently an option.

        Returns:
            The recommended action as a string (e.g., "Hit", "Stand").
        """
        # This is a simplified basic strategy chart.
        if is_soft:
            # Recommendations for soft hands (Ace + X).
            if player_total >= 19:
                return "Stand"
            elif player_total == 18:
                return "Stand" if dealer_upcard in (2, 7, 8) else ("Double" if can_double else "Hit")
            elif player_total == 17 and can_double and dealer_upcard in (3, 4, 5, 6):
                return "Double"
            else:
                return "Hit"
        else:
            # Recommendations for hard hands.
            if player_total >= 17:
                return "Stand"
            elif player_total <= 11:
                return "Double" if can_double and player_total in (10, 11) else "Hit"
            elif player_total in (16, 15, 14, 13):
                return "Stand" if dealer_upcard <= 6 else "Hit"
            elif player_total == 12:
                return "Stand" if 4 <= dealer_upcard <= 6 else "Hit"
            else:
                return "Hit"

    def explain_basic_strategy_decision(self, player_total: int, dealer_upcard: int, is_soft: bool) -> str:
        """Explain why basic strategy recommends a particular action.

        Args:
            player_total: The player's hand total.
            dealer_upcard: The dealer's upcard value.
            is_soft: Whether the player has a soft hand.

        Returns:
            A string explaining the reasoning behind the basic strategy decision.
        """
        action = self.get_basic_strategy_recommendation(player_total, dealer_upcard, is_soft, True, False)
        explanation = f"Basic Strategy recommends: {action}\n\n"

        if action == "Stand":
            explanation += "Your hand is strong enough, or the dealer is likely to bust."
        elif action == "Hit":
            bust_prob = self.calculate_bust_probability(player_total)
            explanation += f"Risk of busting: {self.format_probability(bust_prob)}\n"
            explanation += "Your hand needs improvement, and the risk is acceptable."
        elif action == "Double":
            explanation += "This is a favorable situation to double your bet for a potentially higher payout."

        dealer_bust = self.calculate_dealer_bust_probability(dealer_upcard)
        explanation += f"\nDealer bust probability (upcard {dealer_upcard}): {self.format_probability(dealer_bust)}"

        return explanation


class BlackjackTutorialMode(TutorialMode):
    """A step-by-step tutorial for learning to play blackjack.

    This tutorial guides new players through the rules, objectives, and basic
    strategies of the game.
    """

    def _create_tutorial_steps(self) -> List[TutorialStep]:
        """Create the sequence of tutorial steps for learning blackjack.

        Returns:
            A list of ``TutorialStep`` objects that form the blackjack tutorial.
        """
        return [
            TutorialStep(
                title="Welcome to Blackjack",
                description=(
                    "Blackjack (also called 21) is a card game where you compete against the dealer. "
                    "The goal is to get a hand value as close to 21 as possible without going over (busting). "
                    "You win if your hand is closer to 21 than the dealer's, or if the dealer busts."
                ),
                hint="Number cards are worth their face value, face cards are 10, and Aces are 1 or 11.",
            ),
            TutorialStep(
                title="Card Values",
                description=(
                    "Understanding card values is essential:\n\n"
                    "• Number cards (2-10): Face value\n"
                    "• Face cards (J, Q, K): Worth 10\n"
                    "• Ace (A): Worth 1 or 11 (whichever is better for your hand)\n\n"
                    "A hand with an Ace counted as 11 is called a 'soft' hand. "
                    "For example, an Ace and a 6 make a 'soft 17'."
                ),
                hint="Soft hands give you flexibility because you can't bust on the next card!",
            ),
            TutorialStep(
                title="How to Play",
                description=(
                    "1. Place your bet before the cards are dealt.\n"
                    "2. You receive 2 cards face-up; the dealer gets 1 up, 1 down.\n"
                    "3. Decide to Hit (take another card), Stand (keep your hand), "
                    "Double Down (double your bet for one card), or Split (if you have a pair).\n"
                    "4. After your turn, the dealer reveals their hidden card.\n"
                    "5. The dealer must hit on 16 or less and stand on 17 or more.\n"
                    "6. The hand closer to 21 wins!"
                ),
                hint="If your first two cards total 21, that's a Blackjack and usually pays 3:2!",
            ),
            TutorialStep(
                title="Basic Strategy: Hit or Stand",
                description=(
                    "Basic strategy is the mathematically optimal way to play:\n\n"
                    "ALWAYS HIT on:\n"
                    "• Hard 8 or less\n"
                    "• Soft 17 or less\n\n"
                    "ALWAYS STAND on:\n"
                    "• Hard 17 or more\n"
                    "• Soft 19 or more\n\n"
                    "CONDITIONAL (depends on dealer's upcard):\n"
                    "• Hard 12-16: Stand if the dealer shows 2-6, otherwise hit.\n"
                    "• Soft 18: Stand against a 2, 7, or 8; otherwise hit."
                ),
                hint="When the dealer shows a 2-6, they are more likely to bust, so you can stand on weaker hands.",
            ),
            TutorialStep(
                title="Doubling Down",
                description=(
                    "Doubling down lets you double your bet in exchange for receiving exactly one more card. "
                    "It's a powerful move when you have a strong chance of winning:\n\n"
                    "ALWAYS DOUBLE on:\n"
                    "• 11 (unless the dealer shows an Ace)\n"
                    "• 10 (unless the dealer shows a 10 or Ace)\n\n"
                    "SOMETIMES DOUBLE on:\n"
                    "• 9 (against a dealer's 3-6)\n"
                    "• Soft 16-18 (against a dealer's 4-6)"
                ),
                hint="Doubling down is a key strategy to maximize your winnings in favorable situations.",
            ),
            TutorialStep(
                title="Splitting Pairs",
                description=(
                    "If you are dealt a pair, you can split them into two separate hands:\n\n"
                    "ALWAYS SPLIT:\n"
                    "• Aces (you usually only get one card per Ace)\n"
                    "• 8s (a hand of 16 is weak, but two hands starting with 8 are strong)\n\n"
                    "NEVER SPLIT:\n"
                    "• 10s (a hand of 20 is too good to break up)\n"
                    "• 5s (a hand of 10 is great for doubling down)\n\n"
                    "SOMETIMES SPLIT:\n"
                    "• 2s, 3s, 6s, 7s, 9s (depends on the dealer's upcard)"
                ),
                hint="Splitting Aces and 8s is one of the most important rules of basic strategy.",
            ),
            TutorialStep(
                title="Understanding the Dealer",
                description=(
                    "The dealer plays by strict, mechanical rules:\n"
                    "• Must hit on 16 or less.\n"
                    "• Must stand on 17 or more.\n"
                    "• The dealer has no choice in how to play their hand.\n\n"
                    "Dealer bust rates by upcard:\n"
                    "• 2-6: ~35-42% (high bust rate)\n"
                    "• 7-9: ~23-26% (medium bust rate)\n"
                    "• 10, A: ~17-21% (low bust rate)\n\n"
                    "This is why you play more conservatively when the dealer shows a 2-6."
                ),
                hint="A dealer showing a 5 or 6 is the best situation for the player, as they bust most often.",
            ),
            TutorialStep(
                title="Card Counting Basics (Educational)",
                description=(
                    "Card counting tracks the ratio of high-value to low-value cards left in the shoe:\n\n"
                    "Hi-Lo System:\n"
                    "• 2-6: +1 (good for the dealer, bad for the player)\n"
                    "• 7-9: 0 (neutral)\n"
                    "• 10-A: -1 (good for the player, bad for the dealer)\n\n"
                    "Running Count: Keep a mental tally as cards are played.\n"
                    "True Count: Running Count ÷ Decks Remaining\n\n"
                    "When the true count is +2 or higher, the deck favors the player!"
                ),
                hint="Card counting is for educational purposes only. Casinos do not permit it.",
            ),
            TutorialStep(
                title="Bankroll Management",
                description=(
                    "Smart bankroll management is crucial for long-term play:\n\n"
                    "• Bet a small fraction (1-2%) of your total bankroll per hand.\n"
                    "• Set a loss limit for your session and stick to it.\n"
                    "• Avoid chasing losses by increasing your bets.\n"
                    "• Remember that the house always has a slight edge.\n\n"
                    "Example: With a $500 bankroll, your standard bet might be $5-10."
                ),
                hint="Proper bankroll management helps you play longer and have more fun.",
            ),
            TutorialStep(
                title="Ready to Play!",
                description=(
                    "Congratulations! You now understand:\n"
                    "• Card values and hand totals\n"
                    "• How to hit, stand, double, and split\n"
                    "• Basic strategy for optimal play\n"
                    "• The dealer's rules\n"
                    "• The basics of card counting\n"
                    "• Bankroll management\n\n"
                    "Now you're ready to practice making the right decisions. Good luck!"
                ),
                hint="Focus on mastering basic strategy first—it's the foundation of good blackjack play.",
            ),
        ]
