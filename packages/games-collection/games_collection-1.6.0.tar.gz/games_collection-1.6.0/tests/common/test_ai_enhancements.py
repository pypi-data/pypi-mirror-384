"""Tests for advanced AI helpers used across multiple games."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Sequence

from common.ai_enhancements import (
    AIDifficultyLevel,
    AITrainingExample,
    AITrainingSession,
    DifficultyAdjuster,
    NeuralNetworkStrategy,
    NeuralNetworkTrainingExample,
    PersonalityProfile,
    ReinforcementLearningAgent,
    ReinforcementLearningConfig,
    TrainableEnvironment,
)


@dataclass(frozen=True)
class LineState:
    """State representing the current position on a number line."""

    position: int


class LineEnvironment(TrainableEnvironment[LineState, int]):
    """Tiny environment where the agent must reach the goal position."""

    def __init__(self, goal: int) -> None:
        self.goal = goal

    def valid_moves(self, state: LineState) -> Sequence[int]:
        return [-1, 1]

    def transition(self, state: LineState, move: int) -> tuple[LineState, float]:
        next_state = LineState(position=state.position + move)
        reward = 1.0 if next_state.position == self.goal else -0.05
        return next_state, reward

    def is_terminal(self, state: LineState) -> bool:
        return state.position == self.goal


class TestReinforcementLearningAgent:
    """Validate the Q-learning agent and personality integration."""

    def test_agent_learns_to_move_towards_goal(self) -> None:
        """Ensure the agent converges on the optimal action."""

        env = LineEnvironment(goal=2)
        config = ReinforcementLearningConfig(learning_rate=0.3, exploration_rate=0.6)
        personality = PersonalityProfile(name="Adventurous", aggression=0.7, creativity=0.8)
        agent = ReinforcementLearningAgent[int, LineState](
            config,
            state_encoder=lambda state: state.position,
            move_encoder=lambda move: move,
            personality=personality,
            rng=random.Random(7),
        )
        state = LineState(position=0)
        for _ in range(80):
            env_state = LineState(position=state.position)
            agent.train_episode(env, env_state)
        agent.config.exploration_rate = 0.0
        chosen_move = agent.select_move([-1, 1], LineState(position=1))
        assert chosen_move == 1
        assert agent.last_explanation is not None
        assert "Exploitation" in agent.last_explanation


class TestNeuralNetworkStrategy:
    """Test that the neural network strategy prefers high-value moves."""

    def test_strategy_prefers_positive_moves(self) -> None:
        """Train the strategy and verify the positive move is selected."""

        rng = random.Random(3)
        strategy = NeuralNetworkStrategy[int, None](
            feature_extractor=lambda state, move: [float(move)],
            hidden_layers=(4,),
            learning_rate=0.1,
            epochs=80,
            rng=rng,
        )
        dataset: List[NeuralNetworkTrainingExample] = []
        for _ in range(120):
            dataset.append(NeuralNetworkTrainingExample(features=[1.0], target=1.0))
            dataset.append(NeuralNetworkTrainingExample(features=[-1.0], target=-1.0))
        strategy.train(dataset)
        move = strategy.select_move([-1, 1], None)
        assert move == 1
        assert strategy.last_explanation is not None
        assert "neural score" in strategy.last_explanation


class TestDifficultyAdjuster:
    """Ensure the adaptive difficulty logic responds to player trends."""

    def test_adjuster_updates_difficulty(self) -> None:
        """Record a sequence of wins and losses to trigger adjustments."""

        adjuster = DifficultyAdjuster[int, LineState](window=6)
        agent = ReinforcementLearningAgent[int, LineState](ReinforcementLearningConfig(), rng=random.Random(9))
        for _ in range(4):
            level = adjuster.record_result(player_score=5, ai_score=1)
        assert level == AIDifficultyLevel.HARD
        adjuster.apply_to_agent(agent)
        assert agent.config.exploration_rate <= 0.1
        for _ in range(4):
            level = adjuster.record_result(player_score=0, ai_score=5)
        assert level == AIDifficultyLevel.MEDIUM


class TestAITrainingSession:
    """Validate conversion of human examples into training signals."""

    def test_session_updates_agent_and_prepares_dataset(self) -> None:
        """Ensure recorded examples influence the agent and dataset output."""

        session: AITrainingSession[LineState, int] = AITrainingSession()
        example = AITrainingExample(
            state=LineState(position=0),
            move=1,
            reward=1.0,
            next_state=LineState(position=1),
            next_valid_moves=[-1, 1],
            explanation="Advance towards goal",
        )
        session.record_example(example)
        agent = ReinforcementLearningAgent[int, LineState](
            ReinforcementLearningConfig(),
            state_encoder=lambda state: state.position,
            move_encoder=lambda move: move,
            rng=random.Random(2),
        )
        session.apply_to_agent(agent)
        q_values = agent.policy_snapshot()
        assert q_values
        dataset = session.prepare_supervised_dataset(lambda state, move: [float(move)])
        assert dataset == [NeuralNetworkTrainingExample(features=[1.0], target=1.0)]
