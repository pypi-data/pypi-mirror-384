"""Animation framework for GUI components.

This module provides utilities for creating smooth animations and transitions
in game GUIs using tkinter.
"""

from __future__ import annotations

import importlib
from typing import Any, Callable, Optional

try:
    import tkinter as tk

    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None  # type: ignore

PYQT_SPEC = importlib.util.find_spec("PyQt5")
if PYQT_SPEC is not None:
    from PyQt5 import QtCore, QtGui, QtWidgets  # type: ignore

    PYQT_AVAILABLE = True
else:
    QtCore = None  # type: ignore[assignment]
    QtGui = None  # type: ignore[assignment]
    QtWidgets = None  # type: ignore[assignment]
    PYQT_AVAILABLE = False


class Animation:
    """Base class for animations.

    Attributes:
        widget: The widget to animate.
        duration: Animation duration in milliseconds.
        callback: Optional callback when animation completes.
        steps: Number of animation steps.
    """

    def __init__(
        self,
        widget: Any,
        duration: int = 300,
        callback: Optional[Callable[[], None]] = None,
        steps: int = 20,
    ) -> None:
        """Initialize an animation.

        Args:
            widget: Widget to animate.
            duration: Duration in milliseconds.
            callback: Optional callback when done.
            steps: Number of animation steps.
        """
        self.widget = widget
        self.duration = duration
        self.callback = callback
        self.steps = steps
        self.step_delay = duration // steps
        self.current_step = 0
        self._cancelled = False

    def start(self) -> None:
        """Start the animation."""
        self._cancelled = False
        self.current_step = 0
        self._animate()

    def cancel(self) -> None:
        """Cancel the animation."""
        self._cancelled = True

    def _animate(self) -> None:
        """Execute one animation step."""
        if self._cancelled:
            return

        if self.current_step < self.steps:
            progress = self.current_step / self.steps
            self._update(progress)
            self.current_step += 1

            if hasattr(self.widget, "after"):
                self.widget.after(self.step_delay, self._animate)
        else:
            self._update(1.0)
            if self.callback:
                self.callback()

    def _update(self, progress: float) -> None:
        """Update animation state for the given progress.

        Args:
            progress: Animation progress from 0.0 to 1.0.
        """
        pass  # Override in subclasses


