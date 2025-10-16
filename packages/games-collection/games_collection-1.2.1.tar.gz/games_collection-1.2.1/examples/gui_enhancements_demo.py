"""Demonstration of GUI enhancements.

This example shows how to use themes, sounds, animations, accessibility,
internationalization, and keyboard shortcuts in a game GUI.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:
    print("Error: tkinter is required for this demo")
    sys.exit(1)

from common.animations import animate_widget_highlight
from common.gui_base import BaseGUI, GUIConfig
from common.i18n import _


class GUIEnhancementsDemo(BaseGUI):
    """Demo application showing all GUI enhancements."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the demo application.

        Args:
            root: Root tkinter window.
        """
        config = GUIConfig(
            window_title="GUI Enhancements Demo",
            window_width=900,
            window_height=700,
            enable_sounds=False,  # No sound files yet
            enable_animations=True,
            theme_name="light",
            language="en",
            accessibility_mode=False,
        )
        super().__init__(root, config)
        self.build_layout()

    def build_layout(self) -> None:
        """Build the demo GUI layout."""
        # Main container with padding
        main_frame = tk.Frame(self.root, bg=self.current_theme.colors.background)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        title = tk.Label(
            main_frame,
            text="GUI Enhancements Demo",
            font=(self.current_theme.font_family, 24, "bold"),
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.foreground,
        )
        title.pack(pady=(0, 20))

        # Create sections
        self._create_theme_section(main_frame)
        self._create_animation_section(main_frame)
        self._create_accessibility_section(main_frame)
        self._create_i18n_section(main_frame)
        self._create_shortcut_section(main_frame)

        # Status bar
        self.status_label = tk.Label(
            main_frame,
            text="Ready",
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.info,
            font=(self.current_theme.font_family, 10),
        )
        self.status_label.pack(pady=(20, 0))

    def _create_theme_section(self, parent: tk.Frame) -> None:
        """Create theme control section.

        Args:
            parent: Parent frame.
        """
        frame = self.create_label_frame(parent, "Theme System")
        frame.pack(fill=tk.X, pady=(0, 10))

        # Theme buttons
        themes = ["light", "dark", "high_contrast"]
        button_frame = tk.Frame(frame, bg=self.current_theme.colors.background)
        button_frame.pack(fill=tk.X, pady=5)

        for theme_name in themes:
            btn = tk.Button(
                button_frame,
                text=theme_name.replace("_", " ").title(),
                command=lambda t=theme_name: self.change_theme(t),
                bg=self.current_theme.colors.button_bg,
                fg=self.current_theme.colors.button_fg,
                relief=self.current_theme.button_relief,
            )
            btn.pack(side=tk.LEFT, padx=5)

            # Add accessibility features
            self.accessibility_manager.add_focus_indicator(btn)
            self.accessibility_manager.add_screen_reader_label(btn, f"Switch to {theme_name} theme")

    def _create_animation_section(self, parent: tk.Frame) -> None:
        """Create animation demo section.

        Args:
            parent: Parent frame.
        """
        frame = self.create_label_frame(parent, "Animations")
        frame.pack(fill=tk.X, pady=(0, 10))

        # Animation demo button
        self.anim_button = tk.Button(
            frame,
            text="Click to See Animation",
            command=self.demonstrate_animation,
            bg=self.current_theme.colors.button_bg,
            fg=self.current_theme.colors.button_fg,
            relief=self.current_theme.button_relief,
            padx=20,
            pady=10,
        )
        self.anim_button.pack(pady=10)

        # Add accessibility
        self.accessibility_manager.add_focus_indicator(self.anim_button)

    def _create_accessibility_section(self, parent: tk.Frame) -> None:
        """Create accessibility controls section.

        Args:
            parent: Parent frame.
        """
        frame = self.create_label_frame(parent, "Accessibility")
        frame.pack(fill=tk.X, pady=(0, 10))

        # High contrast toggle
        self.high_contrast_var = tk.BooleanVar(value=self.accessibility_manager.high_contrast)
        high_contrast_check = tk.Checkbutton(
            frame,
            text="High Contrast Mode",
            variable=self.high_contrast_var,
            command=self.toggle_high_contrast,
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.foreground,
            selectcolor=self.current_theme.colors.button_bg,
        )
        high_contrast_check.pack(anchor=tk.W, pady=2)

        # Focus indicators toggle
        self.focus_var = tk.BooleanVar(value=self.accessibility_manager.focus_indicators)
        focus_check = tk.Checkbutton(
            frame,
            text="Enhanced Focus Indicators",
            variable=self.focus_var,
            command=self.toggle_focus_indicators,
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.foreground,
            selectcolor=self.current_theme.colors.button_bg,
        )
        focus_check.pack(anchor=tk.W, pady=2)

    def _create_i18n_section(self, parent: tk.Frame) -> None:
        """Create internationalization section.

        Args:
            parent: Parent frame.
        """
        frame = self.create_label_frame(parent, "Internationalization")
        frame.pack(fill=tk.X, pady=(0, 10))

        # Language selector
        lang_frame = tk.Frame(frame, bg=self.current_theme.colors.background)
        lang_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            lang_frame,
            text="Language:",
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.foreground,
        ).pack(side=tk.LEFT, padx=5)

        languages = self.translation_manager.get_available_languages()
        self.lang_var = tk.StringVar(value=self.translation_manager.current_language)

        lang_menu = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=languages,
            state="readonly",
            width=15,
        )
        lang_menu.pack(side=tk.LEFT, padx=5)
        lang_menu.bind("<<ComboboxSelected>>", lambda e: self.change_language())

        # Sample translated text
        self.translated_label = tk.Label(
            frame,
            text=_("ok"),
            bg=self.current_theme.colors.background,
            fg=self.current_theme.colors.success,
            font=(self.current_theme.font_family, 12),
        )
        self.translated_label.pack(pady=10)

    def _create_shortcut_section(self, parent: tk.Frame) -> None:
        """Create keyboard shortcuts section.

        Args:
            parent: Parent frame.
        """
        frame = self.create_label_frame(parent, "Keyboard Shortcuts")
        frame.pack(fill=tk.X, pady=(0, 10))

        help_btn = tk.Button(
            frame,
            text="Show Keyboard Shortcuts (F1)",
            command=self.show_shortcuts_help,
            bg=self.current_theme.colors.button_bg,
            fg=self.current_theme.colors.button_fg,
            relief=self.current_theme.button_relief,
        )
        help_btn.pack(pady=5)

    def _setup_shortcuts(self) -> None:
        """Set up custom keyboard shortcuts."""
        # Demo shortcuts
        self.register_shortcut("<F1>", self.show_shortcuts_help, "Show keyboard shortcuts")
        self.register_shortcut("<Control-t>", lambda: self.change_theme("dark"), "Toggle to dark theme")
        self.register_shortcut("<Control-l>", lambda: self.change_theme("light"), "Toggle to light theme")
        self.register_shortcut("<Control-a>", self.demonstrate_animation, "Demonstrate animation")
        self.register_shortcut("<Escape>", self.root.quit, "Quit application")

    def change_theme(self, theme_name: str) -> None:
        """Change the current theme.

        Args:
            theme_name: Name of theme to apply.
        """
        if self.set_theme(theme_name):
            self.update_status(f"Theme changed to: {theme_name}")
            # Re-apply colors to all widgets
            self.build_layout()
        else:
            self.update_status(f"Failed to change theme to: {theme_name}")

    def demonstrate_animation(self) -> None:
        """Demonstrate animation effect."""
        if self.config.enable_animations:
            animate_widget_highlight(self.anim_button, duration=600, highlight_color=self.current_theme.colors.highlight)
            self.update_status("Animation demonstrated!")
        else:
            self.update_status("Animations are disabled")

    def toggle_high_contrast(self) -> None:
        """Toggle high contrast mode."""
        enabled = self.high_contrast_var.get()
        self.accessibility_manager.set_high_contrast(enabled)

        if enabled:
            # Switch to high contrast theme
            self.change_theme("high_contrast")
        else:
            # Switch back to light theme
            self.change_theme("light")

        self.update_status(f"High contrast mode: {'enabled' if enabled else 'disabled'}")

    def toggle_focus_indicators(self) -> None:
        """Toggle focus indicators."""
        enabled = self.focus_var.get()
        self.accessibility_manager.set_focus_indicators(enabled)
        self.update_status(f"Focus indicators: {'enabled' if enabled else 'disabled'}")

    def change_language(self) -> None:
        """Change the current language."""
        lang = self.lang_var.get()
        if self.translation_manager.set_language(lang):
            self.update_status(f"Language changed to: {lang}")
            # Update translated text
            self.translated_label.config(text=_("ok"))
        else:
            self.update_status(f"Failed to change language to: {lang}")

    def update_status(self, message: str) -> None:
        """Update status bar message.

        Args:
            message: Status message to display.
        """
        if hasattr(self, "status_label"):
            self.status_label.config(text=message)
            self.accessibility_manager.announce(message)

    def update_display(self) -> None:
        """Update display to reflect current theme."""
        # This is called when theme changes
        # In a real application, you'd update all widget colors here
        pass


def main() -> None:
    """Run the demo application."""
    root = tk.Tk()
    _app = GUIEnhancementsDemo(root)  # noqa: F841 - intentionally unused, sets up GUI

    # Show welcome message
    messagebox.showinfo(
        "Welcome",
        "Welcome to the GUI Enhancements Demo!\n\n"
        "This demo showcases:\n"
        "• Theme system (light, dark, high contrast)\n"
        "• Animation effects\n"
        "• Accessibility features\n"
        "• Internationalization support\n"
        "• Keyboard shortcuts (press F1 for help)\n\n"
        "Try switching themes and using keyboard shortcuts!",
    )

    root.mainloop()


if __name__ == "__main__":
    main()
