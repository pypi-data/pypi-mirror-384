"""A keyboard shortcut system for GUI applications.

This module provides a centralized and extensible system for managing and
handling keyboard shortcuts across all game GUIs. It is designed to be
integrated with a Tkinter-based GUI, but it can be adapted for other
frameworks.

Key features include:
- **Centralized Management**: A `ShortcutManager` class acts as a central
  repository for all keyboard shortcuts.
- **Dynamic Registration**: Shortcuts can be registered, unregistered, enabled,
  and disabled at runtime.
- **Help Generation**: The system can automatically generate a formatted help
  text listing all available shortcuts and their descriptions.
- **Default Shortcuts**: A method is provided to register a set of common,
  default shortcuts (e.g., Ctrl+N for a new game, Ctrl+Q to quit).
- **Singleton Manager**: A global `ShortcutManager` instance ensures
  consistency across the application.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

try:
    # Tkinter is optional, allowing the core logic to be used without a GUI.
    import tkinter as tk

    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None  # type: ignore


class KeyboardShortcut:
    """Represents a single keyboard shortcut.

    This class encapsulates the properties of a keyboard shortcut, including its
    key combination, the callback function to execute, a human-readable
    description, and its enabled state.

    Attributes:
        key: The key combination in a format that the GUI framework
             understands (e.g., '<Control-n>', '<F1>').
        callback: The function to be called when the shortcut is triggered.
        description: A human-readable description of what the shortcut does.
        enabled: A boolean indicating whether the shortcut is currently active.
    """

    def __init__(self, key: str, callback: Callable[[], Any], description: str = "") -> None:
        """Initialize a keyboard shortcut.

        Args:
            key: The key combination in a Tkinter-compatible format.
            callback: The function to be called when the shortcut is triggered.
            description: A description of what the shortcut does, which can be
                         used to generate help text.
        """
        self.key = key
        self.callback = callback
        self.description = description
        self.enabled = True

    def trigger(self) -> Any:
        """Trigger the shortcut's callback function if it is enabled.

        Returns:
            The result of the callback function, or `None` if the shortcut is
            disabled.
        """
        if self.enabled:
            return self.callback()
        return None


class ShortcutManager:
    """A manager for handling all keyboard shortcuts in the application.

    This class provides methods for registering, binding, and executing
    keyboard shortcuts. It is designed to be used as a singleton to ensure a
    consistent state of shortcuts throughout the application.
    """

    def __init__(self, root: Optional[Any] = None) -> None:
        """Initialize the shortcut manager.

        Args:
            root: The root Tkinter widget to which the shortcuts will be bound.
                  This can be set later using the `set_root` method.
        """
        self.root = root
        self.shortcuts: Dict[str, KeyboardShortcut] = {}
        self._default_shortcuts_registered = False

    def register(self, key: str, callback: Callable[[], Any], description: str = "") -> None:
        """Register a new keyboard shortcut.

        Args:
            key: The key combination in a Tkinter-compatible format (e.g.,
                 '<Control-n>', '<F1>').
            callback: The function to be called when the shortcut is triggered.
            description: A human-readable description of the shortcut.
        """
        shortcut = KeyboardShortcut(key, callback, description)
        self.shortcuts[key] = shortcut

        # If a root widget is already set, bind the new shortcut immediately.
        if self.root and TKINTER_AVAILABLE:
            self._bind_shortcut(shortcut)

    def _bind_shortcut(self, shortcut: KeyboardShortcut) -> None:
        """Bind a shortcut to the root widget.

        Args:
            shortcut: The `KeyboardShortcut` object to be bound.
        """
        if not self.root or not hasattr(self.root, "bind_all"):
            return

        def handler(event: tk.Event) -> str | None:
            """A wrapper function to handle the shortcut's key press event."""
            if shortcut.enabled:
                result = shortcut.trigger()
                # Returning "break" prevents the event from propagating further
                # and stops any default behavior associated with the key press.
                return "break" if result is not False else None
            return None

        self.root.bind_all(shortcut.key, handler)

    def unregister(self, key: str) -> bool:
        """Unregister a keyboard shortcut.

        Args:
            key: The key combination of the shortcut to be unregistered.

        Returns:
            True if the shortcut was successfully unregistered, False
            otherwise.
        """
        if key in self.shortcuts:
            # Unbind the shortcut from the root widget if it exists.
            if self.root and hasattr(self.root, "unbind_all"):
                self.root.unbind_all(key)

            del self.shortcuts[key]
            return True
        return False

    def enable(self, key: str) -> bool:
        """Enable a registered keyboard shortcut.

        Args:
            key: The key combination of the shortcut to be enabled.

        Returns:
            True if the shortcut was successfully enabled, False otherwise.
        """
        if key in self.shortcuts:
            self.shortcuts[key].enabled = True
            return True
        return False

    def disable(self, key: str) -> bool:
        """Disable a registered keyboard shortcut.

        Args:
            key: The key combination of the shortcut to be disabled.

        Returns:
            True if the shortcut was successfully disabled, False otherwise.
        """
        if key in self.shortcuts:
            self.shortcuts[key].enabled = False
            return True
        return False

    def set_root(self, root: Any) -> None:
        """Set the root widget and bind all currently registered shortcuts.

        This is typically called once the main application window has been
        created.

        Args:
            root: The root Tkinter widget to which all shortcuts will be bound.
        """
        self.root = root

        # Bind all existing shortcuts to the new root widget.
        for shortcut in self.shortcuts.values():
            self._bind_shortcut(shortcut)

    def get_shortcuts(self) -> Dict[str, KeyboardShortcut]:
        """Get a copy of all registered shortcuts.

        Returns:
            A dictionary mapping key combinations to `KeyboardShortcut` objects.
        """
        return self.shortcuts.copy()

    def get_shortcuts_help(self) -> str:
        """Generate a formatted help text for all registered shortcuts.

        The shortcuts are automatically grouped into categories based on their
        descriptions.

        Returns:
            A formatted string containing all shortcuts and their descriptions.
        """
        lines = ["Keyboard Shortcuts:", ""]

        # Group shortcuts into categories for better organization.
        categories: Dict[str, list[str]] = {
            "General": [],
            "Game": [],
            "View": [],
            "Other": [],
        }

        for key, shortcut in sorted(self.shortcuts.items()):
            if not shortcut.description:
                continue

            # Categorize shortcuts based on keywords in their descriptions.
            desc_lower = shortcut.description.lower()
            if any(word in desc_lower for word in ["new", "quit", "save", "load", "settings"]):
                category = "General"
            elif any(word in desc_lower for word in ["undo", "redo", "hint", "move"]):
                category = "Game"
            elif any(word in desc_lower for word in ["zoom", "fullscreen", "theme"]):
                category = "View"
            else:
                category = "Other"

            # Format the key for display (e.g., "<Control-n>" -> "Ctrl+n").
            display_key = key.replace("<", "").replace(">", "").replace("-", "+")
            display_key = display_key.replace("Control", "Ctrl")
            display_key = display_key.replace("Shift", "⇧")
            display_key = display_key.replace("Alt", "Alt")

            categories[category].append(f"  {display_key:20} - {shortcut.description}")

        # Build the final help text string.
        for category, shortcuts_list in categories.items():
            if shortcuts_list:
                lines.append(f"{category}:")
                lines.extend(shortcuts_list)
                lines.append("")

        return "\n".join(lines)

    def register_default_shortcuts(self, callbacks: Dict[str, Callable[[], Any]]) -> None:
        """Register a set of default shortcuts for common actions.

        This method provides a convenient way to set up standard shortcuts
        without having to register each one manually.

        Args:
            callbacks: A dictionary mapping action names to their corresponding
                       callback functions. Expected keys include 'new_game',
                       'quit', 'undo', 'redo', 'help', 'settings', etc.
        """
        if self._default_shortcuts_registered:
            return

        # General shortcuts
        if "new_game" in callbacks:
            self.register("<Control-n>", callbacks["new_game"], "New Game")
        if "quit" in callbacks:
            self.register("<Control-q>", callbacks["quit"], "Quit Application")
        if "save" in callbacks:
            self.register("<Control-s>", callbacks["save"], "Save Game")
        if "load" in callbacks:
            self.register("<Control-o>", callbacks["load"], "Load Game")

        # Game-specific shortcuts
        if "undo" in callbacks:
            self.register("<Control-z>", callbacks["undo"], "Undo Last Move")
        if "redo" in callbacks:
            self.register("<Control-y>", callbacks["redo"], "Redo Last Move")
            self.register("<Control-Shift-z>", callbacks["redo"], "Redo Last Move")
        if "hint" in callbacks:
            self.register("<Control-h>", callbacks["hint"], "Show a Hint")

        # View-related shortcuts
        if "toggle_theme" in callbacks:
            self.register("<Control-t>", callbacks["toggle_theme"], "Toggle Dark/Light Theme")
        if "fullscreen" in callbacks:
            self.register("<F11>", callbacks["fullscreen"], "Toggle Fullscreen Mode")

        # Help and settings shortcuts
        if "help" in callbacks:
            self.register("<F1>", callbacks["help"], "Show Help")
        if "settings" in callbacks:
            self.register("<Control-comma>", callbacks["settings"], "Open Settings")

        self._default_shortcuts_registered = True


# A global instance of the ShortcutManager to ensure a single source of truth
# for shortcuts throughout the application.
_shortcut_manager: Optional[ShortcutManager] = None


def get_shortcut_manager() -> ShortcutManager:
    """Get the global singleton instance of the `ShortcutManager`.

    This function ensures that a single instance of the `ShortcutManager` is
    used throughout the application, providing a consistent state for
    shortcuts.

    Returns:
        The global `ShortcutManager` instance.
    """
    global _shortcut_manager
    if _shortcut_manager is None:
        _shortcut_manager = ShortcutManager()
    return _shortcut_manager


def register_shortcut(key: str, callback: Callable[[], Any], description: str = "") -> None:
    """A convenience function to register a keyboard shortcut globally.

    Args:
        key: The key combination in a Tkinter-compatible format.
        callback: The function to be called when the shortcut is triggered.
        description: A human-readable description of the shortcut.
    """
    get_shortcut_manager().register(key, callback, description)


def show_shortcuts_help() -> str:
    """A convenience function to get the help text for all registered shortcuts.

    Returns:
        A formatted string containing all shortcuts and their descriptions.
    """
    return get_shortcut_manager().get_shortcuts_help()
