"""Advanced AI utilities for training and personalising game opponents.

The helpers in this module extend the basic strategy classes found in
``common.ai_strategy`` by providing:

* Reinforcement learning support with Q-learning updates and persistence
* Lightweight neural network opponents trained from labelled examples
* Automatic difficulty adjustment driven by recent player performance
* Personality profiles that bias strategy behaviour
* An explainability mixin used to expose the reasoning for the last move
* Training sessions that capture human feedback for multiple strategies

These abstractions keep the existing architecture intact while enabling games
to experiment with richer AI behaviour without depending on heavyweight
third-party frameworks.
"""

from __future__ import annotations

import json
import math
import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Callable,
    Deque,
    Dict,
    Generic,
    Hashable,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    TypeVar,
)

from .ai_strategy import AIStrategy

MoveType = TypeVar("MoveType")
StateType = TypeVar("StateType")


class TrainableEnvironment(Protocol[StateType, MoveType]):
    """Protocol describing the minimum API required for RL training.

    Games can provide lightweight adapters that expose the operations below so
    that the :class:`ReinforcementLearningAgent` can interact with them without
    depending on concrete engine implementations.
    """

    def valid_moves(self, state: StateType) -> Sequence[MoveType]:
        """Return the valid moves for the provided state."""

    def transition(self, state: StateType, move: MoveType) -> Tuple[StateType, float]:
        """Return the next state and reward after applying ``move``."""

    def is_terminal(self, state: StateType) -> bool:
        """Return whether ``state`` is terminal for the current episode."""


@dataclass(slots=True)
class ReinforcementLearningConfig:
    """Configuration values controlling the behaviour of Q-learning agents."""

    learning_rate: float = 0.1
    discount_factor: float = 0.9
    exploration_rate: float = 0.2
    min_exploration_rate: float = 0.01
    exploration_decay: float = 0.995


@dataclass(frozen=True, slots=True)
class PersonalityProfile:
    """Bias configuration used to make AI opponents feel distinct.

    Attributes:
        name: Human friendly name displayed in UIs.
        aggression: Values above ``0.5`` favour high-scoring moves, while lower
            values keep the AI conservative.
        caution: Values above ``0.5`` discourage risky choices by slightly
            damping the perceived score differences between moves.
        creativity: Controls exploration during move selection. Higher values
            cause the AI to try unusual moves more frequently.
        description: Optional text describing the personality to players.
    """

    name: str
    aggression: float = 0.5
    caution: float = 0.5
    creativity: float = 0.5
    description: str = ""

    def adjust_exploration(self, base_rate: float) -> float:
        """Return an exploration rate biased by the personality settings."""

        creativity_bias = (self.creativity - 0.5) * 0.6
        adjusted = base_rate + creativity_bias
        return min(1.0, max(0.0, adjusted))

    def bias_scores(self, scores: Mapping[MoveType, float]) -> Dict[MoveType, float]:
        """Return a new mapping that encodes the personality bias.

        The implementation avoids mutating the original ``scores`` mapping to
        respect repository guidelines. The returned dictionary gently stretches
        or compresses the score distribution to reflect aggression/caution.
        """

        if not scores:
            return {}
        values = list(scores.values())
        max_score = max(values)
        min_score = min(values)
        score_range = max(1e-6, max_score - min_score)
        aggression_factor = 1.0 + (self.aggression - 0.5)
        caution_factor = 1.0 - (self.caution - 0.5) * 0.4
        adjusted: Dict[MoveType, float] = {}
        for move, score in scores.items():
            normalised = (score - min_score) / score_range
            amplified = normalised**aggression_factor
            adjusted_score = score + amplified * score_range * 0.25 * caution_factor
            adjusted[move] = adjusted_score
        return adjusted


class ExplainableStrategyMixin(Generic[MoveType, StateType]):
    """Mixin exposing explanation support for AI strategies."""

    _last_explanation: Optional[str]

    def __init__(self) -> None:
        self._last_explanation = None

    @property
    def last_explanation(self) -> Optional[str]:
        """Return the explanation for the last chosen move, if available."""

        return self._last_explanation


