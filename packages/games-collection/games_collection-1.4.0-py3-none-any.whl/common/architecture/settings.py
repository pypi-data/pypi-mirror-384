"""Unified settings and preferences system.

This module provides a centralized way to manage game settings and user
preferences across all games.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Set


class Settings:
    """Container for game settings.

    This class provides a dictionary-like interface for storing and
    retrieving settings with type conversion and validation.
    """

    def __init__(self, defaults: Optional[Dict[str, Any]] = None) -> None:
        """Initialize settings with optional defaults.

        Args:
            defaults: Default settings values
        """
        self._settings: Dict[str, Any] = defaults.copy() if defaults else {}
        self._defaults = defaults.copy() if defaults else {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value.

        Args:
            key: Setting key
            default: Default value if key doesn't exist

        Returns:
            The setting value or default
        """
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value.

        Args:
            key: Setting key
            value: Setting value
        """
        self._settings[key] = value

    def has(self, key: str) -> bool:
        """Check if a setting exists.

        Args:
            key: Setting key

        Returns:
            True if the setting exists
        """
        return key in self._settings

    def remove(self, key: str) -> bool:
        """Remove a setting.

        Args:
            key: Setting key

        Returns:
            True if the setting was removed
        """
        if key in self._settings:
            del self._settings[key]
            return True
        return False

    def reset(self, key: Optional[str] = None) -> None:
        """Reset settings to defaults.

        Args:
            key: Optional specific key to reset. If None, resets all settings.
        """
        if key is None:
            self._settings = self._defaults.copy()
        elif key in self._defaults:
            self._settings[key] = self._defaults[key]

    def update(self, settings: Dict[str, Any]) -> None:
        """Update multiple settings at once.

        Args:
            settings: Dictionary of settings to update
        """
        self._settings.update(settings)

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to a dictionary.

        Returns:
            Dictionary of all settings
        """
        return self._settings.copy()

    def keys(self) -> Set[str]:
        """Get all setting keys.

        Returns:
            Set of setting keys
        """
        return set(self._settings.keys())

    def __getitem__(self, key: str) -> Any:
        """Get a setting using dictionary syntax."""
        return self._settings[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a setting using dictionary syntax."""
        self._settings[key] = value

    def __contains__(self, key: str) -> bool:
        """Check if a setting exists using 'in' operator."""
        return key in self._settings

    def __repr__(self) -> str:
        """Return string representation of settings."""
        return f"Settings({self._settings})"


class SettingsManager:
    """Manager for loading, saving, and managing settings.

    This class provides high-level functionality for persistent settings
    across game sessions.
    """

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        """Initialize the settings manager.

        Args:
            config_dir: Directory for config files (defaults to ./config)
        """
        self._config_dir = config_dir or Path("./config")
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._settings_cache: Dict[str, Settings] = {}

    def load_settings(self, game_type: str, defaults: Optional[Dict[str, Any]] = None) -> Settings:
        """Load settings for a specific game.

        Args:
            game_type: Type/name of the game
            defaults: Default settings if file doesn't exist

        Returns:
            Settings object for the game
        """
        # Check cache first
        if game_type in self._settings_cache:
            return self._settings_cache[game_type]

        # Create settings with defaults
        settings = Settings(defaults)

        # Try to load from file
        filepath = self._config_dir / f"{game_type}_settings.json"
        if filepath.exists():
            try:
                with filepath.open("r") as f:
                    data = json.load(f)
                    settings.update(data)
            except (json.JSONDecodeError, IOError):
                # Use defaults if file is corrupted
                pass

        # Cache the settings
        self._settings_cache[game_type] = settings
        return settings

    def save_settings(self, game_type: str, settings: Settings) -> bool:
        """Save settings for a specific game.

        Args:
            game_type: Type/name of the game
            settings: Settings to save

        Returns:
            True if saved successfully
        """
        filepath = self._config_dir / f"{game_type}_settings.json"
        try:
            with filepath.open("w") as f:
                json.dump(settings.to_dict(), f, indent=2)
            self._settings_cache[game_type] = settings
            return True
        except IOError:
            return False

    def delete_settings(self, game_type: str) -> bool:
        """Delete settings for a specific game.

        Args:
            game_type: Type/name of the game

        Returns:
            True if deleted successfully
        """
        filepath = self._config_dir / f"{game_type}_settings.json"
        try:
            filepath.unlink()
            if game_type in self._settings_cache:
                del self._settings_cache[game_type]
            return True
        except FileNotFoundError:
            return False

    def list_game_settings(self) -> list[str]:
        """List all games with saved settings.

        Returns:
            List of game type names
        """
        files = self._config_dir.glob("*_settings.json")
        return [f.stem.replace("_settings", "") for f in files]

    def clear_cache(self) -> None:
        """Clear the settings cache."""
        self._settings_cache.clear()

    def get_global_settings(self) -> Settings:
        """Get global settings that apply to all games.

        Returns:
            Global settings object
        """
        return self.load_settings(
            "global",
            defaults={
                "theme": "default",
                "sound_enabled": True,
                "auto_save": True,
                "language": "en",
            },
        )

    def save_global_settings(self, settings: Settings) -> bool:
        """Save global settings.

        Args:
            settings: Global settings to save

        Returns:
            True if saved successfully
        """
        return self.save_settings("global", settings)
