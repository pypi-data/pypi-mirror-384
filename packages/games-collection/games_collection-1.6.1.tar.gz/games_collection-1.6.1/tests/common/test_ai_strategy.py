"""Tests for AI strategy components."""

from __future__ import annotations

from typing import Dict, Tuple

import pytest

from common.ai_strategy import HeuristicStrategy


class CallCountingHeuristic:
    """Track how many times a heuristic function has been invoked."""

    def __init__(self) -> None:
        self.count = 0

    def __call__(self, move: str, game_state: Dict[str, int]) -> float:
        self.count += 1
        return float(game_state.get(move, 0))


def _dict_cache_key(move: str, game_state: Dict[str, int]) -> Tuple[str, Tuple[Tuple[str, int], ...]]:
    """Return a stable cache key for dictionary based game states."""

    return move, tuple(sorted(game_state.items()))


def test_heuristic_strategy_caches_scores() -> None:
    """Ensure repeated evaluations reuse cached scores when enabled."""

    heuristic = CallCountingHeuristic()
    strategy = HeuristicStrategy(heuristic_fn=heuristic, cache_key_fn=_dict_cache_key)

    first_score = strategy.evaluate_move("A", {"A": 3})
    second_score = strategy.evaluate_move("A", {"A": 3})

    assert first_score == pytest.approx(second_score)
    assert heuristic.count == 1, "Heuristic should have been evaluated only once due to caching"

    strategy.clear_cache()
    strategy.evaluate_move("A", {"A": 3})
    assert heuristic.count == 2, "Cache clearing should force the heuristic to run again"


def test_heuristic_strategy_cache_eviction() -> None:
    """Validate cache eviction when the cache exceeds its configured size."""

    heuristic = CallCountingHeuristic()
    strategy = HeuristicStrategy(heuristic_fn=heuristic, cache_key_fn=_dict_cache_key, cache_size=2)

    strategy.evaluate_move("A", {"A": 1})
    strategy.evaluate_move("B", {"B": 2})
    strategy.evaluate_move("C", {"C": 3})

    assert heuristic.count == 3

    strategy.evaluate_move("A", {"A": 1})
    assert heuristic.count == 4, "Oldest entry should have been evicted and recomputed"


def test_select_move_uses_cached_scores() -> None:
    """Confirm select_move leverages cached heuristic values across invocations."""

    heuristic = CallCountingHeuristic()
    strategy = HeuristicStrategy(heuristic_fn=heuristic, cache_key_fn=_dict_cache_key)

    moves = ["A", "B"]
    game_state = {"A": 5, "B": 4}

    best_move_first = strategy.select_move(moves, game_state)
    best_move_second = strategy.select_move(moves, game_state)

    assert best_move_first == "A"
    assert best_move_second == "A"
    assert heuristic.count == 2, "Each unique move should be evaluated only once"
