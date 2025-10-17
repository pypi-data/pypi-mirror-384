"""An animation framework for GUI components.

This module provides a set of utilities for creating smooth animations and
transitions in game GUIs. It is designed to be compatible with both `tkinter`
and `PyQt`, providing a consistent interface for animations regardless of the
underlying GUI framework.

The core of the framework is the `Animation` base class, which provides the
basic structure for creating time-based animations. Several concrete animation
classes are provided, including:
- `FadeAnimation`: For fading widgets in and out.
- `ColorTransitionAnimation`: For smoothly transitioning a widget's color.
- `PulseAnimation`: For creating a pulsing highlight effect.
- `SlideAnimation`: For moving a widget from one position to another.

The module also includes convenience functions for common animation tasks, such
as `animate_widget_highlight`, and a `maybe_animate_highlight` function that
handles animations for both `tkinter` and `PyQt` widgets.
"""

from __future__ import annotations

import importlib
from typing import Any, Callable, Optional

# Conditionally import tkinter to avoid hard dependencies.
try:
    import tkinter as tk

    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None  # type: ignore

# Conditionally import PyQt to support animations in PyQt-based GUIs.
PYQT_SPEC = importlib.util.find_spec("PyQt5")
if PYQT_SPEC is not None:
    from PyQt5 import QtCore, QtGui, QtWidgets

    PYQT_AVAILABLE = True
else:
    QtCore = None
    QtGui = None
    QtWidgets = None
    PYQT_AVAILABLE = False


class Animation:
    """A base class for creating animations.

    This class provides the fundamental structure for an animation, including
    duration, steps, and a callback function. Subclasses should override the
    `_update` method to implement the specific animation logic.

    Attributes:
        widget: The widget to be animated.
        duration: The total duration of the animation in milliseconds.
        callback: An optional function to be called when the animation
                  completes.
        steps: The number of steps in the animation. More steps result in a
               smoother animation.
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
            widget: The widget to be animated.
            duration: The duration of the animation in milliseconds.
            callback: An optional function to be called upon completion.
            steps: The number of steps to divide the animation into.
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
        """Cancel the animation if it is currently running."""
        self._cancelled = True

    def _animate(self) -> None:
        """Execute a single step of the animation."""
        if self._cancelled:
            return

        if self.current_step < self.steps:
            progress = self.current_step / self.steps
            self._update(progress)
            self.current_step += 1

            # For tkinter widgets, use `after` to schedule the next step.
            if hasattr(self.widget, "after"):
                self.widget.after(self.step_delay, self._animate)
        else:
            # Ensure the animation finishes at 100% progress.
            self._update(1.0)
            if self.callback:
                self.callback()

    def _update(self, progress: float) -> None:
        """Update the animation state based on the current progress.

        This method should be overridden by subclasses to implement the
        specific visual changes for the animation.

        Args:
            progress: The current progress of the animation, from 0.0 to 1.0.
        """
        pass  # Subclasses must override this method.


class FadeAnimation(Animation):
    """A fade-in/out animation that simulates opacity changes.

    Note: Since `tkinter` does not support true opacity on most widgets, this
    animation simulates a fade by changing the widget's state. For a true
    fade effect, a canvas with image manipulation would be required.
    """

    def __init__(
        self,
        widget: Any,
        fade_in: bool = True,
        duration: int = 300,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """Initialize a fade animation.

        Args:
            widget: The widget to be faded.
            fade_in: If True, the widget will fade in; otherwise, it will fade
                     out.
            duration: The duration of the animation in milliseconds.
            callback: An optional function to be called upon completion.
        """
        super().__init__(widget, duration, callback)
        self.fade_in = fade_in

    def _update(self, progress: float) -> None:
        """Update the fade animation."""
        # This is a simplified implementation. A true fade would require more
        # complex handling of widget visibility or alpha channels.
        if progress >= 0.5:
            if self.fade_in and hasattr(self.widget, "config"):
                try:
                    self.widget.config(state="normal")
                except Exception:
                    pass  # Ignore if the widget doesn't support state changes.


class ColorTransitionAnimation(Animation):
    """An animation for smoothly transitioning between two colors."""

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
            widget: The widget whose color will be animated.
            from_color: The starting color in hexadecimal format (e.g., "#FF0000").
            to_color: The ending color in hexadecimal format.
            property_name: The name of the color property to be animated
                           (e.g., "bg" for background, "fg" for foreground).
            duration: The duration of the animation in milliseconds.
            callback: An optional function to be called upon completion.
        """
        super().__init__(widget, duration, callback)
        self.from_color = self._parse_color(from_color)
        self.to_color = self._parse_color(to_color)
        self.property_name = property_name

    def _parse_color(self, color: str) -> tuple[int, int, int]:
        """Parse a hexadecimal color string into an RGB tuple."""
        color = color.lstrip("#")
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))

    def _interpolate_color(self, progress: float) -> str:
        """Interpolate between the start and end colors based on progress."""
        r = int(self.from_color[0] + (self.to_color[0] - self.from_color[0]) * progress)
        g = int(self.from_color[1] + (self.to_color[1] - self.from_color[1]) * progress)
        b = int(self.from_color[2] + (self.to_color[2] - self.from_color[2]) * progress)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _update(self, progress: float) -> None:
        """Update the color transition."""
        color = self._interpolate_color(progress)
        if hasattr(self.widget, "config"):
            try:
                self.widget.config(**{self.property_name: color})
            except Exception:
                pass  # Ignore if the widget or property is not configurable.


