"""A unified theme system for GUI components.

This module provides a centralized and extensible theme system that allows for
consistent styling across all game GUIs. It supports predefined themes like
"light," "dark," and "high_contrast," and makes it easy to create and register
custom themes.

The core components are:
- `ThemeColors`: A data class that defines the color palette for a theme.
- `ThemeConfig`: A data class that encapsulates the entire configuration for a
  theme, including colors, fonts, and other style attributes.
- `ThemeManager`: A singleton class that manages all available themes,
  including registering new themes, setting the current theme, and retrieving
  theme configurations.

The `get_theme_manager` function provides global access to the `ThemeManager`
instance, ensuring that all parts of the application can access the same set
of themes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Optional


@dataclass
class ThemeColors:
    """A data class representing the color scheme for a theme.

    Each attribute corresponds to a specific UI element, allowing for detailed
    customization of the application's appearance.

    Attributes:
        background: The main background color of the application.
        foreground: The main color for text and other foreground elements.
        primary: The primary accent color, used for important UI elements.
        secondary: The secondary accent color, used for less prominent
                   elements.
        success: The color used to indicate a successful operation.
        warning: The color used to indicate a warning.
        error: The color used to indicate an error.
        info: The color used for informational messages.
        button_bg: The background color for buttons.
        button_fg: The foreground (text) color for buttons.
        button_active_bg: The background color for buttons when they are
                          active or hovered over.
        button_active_fg: The foreground color for active buttons.
        border: The color for borders around widgets.
        highlight: The color used to highlight selected items or text.
        canvas_bg: The background color for game boards or canvases.
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
    """A data class for the complete configuration of a theme.

    This class combines a `ThemeColors` object with other style attributes,
    such as font settings and button styles, to provide a comprehensive
    definition of a theme.

    Attributes:
        name: The unique name of the theme (e.g., "light", "dark").
        colors: A `ThemeColors` object defining the color palette.
        font_family: The default font family for the theme.
        font_size: The default font size for the theme.
        button_relief: The relief style for buttons (e.g., "flat", "raised").
        high_contrast: A flag indicating whether this is a high-contrast
                       theme, which can be used for accessibility purposes.
    """

    name: str
    colors: ThemeColors
    font_family: str = "Helvetica"
    font_size: int = 12
    button_relief: str = "raised"
    high_contrast: bool = False


# Predefined theme configurations that can be used out of the box.
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
    """A manager for handling themes across the application.

    This class provides a centralized system for registering, retrieving, and
    applying themes to GUI components, ensuring a consistent look and feel.
    """

    def __init__(self) -> None:
        """Initialize the theme manager with the default themes."""
        self._themes: Dict[str, ThemeConfig] = {
            "light": LIGHT_THEME,
            "dark": DARK_THEME,
            "high_contrast": HIGH_CONTRAST_THEME,
        }
        self._current_theme: ThemeConfig = LIGHT_THEME

    def register_theme(self, theme: ThemeConfig) -> None:
        """Register a new custom theme.

        Args:
            theme: The `ThemeConfig` object to be registered.
        """
        self._themes[theme.name] = theme

    def get_theme(self, name: str) -> Optional[ThemeConfig]:
        """Get a theme by its name.

        Args:
            name: The name of the theme to retrieve.

        Returns:
            The `ThemeConfig` object if found, otherwise `None`.
        """
        return self._themes.get(name)

    def set_current_theme(self, name: str) -> bool:
        """Set the current active theme for the application.

        Args:
            name: The name of the theme to be activated.

        Returns:
            True if the theme was successfully set, False if the theme was
            not found.
        """
        theme = self.get_theme(name)
        if theme:
            self._current_theme = theme
            return True
        return False

    def get_current_theme(self) -> ThemeConfig:
        """Get the currently active theme.

        Returns:
            The `ThemeConfig` object for the current theme.
        """
        return self._current_theme

    def list_themes(self) -> list[str]:
        """Get a list of the names of all available themes.

        Returns:
            A list of theme names.
        """
        return list(self._themes.keys())

    def create_custom_theme(
        self,
        name: str,
        base_theme: str = "light",
        color_overrides: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> ThemeConfig:
        """Create a new custom theme by extending an existing one.

        This allows for easy creation of new themes by only specifying the
        attributes that need to be changed from a base theme.

        Args:
            name: The name for the new theme.
            base_theme: The name of the base theme to extend.
            color_overrides: A dictionary of color attributes to override.
            **kwargs: Additional theme configuration attributes to override
                      (e.g., `font_size`, `button_relief`).

        Returns:
            The newly created `ThemeConfig` object.

        Raises:
            ValueError: If the specified base theme does not exist.
        """
        base = self.get_theme(base_theme)
        if not base:
            raise ValueError(f"Base theme '{base_theme}' not found")

        # Create a new color configuration based on the base theme
        colors_dict = asdict(base.colors)
        if color_overrides:
            colors_dict.update(color_overrides)
        new_colors = ThemeColors(**colors_dict)

        # Create a new theme configuration, inheriting from the base theme
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


# A global instance of the ThemeManager to ensure a single source of truth
# for theme management throughout the application.
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get the global singleton instance of the `ThemeManager`.

    This function ensures that a single instance of the `ThemeManager` is
    used throughout the application, providing a consistent state for themes.

    Returns:
        The global `ThemeManager` instance.
    """
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
