"""Central registry for dynamically generated tutorial modes."""

from __future__ import annotations

import importlib
import inspect
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .educational import DocumentationTutorialMode, ProbabilityCalculator, StrategyTip, StrategyTipProvider, TutorialMode
from .game_engine import GameEngine, GameState

ProjectPath = Path(__file__).resolve().parents[1]
CatalogPath = ProjectPath / "docs" / "source" / "games_catalog.rst"


@dataclass
class TutorialMetadata:
    """Metadata describing a tutorial entry."""

    game_key: str
    display_name: str
    category: str
    doc_path: str
    summary: str
    objectives: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)
    difficulty_notes: Dict[str, str] = field(default_factory=dict)
    learning_goals: Dict[str, str] = field(default_factory=dict)
    default_difficulty: str = "beginner"
    engine_class: Optional[Type[GameEngine[Any, Any]]] = None

    def as_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation for tutorials."""

        return {
            "display_name": self.display_name,
            "doc_path": self.doc_path,
            "summary": self.summary,
            "objectives": self.objectives,
            "hints": self.hints,
            "difficulty_notes": self.difficulty_notes,
            "learning_goals": self.learning_goals,
            "default_difficulty": self.default_difficulty,
        }


@dataclass
class TutorialRegistration:
    """Stores tutorial registration data."""

    metadata: TutorialMetadata
    tutorial_class: Type[TutorialMode[Any, Any]]
    strategy_provider: StrategyTipProvider
    probability_calculator: ProbabilityCalculator


class SimpleProgressProbabilityCalculator(ProbabilityCalculator):
    """Estimate progress probability based on basic game state."""

    def calculate_win_probability(self, state: Any) -> float:
        get_state = getattr(state, "get_game_state", None)
        current_state: GameState | str | None = None
        if callable(get_state):
            try:
                current_state = get_state()
            except Exception:  # pragma: no cover - defensive
                current_state = None
        elif hasattr(state, "state"):
            current_state = getattr(state, "state")

        if isinstance(current_state, GameState):
            if current_state is GameState.NOT_STARTED:
                return 0.2
            if current_state is GameState.IN_PROGRESS:
                return 0.5
            if current_state is GameState.FINISHED:
                winner = getattr(state, "get_winner", None)
                if callable(winner):
                    return 1.0 if winner() is not None else 0.5
                return 0.8
        elif isinstance(current_state, str):
            if current_state in {"not_started", "setup"}:
                return 0.2
            if current_state in {"finished", "complete"}:
                return 0.8

        is_over = getattr(state, "is_game_over", None)
        if callable(is_over):
            try:
                if is_over():
                    return 0.8
            except Exception:  # pragma: no cover - defensive
                return 0.5
        return 0.5


class TutorialRegistry:
    """Registry for all available tutorials."""

    def __init__(self) -> None:
        self._tutorials: Dict[str, TutorialRegistration] = {}

    def register(self, registration: TutorialRegistration) -> None:
        """Register a tutorial entry."""

        self._tutorials[registration.metadata.game_key] = registration

    def available_games(self) -> List[str]:
        """Return sorted list of registered game identifiers."""

        return sorted(self._tutorials)

    def get_registration(self, game_key: str) -> TutorialRegistration:
        """Return the registration for a given game."""

        return self._tutorials[game_key]

    def get_metadata(self, game_key: str) -> TutorialMetadata:
        """Return metadata for a game."""

        return self.get_registration(game_key).metadata

    def get_tutorial_class(self, game_key: str) -> Type[TutorialMode[Any, Any]]:
        """Return the tutorial class for the given game."""

        return self.get_registration(game_key).tutorial_class

    def get_strategy_provider(self, game_key: str) -> StrategyTipProvider:
        """Return strategy tips for the given game."""

        return self.get_registration(game_key).strategy_provider

    def get_probability_calculator(self, game_key: str) -> ProbabilityCalculator:
        """Return probability calculator for the given game."""

        return self.get_registration(game_key).probability_calculator


GLOBAL_TUTORIAL_REGISTRY = TutorialRegistry()


def _parse_games_catalog(path: Path) -> List[str]:
    modules: List[str] = []
    if not path.exists():
        return modules
    pattern = re.compile(r"- :mod:`([^`]+)`")
    content = path.read_text(encoding="utf-8")
    modules.extend(pattern.findall(content))
    return modules


def _title_from_module(module_name: str) -> str:
    return module_name.split(".")[-1].replace("_", " ").title()


def _category_from_module(module_name: str) -> str:
    return module_name.split(".")[0]


def _guess_doc_path(module_name: str) -> str:
    relative_path = Path(*module_name.split(".")) / "README.md"
    absolute_path = ProjectPath / relative_path
    if absolute_path.exists():
        return str(relative_path)
    return "docs/source/games_catalog.rst"


def _category_objectives(category: str, display_name: str) -> List[str]:
    base = (
        f"Follow the setup details for {display_name} in the documentation to prepare the play area.",
        "Execute the opening sequence and confirm the game is actively in progress.",
        "Play until you reach a standard end condition to observe how victory is determined.",
    )
    if category == "card_games":
        return [
            base[0],
            "Practice dealing, drawing, or bidding exactly as described in the rules summary.",
            "Complete a hand and tally the score according to the scoring table in the documentation.",
        ]
    if category == "dice_games":
        return [
            base[0],
            "Roll and resolve dice actions, applying any reroll or banking options listed in the rules.",
            "Finish a full round so you can total the points and reset for the next player.",
        ]
    if category == "logic_games":
        return [
            base[0],
            "Perform a legal move that changes the puzzle state and reveals feedback cues.",
            "Continue solving until the puzzle reports completion or no further moves are possible.",
        ]
    if category == "paper_games":
        return [
            base[0],
            "Execute turns respecting the interaction rules (such as marking grids or moving tokens).",
            "Play to a win, loss, or draw to experience the full decision cycle.",
        ]
    if category == "word_games":
        return [
            base[0],
            "Submit guesses or words and observe the validation feedback described in the docs.",
            "Complete a session to reveal scoring or success criteria.",
        ]
    return list(base)


def _category_hints(category: str, doc_path: str) -> List[str]:
    base_hint = f"Keep the documentation ({doc_path}) open so you can double-check rules mid-play."
    if category == "card_games":
        return [
            base_hint,
            "Track the order of play and card visibility to avoid fouls.",
            "Compare your scoring with the example hand in the rules to verify accuracy.",
        ]
    if category == "dice_games":
        return [
            base_hint,
            "Balance risk and reward when deciding whether to reroll or bank points.",
            "Record each turn's outcome so you can analyse probabilities afterwards.",
        ]
    if category == "logic_games":
        return [
            base_hint,
            "Undo is your friend—experiment with moves to learn patterns.",
            "Look for state summaries or counters to gauge proximity to the solution.",
        ]
    if category == "paper_games":
        return [
            base_hint,
            "Watch for opponent reactions or forced moves to anticipate the next turn.",
            "Take notes about strong positions so you can reuse them in later matches.",
        ]
    if category == "word_games":
        return [
            base_hint,
            "Use letter frequency from the docs to prioritise guesses.",
            "Cross-reference clues with example solutions to confirm your reasoning.",
        ]
    return [base_hint]


def _difficulty_notes(category: str) -> Dict[str, str]:
    return {
        "beginner": "Focus on the fundamental turn structure and terminology.",
        "intermediate": "Apply the scoring examples from the documentation to your gameplay.",
        "advanced": "Analyse alternative strategies and edge cases described in the reference material.",
    }


def _learning_goals(category: str) -> Dict[str, str]:
    return {
        "mechanics": "Understand the turn order and legal action set before improvising strategies.",
        "strategy": "Evaluate decisions that maximise your advantage based on documented heuristics.",
        "scoring": "Cross-check every scoring action with the provided tables to avoid mistakes.",
    }


def _locate_engine_class(module_name: str) -> Optional[Type[GameEngine[Any, Any]]]:
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return None

    def candidate_from_module(mod: Any) -> Optional[Type[GameEngine[Any, Any]]]:
        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if issubclass(obj, GameEngine) and obj is not GameEngine:
                return obj
        return None

    candidate = candidate_from_module(module)
    if candidate:
        return candidate

    if hasattr(module, "__all__"):
        for name in getattr(module, "__all__", []):
            attr = getattr(module, name, None)
            if inspect.isclass(attr) and issubclass(attr, GameEngine) and attr is not GameEngine:
                return attr

    return None


def _build_tutorial_class(metadata: TutorialMetadata) -> Type[TutorialMode[Any, Any]]:
    class_name = metadata.display_name.replace(" ", "") + "TutorialMode"
    base_dict = metadata.as_dict()

    def __init__(self, difficulty: Optional[str] = None, learning_goal: Optional[str] = None) -> None:
        DocumentationTutorialMode.__init__(self, base_dict, difficulty=difficulty, learning_goal=learning_goal)

    tutorial_cls = type(
        class_name,
        (DocumentationTutorialMode,),
        {
            "__init__": __init__,
            "__module__": __name__,
            "__doc__": f"Automatically generated tutorial mode for {metadata.display_name}.",
        },
    )
    return tutorial_cls


def _create_strategy_provider(metadata: TutorialMetadata) -> StrategyTipProvider:
    provider = StrategyTipProvider()
    provider.add_tip(
        StrategyTip(
            title=f"{metadata.display_name} fundamentals",
            description=metadata.summary,
            applies_to=metadata.doc_path,
            difficulty="beginner",
        )
    )
    for difficulty, note in metadata.difficulty_notes.items():
        provider.add_tip(
            StrategyTip(
                title=f"{metadata.display_name} {difficulty.title()} focus",
                description=note,
                applies_to=", ".join(metadata.objectives[:1]) if metadata.objectives else metadata.doc_path,
                difficulty=difficulty,
            )
        )
    return provider


def load_default_tutorials() -> None:
    """Populate the global registry using the games catalogue."""

    modules = _parse_games_catalog(CatalogPath)
    for module_name in modules:
        display_name = _title_from_module(module_name)
        category = _category_from_module(module_name)
        doc_path = _guess_doc_path(module_name)
        summary = f"Guided walkthrough for {display_name} using the official rules described in {doc_path}."
        objectives = _category_objectives(category, display_name)
        hints = _category_hints(category, doc_path)
        metadata = TutorialMetadata(
            game_key=module_name,
            display_name=display_name,
            category=category,
            doc_path=doc_path,
            summary=summary,
            objectives=objectives,
            hints=hints,
            difficulty_notes=_difficulty_notes(category),
            learning_goals=_learning_goals(category),
            default_difficulty="beginner",
            engine_class=_locate_engine_class(module_name),
        )
        tutorial_cls = _build_tutorial_class(metadata)
        strategy_provider = _create_strategy_provider(metadata)
        probability_calculator = SimpleProgressProbabilityCalculator()
        registration = TutorialRegistration(
            metadata=metadata,
            tutorial_class=tutorial_cls,
            strategy_provider=strategy_provider,
            probability_calculator=probability_calculator,
        )
        GLOBAL_TUTORIAL_REGISTRY.register(registration)


# Populate registry on import
load_default_tutorials()
