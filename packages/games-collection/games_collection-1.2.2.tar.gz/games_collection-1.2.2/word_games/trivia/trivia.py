"""Trivia game engine."""

from __future__ import annotations

import random
from typing import Dict, List

from common.game_engine import GameEngine, GameState


class TriviaGame(GameEngine[int, int]):
    """Trivia quiz game with multiple choice questions."""

    # Sample questions (in real implementation, could load from file/API)
    QUESTIONS: List[Dict[str, any]] = [
        {"question": "What is the capital of France?", "options": ["London", "Berlin", "Paris", "Madrid"], "correct": 2},
        {"question": "What is 2 + 2?", "options": ["3", "4", "5", "6"], "correct": 1},
        {"question": "Which planet is known as the Red Planet?", "options": ["Venus", "Mars", "Jupiter", "Saturn"], "correct": 1},
        {"question": "Who wrote Romeo and Juliet?", "options": ["Dickens", "Shakespeare", "Austen", "Twain"], "correct": 1},
        {"question": "What is the largest ocean?", "options": ["Atlantic", "Indian", "Arctic", "Pacific"], "correct": 3},
    ]

    def __init__(self, num_questions: int = 5) -> None:
        """Initialize game."""
        self.num_questions = min(num_questions, len(self.QUESTIONS))
        self.reset()

    def reset(self) -> None:
        """Reset game."""
        self.state = GameState.NOT_STARTED
        self.questions = random.sample(self.QUESTIONS, self.num_questions)
        self.current_question_idx = 0
        self.score = 0

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
        return list(range(len(self.questions[self.current_question_idx]["options"])))

    def make_move(self, move: int) -> bool:
        """Submit answer."""
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        if self.is_game_over() or move not in self.get_valid_moves():
            return False

        correct = self.questions[self.current_question_idx]["correct"]
        if move == correct:
            self.score += 1

        self.current_question_idx += 1

        if self.is_game_over():
            self.state = GameState.FINISHED

        return True

    def get_current_question(self) -> Dict[str, any] | None:
        """Get current question."""
        if self.is_game_over():
            return None
        return self.questions[self.current_question_idx]

    def get_winner(self) -> int | None:
        """Get winner (score-based)."""
        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Get current game state.

        Returns:
            Current state of the game
        """
        return self.state