class FadeAnimation(Animation):
    """Fade in/out animation using widget state changes."""

    def __init__(
        self,
        widget: Any,
        fade_in: bool = True,
        duration: int = 300,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """Initialize a fade animation.

        Args:
            widget: Widget to fade.
            fade_in: True for fade in, False for fade out.
            duration: Duration in milliseconds.
            callback: Optional callback when done.
        """
        super().__init__(widget, duration, callback)
        self.fade_in = fade_in

    def _update(self, progress: float) -> None:
        """Update fade animation."""
        # Note: tkinter doesn't support true opacity, so we simulate with state changes
        # For actual fade, would need to use PIL/Pillow and canvas
        if progress >= 0.5:
            if self.fade_in and hasattr(self.widget, "config"):
                try:
                    self.widget.config(state="normal")
                except Exception:
                    pass


class ColorTransitionAnimation(Animation):
    """Animate color transitions."""

    def __init__(
        self,
        widget: Any,
        from_color: str,
        to_color: str,
        property_name: str = "bg",
        duration: int = 300,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """Initialize a color transition animation.

        Args:
            widget: Widget to animate.
            from_color: Starting color (hex format).
            to_color: Ending color (hex format).
            property_name: Property to animate ('bg', 'fg', etc.).
            duration: Duration in milliseconds.
            callback: Optional callback when done.
        """
        super().__init__(widget, duration, callback)
        self.from_color = self._parse_color(from_color)
        self.to_color = self._parse_color(to_color)
        self.property_name = property_name

    def _parse_color(self, color: str) -> tuple[int, int, int]:
        """Parse hex color to RGB tuple."""
        color = color.lstrip("#")
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore

    def _interpolate_color(self, progress: float) -> str:
        """Interpolate between colors based on progress."""
        r = int(self.from_color[0] + (self.to_color[0] - self.from_color[0]) * progress)
        g = int(self.from_color[1] + (self.to_color[1] - self.from_color[1]) * progress)
        b = int(self.from_color[2] + (self.to_color[2] - self.from_color[2]) * progress)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _update(self, progress: float) -> None:
        """Update color transition."""
        color = self._interpolate_color(progress)
        if hasattr(self.widget, "config"):
            try:
                self.widget.config(**{self.property_name: color})
            except Exception:
                pass


class PulseAnimation(Animation):
    """Pulse animation that highlights a widget."""

    def __init__(
        self,
        widget: Any,
        highlight_color: str = "#FFD700",
        duration: int = 600,
        pulses: int = 2,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """Initialize a pulse animation.

        Args:
            widget: Widget to pulse.
            highlight_color: Color to pulse to.
            duration: Duration in milliseconds.
            pulses: Number of pulses.
            callback: Optional callback when done.
        """
        super().__init__(widget, duration, callback, steps=pulses * 10)
        self.highlight_color = highlight_color
        self.pulses = pulses

        # Store original color
        self.original_bg = None
        if hasattr(widget, "cget"):
            try:
                self.original_bg = widget.cget("bg")
            except Exception:
                self.original_bg = "#FFFFFF"

    def _update(self, progress: float) -> None:
        """Update pulse animation."""
        if not self.original_bg or not hasattr(self.widget, "config"):
            return

        # Calculate pulse using sine wave
        import math

        pulse_progress = math.sin(progress * self.pulses * 2 * math.pi)
        pulse_progress = (pulse_progress + 1) / 2  # Normalize to 0-1

        # Interpolate between original and highlight
        try:
            from_rgb = self._parse_color(self.original_bg)
            to_rgb = self._parse_color(self.highlight_color)

            r = int(from_rgb[0] + (to_rgb[0] - from_rgb[0]) * pulse_progress)
            g = int(from_rgb[1] + (to_rgb[1] - from_rgb[1]) * pulse_progress)
            b = int(from_rgb[2] + (to_rgb[2] - from_rgb[2]) * pulse_progress)

            color = f"#{r:02x}{g:02x}{b:02x}"
            self.widget.config(bg=color)
        except Exception:
            pass

    def _parse_color(self, color: str) -> tuple[int, int, int]:
        """Parse hex color to RGB tuple."""
        color = color.lstrip("#")
        if len(color) == 3:
            color = "".join([c * 2 for c in color])
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore


class SlideAnimation(Animation):
    """Slide widget to a new position."""

    def __init__(
        self,
        widget: Any,
        from_x: int,
        from_y: int,
        to_x: int,
        to_y: int,
        duration: int = 300,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """Initialize a slide animation.

        Args:
            widget: Widget to slide (must be placed with place()).
            from_x: Starting x coordinate.
            from_y: Starting y coordinate.
            to_x: Ending x coordinate.
            to_y: Ending y coordinate.
            duration: Duration in milliseconds.
            callback: Optional callback when done.
        """
        super().__init__(widget, duration, callback)
        self.from_x = from_x
        self.from_y = from_y
        self.to_x = to_x
        self.to_y = to_y

    def _update(self, progress: float) -> None:
        """Update slide animation."""
        x = int(self.from_x + (self.to_x - self.from_x) * progress)
        y = int(self.from_y + (self.to_y - self.from_y) * progress)

        if hasattr(self.widget, "place"):
            try:
                self.widget.place(x=x, y=y)
            except Exception:
                pass


def animate_widget_highlight(widget: Any, duration: int = 600, highlight_color: str = "#FFD700") -> None:
    """Convenience function to highlight a widget with a pulse animation.

    Args:
        widget: Widget to highlight.
        duration: Duration in milliseconds.
        highlight_color: Color to highlight with.
    """
    animation = PulseAnimation(widget, highlight_color=highlight_color, duration=duration)
    animation.start()


def animate_color_transition(widget: Any, to_color: str, duration: int = 300, property_name: str = "bg") -> None:
    """Convenience function to animate a color transition.

    Args:
        widget: Widget to animate.
        to_color: Target color.
        duration: Duration in milliseconds.
        property_name: Property to animate.
    """
    if not hasattr(widget, "cget"):
        return

    try:
        from_color = widget.cget(property_name)
        animation = ColorTransitionAnimation(widget, from_color, to_color, property_name, duration)
        animation.start()
    except Exception:
        pass


def maybe_animate_highlight(
    widget: Any,
    *,
    enable: bool,
    highlight_color: str = "#FFD700",
    duration: int = 600,
) -> None:
    """Animate a widget highlight when animations are enabled.

    Args:
        widget: The widget to highlight.
        enable: Whether animations are currently enabled.
        highlight_color: Color used for the highlight effect.
        duration: Duration of the animation in milliseconds.
    """

    if not enable or widget is None:
        return

    if TKINTER_AVAILABLE and hasattr(widget, "after"):
        animate_widget_highlight(widget, duration=duration, highlight_color=highlight_color)
        return

    if PYQT_AVAILABLE and isinstance(widget, QtWidgets.QWidget):  # type: ignore[union-attr]
        effect = QtWidgets.QGraphicsColorizeEffect(widget)
        effect.setColor(QtGui.QColor(highlight_color))  # type: ignore[arg-type]
        widget.setGraphicsEffect(effect)

        animation = QtCore.QPropertyAnimation(effect, b"strength", widget)  # type: ignore[arg-type]
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setKeyValueAt(0.5, 1.0)
        animation.setEndValue(0.0)

        def _cleanup() -> None:
            try:
                stored = getattr(widget, "_cg_active_animations")
            except AttributeError:
                stored = None
            if stored is not None:
                try:
                    stored.remove(animation)
                except ValueError:
                    pass
                if not stored:
                    delattr(widget, "_cg_active_animations")
            widget.setGraphicsEffect(None)

        animation.finished.connect(_cleanup)  # type: ignore[attr-defined]

        active = getattr(widget, "_cg_active_animations", [])
        active.append(animation)
        setattr(widget, "_cg_active_animations", active)
        deletion_policy = (
            QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped
            if hasattr(QtCore.QAbstractAnimation, "DeletionPolicy")
            else QtCore.QAbstractAnimation.DeleteWhenStopped
        )
        animation.start(deletion_policy)  # type: ignore[attr-defined]
