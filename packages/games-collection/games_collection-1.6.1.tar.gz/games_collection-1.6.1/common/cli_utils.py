"""Enhanced CLI utilities for terminal-based games.

This module provides a comprehensive suite of tools for creating rich and
interactive command-line interfaces for games. It includes utilities for:

- **Colors and Themes**: A `Theme` system and `Color` constants for consistent
  and customizable terminal output.
- **ASCII Art**: Pre-designed, colorful ASCII art for banners, victory,
  defeat, and draw screens.
- **Rich Text Formatting**: A `RichText` class for creating styled text, such
  as headers, highlighted messages, and status updates (success, error, etc.).
- **Progress Indicators**: `ProgressBar` and `Spinner` classes to provide
  visual feedback for long-running operations.
- **Interactive Menus**: An `InteractiveMenu` class that supports arrow key
  navigation, with a fallback to a numbered menu for less capable terminals.
- **Command History**: A `CommandHistory` class with support for command
  history navigation (up/down arrows) and basic autocomplete.

These utilities are designed to be easy to use and to degrade gracefully in
environments with limited terminal support.
"""

from __future__ import annotations

import os
import sys
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional

try:
    # Use colorama for cross-platform colored terminal text
    import colorama
    from colorama import Fore, Style

    # Initialize colorama to automatically handle ANSI escape codes
    colorama.init(autoreset=True)
