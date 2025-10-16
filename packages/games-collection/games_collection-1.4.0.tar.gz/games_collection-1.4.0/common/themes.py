"""Unified theme system for GUI components.

This module provides a centralized theme system that supports dark mode, light mode,
and custom themes across all game GUIs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ThemeColors:
    """Color scheme for a theme.

    Attributes:
        background: Main background color
        foreground: Main foreground/text color
        primary: Primary accent color
        secondary: Secondary accent color
        success: Success state color
        warning: Warning state color
        error: Error state color
        info: Information color
        button_bg: Button background color
        button_fg: Button foreground color
        button_active_bg: Active button background
        button_active_fg: Active button foreground
        border: Border color
        highlight: Highlight color
        canvas_bg: Canvas/game board background
    """

    background: str = "#FFFFFF"
    foreground: str = "#000000"
    primary: str = "#007BFF"
    secondary: str = "#6C757D"
    success: str = "#28A745"
    warning: str = "#FFC107"
    error: str = "#DC3545"
    info: str = "#17A2B8"
    button_bg: str = "#E0E0E0"
    button_fg: str = "#000000"
    button_active_bg: str = "#007BFF"
    button_active_fg: str = "#FFFFFF"
    border: str = "#CCCCCC"
    highlight: str = "#FFD700"
    canvas_bg: str = "#FFFFFF"


@dataclass
class ThemeConfig:
    """Configuration for a complete theme.

    Attributes:
        name: Theme name
        colors: Color scheme
        font_family: Default font family
        font_size: Default font size
        button_relief: Button relief style (flat, raised, sunken, ridge, groove)
        high_contrast: Whether this is a high contrast theme
    """

    name: str
    colors: ThemeColors
    font_family: str = "Helvetica"
    font_size: int = 12
    button_relief: str = "raised"
    high_contrast: bool = False


# Predefined themes
LIGHT_THEME = ThemeConfig(
    name="light",
    colors=ThemeColors(
        background="#FFFFFF",
        foreground="#000000",
        primary="#007BFF",
        secondary="#6C757D",
        success="#28A745",
        warning="#FFC107",
        error="#DC3545",
        info="#17A2B8",
        button_bg="#E0E0E0",
        button_fg="#000000",
        button_active_bg="#007BFF",
        button_active_fg="#FFFFFF",
        border="#CCCCCC",
        highlight="#FFD700",
        canvas_bg="#FFFFFF",
    ),
)

DARK_THEME = ThemeConfig(
    name="dark",
    colors=ThemeColors(
        background="#1E1E1E",
        foreground="#E0E0E0",
        primary="#0D6EFD",
        secondary="#6C757D",
        success="#198754",
        warning="#FFC107",
        error="#DC3545",
        info="#0DCAF0",
        button_bg="#2D2D2D",
        button_fg="#E0E0E0",
        button_active_bg="#0D6EFD",
        button_active_fg="#FFFFFF",
        border="#404040",
        highlight="#FFD700",
        canvas_bg="#2D2D2D",
    ),
)

HIGH_CONTRAST_THEME = ThemeConfig(
    name="high_contrast",
    colors=ThemeColors(
        background="#000000",
        foreground="#FFFFFF",
        primary="#00FFFF",
        secondary="#FFFF00",
        success="#00FF00",
        warning="#FFFF00",
        error="#FF0000",
        info="#00FFFF",
        button_bg="#000000",
        button_fg="#FFFFFF",
        button_active_bg="#FFFFFF",
        button_active_fg="#000000",
        border="#FFFFFF",
        highlight="#FFFF00",
        canvas_bg="#000000",
    ),
    button_relief="ridge",
    high_contrast=True,
)


class ThemeManager:
    """Manager for themes across the application.

    This class provides methods to register, retrieve, and apply themes to GUI components.
    """

    def __init__(self) -> None:
        """Initialize the theme manager with default themes."""
        self._themes: Dict[str, ThemeConfig] = {
            "light": LIGHT_THEME,
            "dark": DARK_THEME,
            "high_contrast": HIGH_CONTRAST_THEME,
        }
        self._current_theme: ThemeConfig = LIGHT_THEME

    def register_theme(self, theme: ThemeConfig) -> None:
        """Register a custom theme.

        Args:
            theme: Theme configuration to register
        """
        self._themes[theme.name] = theme

    def get_theme(self, name: str) -> Optional[ThemeConfig]:
        """Get a theme by name.

        Args:
            name: Theme name

        Returns:
            Theme configuration or None if not found
        """
        return self._themes.get(name)

    def set_current_theme(self, name: str) -> bool:
        """Set the current active theme.

        Args:
            name: Theme name to activate

        Returns:
            True if theme was set, False if theme not found
        """
        theme = self.get_theme(name)
        if theme:
            self._current_theme = theme
            return True
        return False

    def get_current_theme(self) -> ThemeConfig:
        """Get the currently active theme.

        Returns:
            Current theme configuration
        """
        return self._current_theme

    def list_themes(self) -> list[str]:
        """List all available theme names.

        Returns:
            List of theme names
        """
        return list(self._themes.keys())

    def create_custom_theme(
        self,
        name: str,
        base_theme: str = "light",
        color_overrides: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> ThemeConfig:
        """Create a custom theme based on an existing theme.

        Args:
            name: Name for the new theme
            base_theme: Name of base theme to extend
            color_overrides: Dictionary of color overrides
            **kwargs: Additional theme config overrides

        Returns:
            New theme configuration

        Raises:
            ValueError: If base theme doesn't exist
        """
        base = self.get_theme(base_theme)
        if not base:
            raise ValueError(f"Base theme '{base_theme}' not found")

        # Create new colors based on base
        colors_dict = {
            "background": base.colors.background,
            "foreground": base.colors.foreground,
            "primary": base.colors.primary,
            "secondary": base.colors.secondary,
            "success": base.colors.success,
            "warning": base.colors.warning,
            "error": base.colors.error,
            "info": base.colors.info,
            "button_bg": base.colors.button_bg,
            "button_fg": base.colors.button_fg,
            "button_active_bg": base.colors.button_active_bg,
            "button_active_fg": base.colors.button_active_fg,
            "border": base.colors.border,
            "highlight": base.colors.highlight,
            "canvas_bg": base.colors.canvas_bg,
        }

        # Apply color overrides
        if color_overrides:
            colors_dict.update(color_overrides)

        new_colors = ThemeColors(**colors_dict)

        # Create new theme config
        theme_config = {
            "name": name,
            "colors": new_colors,
            "font_family": base.font_family,
            "font_size": base.font_size,
            "button_relief": base.button_relief,
            "high_contrast": base.high_contrast,
        }
        theme_config.update(kwargs)

        new_theme = ThemeConfig(**theme_config)
        self.register_theme(new_theme)
        return new_theme


# Global theme manager instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance.

    Returns:
        Global ThemeManager instance
    """
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
