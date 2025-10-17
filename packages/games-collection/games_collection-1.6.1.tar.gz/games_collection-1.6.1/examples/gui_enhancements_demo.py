"""This module provides a comprehensive demonstration of the GUI enhancement features.

It creates a sample tkinter application that showcases the integration and usage of:
- Theming: Dynamically switching between light, dark, and high-contrast themes.
- Animations: Simple, non-blocking animations to provide visual feedback.
- Accessibility: Features like high-contrast mode, enhanced focus indicators, and
  screen reader support.
- Internationalization (i18n): Changing the display language on the fly.
- Keyboard Shortcuts: A centralized system for managing and displaying keyboard shortcuts.

This example is intended to be a practical guide for implementing these features
in other game GUIs within the collection.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add the project's root directory to the Python path to ensure module imports work correctly.
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:
    print("Error: tkinter is required to run this GUI demonstration.")
    sys.exit(1)

from common.animations import animate_widget_highlight
from common.gui_base import BaseGUI, GUIConfig
from common.i18n import _  # The gettext function for internationalization.


class GUIEnhancementsDemo(BaseGUI):
    """A demonstration application that showcases all available GUI enhancements."""

    def __init__(self, root: tk.Tk) -> None:
        """Initializes the demo application.

        Args:
            root: The root tkinter window.
        """
        # Configure the GUI with default settings.
        config = GUIConfig(
            window_title="GUI Enhancements Demo",
            window_width=900,
            window_height=700,
            enable_sounds=False,  # Sounds are disabled as no audio files are included.
            enable_animations=True,
            theme_name="light",
            language="en",
            accessibility_mode=False,
        )
        super().__init__(root, config)
        self.build_layout()
        self._setup_shortcuts()  # Set up keyboard shortcuts after the layout is built.

    def build_layout(self) -> None:
        """Constructs the main layout of the GUI."""
        # Clear existing widgets before rebuilding (e.g., when changing themes).
        for widget in self.root.winfo_children():
            widget.destroy()

        # Main container frame, styled with the current theme's background.
        main_frame = tk.Frame(self.root, bg=self.current_theme.colors.background)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Application Title
        title = tk.Label(
            main_frame,
            text=_("GUI Enhancements Demo"),  # Translated title
            font=(self.current_theme.font_family, 24, "bold"),
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.foreground,
        )
        title.pack(pady=(0, 20))

        # Create and pack the different demonstration sections.
        self._create_theme_section(main_frame)
        self._create_animation_section(main_frame)
        self._create_accessibility_section(main_frame)
        self._create_i18n_section(main_frame)
        self._create_shortcut_section(main_frame)

        # Status bar at the bottom.
        self.status_label = tk.Label(
            main_frame,
            text=_("Ready"),
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.info,
            font=(self.current_theme.font_family, 10),
        )
        self.status_label.pack(pady=(20, 0), side=tk.BOTTOM, fill=tk.X)

    def _create_theme_section(self, parent: tk.Frame) -> None:
        """Creates the UI section for demonstrating theme switching."""
        frame = self.create_label_frame(parent, _("Theme System"))
        frame.pack(fill=tk.X, pady=(0, 10))

        button_frame = tk.Frame(frame, bg=self.current_theme.colors.background)
        button_frame.pack(fill=tk.X, pady=5)

        # Create a button for each available theme.
        for theme_name in ["light", "dark", "high_contrast"]:
            btn = tk.Button(
                button_frame,
                text=_(theme_name.replace("_", " ").title()),
                command=lambda t=theme_name: self.change_theme(t),
                bg=self.current_theme.colors.button_bg,
                fg=self.current_theme.colors.button_fg,
                relief=self.current_theme.button_relief,
            )
            btn.pack(side=tk.LEFT, padx=5)
            # Add accessibility features to the button.
            self.accessibility_manager.add_focus_indicator(btn)
            self.accessibility_manager.add_screen_reader_label(btn, _("Switch to {} theme").format(theme_name))

    def _create_animation_section(self, parent: tk.Frame) -> None:
        """Creates the UI section for demonstrating animations."""
        frame = self.create_label_frame(parent, _("Animations"))
        frame.pack(fill=tk.X, pady=(0, 10))

        self.anim_button = tk.Button(
            frame,
            text=_("Click to See Animation"),
            command=self.demonstrate_animation,
            bg=self.current_theme.colors.button_bg,
            fg=self.current_theme.colors.button_fg,
            relief=self.current_theme.button_relief,
            padx=20,
            pady=10,
        )
        self.anim_button.pack(pady=10)
        self.accessibility_manager.add_focus_indicator(self.anim_button)

    def _create_accessibility_section(self, parent: tk.Frame) -> None:
        """Creates the UI section for accessibility controls."""
        frame = self.create_label_frame(parent, _("Accessibility"))
        frame.pack(fill=tk.X, pady=(0, 10))

        # Checkbox to toggle high-contrast mode.
        self.high_contrast_var = tk.BooleanVar(value=self.accessibility_manager.high_contrast)
        high_contrast_check = tk.Checkbutton(
            frame,
            text=_("High Contrast Mode"),
            variable=self.high_contrast_var,
            command=self.toggle_high_contrast,
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.foreground,
            selectcolor=self.current_theme.colors.button_bg,
        )
        high_contrast_check.pack(anchor=tk.W, pady=2)

        # Checkbox to toggle enhanced focus indicators.
        self.focus_var = tk.BooleanVar(value=self.accessibility_manager.focus_indicators)
        focus_check = tk.Checkbutton(
            frame,
            text=_("Enhanced Focus Indicators"),
            variable=self.focus_var,
            command=self.toggle_focus_indicators,
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.foreground,
            selectcolor=self.current_theme.colors.button_bg,
        )
        focus_check.pack(anchor=tk.W, pady=2)

    def _create_i18n_section(self, parent: tk.Frame) -> None:
        """Creates the UI section for internationalization."""
        frame = self.create_label_frame(parent, _("Internationalization"))
        frame.pack(fill=tk.X, pady=(0, 10))

        lang_frame = tk.Frame(frame, bg=self.current_theme.colors.background)
        lang_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            lang_frame,
            text=_("Language:"),
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.foreground,
        ).pack(side=tk.LEFT, padx=5)

        # A combobox to select the language.
        languages = self.translation_manager.get_available_languages()
        self.lang_var = tk.StringVar(value=self.translation_manager.current_language)
        lang_menu = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=languages, state="readonly", width=15)
        lang_menu.pack(side=tk.LEFT, padx=5)
        lang_menu.bind("<<ComboboxSelected>>", lambda e: self.change_language())

        # A label to display translated text.
        self.translated_label = tk.Label(
            frame,
            text=_("This is a translated message."),
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.success,
            font=(self.current_theme.font_family, 12),
        )
        self.translated_label.pack(pady=10)

    def _create_shortcut_section(self, parent: tk.Frame) -> None:
        """Creates the UI section for keyboard shortcuts."""
        frame = self.create_label_frame(parent, _("Keyboard Shortcuts"))
        frame.pack(fill=tk.X, pady=(0, 10))

        help_btn = tk.Button(
            frame,
            text=_("Show Keyboard Shortcuts (F1)"),
            command=self.show_shortcuts_help,
            bg=self.current_theme.colors.button_bg,
            fg=self.current_theme.colors.button_fg,
            relief=self.current_theme.button_relief,
        )
        help_btn.pack(pady=5)
        self.accessibility_manager.add_focus_indicator(help_btn)

    def _setup_shortcuts(self) -> None:
        """Sets up all custom keyboard shortcuts for the application."""
        self.register_shortcut("<F1>", self.show_shortcuts_help, _("Show keyboard shortcuts help"))
        self.register_shortcut("<Control-t>", lambda: self.change_theme("dark"), _("Switch to dark theme"))
        self.register_shortcut("<Control-l>", lambda: self.change_theme("light"), _("Switch to light theme"))
        self.register_shortcut("<Control-a>", self.demonstrate_animation, _("Trigger animation"))
        self.register_shortcut("<Escape>", self.root.quit, _("Quit application"))

    def change_theme(self, theme_name: str) -> None:
        """Switches the application's theme and rebuilds the UI."""
        if self.set_theme(theme_name):
            self.update_status(_("Theme changed to: {}").format(theme_name))
            self.build_layout()  # Rebuild the layout to apply the new theme.
        else:
            self.update_status(_("Failed to change theme to: {}").format(theme_name))

    def demonstrate_animation(self) -> None:
        """Triggers a highlight animation on a button."""
        if self.config.enable_animations:
            animate_widget_highlight(self.anim_button, duration=600, highlight_color=self.current_theme.colors.highlight)
            self.update_status(_("Animation demonstrated!"))
        else:
            self.update_status(_("Animations are currently disabled."))

    def toggle_high_contrast(self) -> None:
        """Toggles the high-contrast accessibility mode."""
        enabled = self.high_contrast_var.get()
        self.accessibility_manager.set_high_contrast(enabled)
        # Automatically switch to the high-contrast theme when enabled.
        self.change_theme("high_contrast" if enabled else "light")
        self.update_status(_("High contrast mode {}.").format(_("enabled") if enabled else _("disabled")))

    def toggle_focus_indicators(self) -> None:
        """Toggles the enhanced focus indicators for accessibility."""
        enabled = self.focus_var.get()
        self.accessibility_manager.set_focus_indicators(enabled)
        self.update_status(_("Enhanced focus indicators {}.").format(_("enabled") if enabled else _("disabled")))

    def change_language(self) -> None:
        """Switches the application's language and rebuilds the UI."""
        lang = self.lang_var.get()
        if self.translation_manager.set_language(lang):
            self.update_status(_("Language changed to: {}").format(lang))
            self.build_layout()  # Rebuild the layout to apply the new language.
        else:
            self.update_status(_("Failed to change language to: {}").format(lang))

    def update_status(self, message: str) -> None:
        """Updates the text in the status bar."""
        if hasattr(self, "status_label"):
            self.status_label.config(text=message)
            self.accessibility_manager.announce(message)  # Announce for screen readers.

    def update_display(self) -> None:
        """Placeholder for display updates, handled by `build_layout` in this demo."""
        pass


def main() -> None:
    """The main entry point for running the demo application."""
    root = tk.Tk()
    _app = GUIEnhancementsDemo(root)

    # Show a welcome message explaining the demo.
    messagebox.showinfo(
        _("Welcome"),
        _("Welcome to the GUI Enhancements Demo!")
        + "\n\n"
        + _("This demo showcases:")
        + "\n• "
        + _("Theme system (light, dark, high contrast)")
        + "\n• "
        + _("Animation effects")
        + "\n• "
        + _("Accessibility features")
        + "\n• "
        + _("Internationalization support")
        + "\n• "
        + _("Keyboard shortcuts (press F1 for help)")
        + "\n\n"
        + _("Experiment with the controls to see the features in action!"),
    )

    root.mainloop()


if __name__ == "__main__":
    main()