except ImportError:
    # If colorama is not available, provide a fallback implementation with
    # basic ANSI escape codes. This ensures that the utilities can still
    # function, albeit with less robust cross-platform support.
    class _FallbackFore:
        BLACK = "\033[30m"
        RED = "\033[31m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        BLUE = "\033[34m"
        MAGENTA = "\033[35m"
        CYAN = "\033[36m"
        WHITE = "\033[37m"

    class _FallbackStyle:
        RESET_ALL = "\033[0m"
        BRIGHT = "\033[1m"
        NORMAL = "\033[22m"

    Fore = _FallbackFore()  # type: ignore[assignment]
    Style = _FallbackStyle()  # type: ignore[assignment]


# Platform-specific imports for interactive menu navigation
if sys.platform == "win32":
    import msvcrt
else:
    # For Unix-like systems, use termios and tty for raw terminal access
    import select
    import termios
    import tty


class Color(str, Enum):
    """Enumeration of color constants for terminal output.

    This provides a convenient and readable way to specify colors for text.
    """

    BLACK = Fore.BLACK
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    RESET = Style.RESET_ALL


class TextStyle(str, Enum):
    """Enumeration of text style constants for terminal output.

    Allows for applying styles like bold (BRIGHT) to text.
    """

    RESET = Style.RESET_ALL
    BRIGHT = Style.BRIGHT
    DIM = "\033[2m"
    NORMAL = "\033[22m"


@dataclass
class Theme:
    """A data class representing a color theme for CLI elements.

    This allows for consistent and easily customizable styling of the command-
    line interface. Different themes can be created for different moods or
    preferences.
    """

    primary: Color = Color.CYAN
    secondary: Color = Color.YELLOW
    success: Color = Color.GREEN
    error: Color = Color.RED
    warning: Color = Color.YELLOW
    info: Color = Color.BLUE
    text: Color = Color.WHITE
    accent: Color = Color.MAGENTA


# A dictionary of predefined themes that can be easily accessed and used.
THEMES = {
    "default": Theme(),
    "dark": Theme(
        primary=Color.BLUE,
        secondary=Color.CYAN,
        success=Color.GREEN,
        error=Color.RED,
        warning=Color.YELLOW,
        info=Color.MAGENTA,
        text=Color.WHITE,
        accent=Color.CYAN,
    ),
    "light": Theme(
        primary=Color.BLUE,
        secondary=Color.CYAN,
        success=Color.GREEN,
        error=Color.RED,
        warning=Color.YELLOW,
        info=Color.BLUE,
        text=Color.BLACK,
        accent=Color.MAGENTA,
    ),
    "ocean": Theme(
        primary=Color.CYAN,
        secondary=Color.BLUE,
        success=Color.GREEN,
        error=Color.RED,
        warning=Color.YELLOW,
        info=Color.CYAN,
        text=Color.WHITE,
        accent=Color.BLUE,
    ),
    "forest": Theme(
        primary=Color.GREEN,
        secondary=Color.CYAN,
        success=Color.GREEN,
        error=Color.RED,
        warning=Color.YELLOW,
        info=Color.CYAN,
        text=Color.WHITE,
        accent=Color.GREEN,
    ),
}


class ASCIIArt:
    """A collection of colorful ASCII art templates for game states.

    This class provides static methods for generating common game-related
    ASCII art, such as banners and end-game screens.
    """

    @staticmethod
    def banner(text: str, color: Color = Color.CYAN, width: int = 60) -> str:
        """Create a visually appealing banner with the given text.

        Args:
            text: The text to be displayed in the banner.
            color: The color to be used for the banner's border and text.
            width: The width of the banner in characters.

        Returns:
            A formatted string representing the banner.
        """
        border = "=" * width
        padded_text = text.center(width)
        return f"{color}{border}\n{padded_text}\n{border}{Style.RESET_ALL}"

    @staticmethod
    def box(text: str, color: Color = Color.WHITE, padding: int = 1) -> str:
        """Create a decorative box around a block of text.

        Args:
            text: The text to be enclosed in the box.
            color: The color of the box's border.
            padding: The amount of padding to add around the text inside the
                     box.

        Returns:
            A formatted string representing the boxed text.
        """
        lines = text.split("\n")
        max_width = max(len(line) for line in lines)
        width = max_width + 2 * padding

        top = "┌" + "─" * width + "┐"
        bottom = "└" + "─" * width + "┘"
        pad = " " * padding

        boxed_lines = [f"{color}{top}{Style.RESET_ALL}"]
        for line in lines:
            padded = line.ljust(max_width)
            boxed_lines.append(f"{color}│{Style.RESET_ALL}{pad}{padded}{pad}{color}│{Style.RESET_ALL}")
        boxed_lines.append(f"{color}{bottom}{Style.RESET_ALL}")

        return "\n".join(boxed_lines)

    @staticmethod
    def victory(color: Color = Color.YELLOW) -> str:
        """Generate ASCII art for a victory screen.

        Args:
            color: The color of the ASCII art.

        Returns:
            A string containing the victory ASCII art.
        """
        art = """
 ██╗   ██╗██╗ ██████╗████████╗ ██████╗ ██████╗ ██╗   ██╗
 ██║   ██║██║██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝
 ██║   ██║██║██║        ██║   ██║   ██║██████╔╝ ╚████╔╝
 ╚██╗ ██╔╝██║██║        ██║   ██║   ██║██╔══██╗  ╚██╔╝
  ╚████╔╝ ██║╚██████╗   ██║   ╚██████╔╝██║  ██║   ██║
   ╚═══╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝
        """
        return f"{color}{art}{Style.RESET_ALL}"

    @staticmethod
    def defeat(color: Color = Color.RED) -> str:
        """Generate ASCII art for a defeat screen.

        Args:
            color: The color of the ASCII art.

        Returns:
            A string containing the defeat ASCII art.
        """
        art = """
 ██████╗  █████╗ ███╗   ███╗███████╗     ██████╗ ██╗   ██╗███████╗██████╗
██╔════╝ ██╔══██╗████╗ ████║██╔════╝    ██╔═══██╗██║   ██║██╔════╝██╔══██╗
██║  ███╗███████║██╔████╔██║█████╗      ██║   ██║██║   ██║█████╗  ██████╔╝
██║   ██║██╔══██║██║╚██╔╝██║██╔══╝      ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗
╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗    ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝     ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝
        """
        return f"{color}{art}{Style.RESET_ALL}"

    @staticmethod
    def draw(color: Color = Color.CYAN) -> str:
        """Generate ASCII art for a draw or tie screen.

        Args:
            color: The color of the ASCII art.

        Returns:
            A string containing the draw ASCII art.
        """
        art = """
██████╗ ██████╗  █████╗ ██╗    ██╗
██╔══██╗██╔══██╗██╔══██╗██║    ██║
██║  ██║██████╔╝███████║██║ █╗ ██║
██║  ██║██╔══██╗██╔══██║██║███╗██║
██████╔╝██║  ██║██║  ██║╚███╔███╔╝
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝
        """
        return f"{color}{art}{Style.RESET_ALL}"


class RichText:
    """A collection of utilities for creating rich, formatted text.

    This class provides static methods for colorizing text, creating headers,
    and formatting status messages like success, error, and warning notices.
    """

    @staticmethod
    def colorize(text: str, color: Color, style: Optional[TextStyle] = None) -> str:
        """Apply a color and an optional style to a string of text.

        Args:
            text: The text to be colorized.
            color: The color to apply.
            style: An optional text style (e.g., `BRIGHT`).

        Returns:
            The colorized and styled text string.
        """
        style_code = style.value if style else ""
        color_code = color.value if isinstance(color, Color) else color
        return f"{style_code}{color_code}{text}{Style.RESET_ALL}"

    @staticmethod
    def header(text: str, level: int = 1, theme: Theme = THEMES["default"]) -> str:
        """Format a string of text as a header with a specified level.

        Args:
            text: The text of the header.
            level: The header level (1-3), which determines the color and
                   style.
            theme: The color theme to use for styling the header.

        Returns:
            The formatted header string.
        """
        colors = {1: theme.primary, 2: theme.secondary, 3: theme.text}
        color = colors.get(level, theme.text)
        style = TextStyle.BRIGHT if level == 1 else None
        return RichText.colorize(text, color, style)

    @staticmethod
    def highlight(text: str, theme: Theme = THEMES["default"]) -> str:
        """Highlight a string of text to draw attention to it.

        Args:
            text: The text to be highlighted.
            theme: The color theme to use for the highlight color.

        Returns:
            The highlighted text string.
        """
        return RichText.colorize(text, theme.accent, TextStyle.BRIGHT)

    @staticmethod
    def success(text: str, theme: Theme = THEMES["default"]) -> str:
        """Format a string as a success message, with a checkmark icon.

        Args:
            text: The success message.
            theme: The color theme to use.

        Returns:
            The formatted success message.
        """
        return f"{theme.success}✓ {text}{Style.RESET_ALL}"

    @staticmethod
    def error(text: str, theme: Theme = THEMES["default"]) -> str:
        """Format a string as an error message, with a cross icon.

        Args:
            text: The error message.
            theme: The color theme to use.

        Returns:
            The formatted error message.
        """
        return f"{theme.error}✗ {text}{Style.RESET_ALL}"

    @staticmethod
    def warning(text: str, theme: Theme = THEMES["default"]) -> str:
        """Format a string as a warning message, with a warning icon.

        Args:
            text: The warning message.
            theme: The color theme to use.

        Returns:
            The formatted warning message.
        """
        return f"{theme.warning}⚠ {text}{Style.RESET_ALL}"

    @staticmethod
    def info(text: str, theme: Theme = THEMES["default"]) -> str:
        """Format a string as an informational message, with an info icon.

        Args:
            text: The informational message.
            theme: The color theme to use.

        Returns:
            The formatted info message.
        """
        return f"{theme.info}ℹ {text}{Style.RESET_ALL}"


class ProgressBar:
    """A simple, themeable progress bar for indicating loading states.

    This class allows for displaying progress of a task in the terminal by
    rendering a bar that fills up as the task completes.
    """

    def __init__(self, total: int, width: int = 40, theme: Theme = THEMES["default"]):
        """Initialize the progress bar.

        Args:
            total: The total number of steps required for the task to complete.
            width: The width of the progress bar in characters.
            theme: The color theme to use for styling the bar.
        """
        self.total = total
        self.current = 0
        self.width = width
        self.theme = theme

    def update(self, current: Optional[int] = None) -> None:
        """Update the progress bar to a new value.

        Args:
            current: The current progress value. If not provided, the progress
                     is incremented by 1.
        """
        if current is not None:
            self.current = current
        else:
            self.current += 1
        self._render()

    def _render(self) -> None:
        """Render the progress bar to the console."""
        percentage = min(100, int(100 * self.current / self.total))
        filled = int(self.width * self.current / self.total)
        bar = "█" * filled + "░" * (self.width - filled)

        # Use carriage return to overwrite the line
        sys.stdout.write(f"\r{self.theme.primary}[{bar}] {percentage}%{Style.RESET_ALL}")
        sys.stdout.flush()

        if self.current >= self.total:
            # Move to a new line when complete
            sys.stdout.write("\n")
            sys.stdout.flush()

    def complete(self) -> None:
        """Mark the progress as complete and render the final state."""
        self.current = self.total
        self._render()


class Spinner:
    """An animated, themeable spinner for indicating loading states.

    This class is useful for showing that a process is ongoing when the
    progress is indeterminate.
    """

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str = "Loading", theme: Theme = THEMES["default"]):
        """Initialize the spinner.

        Args:
            message: The message to be displayed next to the spinner.
            theme: The color theme to use for styling the spinner.
        """
        self.message = message
        self.theme = theme
        self.frame_index = 0
        self.running = False

    def start(self) -> None:
        """Start the spinner animation.

        Note: In a non-interactive environment, this will only render a
              single frame.
        """
        self.running = True
        self._render()

    def stop(self) -> None:
        """Stop the spinner and clear the line."""
        self.running = False
        # Overwrite the spinner line with spaces
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()

    def _render(self) -> None:
        """Render the current frame of the spinner."""
        frame = self.FRAMES[self.frame_index % len(self.FRAMES)]
        sys.stdout.write(f"\r{self.theme.primary}{frame} {self.message}...{Style.RESET_ALL}")
        sys.stdout.flush()
        self.frame_index += 1

    def tick(self) -> None:
        """Advance the spinner to the next frame.

        This should be called repeatedly in a loop to create the animation.
        """
        if self.running:
            self._render()


