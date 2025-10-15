"""Abstract base class and utilities for GUI components.

This module provides reusable GUI components and a common interface for
game GUIs, reducing code duplication and providing consistent behavior.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

try:
    import tkinter as tk
    from tkinter import scrolledtext, ttk

    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    # Create placeholder types for type hints
    tk = None  # type: ignore
    scrolledtext = None  # type: ignore
    ttk = None  # type: ignore

# Import enhancement modules
from common.accessibility import get_accessibility_manager
from common.i18n import _, get_translation_manager
from common.keyboard_shortcuts import get_shortcut_manager
from common.sound_manager import SoundManager, create_sound_manager
from common.themes import get_theme_manager


@dataclass
class GUIConfig:
    """Configuration options for GUI components.

    Attributes:
        window_title: Title of the main window
        window_width: Width of the window in pixels
        window_height: Height of the window in pixels
        background_color: Background color for the window
        font_family: Default font family
        font_size: Default font size
        log_height: Height of the log widget in lines
        log_width: Width of the log widget in characters
        enable_sounds: Enable sound effects
        enable_animations: Enable animations
        theme_name: Name of the theme to use
        language: Language code for i18n
        accessibility_mode: Enable accessibility features
    """

    window_title: str = "Game"
    window_width: int = 800
    window_height: int = 600
    background_color: str = "#FFFFFF"
    font_family: str = "Helvetica"
    font_size: int = 12
    log_height: int = 10
    log_width: int = 60
    enable_sounds: bool = False
    enable_animations: bool = True
    theme_name: str = "light"
    language: str = "en"
    accessibility_mode: bool = False


class BaseGUI(ABC):
    """Abstract base class for game GUIs.

    This class provides common functionality for building game interfaces
    including layout management, logging, status updates, theming, sound,
    accessibility, i18n, and keyboard shortcuts.
    """

    def __init__(self, root: tk.Tk, config: Optional[GUIConfig] = None) -> None:
        """Initialize the base GUI.

        Args:
            root: The root Tkinter window.
            config: Optional configuration for the GUI.
        """
        self.root = root
        self.config = config or GUIConfig()

        # Initialize enhancement managers
        self.theme_manager = get_theme_manager()
        self.sound_manager: Optional[SoundManager] = None
        self.accessibility_manager = get_accessibility_manager()
        self.translation_manager = get_translation_manager()
        self.shortcut_manager = get_shortcut_manager()

        # Apply initial configuration
        self._setup_enhancements()
        self._setup_window()
        self._setup_shortcuts()

    def _setup_enhancements(self) -> None:
        """Set up all enhancement systems."""
        # Set theme
        self.theme_manager.set_current_theme(self.config.theme_name)
        self.current_theme = self.theme_manager.get_current_theme()

        # Set language
        self.translation_manager.set_language(self.config.language)

        # Initialize sound manager
        if self.config.enable_sounds:
            self.sound_manager = create_sound_manager(enabled=True)

        # Configure accessibility
        if self.config.accessibility_mode:
            self.accessibility_manager.set_high_contrast(True)
            self.accessibility_manager.set_screen_reader(True)

        # Set shortcut manager root
        self.shortcut_manager.set_root(self.root)

    def _setup_window(self) -> None:
        """Configure the main window with default settings."""
        self.root.title(_(self.config.window_title))
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")

        # Apply theme colors
        bg_color = self.current_theme.colors.background

        if TKINTER_AVAILABLE:
            self.root.configure(bg=bg_color)

            # Configure ttk styles
            style = ttk.Style()
            style.theme_use("clam")  # Use clam theme as base for better customization

            # Configure button style
            style.configure(
                "TButton",
                background=self.current_theme.colors.button_bg,
                foreground=self.current_theme.colors.button_fg,
                borderwidth=1,
                focuscolor=self.current_theme.colors.primary,
            )

            style.map(
                "TButton",
                background=[("active", self.current_theme.colors.button_active_bg)],
                foreground=[("active", self.current_theme.colors.button_active_fg)],
            )

        # Make window resizable
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

    def _setup_shortcuts(self) -> None:
        """Set up default keyboard shortcuts."""
        # Subclasses can override this to add custom shortcuts
        pass

    @abstractmethod
    def build_layout(self) -> None:
        """Build the main layout of the GUI.

        This method must be implemented by subclasses to create their
        specific interface components.
        """
        pass

    @abstractmethod
    def update_display(self) -> None:
        """Update the display to reflect the current game state.

        This method must be implemented by subclasses to update their
        specific components based on game state changes.
        """
        pass

    def create_header(self, parent: tk.Widget, text: str) -> tk.Label:
        """Create a standard header label.

        Args:
            parent: Parent widget for the header.
            text: Text to display in the header.

        Returns:
            The created label widget.
        """
        header = tk.Label(
            parent,
            text=text,
            font=(self.config.font_family, self.config.font_size + 6, "bold"),
            pady=8,
        )
        return header

    def create_status_label(self, parent: tk.Widget, text: str = "") -> tk.Label:
        """Create a standard status label.

        Args:
            parent: Parent widget for the label.
            text: Initial text to display.

        Returns:
            The created label widget.
        """
        label = tk.Label(
            parent,
            text=text,
            font=(self.config.font_family, self.config.font_size),
        )
        return label

    def create_log_widget(self, parent: tk.Widget) -> scrolledtext.ScrolledText:
        """Create a standard scrolled text log widget.

        Args:
            parent: Parent widget for the log.

        Returns:
            The created scrolled text widget.
        """
        log = scrolledtext.ScrolledText(
            parent,
            width=self.config.log_width,
            height=self.config.log_height,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Courier New", self.config.font_size - 1),
        )
        return log

    def log_message(self, log_widget: scrolledtext.ScrolledText, message: str) -> None:
        """Append a message to a log widget.

        Args:
            log_widget: The log widget to append to.
            message: The message to append.
        """
        log_widget.configure(state=tk.NORMAL)
        log_widget.insert(tk.END, message + "\n")
        log_widget.see(tk.END)
        log_widget.configure(state=tk.DISABLED)

    def clear_log(self, log_widget: scrolledtext.ScrolledText) -> None:
        """Clear all text from a log widget.

        Args:
            log_widget: The log widget to clear.
        """
        log_widget.configure(state=tk.NORMAL)
        log_widget.delete("1.0", tk.END)
        log_widget.configure(state=tk.DISABLED)

    def create_button_frame(
        self,
        parent: tk.Widget,
        buttons: List[Dict[str, Any]],
    ) -> tk.Frame:
        """Create a frame with multiple buttons.

        Args:
            parent: Parent widget for the button frame.
            buttons: List of button specifications. Each dict should have:
                - 'text': Button text
                - 'command': Button command callback
                - 'state': Optional button state (default: 'normal')

        Returns:
            The created frame containing the buttons.
        """
        frame = tk.Frame(parent)
        for i, btn_spec in enumerate(buttons):
            btn = tk.Button(
                frame,
                text=btn_spec["text"],
                command=btn_spec["command"],
                state=btn_spec.get("state", "normal"),
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)
        return frame

    def create_label_frame(
        self,
        parent: tk.Widget,
        title: str,
        **pack_options: Any,
    ) -> tk.LabelFrame:
        """Create a labeled frame with standard styling.

        Args:
            parent: Parent widget for the frame.
            title: Title of the labeled frame.
            **pack_options: Additional options to pass to pack().

        Returns:
            The created label frame.
        """
        frame = tk.LabelFrame(
            parent,
            text=_(title),
            font=(self.current_theme.font_family, self.current_theme.font_size, "bold"),
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.foreground,
            padx=10,
            pady=10,
        )
        return frame

    def apply_theme(self) -> None:
        """Apply current theme to all widgets."""
        self.current_theme = self.theme_manager.get_current_theme()
        self._setup_window()
        self.update_display()

    def set_theme(self, theme_name: str) -> bool:
        """Change the current theme.

        Args:
            theme_name: Name of theme to apply.

        Returns:
            True if theme was applied successfully.
        """
        if self.theme_manager.set_current_theme(theme_name):
            self.apply_theme()
            return True
        return False

    def play_sound(self, sound_type: str, volume: Optional[float] = None) -> None:
        """Play a sound effect.

        Args:
            sound_type: Type of sound to play.
            volume: Optional volume override.
        """
        if self.sound_manager:
            self.sound_manager.play(sound_type, volume)

    def set_volume(self, volume: float) -> None:
        """Set master sound volume.

        Args:
            volume: Volume level (0.0 to 1.0).
        """
        if self.sound_manager:
            self.sound_manager.set_volume(volume)

    def toggle_sounds(self) -> None:
        """Toggle sound effects on/off."""
        if self.sound_manager:
            enabled = self.sound_manager.is_available()
            self.sound_manager.set_enabled(not enabled)

    def register_shortcut(self, key: str, callback: Callable[[], Any], description: str = "") -> None:
        """Register a keyboard shortcut.

        Args:
            key: Key combination.
            callback: Function to call.
            description: Description of shortcut.
        """
        self.shortcut_manager.register(key, callback, description)

    def show_shortcuts_help(self) -> None:
        """Display keyboard shortcuts help."""
        help_text = self.shortcut_manager.get_shortcuts_help()
        if TKINTER_AVAILABLE:
            from tkinter import messagebox

            messagebox.showinfo(_("keyboard_shortcuts"), help_text)