class ReinforcementLearningAgent(ExplainableStrategyMixin[MoveType, StateType], AIStrategy[MoveType, StateType]):
    """Q-learning strategy that supports training and persistence."""

    def __init__(
        self,
        config: ReinforcementLearningConfig | None = None,
        *,
        state_encoder: Optional[Callable[[StateType], Hashable]] = None,
        move_encoder: Optional[Callable[[MoveType], Hashable]] = None,
        personality: Optional[PersonalityProfile] = None,
        rng: Optional[random.Random] = None,
    ) -> None:
        ExplainableStrategyMixin.__init__(self)
        AIStrategy.__init__(self, rng)
        self.config = config or ReinforcementLearningConfig()
        self.personality = personality
        self.state_encoder = state_encoder or self._default_encoder
        self.move_encoder = move_encoder or self._default_encoder
        self._q_table: Dict[Tuple[Hashable, Hashable], float] = {}

    @staticmethod
    def _default_encoder(value: object) -> Hashable:
        """Return a hashable representation for values that may not be hashable."""

        if isinstance(value, Hashable):
            return value
        return json.dumps(value, sort_keys=True, default=str)

    def select_move(self, valid_moves: List[MoveType], game_state: StateType) -> MoveType:
        """Select a move using an epsilon-greedy policy with personality bias."""

        if not valid_moves:
            raise ValueError("No valid moves available")

        encoded_state = self.state_encoder(game_state)
        exploitation_scores = {move: self._q_table.get((encoded_state, self.move_encoder(move)), 0.0) for move in valid_moves}
        biased_scores = self.personality.bias_scores(exploitation_scores) if self.personality else exploitation_scores
        exploration_rate = self.personality.adjust_exploration(self.config.exploration_rate) if self.personality else self.config.exploration_rate
        if self.rng.random() < exploration_rate:
            chosen_move = self.rng.choice(valid_moves)
            self._last_explanation = f"Exploration selected move {chosen_move!r} with rate {exploration_rate:.2f}."
            return chosen_move

        best_score = max(biased_scores.values())
        best_moves = [move for move, score in biased_scores.items() if math.isclose(score, best_score, rel_tol=1e-9)]
        chosen_move = self.rng.choice(best_moves)
        q_value = exploitation_scores[chosen_move]
        self._last_explanation = f"Exploitation selected move {chosen_move!r} with predicted value {q_value:.3f}."
        return chosen_move

    def update(
        self,
        state: StateType,
        move: MoveType,
        reward: float,
        next_state: StateType,
        next_valid_moves: Sequence[MoveType],
    ) -> float:
        """Apply a single Q-learning update and return the new Q-value."""

        state_key = self.state_encoder(state)
        move_key = self.move_encoder(move)
        next_state_key = self.state_encoder(next_state)
        current_q = self._q_table.get((state_key, move_key), 0.0)
        next_best = 0.0
        if next_valid_moves:
            next_best = max(self._q_table.get((next_state_key, self.move_encoder(candidate)), 0.0) for candidate in next_valid_moves)
        target = reward + self.config.discount_factor * next_best
        updated_q = current_q + self.config.learning_rate * (target - current_q)
        self._q_table[(state_key, move_key)] = updated_q
        return updated_q

    def decay_exploration(self) -> None:
        """Decay the exploration rate within configured bounds."""

        self.config.exploration_rate = max(
            self.config.min_exploration_rate,
            self.config.exploration_rate * self.config.exploration_decay,
        )

    def train_episode(
        self,
        environment: TrainableEnvironment[StateType, MoveType],
        initial_state: StateType,
    ) -> float:
        """Run a full training episode and return the accumulated reward."""

        state = initial_state
        cumulative_reward = 0.0
        while not environment.is_terminal(state):
            valid_moves = list(environment.valid_moves(state))
            if not valid_moves:
                break
            move = self.select_move(valid_moves, state)
            next_state, reward = environment.transition(state, move)
            cumulative_reward += reward
            next_valid_moves = list(environment.valid_moves(next_state))
            self.update(state, move, reward, next_state, next_valid_moves)
            state = next_state
        self.decay_exploration()
        return cumulative_reward

    def policy_snapshot(self) -> Dict[Tuple[Hashable, Hashable], float]:
        """Return a defensive copy of the current Q-table."""

        return dict(self._q_table)

    def save_policy(self) -> Dict[str, Dict[str, float]]:
        """Return a serialisable representation of the learned policy."""

        serialized: Dict[str, Dict[str, float]] = {}
        for (state_key, move_key), value in self._q_table.items():
            serialized.setdefault(str(state_key), {})[str(move_key)] = value
        return serialized

    def load_policy(self, serialized_policy: Mapping[str, Mapping[str, float]]) -> None:
        """Load a policy produced by :meth:`save_policy`."""

        self._q_table.clear()
        for state_key, move_map in serialized_policy.items():
            for move_key, value in move_map.items():
                self._q_table[(state_key, move_key)] = value


