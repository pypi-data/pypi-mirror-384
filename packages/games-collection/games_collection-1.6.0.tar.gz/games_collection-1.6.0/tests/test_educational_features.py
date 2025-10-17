"""Tests for educational features.

This module tests the educational utilities including tutorial modes,
probability calculators, and challenge systems.
"""

from __future__ import annotations

import pytest

from common import (
    Challenge,
    ChallengeManager,
    ChallengePack,
    DifficultyLevel,
    GameTheoryExplainer,
    ProbabilityCalculator,
    StrategyTip,
    StrategyTipProvider,
    TutorialMode,
    TutorialStep,
    get_default_challenge_manager,
)


class TestTutorialMode:
    """Test tutorial mode functionality."""

    def test_tutorial_creation(self):
        """Test creating a simple tutorial."""

        class SimpleTutorial(TutorialMode):
            def _create_tutorial_steps(self):
                return [
                    TutorialStep(title="Step 1", description="First step", hint="Hint 1"),
                    TutorialStep(title="Step 2", description="Second step", hint="Hint 2"),
                ]

        tutorial = SimpleTutorial()
        assert tutorial.current_step == 0
        assert not tutorial.completed
        assert len(tutorial.steps) == 2

    def test_tutorial_progression(self):
        """Test advancing through tutorial steps."""

        class SimpleTutorial(TutorialMode):
            def _create_tutorial_steps(self):
                return [
                    TutorialStep(title="Step 1", description="First step"),
                    TutorialStep(title="Step 2", description="Second step"),
                ]

        tutorial = SimpleTutorial()
        step1 = tutorial.get_current_step()
        assert step1.title == "Step 1"

        success = tutorial.advance_step()
        assert success
        step2 = tutorial.get_current_step()
        assert step2.title == "Step 2"

        success = tutorial.advance_step()
        assert not success  # No more steps
        assert tutorial.completed

    def test_tutorial_reset(self):
        """Test resetting tutorial to beginning."""

        class SimpleTutorial(TutorialMode):
            def _create_tutorial_steps(self):
                return [TutorialStep(title="Step 1", description="First step")]

        tutorial = SimpleTutorial()
        tutorial.advance_step()
        tutorial.reset()
        assert tutorial.current_step == 0
        assert not tutorial.completed


class TestStrategyTips:
    """Test strategy tip functionality."""

    def test_tip_creation(self):
        """Test creating a strategy tip."""
        tip = StrategyTip(
            title="Test Tip",
            description="This is a test tip",
            difficulty="beginner",
        )
        assert tip.title == "Test Tip"
        assert tip.difficulty == "beginner"

    def test_tip_provider(self):
        """Test strategy tip provider."""
        provider = StrategyTipProvider()

        tip1 = StrategyTip(title="Tip 1", description="First tip", difficulty="beginner")
        tip2 = StrategyTip(title="Tip 2", description="Second tip", difficulty="advanced")

        provider.add_tip(tip1)
        provider.add_tip(tip2)

        assert len(provider.tips) == 2

        beginner_tips = provider.get_tips_by_difficulty("beginner")
        assert len(beginner_tips) == 1
        assert beginner_tips[0].title == "Tip 1"

    def test_random_tip(self):
        """Test getting random tip."""
        provider = StrategyTipProvider()
        tip = provider.get_random_tip()
        assert tip is None  # No tips added yet

        provider.add_tip(StrategyTip(title="Tip", description="Desc"))
        tip = provider.get_random_tip()
        assert tip is not None
        assert tip.title == "Tip"


class TestProbabilityCalculator:
    """Test probability calculator functionality."""

    def test_format_probability(self):
        """Test probability formatting."""
        assert ProbabilityCalculator.format_probability(0.5) == "50.0%"
        assert ProbabilityCalculator.format_probability(0.333) == "33.3%"
        assert ProbabilityCalculator.format_probability(1.0) == "100.0%"

    def test_pot_odds_calculation(self):
        """Test pot odds calculation."""
        # $20 to call into $100 pot
        pot_odds = ProbabilityCalculator.calculate_pot_odds(20, 100)
        assert abs(pot_odds - 0.1667) < 0.001  # ~16.67%

        # $50 to call into $150 pot
        pot_odds = ProbabilityCalculator.calculate_pot_odds(50, 150)
        assert abs(pot_odds - 0.25) < 0.001  # 25%


class TestGameTheoryExplainer:
    """Test game theory explanation functionality."""

    def test_explainer_initialization(self):
        """Test that explainer comes with default explanations."""
        explainer = GameTheoryExplainer()
        concepts = explainer.list_concepts()
        assert "Minimax Algorithm" in concepts
        assert "Monte Carlo Simulation" in concepts

    def test_get_explanation(self):
        """Test getting a specific explanation."""
        explainer = GameTheoryExplainer()

        minimax = explainer.get_explanation("minimax")
        assert minimax is not None
        assert "minimax" in minimax.concept.lower()
        assert len(minimax.description) > 0

        monte_carlo = explainer.get_explanation("monte_carlo")
        assert monte_carlo is not None
        assert "monte carlo" in monte_carlo.concept.lower()

    def test_get_nonexistent_explanation(self):
        """Test getting explanation that doesn't exist."""
        explainer = GameTheoryExplainer()
        result = explainer.get_explanation("nonexistent")
        assert result is None


