"""Utilities for running interactive tutorial sessions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, List, Optional, Tuple, TypeVar

from .educational import ProbabilityCalculator, StrategyTip, StrategyTipProvider, TutorialMode, TutorialStep
from .game_engine import GameEngine

MoveType = TypeVar("MoveType")


@dataclass
class TutorialFeedback:
    """Structured feedback returned after processing a move."""

    messages: List[str]
    completed_step: Optional[str] = None
    next_step: Optional[TutorialStep] = None
    tutorial_completed: bool = False


class TutorialSession(Generic[MoveType]):
    """Controller coordinating a game engine with a tutorial mode."""

    def __init__(
        self,
        game: GameEngine[MoveType, Any],
        tutorial: TutorialMode[Any, MoveType],
        *,
        strategy_provider: Optional[StrategyTipProvider] = None,
        probability_calculator: Optional[ProbabilityCalculator] = None,
    ) -> None:
        self.game = game
        self.tutorial = tutorial
        self.strategy_provider = strategy_provider
        self.probability_calculator = probability_calculator

    def get_current_step(self) -> Optional[TutorialStep]:
        """Return the active tutorial step."""

        return self.tutorial.get_current_step()

    def get_hint(self) -> Optional[str]:
        """Return the hint for the active step."""

        step = self.get_current_step()
        return step.hint if step else None

    def request_strategy_tip(self, difficulty: Optional[str] = None) -> Optional[StrategyTip]:
        """Return a contextual strategy tip."""

        if self.strategy_provider is None:
            return None
        if difficulty:
            tips = self.strategy_provider.get_tips_by_difficulty(difficulty)
            return tips[0] if tips else None
        return self.strategy_provider.get_random_tip()

    def estimate_progress(self) -> Optional[str]:
        """Return a formatted progress estimate using the probability calculator."""

        if self.probability_calculator is None:
            return None
        probability = self.probability_calculator.calculate_win_probability(self.game)
        return self.probability_calculator.format_probability(probability)

    def apply_move(self, move: MoveType) -> Tuple[bool, TutorialFeedback]:
        """Execute a move and update tutorial progression."""

        success = self.game.make_move(move)
        messages: List[str] = []
        completed_step: Optional[str] = None

        if not success:
            messages.append("The move was invalid. Revisit the step instructions and try a different action.")
            hint = self.get_hint()
            if hint:
                messages.append(f"Hint: {hint}")
            return success, TutorialFeedback(messages=messages, completed_step=None, next_step=self.get_current_step())

        if self.tutorial.completed:
            messages.append("Tutorial already completed. Continue practising on your own!")
            return success, TutorialFeedback(messages=messages, completed_step=None, tutorial_completed=True)

        current_step = self.get_current_step()
        if current_step is None:
            messages.append("Tutorial completed—great job!")
            return success, TutorialFeedback(messages=messages, completed_step=None, tutorial_completed=True)

        if self.tutorial.validate_current_step(self.game):
            completed_step = current_step.title
            self.tutorial.advance_step()
            messages.append(f"✅ Completed step: {current_step.title}")
            next_step = self.get_current_step()
            if next_step is not None:
                messages.append(f"Next: {next_step.title}\n{next_step.description}")
                if next_step.hint:
                    messages.append(f"Hint: {next_step.hint}")
            else:
                messages.append("🎉 Tutorial completed! Practice a full game to reinforce your learning.")
                return success, TutorialFeedback(
                    messages=messages,
                    completed_step=completed_step,
                    next_step=None,
                    tutorial_completed=True,
                )
            return success, TutorialFeedback(messages=messages, completed_step=completed_step, next_step=next_step)

        hint = self.get_hint()
        messages.append("Progress paused—double-check the instructions before trying again.")
        if hint:
            messages.append(f"Hint: {hint}")
        return success, TutorialFeedback(messages=messages, completed_step=None, next_step=current_step)

    def reset(self) -> None:
        """Reset both tutorial and game state (if supported)."""

        if hasattr(self.game, "reset"):
            try:
                self.game.reset()  # type: ignore[call-arg]
            except TypeError:
                # Some games require extra parameters; ignore and keep current state.
                pass
        self.tutorial.reset()