class AIDifficultyLevel(Enum):
    """Difficulty levels exposed by :class:`DifficultyAdjuster`."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(slots=True)
class DifficultyAdjuster(Generic[MoveType, StateType]):
    """Adaptive difficulty helper that reacts to recent player results."""

    window: int = 10
    promote_threshold: float = 0.65
    demote_threshold: float = 0.35
    level: AIDifficultyLevel = AIDifficultyLevel.MEDIUM
    _history: Deque[float] = field(default_factory=deque, init=False)

    def record_result(self, player_score: float, ai_score: float) -> AIDifficultyLevel:
        """Record a result and update the difficulty level."""

        if len(self._history) >= self.window:
            self._history.popleft()
        if player_score > ai_score:
            outcome = 1.0
        elif player_score < ai_score:
            outcome = 0.0
        else:
            outcome = 0.5
        self._history.append(outcome)
        win_rate = sum(self._history) / len(self._history)
        levels = list(AIDifficultyLevel)
        index = levels.index(self.level)
        if win_rate > self.promote_threshold and index < len(levels) - 1:
            self.level = levels[index + 1]
        elif win_rate < self.demote_threshold and index > 0:
            self.level = levels[index - 1]
        return self.level

    def apply_to_agent(self, agent: ReinforcementLearningAgent[MoveType, StateType]) -> None:
        """Adjust an RL agent's exploration based on the current difficulty."""

        if self.level == AIDifficultyLevel.EASY:
            agent.config.exploration_rate = max(agent.config.exploration_rate, 0.4)
        elif self.level == AIDifficultyLevel.MEDIUM:
            agent.config.exploration_rate = min(max(agent.config.exploration_rate, 0.2), 0.4)
        else:
            agent.config.exploration_rate = min(agent.config.exploration_rate, 0.1)


@dataclass(frozen=True, slots=True)
class NeuralNetworkTrainingExample:
    """Supervised learning example used by :class:`NeuralNetworkStrategy`."""

    features: Sequence[float]
    target: float


class _FeedForwardNetwork:
    """Simple fully connected neural network with tanh activations."""

    def __init__(
        self,
        input_size: int,
        hidden_layers: Sequence[int],
        rng: random.Random,
    ) -> None:
        self.layer_sizes = [input_size, *hidden_layers, 1]
        self.weights: List[List[List[float]]] = []
        self.biases: List[List[float]] = []
        for in_size, out_size in zip(self.layer_sizes[:-1], self.layer_sizes[1:]):
            layer_weights = [[rng.uniform(-0.5, 0.5) for _ in range(in_size)] for _ in range(out_size)]
            layer_biases = [rng.uniform(-0.5, 0.5) for _ in range(out_size)]
            self.weights.append(layer_weights)
            self.biases.append(layer_biases)

    def _forward_internal(self, inputs: Sequence[float]) -> Tuple[List[List[float]], List[List[float]]]:
        activations: List[List[float]] = [list(inputs)]
        pre_activations: List[List[float]] = []
        current = list(inputs)
        for layer_index, (weights, biases) in enumerate(zip(self.weights, self.biases)):
            z_values: List[float] = []
            next_activations: List[float] = []
            for neuron_weights, bias in zip(weights, biases):
                z = sum(weight * value for weight, value in zip(neuron_weights, current)) + bias
                z_values.append(z)
                if layer_index == len(self.weights) - 1:
                    next_activations.append(z)
                else:
                    next_activations.append(math.tanh(z))
            pre_activations.append(z_values)
            activations.append(next_activations)
            current = next_activations
        return activations, pre_activations

    def forward(self, inputs: Sequence[float]) -> float:
        """Return the output of the network for ``inputs``."""

        activations, _ = self._forward_internal(inputs)
        return activations[-1][0]

    def train(
        self,
        dataset: Sequence[NeuralNetworkTrainingExample],
        learning_rate: float,
        epochs: int,
    ) -> None:
        """Train the network using batch gradient descent."""

        if not dataset:
            return
        for _ in range(epochs):
            for example in dataset:
                activations, pre_activations = self._forward_internal(example.features)
                deltas: List[List[float]] = [[0.0 for _ in layer_biases] for layer_biases in self.biases]
                output = activations[-1][0]
                deltas[-1][0] = output - example.target
                for layer in range(len(self.weights) - 2, -1, -1):
                    for neuron_index, z_value in enumerate(pre_activations[layer]):
                        downstream = sum(self.weights[layer + 1][k][neuron_index] * deltas[layer + 1][k] for k in range(len(self.weights[layer + 1])))
                        derivative = 1.0 - math.tanh(z_value) ** 2
                        deltas[layer][neuron_index] = downstream * derivative
                for layer, (weights, biases) in enumerate(zip(self.weights, self.biases)):
                    inputs = activations[layer]
                    for neuron_index, (neuron_weights, bias) in enumerate(zip(weights, biases)):
                        gradient = deltas[layer][neuron_index]
                        self.biases[layer][neuron_index] = bias - learning_rate * gradient
                        for weight_index, weight in enumerate(neuron_weights):
                            update = learning_rate * gradient * inputs[weight_index]
                            neuron_weights[weight_index] = weight - update


