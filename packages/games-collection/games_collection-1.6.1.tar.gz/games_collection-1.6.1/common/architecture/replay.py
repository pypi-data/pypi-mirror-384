"""Replay and undo system as a common utility.

This module provides functionality for recording game actions and replaying
them, as well as implementing undo/redo functionality.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ReplayAction:
    """Represents a single action in a replay.

    Attributes:
        timestamp: Time when the action occurred
        actor: Identifier of who/what performed the action
        action_type: Type of action performed
        data: Additional data about the action
        state_before: Optional snapshot of state before action
    """

    timestamp: float
    actor: str
    action_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    state_before: Optional[Dict[str, Any]] = None


class ReplayRecorder:
    """Records game actions for replay functionality.

    This class maintains a history of all actions taken during a game,
    allowing them to be replayed or analyzed later.
    """

    def __init__(self, capture_state: bool = False) -> None:
        """Initialize the replay recorder.

        Args:
            capture_state: Whether to capture state snapshots before each action
        """
        self._actions: List[ReplayAction] = []
        self._capture_state = capture_state
        self._recording = True

    def record(
        self,
        timestamp: float,
        actor: str,
        action_type: str,
        data: Optional[Dict[str, Any]] = None,
        state_before: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an action.

        Args:
            timestamp: Time when the action occurred
            actor: Identifier of who performed the action
            action_type: Type of action
            data: Additional data about the action
            state_before: Optional state snapshot before the action
        """
        if not self._recording:
            return

        action = ReplayAction(
            timestamp=timestamp,
            actor=actor,
            action_type=action_type,
            data=data or {},
            state_before=state_before if self._capture_state else None,
        )
        self._actions.append(action)

    def get_actions(self) -> List[ReplayAction]:
        """Get all recorded actions.

        Returns:
            List of recorded actions in chronological order
        """
        return self._actions.copy()

    def clear(self) -> None:
        """Clear all recorded actions."""
        self._actions.clear()

    def start_recording(self) -> None:
        """Start recording actions."""
        self._recording = True

    def stop_recording(self) -> None:
        """Stop recording actions."""
        self._recording = False

    def is_recording(self) -> bool:
        """Check if recording is active."""
        return self._recording

    def save_replay(self) -> Dict[str, Any]:
        """Save the replay to a dictionary format.

        Returns:
            Dictionary containing all replay data
        """
        return {
            "actions": [
                {
                    "timestamp": action.timestamp,
                    "actor": action.actor,
                    "action_type": action.action_type,
                    "data": action.data,
                    "state_before": action.state_before,
                }
                for action in self._actions
            ]
        }

    def load_replay(self, replay_data: Dict[str, Any]) -> None:
        """Load a replay from dictionary format.

        Args:
            replay_data: Dictionary containing replay data
        """
        self._actions.clear()
        for action_data in replay_data.get("actions", []):
            self._actions.append(
                ReplayAction(
                    timestamp=action_data["timestamp"],
                    actor=action_data["actor"],
                    action_type=action_data["action_type"],
                    data=action_data.get("data", {}),
                    state_before=action_data.get("state_before"),
                )
            )


class ReplayManager:
    """Manages replay and undo/redo functionality.

    This class provides a complete undo/redo system with action execution
    and reversal capabilities.
    """

    def __init__(self, max_history: int = 100) -> None:
        """Initialize the replay manager.

        Args:
            max_history: Maximum number of actions to keep in history
        """
        self._history: List[ReplayAction] = []
        self._redo_stack: List[ReplayAction] = []
        self._max_history = max_history

    def record_action(
        self,
        timestamp: float,
        actor: str,
        action_type: str,
        data: Optional[Dict[str, Any]] = None,
        state_before: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an action for undo/redo.

        Args:
            timestamp: Time when the action occurred
            actor: Identifier of who performed the action
            action_type: Type of action
            data: Additional data about the action
            state_before: State snapshot before the action
        """
        action = ReplayAction(
            timestamp=timestamp,
            actor=actor,
            action_type=action_type,
            data=data or {},
            state_before=state_before,
        )

        self._history.append(action)

        # Clear redo stack when new action is recorded
        self._redo_stack.clear()

        # Limit history size
        if len(self._history) > self._max_history:
            self._history.pop(0)

    def can_undo(self) -> bool:
        """Check if undo is available.

        Returns:
            True if there are actions to undo
        """
        return len(self._history) > 0

    def can_redo(self) -> bool:
        """Check if redo is available.

        Returns:
            True if there are actions to redo
        """
        return len(self._redo_stack) > 0

    def undo(self) -> Optional[ReplayAction]:
        """Undo the last action.

        Returns:
            The action that was undone, or None if no actions to undo
        """
        if not self.can_undo():
            return None

        action = self._history.pop()
        self._redo_stack.append(action)
        return action

    def redo(self) -> Optional[ReplayAction]:
        """Redo the last undone action.

        Returns:
            The action that was redone, or None if no actions to redo
        """
        if not self.can_redo():
            return None

        action = self._redo_stack.pop()
        self._history.append(action)
        return action

    def clear(self) -> None:
        """Clear all history and redo stack."""
        self._history.clear()
        self._redo_stack.clear()

    def get_history(self) -> List[ReplayAction]:
        """Get the action history.

        Returns:
            List of actions in chronological order
        """
        return self._history.copy()

    def get_redo_stack(self) -> List[ReplayAction]:
        """Get the redo stack.

        Returns:
            List of actions that can be redone
        """
        return self._redo_stack.copy()
