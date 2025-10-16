"""Save/load game state functionality.

This module provides utilities for persisting game state to disk and
loading it back, enabling save/load features across all games.
"""

from __future__ import annotations

import json
import pickle
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class GameStateSerializer(ABC):
    """Abstract base class for game state serializers.

    Serializers convert game state to and from a format suitable for storage.
    """

    @abstractmethod
    def serialize(self, state: Dict[str, Any]) -> bytes:
        """Serialize game state to bytes.

        Args:
            state: Dictionary representation of game state

        Returns:
            Serialized state as bytes
        """
        pass

    @abstractmethod
    def deserialize(self, data: bytes) -> Dict[str, Any]:
        """Deserialize game state from bytes.

        Args:
            data: Serialized state data

        Returns:
            Dictionary representation of game state
        """
        pass


class JSONSerializer(GameStateSerializer):
    """JSON-based serializer for game state.

    Uses JSON format for human-readable saved games.
    """

    def __init__(self, indent: Optional[int] = 2) -> None:
        """Initialize the JSON serializer.

        Args:
            indent: Number of spaces for indentation (None for compact)
        """
        self._indent = indent

    def serialize(self, state: Dict[str, Any]) -> bytes:
        """Serialize game state to JSON bytes."""
        return json.dumps(state, indent=self._indent, default=str).encode("utf-8")

    def deserialize(self, data: bytes) -> Dict[str, Any]:
        """Deserialize game state from JSON bytes."""
        return json.loads(data.decode("utf-8"))


class PickleSerializer(GameStateSerializer):
    """Pickle-based serializer for game state.

    Uses Python's pickle format for efficient binary serialization.
    Note: Pickle files are not human-readable and should only be loaded
    from trusted sources.
    """

    def serialize(self, state: Dict[str, Any]) -> bytes:
        """Serialize game state using pickle."""
        return pickle.dumps(state)

    def deserialize(self, data: bytes) -> Dict[str, Any]:
        """Deserialize game state using pickle."""
        return pickle.loads(data)


class SaveLoadManager:
    """Manager for saving and loading game states.

    This class provides a high-level interface for persisting game state
    to disk with metadata like timestamps and game type.
    """

    def __init__(
        self,
        save_dir: Optional[Path] = None,
        serializer: Optional[GameStateSerializer] = None,
    ) -> None:
        """Initialize the save/load manager.

        Args:
            save_dir: Directory for saved games (defaults to ./saves)
            serializer: Serializer to use (defaults to JSONSerializer)
        """
        self._save_dir = save_dir or Path("./saves")
        self._serializer = serializer or JSONSerializer()
        self._save_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        game_type: str,
        state: Dict[str, Any],
        save_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Save a game state to disk.

        Args:
            game_type: Type/name of the game (e.g., "uno", "poker")
            state: Game state dictionary
            save_name: Optional name for the save file
            metadata: Optional additional metadata

        Returns:
            Path to the saved file
        """
        # Generate filename if not provided
        if save_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_name = f"{game_type}_{timestamp}"

        # Add extension if not present
        if not save_name.endswith(".save"):
            save_name = f"{save_name}.save"

        # Create save data with metadata
        save_data = {
            "game_type": game_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
            "state": state,
        }

        # Serialize and write to file
        filepath = self._save_dir / save_name
        serialized = self._serializer.serialize(save_data)
        filepath.write_bytes(serialized)

        return filepath

    def load(self, filepath: Path) -> Dict[str, Any]:
        """Load a game state from disk.

        Args:
            filepath: Path to the save file

        Returns:
            Dictionary containing the saved game data

        Raises:
            FileNotFoundError: If the save file doesn't exist
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Save file not found: {filepath}")

        data = filepath.read_bytes()
        return self._serializer.deserialize(data)

    def list_saves(self, game_type: Optional[str] = None) -> list[Path]:
        """List all saved games.

        Args:
            game_type: Optional filter by game type

        Returns:
            List of save file paths
        """
        pattern = "*.save"
        if game_type:
            pattern = f"{game_type}_*.save"

        return sorted(self._save_dir.glob(pattern), reverse=True)

    def delete_save(self, filepath: Path) -> bool:
        """Delete a save file.

        Args:
            filepath: Path to the save file

        Returns:
            True if the file was deleted
        """
        try:
            filepath.unlink()
            return True
        except FileNotFoundError:
            return False

    def get_save_info(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Get metadata about a save file without loading the full state.

        Args:
            filepath: Path to the save file

        Returns:
            Dictionary with metadata, or None if file doesn't exist
        """
        try:
            data = self.load(filepath)
            return {
                "game_type": data.get("game_type"),
                "timestamp": data.get("timestamp"),
                "metadata": data.get("metadata", {}),
            }
        except FileNotFoundError:
            return None