class TestChallenges:
    """Test challenge system functionality."""

    def test_challenge_creation(self):
        """Test creating a challenge."""
        challenge = Challenge(
            id="test_1",
            title="Test Challenge",
            description="This is a test",
            difficulty=DifficultyLevel.BEGINNER,
            initial_state={},
            goal="Complete the test",
        )
        assert challenge.id == "test_1"
        assert challenge.difficulty == DifficultyLevel.BEGINNER

    def test_challenge_pack(self):
        """Test challenge pack functionality."""
        pack = ChallengePack(name="Test Pack", description="Test description")

        challenge = Challenge(
            id="test_1",
            title="Test",
            description="Desc",
            difficulty=DifficultyLevel.BEGINNER,
            initial_state={},
            goal="Goal",
        )

        pack.add_challenge(challenge)
        assert len(pack) == 1

        retrieved = pack.get_challenge("test_1")
        assert retrieved is not None
        assert retrieved.id == "test_1"

    def test_challenge_pack_filtering(self):
        """Test filtering challenges by difficulty."""
        pack = ChallengePack(name="Test Pack", description="Test")

        pack.add_challenge(
            Challenge(
                id="easy",
                title="Easy",
                description="Easy challenge",
                difficulty=DifficultyLevel.BEGINNER,
                initial_state={},
                goal="Complete",
            )
        )
        pack.add_challenge(
            Challenge(
                id="hard",
                title="Hard",
                description="Hard challenge",
                difficulty=DifficultyLevel.ADVANCED,
                initial_state={},
                goal="Complete",
            )
        )

        beginner = pack.get_challenges_by_difficulty(DifficultyLevel.BEGINNER)
        assert len(beginner) == 1
        assert beginner[0].id == "easy"

        advanced = pack.get_challenges_by_difficulty(DifficultyLevel.ADVANCED)
        assert len(advanced) == 1
        assert advanced[0].id == "hard"

    def test_challenge_manager(self):
        """Test challenge manager functionality."""
        manager = ChallengeManager()

        pack1 = ChallengePack(name="Pack 1", description="First pack")
        pack2 = ChallengePack(name="Pack 2", description="Second pack")

        manager.register_pack(pack1)
        manager.register_pack(pack2)

        assert len(manager.list_packs()) == 2
        assert "Pack 1" in manager.list_packs()

        retrieved = manager.get_pack("Pack 1")
        assert retrieved is not None
        assert retrieved.name == "Pack 1"

    def test_default_challenge_manager(self):
        """Test that default manager comes with pre-loaded challenges."""
        manager = get_default_challenge_manager()

        packs = manager.list_packs()
        assert len(packs) > 0
        assert "Poker Fundamentals" in packs or "Blackjack Mastery" in packs or "Nim Puzzles" in packs


class TestPokerEducational:
    """Test poker-specific educational features."""

    def test_poker_probability_calculator_import(self):
        """Test that poker educational module can be imported."""
        try:
            from card_games.poker.educational import PokerProbabilityCalculator

            calc = PokerProbabilityCalculator()
            assert calc is not None
        except ImportError:
            pytest.skip("Poker module not available")

    def test_poker_tutorial_import(self):
        """Test that poker tutorial can be imported."""
        try:
            from card_games.poker.educational import PokerTutorialMode

            tutorial = PokerTutorialMode()
            assert tutorial is not None
            assert len(tutorial.steps) > 0
        except ImportError:
            pytest.skip("Poker module not available")


class TestBlackjackEducational:
    """Test blackjack-specific educational features."""

    def test_blackjack_probability_calculator_import(self):
        """Test that blackjack educational module can be imported."""
        try:
            from card_games.blackjack.educational import BlackjackProbabilityCalculator

            calc = BlackjackProbabilityCalculator()
            assert calc is not None
        except ImportError:
            pytest.skip("Blackjack module not available")

    def test_blackjack_tutorial_import(self):
        """Test that blackjack tutorial can be imported."""
        try:
            from card_games.blackjack.educational import BlackjackTutorialMode

            tutorial = BlackjackTutorialMode()
            assert tutorial is not None
            assert len(tutorial.steps) > 0
        except ImportError:
            pytest.skip("Blackjack module not available")

    def test_blackjack_bust_probability(self):
        """Test blackjack bust probability calculation."""
        try:
            from card_games.blackjack.educational import BlackjackProbabilityCalculator

            calc = BlackjackProbabilityCalculator()

            # Test bust probabilities
            assert calc.calculate_bust_probability(21) == 0.0  # Can't bust on 21
            assert calc.calculate_bust_probability(11) < 0.5  # Low probability on 11
            assert calc.calculate_bust_probability(20) > 0.9  # High probability on 20
        except ImportError:
            pytest.skip("Blackjack module not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
