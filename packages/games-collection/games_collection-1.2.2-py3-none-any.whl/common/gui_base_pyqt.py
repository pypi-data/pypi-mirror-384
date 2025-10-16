"""PyQt5-based base class and utilities for GUI components.

This module provides reusable GUI components and a common interface for
game GUIs, reducing code duplication and providing consistent behavior.
This is a PyQt5 implementation that mirrors the tkinter-based gui_base.py
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont, QKeySequence
    from PyQt5.QtWidgets import QFrame, QLabel, QMainWindow, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

    PYQT5_AVAILABLE = True

    # Create a combined metaclass to resolve metaclass conflict
    # This allows BaseGUI to work with both ABC and QWidget
    class CombinedMeta(type(QWidget), ABCMeta):  # type: ignore
        """Metaclass combining Qt's metaclass with ABCMeta."""

        pass

except ImportError:
    PYQT5_AVAILABLE = False
    # Create placeholder types for type hints
    QMainWindow = None  # type: ignore
    QWidget = None  # type: ignore
    QLabel = None  # type: ignore
    CombinedMeta = ABCMeta  # type: ignore

# Import enhancement modules
from common.accessibility import get_accessibility_manager
from common.animations import maybe_animate_highlight
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


class BaseGUI(metaclass=CombinedMeta):
    """Abstract base class for game GUIs using PyQt5.

    This class provides common functionality for building game interfaces
    including layout management, logging, status updates, theming, sound,
    accessibility, i18n, and keyboard shortcuts.

    Note: Uses CombinedMeta to resolve metaclass conflict when inheriting
    from both BaseGUI and QWidget.
    """

    def __init__(self, root: Optional[QMainWindow] = None, config: Optional[GUIConfig] = None) -> None:
        """Initialize the base GUI.

        Args:
            root: The root PyQt5 main window. If None, creates a QWidget.
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

        # Set shortcut manager root (PyQt5 version uses QWidget instead of Tk)
        # Note: Shortcuts will need to be registered differently in PyQt5

    def _setup_window(self) -> None:
        """Configure the main window with default settings."""
        if self.root is not None:
            self.root.setWindowTitle(_(self.config.window_title))
            self.root.resize(self.config.window_width, self.config.window_height)

            # Apply theme colors
            bg_color = self.current_theme.colors.background
            if PYQT5_AVAILABLE:
                self.root.setStyleSheet(f"background-color: {bg_color};")

    def _setup_shortcuts(self) -> None:
        """Set up default keyboard shortcuts."""
        # Subclasses can override this to add custom shortcuts
        pass

    def animate_highlight(self, widget: Any, *, highlight_color: Optional[str] = None, duration: int = 600) -> None:
        """Apply a highlight animation to ``widget`` when animations are enabled.

        Args:
            widget: The widget to animate.
            highlight_color: Optional override for the highlight colour. Defaults to the theme's primary colour.
            duration: Duration of the animation in milliseconds.
        """

        color = highlight_color or getattr(self.current_theme.colors, "accent", self.current_theme.colors.primary)
        maybe_animate_highlight(widget, enable=self.config.enable_animations, highlight_color=color, duration=duration)

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

    def create_header(self, parent: QWidget, text: str) -> QLabel:
        """Create a standard header label.

        Args:
            parent: Parent widget for the header.
            text: Text to display in the header.

        Returns:
            The created label widget.
        """
        header = QLabel(text, parent)
        font = QFont(self.config.font_family, self.config.font_size + 6, QFont.Weight.Bold)
        header.setFont(font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setContentsMargins(0, 8, 0, 8)
        return header

    def create_status_label(self, parent: QWidget, text: str = "") -> QLabel:
        """Create a standard status label.

        Args:
            parent: Parent widget for the label.
            text: Initial text to display.

        Returns:
            The created label widget.
        """
        label = QLabel(text, parent)
        font = QFont(self.config.font_family, self.config.font_size)
        label.setFont(font)
        return label

    def create_log_widget(self, parent: QWidget) -> QTextEdit:
        """Create a standard log widget.

        Args:
            parent: Parent widget for the log.

        Returns:
            The created text edit widget.
        """
        log = QTextEdit(parent)
        log.setReadOnly(True)
        font = QFont("Courier New", self.config.font_size - 2)
        log.setFont(font)
        # Set approximate height based on log_height (characters to pixels)
        log.setFixedHeight(self.config.log_height * 20)
        return log

    def log_message(self, log_widget: QTextEdit, message: str) -> None:
        """Append a message to the log widget.

        Args:
            log_widget: The log widget to append to.
            message: The message to append.
        """
        log_widget.append(message)
        # Auto-scroll to bottom
        scrollbar = log_widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_log(self, log_widget: QTextEdit) -> None:
        """Clear all text from the log widget.

        Args:
            log_widget: The log widget to clear.
        """
        log_widget.clear()

    def create_button_frame(
        self,
        parent: QWidget,
        buttons: List[Dict[str, Any]],
    ) -> QWidget:
        """Create a frame with buttons.

        Args:
            parent: Parent widget for the button frame.
            buttons: List of button configurations, each with 'text' and 'command' keys.

        Returns:
            The created frame widget.
        """
        frame = QFrame(parent)
        layout = QVBoxLayout()

        for btn_config in buttons:
            btn = QPushButton(btn_config["text"], frame)
            btn.clicked.connect(btn_config["command"])
            layout.addWidget(btn)

        frame.setLayout(layout)
        return frame

    def create_label_frame(self, parent: QWidget, text: str) -> QFrame:
        """Create a labeled frame (group box).

        Args:
            parent: Parent widget for the frame.
            text: Label text for the frame.

        Returns:
            The created frame widget.
        """
        from PyQt5.QtWidgets import QGroupBox

        frame = QGroupBox(text, parent)
        return frame

    def apply_theme(self) -> None:
        """Apply the current theme to the GUI."""
        if self.root is None:
            return

        theme = self.current_theme
        stylesheet = f"""
            QWidget {{
                background-color: {theme.colors.background};
                color: {theme.colors.text};
                font-family: {theme.font_family};
                font-size: {theme.font_size}pt;
            }}
            QPushButton {{
                background-color: {theme.colors.button_bg};
                color: {theme.colors.button_fg};
                border: 1px solid {theme.colors.primary};
                padding: 5px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.button_active_bg};
            }}
            QLabel {{
                color: {theme.colors.text};
            }}
        """
        self.root.setStyleSheet(stylesheet)

    def set_theme(self, theme_name: str) -> bool:
        """Set a new theme.

        Args:
            theme_name: Name of the theme to set.

        Returns:
            True if theme was set successfully, False otherwise.
        """
        success = self.theme_manager.set_current_theme(theme_name)
        if success:
            self.current_theme = self.theme_manager.get_current_theme()
            self.apply_theme()
        return success

    def play_sound(self, sound_type: str, volume: Optional[float] = None) -> None:
        """Play a sound effect.

        Args:
            sound_type: Type of sound to play.
            volume: Optional volume level (0.0 to 1.0).
        """
        if self.sound_manager:
            self.sound_manager.play_sound(sound_type, volume)

    def set_volume(self, volume: float) -> None:
        """Set the volume level.

        Args:
            volume: Volume level (0.0 to 1.0).
        """
        if self.sound_manager:
            self.sound_manager.set_volume(volume)

    def toggle_sounds(self) -> None:
        """Toggle sound effects on/off."""
        if self.sound_manager:
            self.sound_manager.toggle_sounds()

    def register_shortcut(self, key: str, callback: Callable[[], Any], description: str = "") -> None:
        """Register a keyboard shortcut.

        Args:
            key: Key sequence (e.g., 'Ctrl+N').
            callback: Function to call when shortcut is triggered.
            description: Description of the shortcut.
        """
        # Note: PyQt5 shortcuts work differently than tkinter
        # This is a simplified version
        if self.root is not None and PYQT5_AVAILABLE:
            from PyQt5.QtWidgets import QShortcut

            shortcut = QShortcut(QKeySequence(key), self.root)
            shortcut.activated.connect(callback)

    def show_shortcuts_help(self) -> None:
        """Show a dialog with available keyboard shortcuts."""
        if PYQT5_AVAILABLE:
            QMessageBox.information(
                self.root,
                _("Keyboard Shortcuts"),
                _("Press F1 to see available shortcuts.\n\nCommon shortcuts:\nCtrl+N: New Game\nCtrl+Q: Quit"),
            )


__all__ = ["BaseGUI", "GUIConfig", "PYQT5_AVAILABLE"]
