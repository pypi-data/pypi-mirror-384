"""Trivia game engine with online fetching, caching, and offline fallbacks."""

from __future__ import annotations

import json
import random
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from common.game_engine import GameEngine, GameState

DEFAULT_API_URL = "https://opentdb.com/api.php"


@dataclass
class TriviaQuestion:
    """Representation of a trivia question.

    Attributes:
        question: Question text.
        options: Normalised list of multiple choice options.
        correct: Index of the correct option.
        category: Optional category provided by the API source.
        difficulty: Optional difficulty level for the question.
    """

    question: str
    options: List[str]
    correct: int
    category: Optional[str] = None
    difficulty: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the question for cache persistence."""

        return {
            "question": self.question,
            "options": self.options,
            "correct": self.correct,
            "category": self.category,
            "difficulty": self.difficulty,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TriviaQuestion":
        """Create a ``TriviaQuestion`` from a JSON payload."""

        return cls(
            question=payload["question"],
            options=list(payload["options"]),
            correct=int(payload["correct"]),
            category=payload.get("category"),
            difficulty=payload.get("difficulty"),
        )


class TriviaCache:
    """Local cache used when offline or to warm cold starts."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._questions: List[TriviaQuestion] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (json.JSONDecodeError, OSError):
            payload = []
        for raw in payload:
            try:
                self._questions.append(TriviaQuestion.from_dict(raw))
            except (KeyError, TypeError, ValueError):
                continue

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump([question.to_dict() for question in self._questions], handle, ensure_ascii=False, indent=2)

    def add(self, questions: Iterable[TriviaQuestion]) -> None:
        """Add questions to the cache if they are not duplicates."""

        seen = {question.question for question in self._questions}
        updated = False
        for question in questions:
            if question.question not in seen:
                self._questions.append(question)
                seen.add(question.question)
                updated = True
        if updated:
            self._persist()

    def pop(self, amount: int) -> List[TriviaQuestion]:
        """Remove and return up to ``amount`` cached questions."""

        selected = self._questions[:amount]
        if not selected:
            return []
        self._questions = self._questions[amount:]
        self._persist()
        return selected


class TriviaAPIError(RuntimeError):
    """Raised when the trivia API cannot be reached or returns invalid payloads."""


class TriviaAPIClient:
    """HTTP client responsible for retrieving trivia questions."""

    def __init__(self, base_url: str = DEFAULT_API_URL) -> None:
        self.base_url = base_url

    def fetch_questions(
        self,
        amount: int,
        category: Optional[int] = None,
        difficulty: Optional[str] = None,
    ) -> List[TriviaQuestion]:
        """Fetch questions from the external API."""

        query = {"amount": str(amount), "type": "multiple"}
        if category is not None:
            query["category"] = str(category)
        if difficulty is not None:
            query["difficulty"] = difficulty
        url = f"{self.base_url}?{urllib.parse.urlencode(query)}"
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, json.JSONDecodeError, urllib.error.URLError) as exc:
            raise TriviaAPIError("Unable to retrieve trivia questions") from exc

        results = payload.get("results", [])
        questions = []
        for item in results:
            incorrect = [unescape(value) for value in item.get("incorrect_answers", [])]
            correct_answer = unescape(item.get("correct_answer", ""))
            options = incorrect + [correct_answer]
            if not options:
                continue
            random.shuffle(options)
            try:
                index = options.index(correct_answer)
            except ValueError:
                continue
            questions.append(
                TriviaQuestion(
                    question=unescape(item.get("question", "")),
                    options=options,
                    correct=index,
                    category=item.get("category"),
                    difficulty=item.get("difficulty"),
                )
            )
        if not questions:
            raise TriviaAPIError("API returned no valid questions")
        return questions


