"""Demo showcasing the enhanced CLI utilities.

This example demonstrates all the CLI enhancement features including:
- Colorful ASCII art for game states
- Rich text formatting with visual hierarchy
- Progress bars and spinners for loading states
- Interactive command-line menus with arrow key navigation
- Command history and autocomplete
- Terminal themes and custom color schemes
"""

from __future__ import annotations

import time

from common.cli_utils import THEMES, ASCIIArt, Color, CommandHistory, InteractiveMenu, ProgressBar, RichText, Spinner, get_terminal_size


def demo_ascii_art() -> None:
    """Demonstrate ASCII art features."""
    print("\n" + "=" * 60)
    print("1. ASCII ART DEMONSTRATION")
    print("=" * 60 + "\n")

    # Banner
    print(ASCIIArt.banner("Welcome to CLI Utils Demo", Color.CYAN, width=60))
    print()

    # Box
    print(ASCIIArt.box("This is a boxed message\nwith multiple lines", Color.YELLOW, padding=2))
    print()

    # Victory
    print("Victory ASCII Art:")
    print(ASCIIArt.victory(Color.GREEN))
    print()

    # Defeat
    print("Defeat ASCII Art:")
    print(ASCIIArt.defeat(Color.RED))
    print()

    # Draw
    print("Draw ASCII Art:")
    print(ASCIIArt.draw(Color.CYAN))
    print()


def demo_rich_text() -> None:
    """Demonstrate rich text formatting."""
    print("\n" + "=" * 60)
    print("2. RICH TEXT FORMATTING")
    print("=" * 60 + "\n")

    # Headers
    print(RichText.header("Main Header (Level 1)", level=1))
    print(RichText.header("Sub Header (Level 2)", level=2))
    print(RichText.header("Minor Header (Level 3)", level=3))
    print()

    # Highlighted text
    print("This is " + RichText.highlight("important text") + " in a sentence.")
    print()

    # Status messages
    print(RichText.success("Operation completed successfully!"))
    print(RichText.error("An error occurred!"))
    print(RichText.warning("This is a warning message."))
    print(RichText.info("Here's some useful information."))
    print()

    # Colorized text
    print("Colorized text examples:")
    print(RichText.colorize("Red text", Color.RED))
    print(RichText.colorize("Green text", Color.GREEN))
    print(RichText.colorize("Blue text", Color.BLUE))
    print(RichText.colorize("Yellow text", Color.YELLOW))
    print(RichText.colorize("Cyan text", Color.CYAN))
    print(RichText.colorize("Magenta text", Color.MAGENTA))
    print()


def demo_progress_indicators() -> None:
    """Demonstrate progress bars and spinners."""
    print("\n" + "=" * 60)
    print("3. PROGRESS INDICATORS")
    print("=" * 60 + "\n")

    # Progress bar
    print("Progress Bar Demo:")
    bar = ProgressBar(total=20, width=40, theme=THEMES["ocean"])
    for i in range(21):
        bar.update(i)
        time.sleep(0.05)
    print()

    # Spinner
    print("Spinner Demo (5 frames):")
    spinner = Spinner(message="Loading game assets", theme=THEMES["forest"])
    spinner.start()
    for _ in range(5):
        time.sleep(0.2)
        spinner.tick()
    spinner.stop()
    print("Done!")
    print()


def demo_interactive_menu() -> None:
    """Demonstrate interactive menus."""
    print("\n" + "=" * 60)
    print("4. INTERACTIVE MENU")
    print("=" * 60 + "\n")

    options = [
        "Start New Game",
        "Load Saved Game",
        "View Statistics",
        "Settings",
        "Exit",
    ]

    _ = InteractiveMenu("Main Menu", options, theme=THEMES["dark"])

    # Use numbered menu for demo (more reliable in different environments)
    print("Selecting 'View Statistics' (option 3)...")

    # Simulate the selection
    print(f"\nYou selected: {options[2]}")
    print()


def demo_command_history() -> None:
    """Demonstrate command history and autocomplete."""
    print("\n" + "=" * 60)
    print("5. COMMAND HISTORY & AUTOCOMPLETE")
    print("=" * 60 + "\n")

    history = CommandHistory(max_size=10)

    # Add commands
    commands = ["start game", "stop game", "save game", "load game", "help", "quit"]
    print("Adding commands to history:")
    for cmd in commands:
        history.add(cmd)
        print(f"  Added: {cmd}")
    print()

    # Navigate history
    print("Navigating history (backward):")
    for _ in range(3):
        prev = history.previous()
        if prev:
            print(f"  Previous: {prev}")
    print()

    print("Navigating history (forward):")
    for _ in range(2):
        next_cmd = history.next()
        if next_cmd:
            print(f"  Next: {next_cmd}")
    print()

    # Search
    print("Searching for commands starting with 'st':")
    results = history.search("st")
    for result in results:
        print(f"  Found: {result}")
    print()

    # Autocomplete
    candidates = ["start", "stop", "status", "settings", "save", "load", "help", "quit"]
    print("Autocomplete examples:")
    print(f"  'st' autocompletes to: {history.autocomplete('st', candidates)}")
    print(f"  'sav' autocompletes to: {history.autocomplete('sav', candidates)}")
    print(f"  'q' autocompletes to: {history.autocomplete('q', candidates)}")
    print()


def demo_themes() -> None:
    """Demonstrate theme support."""
    print("\n" + "=" * 60)
    print("6. THEME SUPPORT")
    print("=" * 60 + "\n")

    print("Available themes:\n")

    for theme_name in THEMES.keys():
        theme = THEMES[theme_name]
        print(f"Theme: {theme_name.upper()}")
        print(f"  Primary: {RichText.colorize('■■■', theme.primary)}")
        print(f"  Secondary: {RichText.colorize('■■■', theme.secondary)}")
        print(f"  Success: {RichText.colorize('■■■', theme.success)}")
        print(f"  Error: {RichText.colorize('■■■', theme.error)}")
        print(f"  Warning: {RichText.colorize('■■■', theme.warning)}")
        print(f"  Info: {RichText.colorize('■■■', theme.info)}")
        print()


def demo_utility_functions() -> None:
    """Demonstrate utility functions."""
    print("\n" + "=" * 60)
    print("7. UTILITY FUNCTIONS")
    print("=" * 60 + "\n")

    # Terminal size
    width, height = get_terminal_size()
    print(f"Terminal size: {width} columns x {height} lines")
    print()

    # Note: We won't actually clear the screen in the demo
    print("clear_screen() function is available to clear the terminal.")
    print()


def main() -> None:
    """Run all demonstrations."""
    print(ASCIIArt.banner("CLI Utils Demo", Color.CYAN, width=60))
    print()
    print(RichText.info("This demo showcases all CLI enhancement features."))
    print(RichText.info("Press Ctrl+C to exit at any time."))
    print()

    try:
        # Run all demos
        demo_ascii_art()
        input("Press Enter to continue...")

        demo_rich_text()
        input("Press Enter to continue...")

        demo_progress_indicators()
        input("Press Enter to continue...")

        demo_interactive_menu()
        input("Press Enter to continue...")

        demo_command_history()
        input("Press Enter to continue...")

        demo_themes()
        input("Press Enter to continue...")

        demo_utility_functions()

        print("\n" + ASCIIArt.banner("Demo Complete!", Color.GREEN, width=60))
        print()
        print(RichText.success("All features demonstrated successfully!"))

    except KeyboardInterrupt:
        print("\n\n" + RichText.warning("Demo interrupted by user."))
        print(RichText.info("Thank you for trying the CLI utils demo!"))


if __name__ == "__main__":
    main()
