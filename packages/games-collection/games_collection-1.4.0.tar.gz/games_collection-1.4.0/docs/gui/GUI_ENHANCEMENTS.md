# GUI Enhancements

This document describes the GUI enhancement features available in the common module.

## Overview

The GUI enhancements provide a unified system for:

- **Theme System**: Dark mode, light mode, high contrast, and custom themes
- **Sound Effects**: Cross-platform sound manager with volume controls
- **Animations**: Smooth transitions and effects for GUI elements
- **Accessibility**: High contrast modes, screen reader support, focus indicators
- **Internationalization (i18n)**: Multi-language support with translation system
- **Responsive Layouts**: Automatic window resizing and layout adaptation
- **Keyboard Shortcuts**: Centralized shortcut management and help system

## Features

### 1. Theme System (`common/themes.py`)

Provides a unified theming system with predefined themes and custom theme support.

#### Built-in Themes

- **Light Theme**: Traditional light color scheme
- **Dark Theme**: Modern dark color scheme
- **High Contrast Theme**: Accessibility-focused high contrast colors

#### Usage

```python
from common.themes import get_theme_manager

# Get theme manager
theme_mgr = get_theme_manager()

# Set theme
theme_mgr.set_current_theme("dark")

# Get current theme
theme = theme_mgr.get_current_theme()
print(f"Background: {theme.colors.background}")
print(f"Foreground: {theme.colors.foreground}")

# Create custom theme
custom = theme_mgr.create_custom_theme(
    "my_theme",
    base_theme="light",
    color_overrides={"primary": "#FF0000"}
)

# List available themes
themes = theme_mgr.list_themes()
```

#### Theme Configuration

Each theme has the following color properties:

- `background` - Main background color
- `foreground` - Main text/foreground color
- `primary` - Primary accent color
- `secondary` - Secondary accent color
- `success` - Success state color
- `warning` - Warning state color
- `error` - Error state color
- `info` - Information color
- `button_bg` - Button background
- `button_fg` - Button foreground
- `button_active_bg` - Active button background
- `button_active_fg` - Active button foreground
- `border` - Border color
- `highlight` - Highlight color
- `canvas_bg` - Canvas/game board background

### 2. Sound Manager (`common/sound_manager.py`)

Cross-platform sound effects system using pygame.mixer (optional dependency).

#### Features

- Automatic sound file loading from directory
- Volume control (master and per-sound)
- Enable/disable sounds
- Graceful fallback when pygame not available
- Support for WAV and MP3 formats

#### Usage

```python
from common.sound_manager import create_sound_manager

# Create sound manager
sound_mgr = create_sound_manager(
    sounds_dir="path/to/sounds",
    enabled=True,
    volume=1.0
)

# Play sound
sound_mgr.play("card_play", volume=0.8)

# Control volume
sound_mgr.set_volume(0.5)
print(f"Volume: {sound_mgr.get_volume()}")

# Toggle sounds
sound_mgr.set_enabled(False)

# Stop sounds
sound_mgr.stop()  # Stop all sounds
sound_mgr.stop("card_play")  # Stop specific sound

# List available sounds
sounds = sound_mgr.list_sounds()
```

#### Sound File Organization

Place sound files in a dedicated directory:

```
sounds/
├── card_play.wav
├── win.wav
├── lose.wav
├── click.wav
└── error.wav
```

### 3. Animation Framework (`common/animations.py`)

Provides smooth animations and transitions for GUI elements.

#### Available Animations

- `ColorTransitionAnimation` - Smooth color transitions
- `PulseAnimation` - Pulsing highlight effect
- `SlideAnimation` - Slide widgets to new positions
- `FadeAnimation` - Fade in/out effects

#### Usage

```python
from common.animations import (
    animate_widget_highlight,
    animate_color_transition,
    PulseAnimation
)

# Quick highlight pulse
animate_widget_highlight(button, duration=600)

# Color transition
animate_color_transition(label, to_color="#FF0000", duration=300)

# Custom pulse animation
pulse = PulseAnimation(
    widget,
    highlight_color="#FFD700",
    duration=600,
    pulses=2
)
pulse.start()
```

### 4. Accessibility Features (`common/accessibility.py`)

Provides accessibility support for users with disabilities.

#### Features

- High contrast mode support
- Screen reader annotations
- Enhanced focus indicators
- Keyboard navigation
- Tooltips for screen readers

#### Usage

