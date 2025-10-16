"""Keyboard shortcut system for GUI applications.

This module provides a centralized system for managing and handling keyboard
shortcuts across all game GUIs.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

try:
    import tkinter as tk

    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None  # type: ignore


class KeyboardShortcut:
    """Represents a keyboard shortcut.

    Attributes:
        key: Key combination (e.g., '<Control-n>', '<F1>').
        callback: Function to call when shortcut is triggered.
        description: Human-readable description of the shortcut.
        enabled: Whether the shortcut is currently enabled.
    """

    def __init__(self, key: str, callback: Callable[[], Any], description: str = "") -> None:
        """Initialize a keyboard shortcut.

        Args:
            key: Key combination in tkinter format.
            callback: Function to call when triggered.
            description: Description of what the shortcut does.
        """
        self.key = key
        self.callback = callback
        self.description = description
        self.enabled = True

    def trigger(self) -> Any:
        """Trigger the shortcut callback.

        Returns:
            Result of callback function.
        """
        if self.enabled:
            return self.callback()
        return None


class ShortcutManager:
    """Manager for keyboard shortcuts.

    This class handles registration, binding, and execution of keyboard shortcuts.
    """

    def __init__(self, root: Optional[Any] = None) -> None:
        """Initialize the shortcut manager.

        Args:
            root: Root tkinter widget to bind shortcuts to.
        """
        self.root = root
        self.shortcuts: Dict[str, KeyboardShortcut] = {}
        self._default_shortcuts_registered = False

    def register(self, key: str, callback: Callable[[], Any], description: str = "") -> None:
        """Register a keyboard shortcut.

        Args:
            key: Key combination (e.g., '<Control-n>', '<F1>').
            callback: Function to call when triggered.
            description: Description of the shortcut.
        """
        shortcut = KeyboardShortcut(key, callback, description)
        self.shortcuts[key] = shortcut

        # Bind to root widget if available
        if self.root and TKINTER_AVAILABLE:
            self._bind_shortcut(shortcut)

    def _bind_shortcut(self, shortcut: KeyboardShortcut) -> None:
        """Bind a shortcut to the root widget.

        Args:
            shortcut: Shortcut to bind.
        """
        if not self.root or not hasattr(self.root, "bind_all"):
            return

        def handler(event):
            """Handle shortcut key press."""
            if shortcut.enabled:
                result = shortcut.trigger()
                # Return 'break' to prevent default behavior
                return "break" if result is not False else None

        self.root.bind_all(shortcut.key, handler)

    def unregister(self, key: str) -> bool:
        """Unregister a keyboard shortcut.

        Args:
            key: Key combination to unregister.

        Returns:
            True if shortcut was unregistered.
        """
        if key in self.shortcuts:
            # Unbind from root widget
            if self.root and hasattr(self.root, "unbind_all"):
                self.root.unbind_all(key)

            del self.shortcuts[key]
            return True
        return False

    def enable(self, key: str) -> bool:
        """Enable a keyboard shortcut.

        Args:
            key: Key combination to enable.

        Returns:
            True if shortcut was enabled.
        """
        if key in self.shortcuts:
            self.shortcuts[key].enabled = True
            return True
        return False

    def disable(self, key: str) -> bool:
        """Disable a keyboard shortcut.

        Args:
            key: Key combination to disable.

        Returns:
            True if shortcut was disabled.
        """
        if key in self.shortcuts:
            self.shortcuts[key].enabled = False
            return True
        return False

    def set_root(self, root: Any) -> None:
        """Set the root widget and bind all registered shortcuts.

        Args:
            root: Root tkinter widget.
        """
        self.root = root

        # Bind all existing shortcuts
        for shortcut in self.shortcuts.values():
            self._bind_shortcut(shortcut)

    def get_shortcuts(self) -> Dict[str, KeyboardShortcut]:
        """Get all registered shortcuts.

        Returns:
            Dictionary of shortcuts.
        """
        return self.shortcuts.copy()

    def get_shortcuts_help(self) -> str:
        """Get formatted help text for all shortcuts.

        Returns:
            Formatted string with all shortcuts and descriptions.
        """
        lines = ["Keyboard Shortcuts:", ""]

        # Group shortcuts by category
        categories = {
            "General": [],
            "Game": [],
            "View": [],
            "Other": [],
        }

        for key, shortcut in sorted(self.shortcuts.items()):
            if not shortcut.description:
                continue

            # Categorize shortcuts
            desc_lower = shortcut.description.lower()
            if any(word in desc_lower for word in ["new", "quit", "save", "load", "settings"]):
                category = "General"
            elif any(word in desc_lower for word in ["undo", "redo", "hint", "move"]):
                category = "Game"
            elif any(word in desc_lower for word in ["zoom", "fullscreen", "theme"]):
                category = "View"
            else:
                category = "Other"

            # Format key for display
            display_key = key.replace("<", "").replace(">", "")
            display_key = display_key.replace("Control", "Ctrl")
            display_key = display_key.replace("Shift", "⇧")
            display_key = display_key.replace("Alt", "Alt")

            categories[category].append(f"  {display_key:20} - {shortcut.description}")

        # Build output
        for category, shortcuts_list in categories.items():
            if shortcuts_list:
                lines.append(f"{category}:")
                lines.extend(shortcuts_list)
                lines.append("")

        return "\n".join(lines)

    def register_default_shortcuts(self, callbacks: Dict[str, Callable[[], Any]]) -> None:
        """Register default shortcuts for common actions.

        Args:
            callbacks: Dictionary mapping action names to callback functions.
                Expected keys: 'new_game', 'quit', 'undo', 'redo', 'help', 'settings'
        """
        if self._default_shortcuts_registered:
            return

        # General shortcuts
        if "new_game" in callbacks:
            self.register("<Control-n>", callbacks["new_game"], "New Game")

        if "quit" in callbacks:
            self.register("<Control-q>", callbacks["quit"], "Quit")
            self.register("<Alt-F4>", callbacks["quit"], "Quit")

        if "save" in callbacks:
            self.register("<Control-s>", callbacks["save"], "Save Game")

        if "load" in callbacks:
            self.register("<Control-o>", callbacks["load"], "Load Game")

        # Game shortcuts
        if "undo" in callbacks:
            self.register("<Control-z>", callbacks["undo"], "Undo Move")

        if "redo" in callbacks:
            self.register("<Control-y>", callbacks["redo"], "Redo Move")
            self.register("<Control-Shift-z>", callbacks["redo"], "Redo Move")

        if "hint" in callbacks:
            self.register("<Control-h>", callbacks["hint"], "Show Hint")

        # View shortcuts
        if "toggle_theme" in callbacks:
            self.register("<Control-t>", callbacks["toggle_theme"], "Toggle Theme")

        if "fullscreen" in callbacks:
            self.register("<F11>", callbacks["fullscreen"], "Toggle Fullscreen")

        # Help shortcuts
        if "help" in callbacks:
            self.register("<F1>", callbacks["help"], "Show Help")

        if "settings" in callbacks:
            self.register("<Control-comma>", callbacks["settings"], "Open Settings")

        self._default_shortcuts_registered = True


# Global shortcut manager
_shortcut_manager: Optional[ShortcutManager] = None


def get_shortcut_manager() -> ShortcutManager:
    """Get the global shortcut manager.

    Returns:
        Global ShortcutManager instance.
    """
    global _shortcut_manager
    if _shortcut_manager is None:
        _shortcut_manager = ShortcutManager()
    return _shortcut_manager


def register_shortcut(key: str, callback: Callable[[], Any], description: str = "") -> None:
    """Register a keyboard shortcut globally.

    Args:
        key: Key combination.
        callback: Function to call when triggered.
        description: Description of the shortcut.
    """
    get_shortcut_manager().register(key, callback, description)


def show_shortcuts_help() -> str:
    """Get help text for all registered shortcuts.

    Returns:
        Formatted shortcuts help text.
    """
    return get_shortcut_manager().get_shortcuts_help()
