"""Tests for the adaptive 20 Questions game."""

from __future__ import annotations

from pathlib import Path

from paper_games.twenty_questions.twenty_questions import (
    TwentyQuestionsGame,
    TwentyQuestionsKnowledgeBase,
)


def build_custom_knowledge_base(path: Path, objects: dict[str, dict[str, bool]]) -> TwentyQuestionsKnowledgeBase:
    """Create a knowledge base with explicit objects for testing."""

    knowledge_base = TwentyQuestionsKnowledgeBase(path)
    knowledge_base.objects = {name: dict(features) for name, features in objects.items()}
    knowledge_base.save()
    knowledge_base.load()
    return knowledge_base


def test_entropy_question_selection_prefers_balanced_question(tmp_path: Path) -> None:
    """The most informative question should have the highest information gain."""

    path = tmp_path / "kb.json"
    objects = {
        "dog": {"Is it a mammal?": True, "Does it bark?": True},
        "cat": {"Is it a mammal?": True, "Does it bark?": False},
        "car": {"Is it a mammal?": False, "Does it bark?": False},
        "robot": {"Is it a mammal?": False, "Does it bark?": False},
    }
    knowledge_base = build_custom_knowledge_base(path, objects)
    game = TwentyQuestionsGame(knowledge_base=knowledge_base)
    game.reset(secret_object="dog")

    question = game.select_best_question()

    assert question == "Is it a mammal?"


def test_learning_from_failure_persists_new_object(tmp_path: Path) -> None:
    """Learning from failure should add objects and distinguishing questions."""

    path = tmp_path / "kb.json"
    game = TwentyQuestionsGame(knowledge_base_path=path)
    game.reset(secret_object="dog")
    game.ask_question("Is it a living thing?", True)

    game.learn_from_failure("hamster", "Does it run on a wheel?", True, failed_guess="dog")

    reloaded = TwentyQuestionsKnowledgeBase(path)
    hamster = reloaded.get_features("hamster")
    assert hamster is not None
    assert hamster["Is it a living thing?"] is True
    assert hamster["Does it run on a wheel?"] is True
    dog = reloaded.get_features("dog")
    assert dog is not None
    assert dog["Does it run on a wheel?"] is False


def test_learning_from_success_updates_features(tmp_path: Path) -> None:
    """Successful guesses should reinforce the knowledge base."""

    path = tmp_path / "kb.json"
    game = TwentyQuestionsGame(knowledge_base_path=path)
    game.reset(secret_object="dog")
    game.ask_question("Does it like belly rubs?", True)

    game.learn_from_success("dog")

    reloaded = TwentyQuestionsKnowledgeBase(path)
    features = reloaded.get_features("dog")
    assert features is not None
    assert features["Does it like belly rubs?"] is True


def test_ai_converges_on_known_object_within_limit(tmp_path: Path) -> None:
    """The AI should deduce known objects using twenty or fewer questions."""

    path = tmp_path / "kb.json"
    game = TwentyQuestionsGame(knowledge_base_path=path)
    target = "dog"
    game.reset(secret_object=target)

    while not game.is_game_over() and game.get_questions_remaining() > 1:
        question = game.select_best_question()
        if question is None:
            break
        answer = game.knowledge_base.get_features(target)[question]
        game.ask_question(question, answer)

    guess = game.get_best_guess()
    assert guess == target
    assert game.make_guess(guess) is True
    assert game.get_state_representation()["questions_asked"] <= 20
