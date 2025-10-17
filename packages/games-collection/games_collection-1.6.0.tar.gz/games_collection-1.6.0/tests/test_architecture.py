"""Tests for the common architecture components."""

import tempfile
import time
from pathlib import Path

from common.architecture import (
    Event,
    EventBus,
    EventHandler,
    FunctionEventHandler,
    GameEngine,
    GamePhase,
    GameState,
    JSONSerializer,
    Observable,
    Observer,
    PickleSerializer,
    PropertyObservable,
    ReplayManager,
    ReplayRecorder,
    SaveLoadManager,
    Settings,
    SettingsManager,
)

# ==================== Event System Tests ====================


class TestEventHandler(EventHandler):
    """Test event handler that stores received events."""

    def __init__(self):
        self.events = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


def test_event_creation():
    """Test creating events."""
    event = Event(type="TEST", data={"key": "value"}, source="test_source")
    assert event.type == "TEST"
    assert event.data["key"] == "value"
    assert event.source == "test_source"
    assert event.timestamp > 0


def test_event_bus_subscribe():
    """Test subscribing to events."""
    bus = EventBus()
    handler = TestEventHandler()

    bus.subscribe("TEST_EVENT", handler)
    bus.emit("TEST_EVENT", data={"msg": "hello"})

    assert len(handler.events) == 1
    assert handler.events[0].type == "TEST_EVENT"
    assert handler.events[0].data["msg"] == "hello"


def test_event_bus_subscribe_all():
    """Test subscribing to all events."""
    bus = EventBus()
    handler = TestEventHandler()

    bus.subscribe_all(handler)
    bus.emit("EVENT1")
    bus.emit("EVENT2")

    assert len(handler.events) == 2
    assert handler.events[0].type == "EVENT1"
    assert handler.events[1].type == "EVENT2"


def test_event_bus_unsubscribe():
    """Test unsubscribing from events."""
    bus = EventBus()
    handler = TestEventHandler()

    bus.subscribe("TEST", handler)
    bus.emit("TEST")
    assert len(handler.events) == 1

    bus.unsubscribe("TEST", handler)
    bus.emit("TEST")
    assert len(handler.events) == 1  # No new events


def test_event_bus_history():
    """Test event history tracking."""
    bus = EventBus()
    bus.emit("EVENT1")
    bus.emit("EVENT2")
    bus.emit("EVENT1")

    history = bus.get_history()
    assert len(history) == 3

    event1_history = bus.get_history("EVENT1")
    assert len(event1_history) == 2


def test_event_bus_enable_disable():
    """Test enabling/disabling event processing."""
    bus = EventBus()
    handler = TestEventHandler()
    bus.subscribe_all(handler)

    bus.emit("EVENT1")
    assert len(handler.events) == 1

    bus.disable()
    bus.emit("EVENT2")
    assert len(handler.events) == 1  # Still 1, not processed

    bus.enable()
    bus.emit("EVENT3")
    assert len(handler.events) == 2  # Now processed


def test_function_event_handler():
    """Test function-based event handler."""
    events = []

    def handle_func(event: Event):
        events.append(event)

    handler = FunctionEventHandler(handle_func, event_types={"TEST"})
    bus = EventBus()
    bus.subscribe_all(handler)

    bus.emit("TEST")
    bus.emit("OTHER")

    # Only TEST should be handled
    assert len(events) == 1
    assert events[0].type == "TEST"


# ==================== Observer Pattern Tests ====================


class TestObserver(Observer):
    """Test observer implementation."""

    def __init__(self):
        self.updates = []

    def update(self, observable: Observable, **kwargs) -> None:
        self.updates.append(kwargs)


def test_observable_attach_detach():
    """Test attaching and detaching observers."""
    observable = Observable()
    observer = TestObserver()

    observable.attach(observer)
    assert observable.has_observers()
    assert observable.observer_count() == 1

    observable.detach(observer)
    assert not observable.has_observers()


def test_observable_notify():
    """Test notifying observers."""
    observable = Observable()
    observer1 = TestObserver()
    observer2 = TestObserver()

    observable.attach(observer1)
    observable.attach(observer2)

    observable.notify(test_data="value")

    assert len(observer1.updates) == 1
    assert observer1.updates[0]["test_data"] == "value"
    assert len(observer2.updates) == 1