```python
from common.accessibility import (
    get_accessibility_manager,
    create_accessible_button
)

# Get accessibility manager
access_mgr = get_accessibility_manager()

# Enable features
access_mgr.set_high_contrast(True)
access_mgr.set_screen_reader(True)
access_mgr.set_focus_indicators(True)

# Apply to widgets
access_mgr.apply_high_contrast(widget)
access_mgr.add_focus_indicator(button)
access_mgr.add_screen_reader_label(button, "Click to start game")

# Enable keyboard navigation
access_mgr.enable_keyboard_navigation(root)

# Announce messages
access_mgr.announce("Game started")

# Create accessible widgets
button = create_accessible_button(
    parent,
    text="New Game",
    command=start_game,
    accessible_label="Start a new game"
)
```

### 5. Internationalization (i18n) (`common/i18n.py`)

Multi-language support with translation system.

#### Features

- Translation management
- Language switching
- Format parameter support
- Fallback to default language
- Translation file persistence

#### Usage

```python
from common.i18n import (
    get_translation_manager,
    _,
    set_language
)

# Get translation manager
i18n_mgr = get_translation_manager()

# Translate text (shorthand)
text = _("new_game")
text_with_params = _("greeting", name="Player")

# Set language
set_language("es")  # Spanish
set_language("fr")  # French

# Add custom translations
i18n_mgr.add_translation("es", "new_game", "Nuevo Juego")
i18n_mgr.add_translation("es", "greeting", "Hola {name}!")

# Get available languages
languages = i18n_mgr.get_available_languages()

# Save translations to file
i18n_mgr.save_translations("es")
```

#### Default Translations

The system includes default English translations for common UI elements:

- `ok`, `cancel`, `yes`, `no`
- `save`, `load`, `quit`, `new_game`
- `settings`, `help`, `about`, `close`
- `player`, `score`, `turn`, `winner`
- `game_over`, `your_turn`, `thinking`
- `volume`, `theme`, `language`, `difficulty`
- And many more...

### 6. Keyboard Shortcuts (`common/keyboard_shortcuts.py`)

Centralized keyboard shortcut management.

#### Features

- Global shortcut registration
- Enable/disable shortcuts
- Default shortcuts for common actions
- Formatted help text
- Category-based organization

#### Usage

```python
from common.keyboard_shortcuts import (
    get_shortcut_manager,
    register_shortcut
)

# Get shortcut manager
shortcut_mgr = get_shortcut_manager()
shortcut_mgr.set_root(root)  # Set tkinter root

# Register shortcuts
def new_game():
    print("New game started")

shortcut_mgr.register("<Control-n>", new_game, "New Game")
shortcut_mgr.register("<Control-q>", quit_game, "Quit")

# Register default shortcuts
shortcuts = {
    "new_game": new_game,
    "quit": quit_game,
    "undo": undo_move,
    "redo": redo_move,
    "help": show_help,
}
shortcut_mgr.register_default_shortcuts(shortcuts)

# Enable/disable shortcuts
shortcut_mgr.disable("<Control-n>")
shortcut_mgr.enable("<Control-n>")

# Get help text
help_text = shortcut_mgr.get_shortcuts_help()
print(help_text)
```

#### Default Shortcuts

The system registers these default shortcuts:

- `Ctrl+N` - New Game
- `Ctrl+Q` / `Alt+F4` - Quit
- `Ctrl+S` - Save Game
- `Ctrl+O` - Load Game
- `Ctrl+Z` - Undo Move
- `Ctrl+Y` / `Ctrl+Shift+Z` - Redo Move
- `Ctrl+H` - Show Hint
- `Ctrl+T` - Toggle Theme
- `F11` - Toggle Fullscreen
- `F1` - Show Help
- `Ctrl+,` - Open Settings

### 7. Enhanced BaseGUI (`common/gui_base.py`)

The `BaseGUI` class has been enhanced to integrate all these features.

#### New Configuration Options

```python
from common.gui_base import GUIConfig

config = GUIConfig(
    window_title="My Game",
    window_width=800,
    window_height=600,
    enable_sounds=True,
    enable_animations=True,
    theme_name="dark",
    language="en",
    accessibility_mode=False,
)
```

#### Enhanced Methods

```python
class MyGameGUI(BaseGUI):
    def __init__(self, root):
        super().__init__(root, config)

    def _setup_shortcuts(self):
        """Override to add custom shortcuts."""
        self.register_shortcut("<Space>", self.make_move, "Make Move")

    def update_display(self):
        """Update display with theme colors."""
        self.canvas.config(bg=self.current_theme.colors.canvas_bg)

# Usage
root = tk.Tk()
gui = MyGameGUI(root)

# Change theme
gui.set_theme("dark")

# Play sound
gui.play_sound("card_play", volume=0.8)

# Control volume
gui.set_volume(0.5)
gui.toggle_sounds()

# Show shortcuts help
gui.show_shortcuts_help()
```

