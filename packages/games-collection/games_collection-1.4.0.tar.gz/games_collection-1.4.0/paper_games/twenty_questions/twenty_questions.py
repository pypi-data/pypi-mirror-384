"""Core logic and CLI for 20 Questions with a persistent knowledge base."""

from __future__ import annotations

import json
import math
import os
import random
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from common.game_engine import GameEngine, GameState


def _default_knowledge_base_path() -> Path:
    """Return the default writable location for the knowledge base file."""

    if os.name == "nt":
        base_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base_dir / "games" / "twenty_questions" / "knowledge_base.json"


class TwentyQuestionsKnowledgeBase:
    """Persistent storage for objects and their yes/no features."""

    DEFAULT_OBJECTS = (
        {
            "name": "dog",
            "features": {
                "Is it a living thing?": True,
                "Is it an animal?": True,
                "Is it a pet?": True,
                "Is it a food?": False,
                "Is it a vehicle?": False,
                "Is it a sport?": False,
                "Can you eat it?": False,
                "Does it have wheels?": False,
                "Does it fly?": False,
                "Does it swim?": True,
                "Is it bigger than a person?": False,
            },
        },
        {
            "name": "cat",
            "features": {
                "Is it a living thing?": True,
                "Is it an animal?": True,
                "Is it a pet?": True,
                "Is it a food?": False,
                "Is it a vehicle?": False,
                "Is it a sport?": False,
                "Can you eat it?": False,
                "Does it have wheels?": False,
                "Does it fly?": False,
                "Does it swim?": False,
                "Is it bigger than a person?": False,
            },
        },
        {
            "name": "elephant",
            "features": {
                "Is it a living thing?": True,
                "Is it an animal?": True,
                "Is it a pet?": False,
                "Is it a food?": False,
                "Is it a vehicle?": False,
                "Is it a sport?": False,
                "Can you eat it?": False,
                "Does it have wheels?": False,
                "Does it fly?": False,
                "Does it swim?": True,
                "Is it bigger than a person?": True,
            },
        },
        {
            "name": "bird",
            "features": {
                "Is it a living thing?": True,
                "Is it an animal?": True,
                "Is it a pet?": False,
                "Is it a food?": False,
                "Is it a vehicle?": False,
                "Is it a sport?": False,
                "Can you eat it?": False,
                "Does it have wheels?": False,
                "Does it fly?": True,
                "Does it swim?": False,
                "Is it bigger than a person?": False,
            },
        },
        {
            "name": "fish",
            "features": {
                "Is it a living thing?": True,
                "Is it an animal?": True,
                "Is it a pet?": False,
                "Is it a food?": False,
                "Is it a vehicle?": False,
                "Is it a sport?": False,
                "Can you eat it?": False,
                "Does it have wheels?": False,
                "Does it fly?": False,
                "Does it swim?": True,
                "Is it bigger than a person?": False,
            },
        },
        {
            "name": "pizza",
            "features": {
                "Is it a living thing?": False,
                "Is it an animal?": False,
                "Is it a pet?": False,
                "Is it a food?": True,
                "Is it a vehicle?": False,
                "Is it a sport?": False,
                "Can you eat it?": True,
                "Does it have wheels?": False,
                "Does it fly?": False,
                "Does it swim?": False,
                "Is it bigger than a person?": False,
            },
        },
        {
            "name": "apple",
            "features": {
                "Is it a living thing?": False,
                "Is it an animal?": False,
                "Is it a pet?": False,
                "Is it a food?": True,
                "Is it a vehicle?": False,
                "Is it a sport?": False,
                "Can you eat it?": True,
                "Does it have wheels?": False,
                "Does it fly?": False,
                "Does it swim?": False,
                "Is it bigger than a person?": False,
            },
        },
        {
            "name": "car",
            "features": {
                "Is it a living thing?": False,
                "Is it an animal?": False,
                "Is it a pet?": False,
                "Is it a food?": False,
                "Is it a vehicle?": True,
                "Is it a sport?": False,
                "Can you eat it?": False,
                "Does it have wheels?": True,
                "Does it fly?": False,
                "Does it swim?": False,
                "Is it bigger than a person?": True,
            },
        },
        {
            "name": "bicycle",
            "features": {
                "Is it a living thing?": False,
                "Is it an animal?": False,
                "Is it a pet?": False,
                "Is it a food?": False,
                "Is it a vehicle?": True,
                "Is it a sport?": False,
                "Can you eat it?": False,
                "Does it have wheels?": True,
                "Does it fly?": False,
                "Does it swim?": False,
                "Is it bigger than a person?": False,
            },
        },
        {
            "name": "airplane",
            "features": {
                "Is it a living thing?": False,
                "Is it an animal?": False,
                "Is it a pet?": False,
                "Is it a food?": False,
                "Is it a vehicle?": True,
                "Is it a sport?": False,
                "Can you eat it?": False,
                "Does it have wheels?": True,
                "Does it fly?": True,
                "Does it swim?": False,
                "Is it bigger than a person?": True,
            },
        },
        {
            "name": "boat",
            "features": {
                "Is it a living thing?": False,
                "Is it an animal?": False,
                "Is it a pet?": False,
                "Is it a food?": False,
                "Is it a vehicle?": True,
                "Is it a sport?": False,
                "Can you eat it?": False,
                "Does it have wheels?": False,
                "Does it fly?": False,
                "Does it swim?": True,
                "Is it bigger than a person?": True,
            },
        },
        {
            "name": "soccer",
            "features": {
                "Is it a living thing?": False,
                "Is it an animal?": False,
                "Is it a pet?": False,
                "Is it a food?": False,
                "Is it a vehicle?": False,
                "Is it a sport?": True,
                "Can you eat it?": False,
                "Does it have wheels?": False,
                "Does it fly?": False,
                "Does it swim?": False,
                "Is it bigger than a person?": False,
            },
        },
    )

    def __init__(self, path: Optional[Path] = None) -> None:
        """Create a knowledge base and load any persisted knowledge."""

        self.path = path or _default_knowledge_base_path()
        self.objects: Dict[str, Dict[str, bool]] = {}
        self._name_index: Dict[str, str] = {}
        self.load()

    def load(self) -> None:
        """Load objects and features from disk or seed defaults."""

        if not self.path.exists():
            self.objects = {item["name"]: dict(item["features"]) for item in self.DEFAULT_OBJECTS}
            self.save()
        else:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            self.objects = {entry["name"]: dict(entry["features"]) for entry in data.get("objects", [])}
        self._refresh_name_index()

    def save(self) -> None:
        """Persist the knowledge base to disk."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        serialisable = [{"name": name, "features": features} for name, features in sorted(self.objects.items(), key=lambda item: item[0])]
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump({"objects": serialisable}, handle, indent=2, sort_keys=True)

    def _refresh_name_index(self) -> None:
        """Refresh the lookup table for case-insensitive name access."""

        self._name_index = {name.lower(): name for name in self.objects}

    def _resolve_name(self, name: str) -> Optional[str]:
        """Resolve a case-insensitive object name to its canonical form."""

        return self._name_index.get(name.lower())

    def list_questions(self) -> List[str]:
        """Return all questions known in the knowledge base."""

        return sorted({question for features in self.objects.values() for question in features})

    def get_object_names(self) -> List[str]:
        """Return every object currently stored."""

        return sorted(self.objects.keys())

    def get_features(self, name: str) -> Optional[Dict[str, bool]]:
        """Retrieve features for an object by name."""

        canonical = self._resolve_name(name)
        if canonical is None:
            return None
        return self.objects[canonical]

    def iter_objects(self) -> Iterable[Tuple[str, Dict[str, bool]]]:
        """Iterate over all objects and their features."""

        return self.objects.items()

    def add_or_update_object(self, name: str, features: Dict[str, bool]) -> None:
        """Insert a new object or update an existing one with new features."""

        canonical = self._resolve_name(name) or name
        combined = dict(self.objects.get(canonical, {}))
        combined.update({question: bool(answer) for question, answer in features.items()})
        self.objects[canonical] = combined
        self._refresh_name_index()
        self.save()

    def get_candidate_objects(self, responses: Dict[str, bool]) -> Dict[str, Dict[str, bool]]:
        """Return objects consistent with the provided responses."""

        candidates: Dict[str, Dict[str, bool]] = {}
        for name, features in self.objects.items():
            consistent = True
            for question, expected_answer in responses.items():
                if question in features and features[question] != expected_answer:
                    consistent = False
                    break
            if consistent:
                candidates[name] = features
        return candidates


class TwentyQuestionsGame(GameEngine[str, int]):
    """20 Questions AI guessing game backed by an adaptive knowledge base."""

    def __init__(self, knowledge_base: Optional[TwentyQuestionsKnowledgeBase] = None, knowledge_base_path: Optional[Path] = None) -> None:
        """Initialise the game engine."""

        if knowledge_base is not None and knowledge_base_path is not None:
            raise ValueError("Provide either a knowledge base instance or a path, not both")
        self.knowledge_base = knowledge_base or TwentyQuestionsKnowledgeBase(knowledge_base_path)
        self._secret_object: Optional[str] = None
        self._questions_asked = 0
        self._max_questions = 20
        self._state = GameState.NOT_STARTED
        self._guessed_correct = False
        self._responses: Dict[str, bool] = {}
        self.reset()

    def reset(self, secret_object: Optional[str] = None) -> None:  # type: ignore[override]
        """Reset the game to its initial state."""

        if secret_object is None:
            available = self.knowledge_base.get_object_names()
            self._secret_object = random.choice(available) if available else None
        else:
            if self.knowledge_base.get_features(secret_object) is None:
                raise ValueError(f"Unknown secret object: {secret_object}")
            self._secret_object = secret_object
        self._questions_asked = 0
        self._state = GameState.IN_PROGRESS
        self._guessed_correct = False
        self._responses = {}

    def is_game_over(self) -> bool:
        """Check if the game has finished."""

        return self._state == GameState.FINISHED

    def get_current_player(self) -> int:
        """Return the active player (AI only)."""

        return 0

    def get_valid_moves(self) -> List[str]:
        """Return valid actions for the AI."""

        if self.is_game_over():
            return []
        return ["ask_question", "make_guess"]

    def make_move(self, move: str) -> bool:
        """The CLI manages moves directly, so this method simply validates state."""

        return not self.is_game_over()

    def ask_question(self, question: str, answer: bool) -> None:
        """Record the answer to a question asked by the AI."""

        if self.is_game_over():
            return
        self._questions_asked += 1
        self._responses[question] = answer
        if self._questions_asked >= self._max_questions:
            self._state = GameState.FINISHED

    def make_guess(self, guess: str) -> bool:
        """Attempt to guess the secret object."""

        if self.is_game_over():
            return False
        self._questions_asked += 1
        if self._secret_object is not None and guess.lower() == self._secret_object.lower():
            self._guessed_correct = True
            self._state = GameState.FINISHED
            return True
        if self._questions_asked >= self._max_questions:
            self._state = GameState.FINISHED
        return False

    def select_best_question(self) -> Optional[str]:
        """Pick the question with the highest expected information gain."""

        candidates = self.get_candidate_objects()
        unanswered = [question for question in self.knowledge_base.list_questions() if question not in self._responses]
        best_question: Optional[str] = None
        best_score = -1.0
        candidate_count = len(candidates)
        if candidate_count == 0:
            return None
        for question in unanswered:
            yes_count = 0
            no_count = 0
            for features in candidates.values():
                if question in features:
                    if features[question]:
                        yes_count += 1
                    else:
                        no_count += 1
            known = yes_count + no_count
            if known == 0:
                continue
            probability_yes = yes_count / known
            entropy = 0.0
            if 0 < probability_yes < 1:
                entropy = -(probability_yes * math.log2(probability_yes) + (1 - probability_yes) * math.log2(1 - probability_yes))
            coverage = known / candidate_count
            score = entropy * coverage
            if score > best_score:
                best_score = score
                best_question = question
        return best_question

    def get_candidate_objects(self) -> Dict[str, Dict[str, bool]]:
        """Return objects still consistent with recorded answers."""

        return self.knowledge_base.get_candidate_objects(self._responses)

    def get_best_guess(self) -> Optional[str]:
        """Return the most plausible guess based on current knowledge."""

        candidates = self.get_candidate_objects()
        if not candidates:
            return None

        def score(item: Tuple[str, Dict[str, bool]]) -> Tuple[int, int, int]:
            features = item[1]
            matches = sum(1 for question, answer in self._responses.items() if features.get(question) == answer)
            known_matches = sum(1 for question in self._responses if question in features)
            return matches, known_matches, -len(features)

        return max(candidates.items(), key=score)[0]

    def learn_from_failure(self, actual_object: str, distinguishing_question: str, actual_answer: bool, failed_guess: Optional[str] = None) -> None:
        """Update the knowledge base with a new object and distinguishing question."""

        features = dict(self._responses)
        features[distinguishing_question] = actual_answer
        self.knowledge_base.add_or_update_object(actual_object, features)
        if failed_guess is not None:
            self.knowledge_base.add_or_update_object(failed_guess, {distinguishing_question: not actual_answer})

    def learn_from_success(self, object_name: str) -> None:
        """Update known features for a successfully guessed object."""

        self.knowledge_base.add_or_update_object(object_name, dict(self._responses))

    def get_winner(self) -> Optional[int]:
        """Return the winner index if the game has concluded."""

        if not self.is_game_over():
            return None
        return 0 if self._guessed_correct else None

    def get_game_state(self) -> GameState:
        """Expose the current game state."""

        return self._state

    def get_state_representation(self) -> Dict[str, object]:
        """Provide a serialisable representation of the game state."""

        return {
            "questions_asked": self._questions_asked,
            "questions_remaining": self.get_questions_remaining(),
            "guessed_correct": self._guessed_correct,
        }

    def get_questions_remaining(self) -> int:
        """Return the number of remaining questions."""

        return max(0, self._max_questions - self._questions_asked)

    def get_secret_object(self) -> Optional[str]:
        """Expose the secret object for automated tests."""

        return self._secret_object


class TwentyQuestionsCLI:
    """Command line interface for the adaptive 20 Questions game."""

    def __init__(self, game: Optional[TwentyQuestionsGame] = None) -> None:
        """Create the CLI wrapper."""

        self.game = game or TwentyQuestionsGame()

    def _prompt_yes_no(self, prompt: str) -> bool:
        """Prompt the user for a yes/no answer."""

        while True:
            response = input(f"{prompt} (yes/no): ").strip().lower()
            if response in {"y", "yes"}:
                return True
            if response in {"n", "no"}:
                return False
            print("Please respond with 'yes' or 'no'.")

    def _sorted_candidates(self) -> List[str]:
        """Return candidate objects ordered by plausibility."""

        candidates = self.game.get_candidate_objects()
        ranked = sorted(
            candidates.items(),
            key=lambda item: (
                -sum(1 for question, answer in self.game._responses.items() if item[1].get(question) == answer),
                sum(question in item[1] for question in self.game._responses),
                item[0],
            ),
        )
        return [name for name, _ in ranked]

    def run(self) -> None:
        """Run the interactive game loop."""

        print("Welcome to 20 Questions!")
        print("=" * 60)
        print("Think of an object, and I'll try to guess it!")
        print("Answer my questions with 'yes' or 'no'.")
        print()

        self.game.reset(secret_object=None)
        failed_guess: Optional[str] = None

        while self.game.get_questions_remaining() > 0:
            question = self.game.select_best_question()
            if question is None:
                break
            answer = self._prompt_yes_no(question)
            self.game.ask_question(question, answer)
            candidates = self.game.get_candidate_objects()
            print(f"I now have {len(candidates)} possible objects in mind.")
            if len(candidates) <= 1:
                break

        for guess in self._sorted_candidates():
            if self.game.get_questions_remaining() == 0:
                break
            if guess == failed_guess:
                continue
            if self._prompt_yes_no(f"Is it {guess}?"):
                print("\n🎉 I guessed it! Thanks for playing! 🎉")
                self.game.learn_from_success(guess)
                return
            failed_guess = guess
            self.game.ask_question(f"Is it {guess}?", False)

        print("\nI give up! Let's learn together.")
        actual_object = input("What were you thinking of? ").strip()
        distinguishing_question = input("Give me a yes/no question that distinguishes your object: ").strip()
        actual_answer = self._prompt_yes_no("What is the answer for your object?")
        self.game.learn_from_failure(actual_object, distinguishing_question, actual_answer, failed_guess)
        print("Thanks! I'll remember that for next time.")


def main() -> None:
    """Entrypoint for running the CLI via ``python -m``."""

    TwentyQuestionsCLI().run()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