class TriviaGame(GameEngine[int, int]):
    """Trivia quiz game with adaptive online/offline sourcing."""

    FALLBACK_QUESTIONS: List[TriviaQuestion] = [
        TriviaQuestion("What is the capital of France?", ["London", "Berlin", "Paris", "Madrid"], 2, "Geography", "easy"),
        TriviaQuestion("What is 2 + 2?", ["3", "4", "5", "6"], 1, "Mathematics", "easy"),
        TriviaQuestion("Which planet is known as the Red Planet?", ["Venus", "Mars", "Jupiter", "Saturn"], 1, "Science", "easy"),
        TriviaQuestion("Who wrote Romeo and Juliet?", ["Dickens", "Shakespeare", "Austen", "Twain"], 1, "Literature", "medium"),
        TriviaQuestion("What is the largest ocean?", ["Atlantic", "Indian", "Arctic", "Pacific"], 3, "Geography", "medium"),
    ]

    def __init__(
        self,
        num_questions: int = 5,
        *,
        category: Optional[int] = None,
        difficulty: Optional[str] = None,
        cache_path: Optional[Path] = None,
        client: Optional[TriviaAPIClient] = None,
        enable_online: bool = True,
    ) -> None:
        """Initialize the game with API integration and caching."""

        self.num_questions = num_questions
        self.category = category
        self.difficulty = difficulty
        self.enable_online = enable_online
        self.client = client or TriviaAPIClient()
        default_cache = Path(__file__).with_name("cache").joinpath("questions.json")
        self.cache = TriviaCache(cache_path or default_cache)
        self.reset()

    def reset(self) -> None:
        """Reset game."""
        self.state = GameState.NOT_STARTED
        self.questions = self._prepare_questions()
        self.current_question_idx = 0
        self.score = 0

    def _prepare_questions(self) -> List[TriviaQuestion]:
        """Load questions via API with caching and fallbacks."""

        questions: List[TriviaQuestion] = []
        fetched: List[TriviaQuestion] = []
        if self.enable_online:
            try:
                fetched = self.client.fetch_questions(self.num_questions, category=self.category, difficulty=self.difficulty)
            except TriviaAPIError:
                fetched = []
        if fetched:
            self.cache.add(fetched)
            questions.extend(fetched)
        if len(questions) < self.num_questions:
            cached = self.cache.pop(self.num_questions - len(questions))
            questions.extend(cached)
        if len(questions) < self.num_questions and self.FALLBACK_QUESTIONS:
            remaining = self.num_questions - len(questions)
            if remaining <= len(self.FALLBACK_QUESTIONS):
                fallback = random.sample(self.FALLBACK_QUESTIONS, remaining)
            else:
                fallback = [random.choice(self.FALLBACK_QUESTIONS) for _ in range(remaining)]
            questions.extend(fallback)
        return questions[: self.num_questions]

    def is_game_over(self) -> bool:
        """Check if game over."""
        return self.current_question_idx >= len(self.questions)

    def get_current_player(self) -> int:
        """Get current player."""
        return 0

    def get_valid_moves(self) -> List[int]:
        """Get valid answer options (0-3)."""
        if self.is_game_over():
            return []
        current = self.questions[self.current_question_idx]
        return list(range(len(current.options)))

    def make_move(self, move: int) -> bool:
        """Submit answer."""
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        if self.is_game_over() or move not in self.get_valid_moves():
            return False

        correct = self.questions[self.current_question_idx].correct
        if move == correct:
            self.score += 1

        self.current_question_idx += 1

        if self.is_game_over():
            self.state = GameState.FINISHED

        return True

    def get_current_question(self) -> Dict[str, Any] | None:
        """Get current question."""
        if self.is_game_over():
            return None
        question = self.questions[self.current_question_idx]
        return {
            "question": question.question,
            "options": question.options,
            "correct": question.correct,
            "category": question.category,
            "difficulty": question.difficulty,
        }

    def get_winner(self) -> int | None:
        """Get winner (score-based)."""
        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Get current game state.

        Returns:
            Current state of the game
        """
        return self.state
