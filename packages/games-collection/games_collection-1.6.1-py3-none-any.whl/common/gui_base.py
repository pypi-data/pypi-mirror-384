"""Abstract base class and utilities for GUI components.

This module provides a robust foundation for creating graphical user interfaces
for games. It leverages Tkinter for the underlying GUI framework and integrates
various enhancement modules to provide a rich user experience out of the box.

The `BaseGUI` class serves as the core component, offering a standardized
structure for building game interfaces. It includes support for:
- Theming and styling
- Sound effects
- Internationalization (i18n)
- Accessibility features
- Keyboard shortcuts
- Achievements

By subclassing `BaseGUI`, developers can create new game GUIs with minimal
boilerplate, ensuring a consistent look and feel across the entire application.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

try:
    # Attempt to import Tkinter for the GUI framework
    import tkinter as tk
    from tkinter import scrolledtext, ttk

    TKINTER_AVAILABLE = True
except ImportError:
    # If Tkinter is not available, set a flag and create placeholder types
    # to avoid runtime errors and allow for type hinting.
    TKINTER_AVAILABLE = False
    tk = None  # type: ignore
    scrolledtext = None  # type: ignore
    ttk = None  # type: ignore

# Import enhancement modules that provide additional functionality
from common.accessibility import get_accessibility_manager
from common.achievements_registry import get_achievement_registry
from common.animations import maybe_animate_highlight
from common.i18n import _, get_translation_manager
from common.keyboard_shortcuts import get_shortcut_manager
from common.sound_manager import SoundManager, create_sound_manager
from common.themes import get_theme_manager


@dataclass
class GUIConfig:
    """Configuration options for GUI components.

    This data class holds all the settings required to customize the appearance
    and behavior of the GUI. An instance of this class is passed to the
    `BaseGUI` constructor.

    Attributes:
        window_title: The title displayed in the main window's title bar.
        window_width: The initial width of the main window in pixels.
        window_height: The initial height of the main window in pixels.
        background_color: The default background color for the window.
        font_family: The default font family to be used for text elements.
        font_size: The default font size for text elements.
        log_height: The height of the log widget, in lines of text.
        log_width: The width of the log widget, in characters.
        enable_sounds: A flag to enable or disable sound effects.
        enable_animations: A flag to enable or disable UI animations.
        theme_name: The name of the theme to apply to the GUI.
        language: The language code (e.g., "en", "fr") for i18n.
        accessibility_mode: A flag to enable accessibility features like high
                            contrast mode.
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

    This class provides a comprehensive set of common functionalities for
    building game interfaces, including layout management, logging, status
    updates, and integration with various enhancement systems like theming,
    sound, accessibility, i18n, and keyboard shortcuts.

    Subclasses must implement the `build_layout` and `update_display` methods
    to create the specific UI for their game.
    """

    def __init__(self, root: tk.Tk, config: Optional[GUIConfig] = None) -> None:
        """Initialize the base GUI.

        This sets up the main window, initializes all enhancement managers, and
        applies the initial configuration.

        Args:
            root: The root Tkinter window, which serves as the main container
                  for the GUI.
            config: An optional `GUIConfig` object to customize the GUI. If not
                    provided, a default configuration will be used.
        """
        self.root = root
        self.config = config or GUIConfig()

        # Initialize managers for various enhancement systems
        self.theme_manager = get_theme_manager()
        self.sound_manager: Optional[SoundManager] = None
        self.accessibility_manager = get_accessibility_manager()
        self.translation_manager = get_translation_manager()
        self.shortcut_manager = get_shortcut_manager()

        # Apply the initial configuration to the GUI
        self._setup_enhancements()
        self._setup_window()
        self._setup_shortcuts()

        # Enable GUI notifications for achievements
        get_achievement_registry().enable_gui_notifications(self.root)

    def _setup_enhancements(self) -> None:
        """Set up all enhancement systems based on the current configuration."""
        # Set the initial theme
        self.theme_manager.set_current_theme(self.config.theme_name)
        self.current_theme = self.theme_manager.get_current_theme()

        # Set the initial language for internationalization
        self.translation_manager.set_language(self.config.language)

        # Initialize the sound manager if sounds are enabled
        if self.config.enable_sounds:
            self.sound_manager = create_sound_manager(enabled=True)

        # Configure accessibility features if enabled
        if self.config.accessibility_mode:
            self.accessibility_manager.set_high_contrast(True)
            self.accessibility_manager.set_screen_reader(True)

        # Set the root window for the shortcut manager
        self.shortcut_manager.set_root(self.root)

    def _setup_window(self) -> None:
        """Configure the main window with default settings and theme."""
        self.root.title(_(self.config.window_title))
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")

        # Apply theme colors to the main window
        bg_color = self.current_theme.colors.background
        if TKINTER_AVAILABLE:
            self.root.configure(bg=bg_color)

            # Configure ttk styles for themed widgets
            style = ttk.Style()
            # The "clam" theme is used as a base because it is more customizable
            # than the default theme on some platforms.
            style.theme_use("clam")

            # Configure a standard button style using the theme's colors.
            style.configure(
                "TButton",
                background=self.current_theme.colors.button_bg,
                foreground=self.current_theme.colors.button_fg,
                borderwidth=1,
                focuscolor=self.current_theme.colors.primary,
            )
            # Map the "active" state to different colors to provide visual
            # feedback when a button is pressed or hovered over.
            style.map(
                "TButton",
                background=[("active", self.current_theme.colors.button_active_bg)],
                foreground=[("active", self.current_theme.colors.button_active_fg)],
            )

        # Make the main window resizable by default
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

    def _setup_shortcuts(self) -> None:
        """Set up default keyboard shortcuts.

        Subclasses can override this method to register their own custom
        shortcuts.
        """
        pass

    def animate_highlight(self, widget: Any, *, highlight_color: Optional[str] = None, duration: int = 600) -> None:
        """Apply a highlight animation to a widget if animations are enabled.

        This provides a visual cue for events like a correct move or an
        important notification.

        Args:
            widget: The widget to animate.
            highlight_color: An optional color for the highlight. If not
                             provided, the theme's primary color is used.
            duration: The duration of the animation in milliseconds.
        """
        color = highlight_color or getattr(self.current_theme.colors, "accent", self.current_theme.colors.primary)
        maybe_animate_highlight(widget, enable=self.config.enable_animations, highlight_color=color, duration=duration)

    @abstractmethod
    def build_layout(self) -> None:
        """Build the main layout of the GUI.

        This abstract method must be implemented by subclasses to create and
        arrange all the necessary widgets for their specific game interface.
        """
        pass

    @abstractmethod
    def update_display(self) -> None:
        """Update the display to reflect the current game state.

        This abstract method is called whenever the game state changes, and it
        should be implemented by subclasses to update their UI components
        accordingly.
        """
        pass

    def create_header(self, parent: tk.Widget, text: str) -> tk.Label:
        """Create a standard header label with consistent styling.

        Args:
            parent: The parent widget to contain the header.
            text: The text to be displayed in the header.

        Returns:
            The created Tkinter Label widget.
        """
        header = tk.Label(
            parent,
            text=text,
            font=(self.config.font_family, self.config.font_size + 6, "bold"),
            pady=8,
        )
        return header

    def create_status_label(self, parent: tk.Widget, text: str = "") -> tk.Label:
        """Create a standard status label for displaying information.

        Args:
            parent: The parent widget to contain the label.
            text: The initial text to be displayed.

        Returns:
            The created Tkinter Label widget.
        """
        label = tk.Label(
            parent,
            text=text,
            font=(self.config.font_family, self.config.font_size),
        )
        return label

    def create_log_widget(self, parent: tk.Widget) -> scrolledtext.ScrolledText:
        """Create a standard scrolled text widget for logging messages.

        Args:
            parent: The parent widget to contain the log.

        Returns:
            The created ScrolledText widget.
        """
        log = scrolledtext.ScrolledText(
            parent,
            width=self.config.log_width,
            height=self.config.log_height,
            state=tk.DISABLED,  # Start in a read-only state
            wrap=tk.WORD,
            font=("Courier New", self.config.font_size - 1),
        )
        return log

    def log_message(self, log_widget: scrolledtext.ScrolledText, message: str) -> None:
        """Append a message to a log widget.

        The widget is temporarily enabled to add the message and then disabled
        again to maintain a read-only state.

        Args:
            log_widget: The log widget to which the message will be appended.
            message: The message to append.
        """
        # The state of the widget must be temporarily set to NORMAL to allow
        # for insertion of text.
        log_widget.configure(state=tk.NORMAL)
        log_widget.insert(tk.END, message + "\n")
        log_widget.see(tk.END)  # Scroll to the end to show the latest message
        # The state is returned to DISABLED to prevent user interaction.
        log_widget.configure(state=tk.DISABLED)

    def clear_log(self, log_widget: scrolledtext.ScrolledText) -> None:
        """Clear all text from a log widget.

        Args:
            log_widget: The log widget to be cleared.
        """
        log_widget.configure(state=tk.NORMAL)
        log_widget.delete("1.0", tk.END)
        log_widget.configure(state=tk.DISABLED)

    def create_button_frame(
        self,
        parent: tk.Widget,
        buttons: List[Dict[str, Any]],
    ) -> tk.Frame:
        """Create a frame containing multiple buttons.

        This is a convenience method for creating a row of buttons with
        specified text and commands.

        Args:
            parent: The parent widget to contain the button frame.
            buttons: A list of dictionaries, where each dictionary specifies
                     the 'text', 'command', and optional 'state' of a button.

        Returns:
            The created Tkinter Frame containing the buttons.
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

        This is useful for grouping related widgets under a common title.

        Args:
            parent: The parent widget for the frame.
            title: The title to be displayed on the frame's border.
            **pack_options: Additional options to pass to the `pack()` method.

        Returns:
            The created Tkinter LabelFrame.
        """
        frame = tk.LabelFrame(
            parent,
            text=_(title),  # Apply translation to the title
            font=(self.current_theme.font_family, self.current_theme.font_size, "bold"),
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.foreground,
            padx=10,
            pady=10,
        )
        return frame

    def apply_theme(self) -> None:
        """Apply the current theme to all relevant widgets.

        This method reloads the current theme and reapplies it to the window,
        which is useful after a theme has been changed.
        """
        self.current_theme = self.theme_manager.get_current_theme()
        self._setup_window()
        self.update_display()

    def set_theme(self, theme_name: str) -> bool:
        """Change the current theme and apply it to the GUI.

        Args:
            theme_name: The name of the theme to apply.

        Returns:
            True if the theme was applied successfully, False otherwise.
        """
        if self.theme_manager.set_current_theme(theme_name):
            self.apply_theme()
            return True
        return False

    def play_sound(self, sound_type: str, volume: Optional[float] = None) -> None:
        """Play a sound effect if the sound manager is enabled.

        Args:
            sound_type: The type of sound to play (e.g., "click", "win").
            volume: An optional volume override for this specific sound.
        """
        if self.sound_manager:
            self.sound_manager.play(sound_type, volume)

    def set_volume(self, volume: float) -> None:
        """Set the master volume for all sound effects.

        Args:
            volume: The volume level, from 0.0 (muted) to 1.0 (full).
        """
        if self.sound_manager:
            self.sound_manager.set_volume(volume)

    def toggle_sounds(self) -> None:
        """Toggle sound effects on or off."""
        if self.sound_manager:
            enabled = self.sound_manager.is_available()
            self.sound_manager.set_enabled(not enabled)

    def register_shortcut(self, key: str, callback: Callable[[], Any], description: str = "") -> None:
        """Register a keyboard shortcut.

        Args:
            key: The key combination for the shortcut (e.g., "<Control-s>").
            callback: The function to be called when the shortcut is activated.
            description: A brief description of what the shortcut does.
        """
        self.shortcut_manager.register(key, callback, description)

    def show_shortcuts_help(self) -> None:
        """Display a help window showing all registered keyboard shortcuts."""
        help_text = self.shortcut_manager.get_shortcuts_help()
        if TKINTER_AVAILABLE:
            from tkinter import messagebox

            messagebox.showinfo(_("keyboard_shortcuts"), help_text)