class PulseAnimation(Animation):
    """An animation that creates a pulsing highlight effect on a widget."""

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
            widget: The widget to be pulsed.
            highlight_color: The color to pulse to.
            duration: The total duration of the animation in milliseconds.
            pulses: The number of pulses to perform within the duration.
            callback: An optional function to be called upon completion.
        """
        super().__init__(widget, duration, callback, steps=pulses * 20)
        self.highlight_color = highlight_color
        self.pulses = pulses

        # Store the original background color of the widget.
        self.original_bg = None
        if hasattr(widget, "cget"):
            try:
                self.original_bg = widget.cget("bg")
            except Exception:
                self.original_bg = "#FFFFFF"

    def _update(self, progress: float) -> None:
        """Update the pulse animation."""
        if not self.original_bg or not hasattr(self.widget, "config"):
            return

        # Use a sine wave to create a smooth pulsing effect.
        import math

        pulse_progress = math.sin(progress * self.pulses * 2 * math.pi)
        pulse_progress = (pulse_progress + 1) / 2  # Normalize to a 0-1 range.

        # Interpolate between the original and highlight colors.
        try:
            from_rgb = self._parse_color(self.original_bg)
            to_rgb = self._parse_color(self.highlight_color)

            r = int(from_rgb[0] + (to_rgb[0] - from_rgb[0]) * pulse_progress)
            g = int(from_rgb[1] + (to_rgb[1] - from_rgb[1]) * pulse_progress)
            b = int(from_rgb[2] + (to_rgb[2] - from_rgb[2]) * pulse_progress)

            color = f"#{r:02x}{g:02x}{b:02x}"
            self.widget.config(bg=color)
        except Exception:
            pass  # Ignore errors during color calculation or application.

    def _parse_color(self, color: str) -> tuple[int, int, int]:
        """Parse a hexadecimal color string into an RGB tuple."""
        color = color.lstrip("#")
        if len(color) == 3:
            color = "".join([c * 2 for c in color])
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


class SlideAnimation(Animation):
    """An animation for sliding a widget from one position to another."""

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
            widget: The widget to be slid. It must be placed using the
                    `place()` geometry manager.
            from_x: The starting x-coordinate.
            from_y: The starting y-coordinate.
            to_x: The ending x-coordinate.
            to_y: The ending y-coordinate.
            duration: The duration of the animation in milliseconds.
            callback: An optional function to be called upon completion.
        """
        super().__init__(widget, duration, callback)
        self.from_x = from_x
        self.from_y = from_y
        self.to_x = to_x
        self.to_y = to_y

    def _update(self, progress: float) -> None:
        """Update the slide animation."""
        x = int(self.from_x + (self.to_x - self.from_x) * progress)
        y = int(self.from_y + (self.to_y - self.from_y) * progress)

        if hasattr(self.widget, "place"):
            try:
                self.widget.place(x=x, y=y)
            except Exception:
                pass  # Ignore if the widget cannot be placed.