def test_observable_disable_notifications():
    """Test disabling notifications."""
    observable = Observable()
    observer = TestObserver()
    observable.attach(observer)

    observable.notify(data=1)
    assert len(observer.updates) == 1

    observable.disable_notifications()
    observable.notify(data=2)
    assert len(observer.updates) == 1  # Not notified

    observable.enable_notifications()
    observable.notify(data=3)
    assert len(observer.updates) == 2  # Notified again


def test_property_observable():
    """Test property-specific observation."""
    observable = PropertyObservable()
    observer = TestObserver()

    observable.attach_to_property("score", observer)
    observable.notify_property_changed("score", old_value=0, new_value=10)

    assert len(observer.updates) == 1
    assert observer.updates[0]["property"] == "score"
    assert observer.updates[0]["new_value"] == 10


# ==================== Game Engine Tests ====================


class TestGameEngine(GameEngine):
    """Test game engine implementation."""

    def __init__(self):
        super().__init__()
        self.initialized = False
        self.reset_called = False

    def initialize(self, **kwargs):
        self.initialized = True
        self._state = GameState(phase=GamePhase.RUNNING)

    def reset(self):
        self.reset_called = True
        self._state = GameState(phase=GamePhase.SETUP)

    def is_finished(self):
        return self._state and self._state.phase == GamePhase.FINISHED

    def get_current_player(self):
        return None

    def get_valid_actions(self):
        return []

    def execute_action(self, action):
        return True


def test_game_engine_initialization():
    """Test game engine initialization."""
    engine = TestGameEngine()
    assert not engine.initialized

    engine.initialize()
    assert engine.initialized
    assert engine.state is not None
    assert engine.state.phase == GamePhase.RUNNING


def test_game_engine_reset():
    """Test game engine reset."""
    engine = TestGameEngine()
    engine.initialize()
    engine.reset()

    assert engine.reset_called
    assert engine.state.phase == GamePhase.SETUP


def test_game_engine_events():
    """Test game engine event emission."""
    engine = TestGameEngine()
    handler = TestEventHandler()

    engine.event_bus.subscribe_all(handler)
    engine.emit_event("TEST_EVENT", data={"value": 42})

    assert len(handler.events) == 1
    assert handler.events[0].data["value"] == 42


def test_game_state_serialization():
    """Test game state serialization."""
    state = GameState(phase=GamePhase.RUNNING, metadata={"player": "Alice"})
    state_dict = state.to_dict()

    assert state_dict["phase"] == "RUNNING"
    assert state_dict["metadata"]["player"] == "Alice"

    restored = GameState.from_dict(state_dict)
    assert restored.phase == GamePhase.RUNNING
    assert restored.metadata["player"] == "Alice"


# ==================== Persistence Tests ====================


def test_json_serializer():
    """Test JSON serialization."""
    serializer = JSONSerializer()
    data = {"key": "value", "number": 42}

    serialized = serializer.serialize(data)
    assert isinstance(serialized, bytes)

    deserialized = serializer.deserialize(serialized)
    assert deserialized == data


def test_pickle_serializer():
    """Test pickle serialization."""
    serializer = PickleSerializer()
    data = {"key": "value", "list": [1, 2, 3]}

    serialized = serializer.serialize(data)
    deserialized = serializer.deserialize(serialized)

    assert deserialized == data


def test_save_load_manager():
    """Test save/load functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SaveLoadManager(save_dir=Path(tmpdir))

        state = {"score": 100, "level": 5}
        filepath = manager.save("test_game", state, save_name="test1")

        assert filepath.exists()

        loaded = manager.load(filepath)
        assert loaded["game_type"] == "test_game"
        assert loaded["state"]["score"] == 100


def test_save_load_manager_list_saves():
    """Test listing saved games."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SaveLoadManager(save_dir=Path(tmpdir))

        manager.save("game1", {"data": 1}, save_name="game1_save1")
        manager.save("game2", {"data": 2}, save_name="game2_save1")
        manager.save("game1", {"data": 3}, save_name="game1_save2")

        all_saves = manager.list_saves()
        assert len(all_saves) == 3

        game1_saves = manager.list_saves("game1")
        assert len(game1_saves) == 2


