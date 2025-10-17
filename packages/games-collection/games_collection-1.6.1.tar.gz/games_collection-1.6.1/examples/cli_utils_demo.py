"""This module provides a comprehensive demonstration of the `common.cli_utils` package.

It individually showcases each component of the CLI enhancement toolkit,
explaining its purpose and showing it in action. This script is intended to be run
directly to see the visual output of each feature.

The demonstrations include:
- `ASCIIArt`: For creating banners, boxes, and other decorative text art.
- `RichText`: For applying colors, styles, and semantic formatting to text.
- `ProgressBar` and `Spinner`: For visualizing progress and loading states.
- `InteractiveMenu`: For creating user-friendly, navigable console menus.
- `CommandHistory`: For managing input history and providing autocomplete.
- `THEMES`: For applying consistent color schemes across UI components.
- Utility functions like `get_terminal_size`.
"""

from __future__ import annotations

import time

from common.cli_utils import THEMES, ASCIIArt, Color, CommandHistory, InteractiveMenu, ProgressBar, RichText, Spinner, get_terminal_size


def demo_ascii_art() -> None:
    """Demonstrates the various ASCII art generation capabilities."""
    print("\n" + "=" * 60)
    print("1. ASCII ART DEMONSTRATION")
    print("=" * 60 + "\n")

    # `ASCIIArt.banner` is great for titles and welcome messages.
    print(ASCIIArt.banner("Welcome to the Demo", Color.CYAN, width=60))
    print()

    # `ASCIIArt.box` can be used to frame important information.
    print(ASCIIArt.box("This is a message enclosed in a decorative box.\nIt supports multiple lines.", Color.YELLOW, padding=2))
    print()

    # Pre-defined art for common game states.
    print("Victory Art:")
    print(ASCIIArt.victory(Color.GREEN))
    print()

    print("Defeat Art:")
    print(ASCIIArt.defeat(Color.RED))
    print()

    print("Draw Art:")
    print(ASCIIArt.draw(Color.CYAN))
    print()


def demo_rich_text() -> None:
    """Demonstrates various text formatting and styling options."""
    print("\n" + "=" * 60)
    print("2. RICH TEXT FORMATTING DEMONSTRATION")
    print("=" * 60 + "\n")

    # `RichText.header` helps create a visual hierarchy.
    print(RichText.header("Main Header (Level 1)", level=1))
    print(RichText.header("Sub-Header (Level 2)", level=2))
    print(RichText.header("Minor Header (Level 3)", level=3))
    print()

    # `RichText.highlight` is used to draw attention to specific words.
    print("This is " + RichText.highlight("important text") + " within a sentence.")
    print()

    # Semantic methods for conveying status.
    print(RichText.success("Operation completed successfully!"))
    print(RichText.error("An error occurred during the process."))
    print(RichText.warning("This action is not recommended."))
    print(RichText.info("Here is some useful information for the user."))
    print()

    # `RichText.colorize` provides direct access to terminal colors.
    print("Direct colorization examples:")
    print(RichText.colorize("This text is red.", Color.RED))
    print(RichText.colorize("This text is green.", Color.GREEN))
    print(RichText.colorize("This text is blue.", Color.BLUE))
    print()


def demo_progress_indicators() -> None:
    """Demonstrates visual feedback for long-running tasks."""
    print("\n" + "=" * 60)
    print("3. PROGRESS INDICATORS DEMONSTRATION")
    print("=" * 60 + "\n")

    # `ProgressBar` is for tasks with a known number of steps.
    print("Progress Bar:")
    # It can be styled with a theme.
    bar = ProgressBar(total=20, width=40, theme=THEMES["ocean"])
    for i in range(21):
        bar.update(i)
        time.sleep(0.05)
    print("\n")

    # `Spinner` is for tasks of indeterminate length.
    print("Spinner (runs for 2 seconds):")
    spinner = Spinner(message="Processing data...", theme=THEMES["forest"])
    spinner.start()
    time.sleep(2)
    spinner.stop()
    print("Processing complete!")
    print()


def demo_interactive_menu() -> None:
    """Demonstrates a navigable, interactive menu.

    Note: This demo simulates the selection programmatically to avoid blocking
    the script. In a real application, `menu.display()` would wait for user input.
    """
    print("\n" + "=" * 60)
    print("4. INTERACTIVE MENU DEMONSTRATION")
    print("=" * 60 + "\n")

    options = [
        "Start New Game",
        "Load Saved Game",
        "View Statistics",
        "Settings",
        "Exit",
    ]

    # The menu is created with a title, options, and a theme.
    menu = InteractiveMenu("Main Menu", options, theme=THEMES["dark"])
    print("An interactive menu would be displayed here.")
    print("Use arrow keys to navigate and Enter to select.")
    print(f"Menu Title: {menu.title}")
    for i, option in enumerate(menu.options):
        print(f"  [{i+1}] {option}")
    print()

    # Simulate selecting the third option ("View Statistics").
    selected_option = options[2]
    print(f"Simulating selection of '{selected_option}'...")
    print(f"\nUser selected: {selected_option}")
    print()


