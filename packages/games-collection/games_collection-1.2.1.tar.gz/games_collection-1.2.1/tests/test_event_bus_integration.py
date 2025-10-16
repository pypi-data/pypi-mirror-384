"""Integration tests validating the shared event bus contract."""

from __future__ import annotations

from typing import List

import dice_games.craps.craps as craps_module
import dice_games.farkle.farkle as farkle_module
import pytest

from common import Event, EventBus, EventHandler, GameEventType
from dice_games import CrapsGame, FarkleGame


class RecordingHandler(EventHandler):
    """Test handler that records every event it processes."""

    def __init__(self) -> None:
        """Initialize the recording handler."""
        self.events: List[str] = []

    def handle(self, event: Event) -> None:
        """Store the event type for later assertions."""

        self.events.append(event.type)


class TestEventBusIntegration:
    """Verify dice game engines emit standardized events."""

    def test_craps_emits_core_events(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Craps should broadcast start, score, and turn events."""

        bus = EventBus()
        handler = RecordingHandler()
        bus.subscribe_all(handler)

        game = CrapsGame()
        game.set_event_bus(bus)
        game.current_bet = 25

        rolls = iter([3, 4])

        def rigged_randint(_: int, __: int) -> int:
            return next(rolls)

        monkeypatch.setattr(craps_module.random, "randint", rigged_randint)

        assert game.make_move("roll")

        history_types = [event.type for event in bus.get_history()]
        assert GameEventType.GAME_START.value in history_types
        assert GameEventType.SCORE_UPDATED.value in history_types
        assert GameEventType.TURN_COMPLETE.value in history_types
        assert GameEventType.GAME_START.value in handler.events

    def test_farkle_emits_turn_events(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Farkle should notify listeners about scoring and turn transitions."""

        bus = EventBus()
        handler = RecordingHandler()
        bus.subscribe_all(handler)

        game = FarkleGame(num_players=2)
        game.set_event_bus(bus)

        rolls = iter([1, 1, 1, 5, 2, 3])

        def rigged_randint(_: int, __: int) -> int:
            return next(rolls)

        monkeypatch.setattr(farkle_module.random, "randint", rigged_randint)

        assert game.make_move(([], True))
        assert game.make_move(([1, 1, 1], False))

        history_types = [event.type for event in bus.get_history()]
        assert GameEventType.GAME_START.value in history_types
        assert GameEventType.SCORE_UPDATED.value in history_types
        assert GameEventType.TURN_COMPLETE.value in history_types
        assert GameEventType.SCORE_UPDATED.value in handler.events