class InteractiveMenu:
    """An interactive command-line menu with arrow key navigation.

    This class provides a user-friendly way to present a list of options to
    the user. It supports navigation with up and down arrow keys and falls
    back to a numbered menu in terminals that do not support raw input.
    """

    def __init__(self, title: str, options: list[str], theme: Theme = THEMES["default"]):
        """Initialize the interactive menu.

        Args:
            title: The title to be displayed above the menu.
            options: A list of strings representing the menu options.
            theme: The color theme to use for styling the menu.
        """
        self.title = title
        self.options = options
        self.theme = theme
        self.selected = 0

    def display(self, allow_arrow_keys: bool = True) -> int:
        """Display the menu and wait for the user's selection.

        Args:
            allow_arrow_keys: A flag to enable or disable arrow key
                              navigation. If False, or if the terminal does
                              not support it, a numbered menu is shown.

        Returns:
            The index of the selected option in the `options` list.
        """
        # Fallback to a numbered menu if arrow keys are disabled or not supported
        if not allow_arrow_keys or not self._has_terminal_support():
            return self._display_numbered_menu()

        # Attempt to display the interactive menu with arrow key support
        try:
            return self._display_interactive_menu()
        except Exception:
            # If any error occurs, fallback to the numbered menu
            return self._display_numbered_menu()

    def _has_terminal_support(self) -> bool:
        """Check if the current terminal supports interactive features.

        Returns:
            True if the terminal is interactive and supports raw input,
            False otherwise.
        """
        if not sys.stdin.isatty():
            return False
        if sys.platform == "win32":
            return True
        try:
            # On Unix, check if we can get terminal attributes
            termios.tcgetattr(sys.stdin)
            return True
        except Exception:
            return False

    def _display_numbered_menu(self) -> int:
        """Display a simple numbered menu as a fallback.

        Returns:
            The index of the selected option.
        """
        print(f"\n{self.theme.primary}{self.title}{Style.RESET_ALL}")
        print(f"{self.theme.secondary}{'─' * 40}{Style.RESET_ALL}")

        for i, option in enumerate(self.options, 1):
            print(f"{self.theme.text}{i}. {option}{Style.RESET_ALL}")

        while True:
            try:
                choice = input(f"\n{self.theme.info}Select option (1-{len(self.options)}): {Style.RESET_ALL}").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(self.options):
                    return idx
                print(f"{self.theme.error}Invalid selection. Please try again.{Style.RESET_ALL}")
            except (ValueError, KeyboardInterrupt):
                print(f"\n{self.theme.error}Invalid input. Please enter a number.{Style.RESET_ALL}")

    def _display_interactive_menu(self) -> int:
        """Display the interactive menu, dispatching to the correct platform-
        specific implementation.

        Returns:
            The index of the selected option.
        """
        if sys.platform == "win32":
            return self._display_windows_menu()
        else:
            return self._display_unix_menu()

    def _display_windows_menu(self) -> int:
        """Display and handle the interactive menu on Windows.

        Returns:
            The index of the selected option.
        """
        while True:
            self._render_menu()

            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b"\xe0":  # Arrow key prefix
                    key = msvcrt.getch()
                    if key == b"H":  # Up arrow
                        self.selected = (self.selected - 1) % len(self.options)
                    elif key == b"P":  # Down arrow
                        self.selected = (self.selected + 1) % len(self.options)
                elif key in (b"\r", b"\n"):  # Enter key
                    print("\n")
                    return self.selected

    def _display_unix_menu(self) -> int:
        """Display and handle the interactive menu on Unix-like systems.

        Returns:
            The index of the selected option.
        """
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            # Set the terminal to raw mode to capture key presses immediately
            tty.setraw(fd)

            while True:
                self._render_menu()

                # Wait for a key press
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    ch = sys.stdin.read(1)

                    if ch == "\x1b":  # Escape sequence for arrow keys
                        ch = sys.stdin.read(2)
                        if ch == "[A":  # Up arrow
                            self.selected = (self.selected - 1) % len(self.options)
                        elif ch == "[B":  # Down arrow
                            self.selected = (self.selected + 1) % len(self.options)
                    elif ch in ("\r", "\n"):  # Enter key
                        print("\n")
                        return self.selected
        finally:
            # Restore the original terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _render_menu(self) -> None:
        """Render the current state of the menu to the console."""
        # Clear the screen and move the cursor to the top-left
        sys.stdout.write("\033[H\033[J")

        print(f"{self.theme.primary}{self.title}{Style.RESET_ALL}")
        print(f"{self.theme.secondary}{'─' * 40}{Style.RESET_ALL}\n")

        for i, option in enumerate(self.options):
            if i == self.selected:
                # Highlight the selected option
                print(f"{self.theme.accent}▶ {option}{Style.RESET_ALL}")
            else:
                print(f"{self.theme.text}  {option}{Style.RESET_ALL}")

        print(f"\n{self.theme.info}Use ↑/↓ arrows to navigate, Enter to select{Style.RESET_ALL}")


