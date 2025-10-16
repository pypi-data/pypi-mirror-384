"""Accessibility features for GUI components.

This module provides accessibility support including high contrast modes,
screen reader annotations, and keyboard navigation helpers.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

try:
    import tkinter as tk

    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None  # type: ignore


class AccessibilityManager:
    """Manager for accessibility features.

    Attributes:
        high_contrast: Whether high contrast mode is enabled.
        screen_reader: Whether screen reader support is enabled.
        focus_indicators: Whether to show enhanced focus indicators.
    """

    def __init__(
        self,
        high_contrast: bool = False,
        screen_reader: bool = False,
        focus_indicators: bool = True,
    ) -> None:
        """Initialize accessibility manager.

        Args:
            high_contrast: Enable high contrast mode.
            screen_reader: Enable screen reader support.
            focus_indicators: Enable enhanced focus indicators.
        """
        self.high_contrast = high_contrast
        self.screen_reader = screen_reader
        self.focus_indicators = focus_indicators
        self._focus_styles: Dict[Any, Dict[str, Any]] = {}

    def apply_high_contrast(self, widget: Any) -> None:
        """Apply high contrast styling to a widget.

        Args:
            widget: Widget to apply high contrast to.
        """
        if not self.high_contrast or not hasattr(widget, "config"):
            return

        try:
            # High contrast colors
            widget.config(
                bg="#000000",
                fg="#FFFFFF",
                highlightbackground="#FFFFFF",
                highlightcolor="#FFFF00",
                highlightthickness=2,
            )
        except Exception:
            # Some widgets don't support all options
            pass

    def add_focus_indicator(self, widget: Any, style: Optional[Dict[str, Any]] = None) -> None:
        """Add enhanced focus indicator to a widget.

        Args:
            widget: Widget to add focus indicator to.
            style: Optional custom style dict.
        """
        if not self.focus_indicators or not TKINTER_AVAILABLE:
            return

        default_style = {
            "highlightbackground": "#0000FF",
            "highlightcolor": "#0000FF",
            "highlightthickness": 3,
        }

        if style:
            default_style.update(style)

        # Store original style
        if hasattr(widget, "cget"):
            try:
                self._focus_styles[widget] = {
                    "highlightbackground": widget.cget("highlightbackground"),
                    "highlightcolor": widget.cget("highlightcolor"),
                    "highlightthickness": widget.cget("highlightthickness"),
                }
            except Exception:
                pass

        def on_focus_in(event):
            """Handle focus in event."""
            if hasattr(widget, "config"):
                try:
                    widget.config(**default_style)
                except Exception:
                    pass

        def on_focus_out(event):
            """Handle focus out event."""
            if widget in self._focus_styles and hasattr(widget, "config"):
                try:
                    widget.config(**self._focus_styles[widget])
                except Exception:
                    pass

        if hasattr(widget, "bind"):
            widget.bind("<FocusIn>", on_focus_in)
            widget.bind("<FocusOut>", on_focus_out)

    def add_screen_reader_label(self, widget: Any, label: str) -> None:
        """Add screen reader label to a widget.

        Args:
            widget: Widget to label.
            label: Label text for screen readers.
        """
        if not self.screen_reader:
            return

        # Set tooltip or accessible name
        # Note: tkinter doesn't have native screen reader support,
        # but we can add tooltips and window titles
        if hasattr(widget, "configure"):
            try:
                # Try to set accessible name (may not work on all platforms)
                widget.configure(takefocus=True)
            except Exception:
                pass

        # Create tooltip on hover
        self._create_tooltip(widget, label)

    def _create_tooltip(self, widget: Any, text: str) -> None:
        """Create a tooltip for a widget.

        Args:
            widget: Widget to add tooltip to.
            text: Tooltip text.
        """
        if not TKINTER_AVAILABLE:
            return

        tooltip = None

        def show_tooltip(event):
            """Show tooltip on hover."""
            nonlocal tooltip
            if tooltip:
                return

            x, y, _, _ = widget.bbox("insert") if hasattr(widget, "bbox") else (0, 0, 0, 0)
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20

            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")

            label = tk.Label(
                tooltip,
                text=text,
                background="#FFFFE0",
                foreground="#000000",
                relief="solid",
                borderwidth=1,
                font=("Helvetica", 10),
                padx=5,
                pady=3,
            )
            label.pack()

        def hide_tooltip(event):
            """Hide tooltip."""
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None

        if hasattr(widget, "bind"):
            widget.bind("<Enter>", show_tooltip)
            widget.bind("<Leave>", hide_tooltip)

    def enable_keyboard_navigation(self, root_widget: Any) -> None:
        """Enable enhanced keyboard navigation.

        Args:
            root_widget: Root widget to enable navigation on.
        """
        if not TKINTER_AVAILABLE or not hasattr(root_widget, "bind_all"):
            return

        def focus_next(event):
            """Focus next widget on Tab."""
            event.widget.tk_focusNext().focus()
            return "break"

        def focus_prev(event):
            """Focus previous widget on Shift+Tab."""
            event.widget.tk_focusPrev().focus()
            return "break"

        root_widget.bind_all("<Tab>", focus_next)
        root_widget.bind_all("<Shift-Tab>", focus_prev)

    def announce(self, message: str) -> None:
        """Announce a message for screen readers.

        Args:
            message: Message to announce.
        """
        if not self.screen_reader:
            return

        # Print to console as fallback
        # Real screen reader integration would use platform-specific APIs
        print(f"[Screen Reader]: {message}")

    def set_high_contrast(self, enabled: bool) -> None:
        """Enable or disable high contrast mode.

        Args:
            enabled: Whether to enable high contrast.
        """
        self.high_contrast = enabled

    def set_screen_reader(self, enabled: bool) -> None:
        """Enable or disable screen reader support.

        Args:
            enabled: Whether to enable screen reader.
        """
        self.screen_reader = enabled

    def set_focus_indicators(self, enabled: bool) -> None:
        """Enable or disable focus indicators.

        Args:
            enabled: Whether to enable focus indicators.
        """
        self.focus_indicators = enabled


# Global accessibility manager
_accessibility_manager: Optional[AccessibilityManager] = None


def get_accessibility_manager() -> AccessibilityManager:
    """Get the global accessibility manager.

    Returns:
        Global AccessibilityManager instance.
    """
    global _accessibility_manager
    if _accessibility_manager is None:
        _accessibility_manager = AccessibilityManager()
    return _accessibility_manager


def create_accessible_button(
    parent: Any,
    text: str,
    command: Any,
    accessible_label: Optional[str] = None,
    **kwargs,
) -> Any:
    """Create an accessible button with proper labels and focus.

    Args:
        parent: Parent widget.
        text: Button text.
        command: Button command.
        accessible_label: Optional screen reader label.
        **kwargs: Additional button options.

    Returns:
        Created button widget.
    """
    if not TKINTER_AVAILABLE:
        return None

    button = tk.Button(parent, text=text, command=command, **kwargs)

    # Add accessibility features
    manager = get_accessibility_manager()
    manager.add_focus_indicator(button)

    if accessible_label or text:
        manager.add_screen_reader_label(button, accessible_label or text)

    return button


def create_accessible_label(parent: Any, text: str, **kwargs) -> Any:
    """Create an accessible label.

    Args:
        parent: Parent widget.
        text: Label text.
        **kwargs: Additional label options.

    Returns:
        Created label widget.
    """
    if not TKINTER_AVAILABLE:
        return None

    label = tk.Label(parent, text=text, **kwargs)

    # Add accessibility features
    manager = get_accessibility_manager()
    if manager.screen_reader:
        manager.add_screen_reader_label(label, text)

    return label