def animate_widget_highlight(widget: Any, duration: int = 600, highlight_color: str = "#FFD700") -> None:
    """A convenience function to highlight a widget with a pulse animation.

    Args:
        widget: The widget to be highlighted.
        duration: The duration of the animation in milliseconds.
        highlight_color: The color to be used for the highlight.
    """
    animation = PulseAnimation(widget, highlight_color=highlight_color, duration=duration)
    animation.start()


def animate_color_transition(widget: Any, to_color: str, duration: int = 300, property_name: str = "bg") -> None:
    """A convenience function to animate a color transition on a widget.

    Args:
        widget: The widget whose color will be animated.
        to_color: The target color in hexadecimal format.
        duration: The duration of the animation in milliseconds.
        property_name: The name of the color property to be animated.
    """
    if not hasattr(widget, "cget"):
        return

    try:
        from_color = widget.cget(property_name)
        animation = ColorTransitionAnimation(widget, from_color, to_color, property_name, duration)
        animation.start()
    except Exception:
        pass  # Ignore if the color property cannot be retrieved.


def maybe_animate_highlight(
    widget: Any,
    *,
    enable: bool,
    highlight_color: str = "#FFD700",
    duration: int = 600,
) -> None:
    """Animate a widget highlight, but only if animations are enabled.

    This function provides a unified interface for highlighting widgets in
    both `tkinter` and `PyQt` applications.

    Args:
        widget: The widget to be highlighted.
        enable: A flag indicating whether animations are currently enabled.
        highlight_color: The color to be used for the highlight effect.
        duration: The duration of the animation in milliseconds.
    """
    if not enable or widget is None:
        return

    # Handle tkinter widgets
    if TKINTER_AVAILABLE and hasattr(widget, "after"):
        animate_widget_highlight(widget, duration=duration, highlight_color=highlight_color)
        return

    # Handle PyQt widgets
    if PYQT_AVAILABLE and isinstance(widget, QtWidgets.QWidget):
        effect = QtWidgets.QGraphicsColorizeEffect(widget)
        effect.setColor(QtGui.QColor(highlight_color))
        widget.setGraphicsEffect(effect)

        animation = QtCore.QPropertyAnimation(effect, b"strength", widget)
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setKeyValueAt(0.5, 1.0)
        animation.setEndValue(0.0)

        def _cleanup() -> None:
            """Clean up the animation and graphics effect."""
            try:
                stored = getattr(widget, "_cg_active_animations", [])
                if animation in stored:
                    stored.remove(animation)
                if not stored:
                    delattr(widget, "_cg_active_animations")
            finally:
                widget.setGraphicsEffect(None)

        animation.finished.connect(_cleanup)

        # Store the animation object to prevent it from being garbage collected.
        active_animations = getattr(widget, "_cg_active_animations", [])
        active_animations.append(animation)
        setattr(widget, "_cg_active_animations", active_animations)

        # Start the animation with a policy to delete it when stopped.
        deletion_policy = (
            QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped
            if hasattr(QtCore.QAbstractAnimation, "DeletionPolicy")
            else QtCore.QAbstractAnimation.DeleteWhenStopped
        )
        animation.start(deletion_policy)
