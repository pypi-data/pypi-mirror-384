"""Core architecture components for game engines."""

from .engine import GameEngine, GamePhase, GameState
from .events import Event, EventBus, EventHandler, FunctionEventHandler
from .observer import Observable, Observer, PropertyObservable
from .persistence import GameStateSerializer, JSONSerializer, PickleSerializer, SaveLoadManager
from .plugin import GamePlugin, PluginManager, PluginMetadata
from .replay import ReplayAction, ReplayManager, ReplayRecorder
from .settings import Settings, SettingsManager

__all__ = [
    "GameEngine",
    "GameState",
    "GamePhase",
    "Event",
    "EventBus",
    "EventHandler",
    "FunctionEventHandler",
    "Observable",
    "Observer",
    "PropertyObservable",
    "GameStateSerializer",
    "SaveLoadManager",
    "GamePlugin",
    "PluginManager",
    "ReplayManager",
    "ReplayRecorder",
    "Settings",
    "SettingsManager",
    "JSONSerializer",
    "PickleSerializer",
    "ReplayAction",
]