## Integration Example

Here's a complete example integrating all features:

```python
import tkinter as tk
from common.gui_base import BaseGUI, GUIConfig
from common import _

class MyGameGUI(BaseGUI):
    def __init__(self, root):
        config = GUIConfig(
            window_title="my_game",  # Will be translated
            enable_sounds=True,
            enable_animations=True,
            theme_name="dark",
            language="en",
            accessibility_mode=False,
        )
        super().__init__(root, config)
        self.build_layout()

    def build_layout(self):
        """Build GUI layout."""
        # Header with translated text
        header = self.create_header(self.root, _("my_game"))
        header.pack(pady=10)

        # Game button with theme colors
        self.game_button = tk.Button(
            self.root,
            text=_("new_game"),
            command=self.start_game,
            bg=self.current_theme.colors.button_bg,
            fg=self.current_theme.colors.button_fg,
        )
        self.game_button.pack(pady=10)

        # Add accessibility features
        self.accessibility_manager.add_focus_indicator(self.game_button)
        self.accessibility_manager.add_screen_reader_label(
            self.game_button,
            _("new_game")
        )

    def _setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        self.register_shortcut("<Control-n>", self.start_game, "New Game")
        self.register_shortcut("<F1>", self.show_help, "Show Help")

    def start_game(self):
        """Start a new game."""
        # Play sound
        self.play_sound("game_start")

        # Animate button
        from common.animations import animate_widget_highlight
        animate_widget_highlight(self.game_button)

        # Announce for screen readers
        self.accessibility_manager.announce(_("game_started"))

    def show_help(self):
        """Show help dialog."""
        self.show_shortcuts_help()

    def update_display(self):
        """Update display based on game state."""
        # Apply theme colors to widgets
        self.game_button.config(
            bg=self.current_theme.colors.button_bg,
            fg=self.current_theme.colors.button_fg,
        )

# Run the GUI
if __name__ == "__main__":
    root = tk.Tk()
    gui = MyGameGUI(root)
    root.mainloop()
```

## Testing

All GUI enhancements include comprehensive tests in `tests/test_gui_enhancements.py`:

```bash
# Run tests
pytest tests/test_gui_enhancements.py -v

# Run specific test class
pytest tests/test_gui_enhancements.py::TestThemes -v
```

## Requirements

### Core Requirements

- Python 3.9+
- tkinter (usually included with Python)

### Optional Requirements

- `pygame>=2.0` - For sound effects

Install optional requirements:

```bash
pip install pygame
```

## Best Practices

1. **Theme Consistency**: Always use theme colors from `self.current_theme.colors` instead of hardcoded colors.

1. **Sound Management**: Initialize sound manager with proper sound directory and handle graceful degradation.

1. **Accessibility**: Always add screen reader labels and focus indicators to interactive elements.

1. **Internationalization**: Use `_()` function for all user-facing text to support translation.

1. **Keyboard Shortcuts**: Register shortcuts in `_setup_shortcuts()` method and provide descriptions.

1. **Responsive Design**: Use grid layout with weight configuration for responsive behavior.

## Migration Guide

To migrate existing GUIs to use these enhancements:

1. **Update imports**:

   ```python
   from common.gui_base import BaseGUI, GUIConfig
   from common import _
   ```

1. **Update GUIConfig**:

   ```python
   config = GUIConfig(
       # ... existing config
       enable_sounds=True,
       theme_name="light",
   )
   ```

1. **Replace hardcoded colors** with theme colors:

   ```python
   # Before
   button.config(bg="#FFFFFF", fg="#000000")

   # After
   button.config(
       bg=self.current_theme.colors.button_bg,
       fg=self.current_theme.colors.button_fg,
   )
   ```

1. **Wrap UI text** in translation function:

   ```python
   # Before
   label = tk.Label(root, text="New Game")

   # After
   label = tk.Label(root, text=_("new_game"))
   ```

1. **Add shortcuts** in `_setup_shortcuts()`:

   ```python
   def _setup_shortcuts(self):
       self.register_shortcut("<Control-n>", self.new_game, "New Game")
   ```

## See Also

- [Theme System Documentation](themes.py)
- [Sound Manager Documentation](sound_manager.py)
- [Accessibility Features Documentation](accessibility.py)
- [i18n Documentation](i18n.py)
- [Keyboard Shortcuts Documentation](keyboard_shortcuts.py)
- [Animation Framework Documentation](animations.py)