def demo_command_history() -> None:
    """Demonstrates command history tracking and autocomplete functionality."""
    print("\n" + "=" * 60)
    print("5. COMMAND HISTORY & AUTOCOMPLETE DEMONSTRATION")
    print("=" * 60 + "\n")

    history = CommandHistory(max_size=10)
    print(f"CommandHistory created with max size {history.max_size}.")

    # Populate the history with some example commands.
    commands_to_add = ["start game", "stop game", "save game", "load game", "help", "quit"]
    print("Adding commands to history:")
    for cmd in commands_to_add:
        history.add(cmd)
        print(f"  - Added: '{cmd}'")
    print()

    # `previous()` and `next()` allow navigation through the history.
    print("Navigating history backward:")
    print(f"  Previous: {history.previous()}")  # Expected: 'quit'
    print(f"  Previous: {history.previous()}")  # Expected: 'help'
    print("\nNavigating history forward:")
    print(f"  Next: {history.next()}")  # Expected: 'quit'
    print()

    # `search()` finds past commands matching a prefix.
    print("Searching for commands starting with 's':")
    results = history.search("s")
    for result in results:
        print(f"  - Found: '{result}'")
    print()

    # `autocomplete()` suggests a completion from a list of candidates.
    candidates = ["start", "stop", "status", "settings", "save", "load", "help", "quit"]
    print("Autocomplete examples:")
    print(f"  - 'st' -> '{history.autocomplete('st', candidates)}'")
    print(f"  - 'sav' -> '{history.autocomplete('sav', candidates)}'")
    print(f"  - 'q' -> '{history.autocomplete('q', candidates)}'")
    print()


def demo_themes() -> None:
    """Demonstrates the available color themes."""
    print("\n" + "=" * 60)
    print("6. THEME SUPPORT DEMONSTRATION")
    print("=" * 60 + "\n")

    print("The `THEMES` dictionary provides pre-defined color schemes for UI components.\n")

    for theme_name, theme in THEMES.items():
        print(f"Theme: {theme_name.upper()}")
        print(f"  - Primary:   {RichText.colorize('■■■■■', theme.primary)}")
        print(f"  - Secondary: {RichText.colorize('■■■■■', theme.secondary)}")
        print(f"  - Success:   {RichText.colorize('■■■■■', theme.success)}")
        print(f"  - Error:     {RichText.colorize('■■■■■', theme.error)}")
        print(f"  - Warning:   {RichText.colorize('■■■■■', theme.warning)}")
        print(f"  - Info:      {RichText.colorize('■■■■■', theme.info)}")
        print()


def demo_utility_functions() -> None:
    """Demonstrates miscellaneous utility functions."""
    print("\n" + "=" * 60)
    print("7. UTILITY FUNCTIONS DEMONSTRATION")
    print("=" * 60 + "\n")

    # `get_terminal_size()` is useful for responsive CLI design.
    width, height = get_terminal_size()
    print(f"Detected terminal size: {width} columns x {height} lines.")
    print()

    # `clear_screen()` is also available but not called here to preserve the demo output.
    print("The `clear_screen()` function can be used to clear the terminal window.")
    print()


def main() -> None:
    """Runs all CLI utility demonstrations in sequence."""
    print(ASCIIArt.banner("CLI Utils Demo", Color.CYAN, width=60))
    print()
    print(RichText.info("This script showcases the features of the `cli_utils` module."))
    print(RichText.info("Press Enter to advance to the next demo, or Ctrl+C to exit."))
    print()

    try:
        # Define the sequence of demonstrations.
        demos = {
            "ASCII Art": demo_ascii_art,
            "Rich Text Formatting": demo_rich_text,
            "Progress Indicators": demo_progress_indicators,
            "Interactive Menu": demo_interactive_menu,
            "Command History": demo_command_history,
            "Themes": demo_themes,
            "Utility Functions": demo_utility_functions,
        }

        # Run each demo, pausing for user input.
        for name, func in demos.items():
            func()
            input(f"--- Press Enter to continue to the '{name}' demo ---")

        print("\n" + ASCIIArt.banner("Demo Complete!", Color.GREEN, width=60))
        print()
        print(RichText.success("All features have been demonstrated successfully!"))

    except (KeyboardInterrupt, EOFError):
        print("\n\n" + RichText.warning("Demo interrupted by user."))
        print(RichText.info("Thank you for trying the CLI utils demo!"))


if __name__ == "__main__":
    main()
