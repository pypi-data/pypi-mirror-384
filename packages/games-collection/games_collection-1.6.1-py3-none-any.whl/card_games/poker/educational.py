"""Educational features for poker.

This module provides tutorial mode, probability calculators, and AI move
explanations for poker games.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from common.educational import AIExplainer, ProbabilityCalculator, TutorialMode, TutorialStep

if TYPE_CHECKING:
    from ..common.cards import Card
    from .poker import Action, Player, PokerTable


class PokerProbabilityCalculator(ProbabilityCalculator):
    """Calculates probabilities and odds for poker situations."""

    def calculate_win_probability(self, state: PokerTable) -> float:
        """Calculate win probability using Monte Carlo simulation.

        Args:
            state: Current poker table state.

        Returns:
            Estimated win probability (0.0 to 1.0).
        """
        from .poker import estimate_win_rate

        # Get current player
        current_player = next((p for p in state.players if not p.folded and p.chips > 0), None)
        if not current_player:
            return 0.0

        return estimate_win_rate(
            hero=current_player,
            players=[p for p in state.players if not p.folded],
            community_cards=state.community_cards,
            simulations=1000,
            rng=state.rng,
        )

    def calculate_hand_odds(self, player: Player, community: List[Card], simulations: int = 1000) -> dict[str, float]:
        """Calculate odds of making various hands.

        Args:
            player: Player whose hand to evaluate.
            community: Community cards on the table.
            simulations: Number of Monte Carlo simulations.

        Returns:
            Dictionary of hand types to their probabilities.
        """

        # This is a simplified version - in a full implementation,
        # we'd track how often each hand rank is made
        return {
            "any_pair": 0.0,  # Placeholder
            "two_pair": 0.0,
            "trips": 0.0,
            "straight": 0.0,
            "flush": 0.0,
            "full_house": 0.0,
            "quads": 0.0,
            "straight_flush": 0.0,
        }

    def calculate_outs(self, hole_cards: List[Card], community: List[Card], target: str) -> tuple[int, float]:
        """Calculate number of outs and probability of hitting.

        Args:
            hole_cards: Player's hole cards.
            community: Community cards shown.
            target: Target hand type (e.g., "flush", "straight").

        Returns:
            Tuple of (number_of_outs, probability_of_hitting).
        """
        # Simplified implementation
        cards_remaining = 52 - len(hole_cards) - len(community)
        cards_to_come = 5 - len(community)

        # Example: flush draw typically has 9 outs
        if target == "flush":
            outs = 9
        elif target == "straight":
            outs = 8
        elif target == "pair":
            outs = 6
        else:
            outs = 0

        if cards_to_come == 2:
            # Turn and river
            prob = 1 - ((cards_remaining - outs) / cards_remaining) * ((cards_remaining - outs - 1) / (cards_remaining - 1))
        elif cards_to_come == 1:
            # River only
            prob = outs / cards_remaining
        else:
            prob = 0.0

        return outs, prob

    def format_pot_odds_comparison(self, amount_to_call: int, current_pot: int, win_probability: float) -> str:
        """Format a comparison of pot odds vs win probability.

        Args:
            amount_to_call: Amount needed to call.
            current_pot: Current pot size.
            win_probability: Estimated win probability.

        Returns:
            Formatted string explaining the comparison.
        """
        pot_odds = self.calculate_pot_odds(amount_to_call, current_pot)
        pot_odds_pct = self.format_probability(pot_odds)
        win_prob_pct = self.format_probability(win_probability)

        msg = f"Pot Odds: {pot_odds_pct} (need to win {pot_odds_pct} of the time to break even)\n"
        msg += f"Win Probability: {win_prob_pct}\n"

        if win_probability > pot_odds:
            advantage = win_probability - pot_odds
            msg += f"✓ PROFITABLE CALL (+{self.format_probability(advantage)} edge)"
        elif win_probability < pot_odds:
            disadvantage = pot_odds - win_probability
            msg += f"✗ UNPROFITABLE CALL (-{self.format_probability(disadvantage)} edge)"
        else:
            msg += "= BREAK-EVEN CALL"

        return msg


class PokerAIExplainer(AIExplainer):
    """Explains poker AI decision-making."""

    def explain_move(self, state: PokerTable, move: Action) -> str:
        """Explain why the AI chose a particular action.

        Args:
            state: Poker table state when move was made.
            move: The action the AI took.

        Returns:
            Explanation of the AI's reasoning.
        """
        from .poker import ActionType

        explanation = f"AI chose to {move.kind.value}"

        if move.kind == ActionType.FOLD:
            explanation += " - Hand strength was too weak relative to the pot odds and bet size."
        elif move.kind == ActionType.CHECK:
            explanation += " - No bet to call, and hand strength doesn't warrant a bet."
        elif move.kind == ActionType.CALL:
            explanation += f" ${move.target_bet} - Hand has sufficient equity to justify calling based on pot odds."
        elif move.kind in (ActionType.BET, ActionType.RAISE):
            explanation += f" to ${move.target_bet} - Strong hand or profitable bluffing opportunity."
        elif move.kind == ActionType.ALL_IN:
            explanation += " - Maximum aggression with very strong hand or calculated bluff."

        return explanation


class PokerTutorialMode(TutorialMode):
    """Tutorial mode for learning poker."""

    def _create_tutorial_steps(self) -> List[TutorialStep]:
        """Create poker tutorial steps.

        Returns:
            List of tutorial steps for learning poker.
        """
        return [
            TutorialStep(
                title="Welcome to Texas Hold'em Poker",
                description=(
                    "Texas Hold'em is played with 2-10 players using a standard 52-card deck. "
                    "Each player receives 2 private hole cards, and 5 community cards are dealt "
                    "face-up on the table. The goal is to make the best 5-card hand using any "
                    "combination of your hole cards and the community cards."
                ),
                hint="The player with the best hand at showdown wins the pot!",
            ),
            TutorialStep(
                title="Understanding Hand Rankings",
                description=(
                    "Poker hands are ranked from highest to lowest:\n"
                    "1. Royal Flush (A-K-Q-J-10 of same suit)\n"
                    "2. Straight Flush (5 cards in sequence, same suit)\n"
                    "3. Four of a Kind\n"
                    "4. Full House (3 of a kind + pair)\n"
                    "5. Flush (5 cards of same suit)\n"
                    "6. Straight (5 cards in sequence)\n"
                    "7. Three of a Kind\n"
                    "8. Two Pair\n"
                    "9. One Pair\n"
                    "10. High Card"
                ),
                hint="Memorizing hand rankings is essential for playing poker!",
            ),
            TutorialStep(
                title="The Betting Rounds",
                description=(
                    "A hand of poker has four betting rounds:\n\n"
                    "1. PRE-FLOP: After receiving hole cards, before community cards are dealt\n"
                    "2. FLOP: After the first 3 community cards are dealt\n"
                    "3. TURN: After the 4th community card is dealt\n"
                    "4. RIVER: After the 5th (final) community card is dealt\n\n"
                    "In each round, players can check, bet, call, raise, or fold."
                ),
                hint="Each betting round continues until all active players have put in the same amount.",
            ),
            TutorialStep(
                title="Understanding Position",
                description=(
                    "Your position at the table determines when you act during each betting round. "
                    "The dealer button rotates clockwise after each hand. Players acting later have "
                    "an advantage because they see what others do first.\n\n"
                    "Position order (from worst to best):\n"
                    "- Small Blind (SB): Posts small blind\n"
                    "- Big Blind (BB): Posts big blind\n"
                    "- Early Position: First to act after blinds\n"
                    "- Middle Position\n"
                    "- Late Position\n"
                    "- Button: Last to act (best position)"
                ),
                hint="Play more hands from late position and fewer from early position!",
            ),
            TutorialStep(
                title="Reading the Board",
                description=(
                    "The community cards (the board) are crucial to evaluating your hand strength. "
                    "You need to consider:\n\n"
                    "- What's the best possible hand (the 'nuts')?\n"
                    "- Are there flush or straight possibilities?\n"
                    "- How does my hand rank against possible opponent hands?\n"
                    "- What draws are available?"
                ),
                hint="Always be aware of what hands are possible with the community cards!",
            ),
            TutorialStep(
                title="Pot Odds and Equity",
                description=(
                    "Pot odds tell you whether a call is profitable:\n\n"
                    "Pot odds = (Amount to call) / (Pot + Amount to call)\n\n"
                    "Compare pot odds to your win probability (equity). If your equity is higher "
                    "than the pot odds, calling is profitable in the long run.\n\n"
                    "Example: $50 pot, $10 to call = 16.7% pot odds\n"
                    "If you have >16.7% chance to win, calling is profitable."
                ),
                hint="Understanding pot odds is key to making profitable decisions!",
            ),
            TutorialStep(
                title="Basic Strategy Tips",
                description=(
                    "Here are some fundamental poker strategies:\n\n"
                    "1. Play tight-aggressive: Play fewer hands, but play them aggressively\n"
                    "2. Position matters: Play more hands in late position\n"
                    "3. Pay attention to opponents: Look for patterns in their play\n"
                    "4. Manage your bankroll: Don't risk more than you can afford to lose\n"
                    "5. Avoid tilt: Don't let emotions control your decisions"
                ),
                hint="Good poker is about making +EV (positive expected value) decisions!",
            ),
            TutorialStep(
                title="Ready to Play!",
                description=(
                    "You've completed the poker tutorial! Now you understand:\n"
                    "- Hand rankings\n"
                    "- Betting rounds\n"
                    "- Position importance\n"
                    "- Pot odds and equity\n"
                    "- Basic strategy\n\n"
                    "Start with low stakes and focus on making good decisions. "
                    "Remember: poker is a game of skill that takes time to master!"
                ),
                hint="Practice makes perfect. Good luck at the tables!",
            ),
        ]