def test_save_load_manager_delete():
    """Test deleting saved games."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SaveLoadManager(save_dir=Path(tmpdir))

        filepath = manager.save("test", {"data": 1})
        assert filepath.exists()

        assert manager.delete_save(filepath)
        assert not filepath.exists()


# ==================== Replay System Tests ====================


def test_replay_recorder():
    """Test replay recording."""
    recorder = ReplayRecorder()

    recorder.record(time.time(), "Player1", "MOVE", {"position": "A1"})
    recorder.record(time.time(), "Player2", "MOVE", {"position": "B2"})

    actions = recorder.get_actions()
    assert len(actions) == 2
    assert actions[0].actor == "Player1"
    assert actions[1].action_type == "MOVE"


def test_replay_recorder_start_stop():
    """Test starting and stopping recording."""
    recorder = ReplayRecorder()

    recorder.record(time.time(), "Player", "ACTION1")
    assert len(recorder.get_actions()) == 1

    recorder.stop_recording()
    recorder.record(time.time(), "Player", "ACTION2")
    assert len(recorder.get_actions()) == 1  # Not recorded

    recorder.start_recording()
    recorder.record(time.time(), "Player", "ACTION3")
    assert len(recorder.get_actions()) == 2


def test_replay_recorder_save_load():
    """Test saving and loading replays."""
    recorder = ReplayRecorder()
    recorder.record(time.time(), "Player1", "MOVE", {"x": 1})

    replay_data = recorder.save_replay()
    assert len(replay_data["actions"]) == 1

    new_recorder = ReplayRecorder()
    new_recorder.load_replay(replay_data)
    assert len(new_recorder.get_actions()) == 1


def test_replay_manager_undo_redo():
    """Test undo/redo functionality."""
    manager = ReplayManager()

    manager.record_action(time.time(), "Player", "MOVE", {"pos": "A1"})
    manager.record_action(time.time(), "Player", "MOVE", {"pos": "B2"})

    assert manager.can_undo()
    assert not manager.can_redo()

    action = manager.undo()
    assert action.data["pos"] == "B2"
    assert manager.can_redo()

    action = manager.redo()
    assert action.data["pos"] == "B2"
    assert not manager.can_redo()


def test_replay_manager_history_limit():
    """Test replay history limit."""
    manager = ReplayManager(max_history=3)

    for i in range(5):
        manager.record_action(time.time(), "Player", "MOVE", {"num": i})

    history = manager.get_history()
    assert len(history) == 3
    assert history[0].data["num"] == 2  # First 2 were dropped


# ==================== Settings Tests ====================


def test_settings_basic():
    """Test basic settings functionality."""
    settings = Settings(defaults={"volume": 100, "theme": "dark"})

    assert settings.get("volume") == 100
    assert settings.get("nonexistent", "default") == "default"

    settings.set("volume", 50)
    assert settings.get("volume") == 50


def test_settings_dict_interface():
    """Test dictionary-like interface."""
    settings = Settings()

    settings["key"] = "value"
    assert settings["key"] == "value"
    assert "key" in settings


def test_settings_reset():
    """Test resetting settings."""
    settings = Settings(defaults={"a": 1, "b": 2})

    settings.set("a", 10)
    settings.set("b", 20)

    settings.reset("a")
    assert settings.get("a") == 1
    assert settings.get("b") == 20

    settings.reset()
    assert settings.get("a") == 1
    assert settings.get("b") == 2


def test_settings_manager():
    """Test settings manager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SettingsManager(config_dir=Path(tmpdir))

        settings = manager.load_settings("test_game", defaults={"level": 1})
        settings.set("level", 5)

        assert manager.save_settings("test_game", settings)

        new_settings = manager.load_settings("test_game")
        assert new_settings.get("level") == 5


def test_settings_manager_global():
    """Test global settings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SettingsManager(config_dir=Path(tmpdir))

        global_settings = manager.get_global_settings()
        assert global_settings.has("sound_enabled")

        global_settings.set("sound_enabled", False)
        manager.save_global_settings(global_settings)

        loaded = manager.get_global_settings()
        assert not loaded.get("sound_enabled")


def test_settings_manager_list_games():
    """Test listing games with settings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SettingsManager(config_dir=Path(tmpdir))

        manager.save_settings("game1", Settings({"a": 1}))
        manager.save_settings("game2", Settings({"b": 2}))

        games = manager.list_game_settings()
        assert "game1" in games
        assert "game2" in games
