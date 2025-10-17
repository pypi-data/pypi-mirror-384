# Event Bus Contract

This document standardizes the lifecycle events emitted by game engines, controllers, AIs, and user interfaces.
The shared `EventBus` enables cross-cutting features—such as analytics, achievements, tutorials, and telemetry—to listen for
consistent signals across all games.

## Event Types

| Event | Description | Typical Payload |
| ----- | ----------- | --------------- |
| `game.initialized` | Game objects constructed or `reset()` invoked. | `{"num_players": int, "winning_score": int}` |
| `game.start` | Gameplay transitions from setup to the first actionable turn. | `{"player": int, "bet_type": str}` |
| `game.action_processed` | An input (roll, move, bet change) was applied successfully. | `{"action": str, "roll": list[int]}` |
| `game.score_updated` | Player-visible score or bankroll changed. | `{"player": int, "scores": list[int]}` |
| `game.turn_complete` | Turn ended and control passed to another participant. | `{"next_player": int, "scores": list[int]}` |
| `game.over` | Game reached a terminal state with optional winner metadata. | `{"winner": int, "scores": list[int]}` |

All events are represented by the `GameEventType` enum. Emitters may include additional metadata, but the core keys listed above must remain stable.

## Subscription Guidelines

- **Game Engines** – Call `self.emit_event(GameEventType.*, data)` when transitioning phases, mutating scores, or completing turns.
- **Controllers / AI** – Implement `EventHandler` subclasses to react to events. Use `EventBus.subscribe()` or `subscribe_all()` during initialization.
- **User Interfaces** – Register handlers that transform events into UI updates, accessibility cues, or sound effects.
  Prefer small handlers composed per widget.
- **Shared Services** – Analytics, replay, and tutorial systems should rely solely on these signals to avoid tight coupling.

## Event History

The bus records every emitted `Event` accessible through `EventBus.get_history()`. Tests can assert against this history to verify contracts:

```python
bus = EventBus()
engine.set_event_bus(bus)
# ... run scenario ...
assert any(evt.type == GameEventType.TURN_COMPLETE.value for evt in bus.get_history())
```

Always clear history with `EventBus.clear_history()` when reusing a bus across scenarios.

## Inventory Status

| Package | Migrated Modules | Pending Migration |
| ------- | ---------------- | ----------------- |
| `dice_games` | `craps.craps`, `farkle.farkle` (full), CLIs adopting shared bus. | `bunco`, `liars_dice` (emit direct state changes). |
| `card_games` | Pending – most engines invoke direct callbacks without events. |
| `paper_games` | Pending – board/word games still notify controllers directly. |
| `logic_games` | Pending – AI modules poll engine state without events. |
| `word_games` | Pending – hangman/unscramble rely on direct method calls. |

Future work should prioritize the pending modules, progressively refactoring them to the standardized contract defined here.
