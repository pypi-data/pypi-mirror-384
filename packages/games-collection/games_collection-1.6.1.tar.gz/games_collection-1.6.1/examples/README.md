# Games Collection - Code Examples

This directory contains a set of Python scripts that demonstrate the various systems, architectural components, and best practices used throughout the Games Collection project. Each script is a self-contained demonstration designed to be run and understood easily.

## How to Run Examples

All examples should be run from the **root directory** of the repository to ensure that all module imports work correctly.

You can run them using the following command format:

```bash
# Replace <example_name> with the name of the script you want to run.
python -m examples.<example_name>
```

For example, to run the architecture demonstration:

```bash
python -m examples.architecture_demo
```

---

## Available Examples

### 1. Core Architecture & Engine

These examples demonstrate the fundamental building blocks of the game engine and architecture.

- **`simple_game_example.py`**
  - **Purpose**: Shows the most basic implementation of a game by inheriting from the `GameEngine` abstract base class.
  - **Features**:
    - A simple `NumberGuessingGame` class.
    - Integration of `RandomStrategy` and `HeuristicStrategy` for AI players.
    - A clear, minimal example of the core game loop.

- **`architecture_demo.py`**
  - **Purpose**: A comprehensive showcase of all interconnected architectural components working together.
  - **Features**:
    - **Plugin System**: Dynamically discovers and loads a game plugin.
    - **Event System**: Logs events as they are published by the game engine.
    - **Observer Pattern**: Notifies observers of game state changes.
    - **Settings, Save/Load, and Replay**: Demonstrates state persistence, configuration, and action recording/undo.

### 2. Command-Line Interface (CLI)

These examples focus on the tools available for building rich and interactive CLI applications.

- **`cli_utils_demo.py`**
  - **Purpose**: A gallery of all available CLI enhancement features.
  - **Features**:
    - `ASCIIArt`: Banners, boxes, and status art.
    - `RichText`: Colored and styled text.
    - `ProgressBar` and `Spinner`: For indicating progress.
    - `InteractiveMenu`: For keyboard-navigable menus.
    - `CommandHistory` and `THEMES`.

- **`cli_enhanced_game.py`**
  - **Purpose**: A fully-functional Number Guessing Game that uses all the `cli_utils` to create a polished user experience.
  - **Features**:
    - An interactive main menu and difficulty selection.
    - Themed UI elements and status messages.
    - Loading animations and user input with autocomplete hints.

### 3. Graphical User Interface (GUI)

This example demonstrates the features available for building graphical interfaces with `tkinter`.

- **`gui_enhancements_demo.py`**
  - **Purpose**: An interactive demo of all GUI enhancement features in a single window.
  - **Features**:
    - **Theming**: Switch between light, dark, and high-contrast modes in real-time.
    - **Animations**: Simple visual feedback on button clicks.
    - **Accessibility**: Controls for high-contrast mode and enhanced focus indicators.
    - **Internationalization (i18n)**: A dropdown to change the application's language.
    - **Keyboard Shortcuts**: A help system (F1) to display available shortcuts.

### 4. Analytics and Player Data

These examples show how to instrument games to collect, analyze, and display data.

- **`analytics_demo.py`**
  - **Purpose**: Demonstrates each component of the analytics system individually.
  - **Features**:
    - `GameStatistics`: Tracking wins, losses, and game durations.
    - `PerformanceMetrics`: Monitoring player decision times.
    - `EloRating`: Managing a competitive player rating system.
    - `Heatmap`, `Dashboard`, and `ReplayAnalyzer`.

- **`tic_tac_toe_with_analytics.py`**
  - **Purpose**: A practical example of integrating the analytics system into a complete game (`TicTacToe`).
  - **Features**:
    - Records game outcomes, player decisions, and ELO ratings after each match.
    - Loads and persists analytics data across sessions.
    - Displays a summary dashboard and a move-frequency heatmap.

### 5. Educational Features

This example showcases the tools designed to help players learn and improve.

- **`educational_demo.py`**
  - **Purpose**: A tour of the educational components available in the collection.
  - **Features**:
    - **Tutorial Modes**: Step-by-step guides for games like Poker and Blackjack.
    - **Probability Calculators**: Tools to analyze odds (e.g., pot odds, bust probability).
    - **Game Theory Explainer**: Definitions and examples of core AI concepts.
    - **Strategy Tips** and **Challenge Packs**.

---

## Creating Your Own Example

To add a new example:

1.  Create a new Python file in this directory (e.g., `your_example.py`).
2.  Follow the structure of the existing examples, including a docstring explaining the purpose of the script.
3.  Ensure the script can be run from the root directory.
4.  Update this `README.md` file to include a description of your new example.