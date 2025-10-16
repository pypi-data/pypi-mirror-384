"""Educational utilities for games.

This module provides base classes and utilities for implementing educational
features across all games, including tutorial modes, strategy tips, probability
calculators, and game theory explanations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from .game_engine import GameState

StateType = TypeVar("StateType")
MoveType = TypeVar("MoveType")


@dataclass
class TutorialStep:
    """Represents a single step in a tutorial.

    Attributes:
        title: Short title for this step.
        description: Detailed description of what to do.
        hint: Optional hint for this step.
        validate: Optional function to validate if step is completed correctly.
    """

    title: str
    description: str
    hint: Optional[str] = None
    validate: Optional[Callable[[Any], bool]] = None


class TutorialMode(ABC, Generic[StateType, MoveType]):
    """Base class for tutorial modes in games.

    Provides step-by-step guidance for learning how to play a game.
    """

    def __init__(self) -> None:
        """Initialize tutorial mode."""
        self.current_step = 0
        self.steps = self._create_tutorial_steps()
        self.completed = False

    @abstractmethod
    def _create_tutorial_steps(self) -> List[TutorialStep]:
        """Create the list of tutorial steps for this game.

        Returns:
            List of tutorial steps in order.
        """
        pass

    def get_current_step(self) -> Optional[TutorialStep]:
        """Get the current tutorial step.

        Returns:
            The current TutorialStep, or None if tutorial is completed.
        """
        if self.current_step >= len(self.steps):
            self.completed = True
            return None
        return self.steps[self.current_step]

    def advance_step(self) -> bool:
        """Advance to the next tutorial step.

        Returns:
            True if advanced successfully, False if tutorial is completed.
        """
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            return True
        self.current_step = len(self.steps)
        self.completed = True
        return False

    def validate_current_step(self, state: Any) -> bool:
        """Validate if the current step was completed correctly.

        Args:
            state: Current game state to validate against.

        Returns:
            True if step is valid, False otherwise.
        """
        step = self.get_current_step()
        if step is None or step.validate is None:
            return True
        return step.validate(state)

    def reset(self) -> None:
        """Reset tutorial to the beginning."""
        self.current_step = 0
        self.completed = False


class DocumentationTutorialMode(TutorialMode[StateType, MoveType]):
    """Tutorial mode that generates steps from documentation metadata.

    Parameters
    ----------
    metadata:
        Dictionary containing descriptive tutorial information.  Expected keys
        are ``display_name``, ``doc_path``, ``summary``, ``objectives``,
        ``hints`` and optional ``difficulty_notes`` / ``learning_goals``.
    difficulty:
        Selected difficulty level; defaults to the metadata's
        ``default_difficulty`` value when omitted.
    learning_goal:
        Focus area chosen by the player (for example "strategy" or
        "mechanics").  When provided it is surfaced in the generated step
        descriptions.
    """

    def __init__(
        self,
        metadata: Dict[str, Any],
        difficulty: Optional[str] = None,
        learning_goal: Optional[str] = None,
    ) -> None:
        self.metadata = metadata
        self.selected_difficulty = difficulty or metadata.get("default_difficulty", "beginner")
        self.learning_goal = learning_goal
        super().__init__()

    def _create_tutorial_steps(self) -> List[TutorialStep]:
        """Generate tutorial steps from metadata."""

        doc_path = self.metadata.get("doc_path", "docs/source/games_catalog.rst")
        summary = self.metadata.get("summary", "Follow the official rules outlined in the documentation.")
        objectives = list(self.metadata.get("objectives", []))
        if not objectives:
            objectives = [
                "Review the rules described in the documentation.",
                "Execute a legal move to start the game.",
                "Finish a full round to observe scoring or end conditions.",
            ]
        hints = list(self.metadata.get("hints", []))
        difficulty_notes = self.metadata.get("difficulty_notes", {})
        learning_focus = None
        if self.learning_goal:
            learning_focus = self.metadata.get("learning_goals", {}).get(self.learning_goal)

        steps: List[TutorialStep] = []
        intro_hint = hints[0] if hints else None
        intro_description = (
            f"{summary}\n\n"
            f"Reference: ``{doc_path}``."
        )
        if learning_focus:
            intro_description += f"\n\nFocus: {learning_focus}"
        steps.append(
            TutorialStep(
                title=f"Study {self.metadata.get('display_name', 'the rules')}",
                description=intro_description,
                hint=intro_hint,
            )
        )

        if len(objectives) > 0:
            hint = hints[1] if len(hints) > 1 else None
            description = objectives[0]
            extra = difficulty_notes.get(self.selected_difficulty)
            if extra:
                description += f"\n\nDifficulty focus: {extra}"
            steps.append(
                TutorialStep(
                    title="Take your opening actions",
                    description=description,
                    hint=hint,
                    validate=self._validate_started,
                )
            )

        if len(objectives) > 1:
            hint = hints[2] if len(hints) > 2 else None
            description = objectives[1]
            if len(objectives) > 2:
                description += f"\n\nNext: {objectives[2]}"
            steps.append(
                TutorialStep(
                    title="Play through a complete round",
                    description=description,
                    hint=hint,
                    validate=self._validate_finished,
                )
            )

        return steps

    @staticmethod
    def _validate_started(state: Any) -> bool:
        """Check that the underlying game has started."""

        get_state = getattr(state, "get_game_state", None)
        if callable(get_state):
            try:
                value = get_state()
            except Exception:  # pragma: no cover - defensive
                return False
            if isinstance(value, GameState):
                return value in {GameState.IN_PROGRESS, GameState.FINISHED}
            return value not in (None, "not_started")
        game_state = getattr(state, "state", None)
        if isinstance(game_state, GameState):
            return game_state in {GameState.IN_PROGRESS, GameState.FINISHED}
        return game_state not in (None, "not_started")

    @staticmethod
    def _validate_finished(state: Any) -> bool:
        """Check that the underlying game has reached an end condition."""

        is_over = getattr(state, "is_game_over", None)
        if callable(is_over):
            try:
                if is_over():
                    return True
            except Exception:  # pragma: no cover - defensive
                return False
        get_state = getattr(state, "get_game_state", None)
        if callable(get_state):
            try:
                value = get_state()
            except Exception:  # pragma: no cover - defensive
                return False
            if isinstance(value, GameState):
                return value is GameState.FINISHED
            return value in {"finished", "complete"}
        return False


@dataclass
class StrategyTip:
    """Represents a strategy tip for gameplay.

    Attributes:
        title: Short title for the tip.
        description: Detailed explanation of the strategy.
        applies_to: Optional description of when this tip applies.
        difficulty: Difficulty level of this tip (beginner, intermediate, advanced).
    """

    title: str
    description: str
    applies_to: Optional[str] = None
    difficulty: str = "beginner"


class StrategyTipProvider:
    """Provides context-aware strategy tips during gameplay."""

    def __init__(self) -> None:
        """Initialize the strategy tip provider."""
        self.tips: List[StrategyTip] = []

    def add_tip(self, tip: StrategyTip) -> None:
        """Add a strategy tip to the provider.

        Args:
            tip: The strategy tip to add.
        """
        self.tips.append(tip)

    def get_random_tip(self) -> Optional[StrategyTip]:
        """Get a random strategy tip.

        Returns:
            A random strategy tip, or None if no tips available.
        """
        if not self.tips:
            return None
        import random

        return random.choice(self.tips)

    def get_tips_by_difficulty(self, difficulty: str) -> List[StrategyTip]:
        """Get all tips for a specific difficulty level.

        Args:
            difficulty: The difficulty level to filter by.

        Returns:
            List of tips matching the difficulty level.
        """
        return [tip for tip in self.tips if tip.difficulty == difficulty]


class ProbabilityCalculator(ABC):
    """Base class for probability calculators.

    Provides methods to calculate probabilities and odds in games.
    """

    @abstractmethod
    def calculate_win_probability(self, state: Any) -> float:
        """Calculate the probability of winning from current state.

        Args:
            state: Current game state.

        Returns:
            Probability of winning (0.0 to 1.0).
        """
        pass

    @staticmethod
    def format_probability(probability: float) -> str:
        """Format a probability as a percentage string.

        Args:
            probability: Probability value (0.0 to 1.0).

        Returns:
            Formatted probability string (e.g., "65.4%").
        """
        return f"{probability * 100:.1f}%"

    @staticmethod
    def calculate_pot_odds(amount_to_call: int, current_pot: int) -> float:
        """Calculate pot odds.

        Args:
            amount_to_call: Amount needed to call.
            current_pot: Current size of the pot.

        Returns:
            Pot odds as a ratio (0.0 to 1.0).
        """
        if amount_to_call <= 0:
            return 0.0
        total_pot = current_pot + amount_to_call
        return amount_to_call / total_pot if total_pot > 0 else 0.0


@dataclass
class GameTheoryExplanation:
    """Represents a game theory concept explanation.

    Attributes:
        concept: Name of the concept (e.g., "Minimax", "Monte Carlo").
        description: Detailed explanation of the concept.
        example: Optional example demonstrating the concept.
        code_snippet: Optional code snippet showing implementation.
    """

    concept: str
    description: str
    example: Optional[str] = None
    code_snippet: Optional[str] = None


class GameTheoryExplainer:
    """Provides explanations of game theory concepts used in games."""

    def __init__(self) -> None:
        """Initialize the game theory explainer with common concepts."""
        self.explanations: dict[str, GameTheoryExplanation] = {}
        self._add_default_explanations()

    def _add_default_explanations(self) -> None:
        """Add default game theory explanations."""
        self.explanations["minimax"] = GameTheoryExplanation(
            concept="Minimax Algorithm",
            description=(
                "Minimax is a decision-making algorithm used in two-player games. "
                "It works by assuming both players play optimally: one player tries to "
                "maximize their score (max player) while the other tries to minimize it "
                "(min player). The algorithm recursively explores all possible game states "
                "to find the best move."
            ),
            example=(
                "In Tic-Tac-Toe, the AI evaluates all possible moves and their outcomes. "
                "It assumes you will make the best possible response to each of its moves, "
                "and chooses the move that leads to the best outcome even against perfect play."
            ),
        )

        self.explanations["monte_carlo"] = GameTheoryExplanation(
            concept="Monte Carlo Simulation",
            description=(
                "Monte Carlo methods use random sampling to estimate outcomes in situations "
                "where calculating exact probabilities is too complex or computationally expensive. "
                "The algorithm runs many random simulations and uses the results to estimate "
                "probabilities and make decisions."
            ),
            example=(
                "In poker, instead of calculating exact win probabilities (which requires "
                "considering all possible card combinations), the AI runs thousands of random "
                "simulations where it deals random cards and sees how often it wins. This gives "
                "a good estimate of win probability much faster than exact calculation."
            ),
        )

        self.explanations["nim_sum"] = GameTheoryExplanation(
            concept="Nim-Sum (XOR Strategy)",
            description=(
                "In Nim and similar games, the nim-sum (XOR of all heap sizes) determines "
                "if a position is winning or losing. If the nim-sum is 0, the position is losing; "
                "if non-zero, there exists a winning move. The optimal strategy is to always "
                "make a move that results in a nim-sum of 0."
            ),
            example=(
                "With heaps [3, 4, 5], the nim-sum is 3 XOR 4 XOR 5 = 2 (non-zero), so it's "
                "a winning position. The winning move is to reduce the heap of 5 to 4, giving "
                "[3, 4, 4] with nim-sum = 3 XOR 4 XOR 4 = 3, which is winning for the opponent."
            ),
        )

        self.explanations["expected_value"] = GameTheoryExplanation(
            concept="Expected Value",
            description=(
                "Expected value (EV) is the average outcome of a decision if it were repeated "
                "many times. It's calculated by multiplying each possible outcome by its probability "
                "and summing the results. In games, positive EV decisions are profitable in the long run."
            ),
            example=(
                "In poker, if there's $100 in the pot and you need to call $20 with a 30% chance "
                "to win: EV = (0.30 × $100) - (0.70 × $20) = $30 - $14 = +$16. This is a +EV call, "
                "meaning you should call because on average you'll profit $16."
            ),
        )

        self.explanations["card_counting"] = GameTheoryExplanation(
            concept="Card Counting (Hi-Lo System)",
            description=(
                "Card counting in blackjack tracks the ratio of high cards (10, J, Q, K, A) to "
                "low cards (2-6) remaining in the deck. High cards favor the player, low cards favor "
                "the dealer. The Hi-Lo system assigns: +1 for low cards (2-6), 0 for neutral (7-9), "
                "and -1 for high cards (10-A). The 'true count' divides the running count by decks remaining."
            ),
            example=(
                "If the running count is +8 with 4 decks remaining, the true count is +2. "
                "This suggests the deck is slightly favorable, so you might increase your bet size. "
                "At true count +3 or higher, the advantage significantly favors the player."
            ),
        )

    def get_explanation(self, concept: str) -> Optional[GameTheoryExplanation]:
        """Get an explanation for a game theory concept.

        Args:
            concept: Name of the concept to explain.

        Returns:
            GameTheoryExplanation if found, None otherwise.
        """
        return self.explanations.get(concept.lower())

    def add_explanation(self, explanation: GameTheoryExplanation) -> None:
        """Add a new game theory explanation.

        Args:
            explanation: The explanation to add.
        """
        self.explanations[explanation.concept.lower()] = explanation

    def list_concepts(self) -> List[str]:
        """List all available game theory concepts.

        Returns:
            List of concept names.
        """
        return [exp.concept for exp in self.explanations.values()]


class AIExplainer(ABC):
    """Base class for explaining AI decision-making.

    Allows the AI to explain why it made a particular move.
    """

    @abstractmethod
    def explain_move(self, state: Any, move: Any) -> str:
        """Explain why the AI chose a particular move.

        Args:
            state: The game state when the move was made.
            move: The move that was made.

        Returns:
            Explanation string describing the AI's reasoning.
        """
        pass