class NeuralNetworkStrategy(ExplainableStrategyMixin[MoveType, StateType], AIStrategy[MoveType, StateType]):
    """Strategy that evaluates moves using a tiny neural network."""

    def __init__(
        self,
        feature_extractor: Callable[[StateType, MoveType], Sequence[float]],
        *,
        hidden_layers: Sequence[int] | None = None,
        learning_rate: float = 0.05,
        epochs: int = 50,
        rng: Optional[random.Random] = None,
    ) -> None:
        ExplainableStrategyMixin.__init__(self)
        AIStrategy.__init__(self, rng)
        self.feature_extractor = feature_extractor
        self.learning_rate = learning_rate
        self.epochs = epochs
        self._network: Optional[_FeedForwardNetwork] = None
        self._hidden_layers = list(hidden_layers or (8,))

    def ensure_network(self, input_size: int) -> None:
        """Initialise the network if it has not been created yet."""

        if self._network is None:
            self._network = _FeedForwardNetwork(input_size, self._hidden_layers, self.rng)

    def train(self, dataset: Sequence[NeuralNetworkTrainingExample]) -> None:
        """Train the underlying neural network on labelled data."""

        if not dataset:
            return
        input_size = len(dataset[0].features)
        self.ensure_network(input_size)
        if self._network is None:
            raise ValueError("Network initialisation failed")
        self._network.train(dataset, self.learning_rate, self.epochs)

    def select_move(self, valid_moves: List[MoveType], game_state: StateType) -> MoveType:
        """Select the move with the highest predicted score."""

        if not valid_moves:
            raise ValueError("No valid moves available")
        feature_map: Dict[MoveType, Sequence[float]] = {move: list(self.feature_extractor(game_state, move)) for move in valid_moves}
        self.ensure_network(len(next(iter(feature_map.values()))))
        if self._network is None:
            raise ValueError("Network initialisation failed")
        scores = {move: self._network.forward(features) for move, features in feature_map.items()}
        best_score = max(scores.values())
        best_moves = [move for move, score in scores.items() if math.isclose(score, best_score, rel_tol=1e-9)]
        chosen = self.rng.choice(best_moves)
        contributions = self._feature_contributions(feature_map[chosen])
        formatted = ", ".join(f"f{i}={value:.2f}" for i, value in enumerate(contributions))
        self._last_explanation = f"Selected move {chosen!r} with neural score {best_score:.3f} ({formatted})."
        return chosen

    def _feature_contributions(self, features: Sequence[float]) -> Sequence[float]:
        if self._network is None:
            return features
        if not self._network.weights:
            return features
        first_layer = self._network.weights[0]
        contributions: List[float] = []
        for neuron_weights in first_layer:
            contribution = sum(weight * value for weight, value in zip(neuron_weights, features))
            contributions.append(contribution)
        return contributions


@dataclass(frozen=True, slots=True)
class AITrainingExample(Generic[StateType, MoveType]):
    """Example captured from human demonstrations or scripted sessions."""

    state: StateType
    move: MoveType
    reward: float
    next_state: Optional[StateType] = None
    next_valid_moves: Optional[Sequence[MoveType]] = None
    explanation: str | None = None


@dataclass(slots=True)
class AITrainingSession(Generic[StateType, MoveType]):
    """Collects AI training examples and can feed them to strategies."""

    examples: List[AITrainingExample[StateType, MoveType]] = field(default_factory=list)

    def record_example(self, example: AITrainingExample[StateType, MoveType]) -> None:
        """Record a new example."""

        self.examples.append(example)

    def apply_to_agent(
        self,
        agent: ReinforcementLearningAgent[MoveType, StateType],
    ) -> None:
        """Replay collected experiences into the supplied RL agent."""

        for example in self.examples:
            if example.next_state is None or example.next_valid_moves is None:
                continue
            agent.update(
                example.state,
                example.move,
                example.reward,
                example.next_state,
                example.next_valid_moves,
            )

    def prepare_supervised_dataset(
        self,
        feature_extractor: Callable[[StateType, MoveType], Sequence[float]],
    ) -> List[NeuralNetworkTrainingExample]:
        """Create supervised training examples from the recorded data."""

        dataset: List[NeuralNetworkTrainingExample] = []
        for example in self.examples:
            features = list(feature_extractor(example.state, example.move))
            dataset.append(NeuralNetworkTrainingExample(features=features, target=example.reward))
        return dataset


__all__ = [
    "AITrainingExample",
    "AITrainingSession",
    "DifficultyAdjuster",
    "AIDifficultyLevel",
    "NeuralNetworkStrategy",
    "NeuralNetworkTrainingExample",
    "PersonalityProfile",
    "ReinforcementLearningAgent",
    "ReinforcementLearningConfig",
    "TrainableEnvironment",
]