class CommandHistory:
    """A class for managing command history with autocomplete support.

    This is useful for creating interactive command-line prompts where users
    can recall and reuse previous commands.
    """

    def __init__(self, max_size: int = 100):
        """Initialize the command history.

        Args:
            max_size: The maximum number of commands to store in the history.
        """
        self.history: deque[str] = deque(maxlen=max_size)
        self.position = 0

    def add(self, command: str) -> None:
        """Add a command to the history.

        Args:
            command: The command to be added.
        """
        # Avoid adding duplicate consecutive commands
        if command and (not self.history or command != self.history[-1]):
            self.history.append(command)
        self.position = len(self.history)

    def previous(self) -> Optional[str]:
        """Get the previous command in the history.

        Returns:
            The previous command as a string, or None if at the beginning of
            the history.
        """
        if self.position > 0:
            self.position -= 1
            return self.history[self.position]
        return None

    def next(self) -> Optional[str]:
        """Get the next command in the history.

        Returns:
            The next command as a string, or an empty string if at the end of
            the history.
        """
        if self.position < len(self.history) - 1:
            self.position += 1
            return self.history[self.position]
        elif self.position == len(self.history) - 1:
            self.position = len(self.history)
            return ""
        return None

    def search(self, prefix: str) -> list[str]:
        """Search the history for commands that match a given prefix.

        Args:
            prefix: The prefix to search for.

        Returns:
            A list of matching commands.
        """
        return [cmd for cmd in self.history if cmd.startswith(prefix)]

    def autocomplete(self, partial: str, candidates: Iterable[str]) -> Optional[str]:
        """Provide an autocomplete suggestion for a partial command.

        Args:
            partial: The partial command entered by the user.
            candidates: A list of all possible valid commands.

        Returns:
            The completed command if there is a unique match, or a common
            prefix if there are multiple matches. Returns None if there is
            no match.
        """
        matches = [cmd for cmd in candidates if cmd.startswith(partial)]

        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            # If multiple matches, find the common prefix
            common = os.path.commonprefix(matches)
            if len(common) > len(partial):
                return common
        return None


def clear_screen() -> None:
    """Clear the terminal screen in a platform-independent way."""
    os.system("cls" if sys.platform == "win32" else "clear")


def get_terminal_size() -> tuple[int, int]:
    """Get the size of the terminal window.

    Returns:
        A tuple containing the width and height of the terminal in characters.
        Falls back to a default size of (80, 24) if the size cannot be
        determined.
    """
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except OSError:
        return 80, 24  # Default size if detection fails
