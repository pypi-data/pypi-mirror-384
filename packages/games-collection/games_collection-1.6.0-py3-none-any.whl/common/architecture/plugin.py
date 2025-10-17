"""Plugin system for third-party game additions.

This module provides a flexible plugin system that allows third-party
developers to add new games without modifying the core codebase.
"""

from __future__ import annotations

import importlib.util
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Type


@dataclass
class PluginMetadata:
    """Metadata about a plugin.

    Attributes:
        name: Name of the plugin
        version: Plugin version
        author: Plugin author
        description: Description of what the plugin provides
        dependencies: List of required dependencies
    """

    name: str
    version: str
    author: str = "Unknown"
    description: str = ""
    dependencies: List[str] = None

    def __post_init__(self) -> None:
        """Initialize dependencies list if not provided."""
        if self.dependencies is None:
            self.dependencies = []


class GamePlugin(ABC):
    """Abstract base class for game plugins.

    Plugins must implement this interface to be loaded by the plugin system.
    """

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Get metadata about this plugin.

        Returns:
            Plugin metadata
        """
        pass

    @abstractmethod
    def initialize(self, **kwargs: Any) -> None:
        """Initialize the plugin.

        Called when the plugin is loaded.

        Args:
            **kwargs: Initialization parameters
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the plugin.

        Called when the plugin is unloaded or the application exits.
        """
        pass

    @abstractmethod
    def get_game_class(self) -> Type:
        """Get the game class provided by this plugin.

        Returns:
            The game engine class
        """
        pass

    def get_ui_class(self) -> Optional[Type]:
        """Get the UI class for the game, if any.

        Returns:
            The UI class, or None if not provided
        """
        return None

    def get_config_schema(self) -> Optional[Dict[str, Any]]:
        """Get the configuration schema for the game.

        Returns:
            Configuration schema dictionary, or None
        """
        return None


class PluginManager:
    """Manager for loading and managing game plugins.

    The plugin system allows third-party games to be added dynamically
    without modifying the core codebase.
    """

    def __init__(self, plugin_dirs: Optional[List[Path]] = None) -> None:
        """Initialize the plugin manager.

        Args:
            plugin_dirs: List of directories to search for plugins
        """
        self._plugin_dirs = plugin_dirs or [Path("./plugins")]
        self._plugins: Dict[str, GamePlugin] = {}
        self._plugin_metadata: Dict[str, PluginMetadata] = {}

    def discover_plugins(self) -> List[str]:
        """Discover available plugins in plugin directories.

        Returns:
            List of discovered plugin names
        """
        discovered = []

        for plugin_dir in self._plugin_dirs:
            if not plugin_dir.exists():
                continue

            # Look for Python files and packages
            for item in plugin_dir.iterdir():
                if item.is_file() and item.suffix == ".py" and not item.name.startswith("_"):
                    discovered.append(item.stem)
                elif item.is_dir() and (item / "__init__.py").exists():
                    discovered.append(item.name)

        return discovered

    def load_plugin(self, plugin_name: str) -> bool:
        """Load a plugin by name.

        Args:
            plugin_name: Name of the plugin to load

        Returns:
            True if the plugin was loaded successfully
        """
        # Check if already loaded
        if plugin_name in self._plugins:
            return True

        # Try to load from each plugin directory
        for plugin_dir in self._plugin_dirs:
            plugin_path = plugin_dir / f"{plugin_name}.py"
            plugin_package = plugin_dir / plugin_name

            # Try loading as a module file
            if plugin_path.exists():
                try:
                    spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[plugin_name] = module
                        try:
                            spec.loader.exec_module(module)
                        except Exception:
                            sys.modules.pop(plugin_name, None)
                            raise

                        # Look for plugin class
                        plugin_instance = self._find_plugin_instance(module)
                        if plugin_instance:
                            self._register_plugin(plugin_name, plugin_instance)
                            return True
                except Exception as e:
                    print(f"Error loading plugin {plugin_name}: {e}")
                    continue

            # Try loading as a package
            elif plugin_package.exists() and (plugin_package / "__init__.py").exists():
                try:
                    spec = importlib.util.spec_from_file_location(
                        plugin_name,
                        plugin_package / "__init__.py",
                        submodule_search_locations=[str(plugin_package)],
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[plugin_name] = module
                        try:
                            spec.loader.exec_module(module)
                        except Exception:
                            sys.modules.pop(plugin_name, None)
                            raise

                        # Look for plugin class
                        plugin_instance = self._find_plugin_instance(module)
                        if plugin_instance:
                            self._register_plugin(plugin_name, plugin_instance)
                            return True
                except Exception as e:
                    print(f"Error loading plugin {plugin_name}: {e}")
                    continue

        return False

    def _find_plugin_instance(self, module: Any) -> Optional[GamePlugin]:
        """Find a GamePlugin instance in a module.

        Args:
            module: The module to search

        Returns:
            Plugin instance if found, None otherwise
        """
        # Look for a 'plugin' attribute
        if hasattr(module, "plugin") and isinstance(module.plugin, GamePlugin):
            return module.plugin

        # Look for a class that inherits from GamePlugin
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, GamePlugin) and attr is not GamePlugin:
                return attr()

        return None

    def _register_plugin(self, name: str, plugin: GamePlugin) -> None:
        """Register a loaded plugin.

        Args:
            name: Plugin name
            plugin: Plugin instance
        """
        plugin.initialize()
        self._plugins[name] = plugin
        self._plugin_metadata[name] = plugin.get_metadata()

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin.

        Args:
            plugin_name: Name of the plugin to unload

        Returns:
            True if the plugin was unloaded
        """
        if plugin_name not in self._plugins:
            return False

        plugin = self._plugins[plugin_name]
        plugin.shutdown()

        del self._plugins[plugin_name]
        del self._plugin_metadata[plugin_name]

        # Remove from sys.modules
        if plugin_name in sys.modules:
            del sys.modules[plugin_name]

        return True

    def get_plugin(self, plugin_name: str) -> Optional[GamePlugin]:
        """Get a loaded plugin by name.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin instance, or None if not loaded
        """
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> List[str]:
        """List all loaded plugins.

        Returns:
            List of plugin names
        """
        return list(self._plugins.keys())

    def get_plugin_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """Get metadata for a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin metadata, or None if not loaded
        """
        return self._plugin_metadata.get(plugin_name)

    def load_all_plugins(self) -> Dict[str, bool]:
        """Load all discovered plugins.

        Returns:
            Dictionary mapping plugin names to load success status
        """
        results = {}
        for plugin_name in self.discover_plugins():
            results[plugin_name] = self.load_plugin(plugin_name)
        return results

    def unload_all_plugins(self) -> None:
        """Unload all loaded plugins."""
        plugin_names = list(self._plugins.keys())
        for plugin_name in plugin_names:
            self.unload_plugin(plugin_name)

    def add_plugin_directory(self, directory: Path) -> None:
        """Add a directory to search for plugins.

        Args:
            directory: Path to plugin directory
        """
        if directory not in self._plugin_dirs:
            self._plugin_dirs.append(directory)
