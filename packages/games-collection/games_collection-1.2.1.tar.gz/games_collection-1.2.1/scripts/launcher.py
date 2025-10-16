#!/usr/bin/env python3
"""Universal launcher for Games Collection.

This script provides a menu-based interface to launch any game in the collection.
It's used as the entry point for standalone executables.
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable, Dict, List, Optional

from common.challenges import get_default_challenge_manager
from common.daily_challenges import DailyChallengeScheduler, DailyChallengeSelection
from common.profile_service import ProfileService, ProfileServiceError, get_profile_service
from common.tutorial_registry import GLOBAL_TUTORIAL_REGISTRY, TutorialMetadata
from common.tutorial_session import TutorialSession

# Try to use colorama if available, fall back to plain text
try:
    from colorama import Fore, Style
    from colorama import init as colorama_init

    colorama_init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False

    # Define dummy color constants
    class Fore:
        RED = ""
        GREEN = ""
        YELLOW = ""
        BLUE = ""
        MAGENTA = ""
        CYAN = ""
        WHITE = ""

    class Style:
        BRIGHT = ""
        RESET_ALL = ""


GAME_MAP: dict[str, tuple[str, Callable[[], None]]] = {
    "1": ("poker", lambda: __import__("card_games.poker.__main__", fromlist=["main"]).main()),
    "2": ("blackjack", lambda: __import__("card_games.blackjack.__main__", fromlist=["main"]).main()),
    "3": ("uno", lambda: __import__("card_games.uno.__main__", fromlist=["main"]).main()),
    "4": ("hearts", lambda: __import__("card_games.hearts.__main__", fromlist=["main"]).main()),
    "5": ("spades", lambda: __import__("card_games.spades.__main__", fromlist=["main"]).main()),
    "6": ("bridge", lambda: __import__("card_games.bridge.__main__", fromlist=["main"]).main()),
    "7": ("gin_rummy", lambda: __import__("card_games.gin_rummy.__main__", fromlist=["main"]).main()),
    "8": ("solitaire", lambda: __import__("card_games.solitaire.__main__", fromlist=["main"]).main()),
    "9": ("bluff", lambda: __import__("card_games.bluff.__main__", fromlist=["main"]).main()),
    "10": ("war", lambda: __import__("card_games.war.__main__", fromlist=["main"]).main()),
    "11": ("go_fish", lambda: __import__("card_games.go_fish.__main__", fromlist=["main"]).main()),
    "12": ("crazy_eights", lambda: __import__("card_games.crazy_eights.__main__", fromlist=["main"]).main()),
    "13": ("cribbage", lambda: __import__("card_games.cribbage.__main__", fromlist=["main"]).main()),
    "14": ("euchre", lambda: __import__("card_games.euchre.__main__", fromlist=["main"]).main()),
    "15": ("rummy500", lambda: __import__("card_games.rummy500.__main__", fromlist=["main"]).main()),
    "16": ("tic_tac_toe", lambda: __import__("paper_games.tic_tac_toe.__main__", fromlist=["main"]).main()),
    "17": ("battleship", lambda: __import__("paper_games.battleship.__main__", fromlist=["main"]).main()),
    "18": ("checkers", lambda: __import__("paper_games.checkers.__main__", fromlist=["main"]).main()),
    "19": ("connect_four", lambda: __import__("paper_games.connect_four.__main__", fromlist=["main"]).main()),
    "20": ("othello", lambda: __import__("paper_games.othello.__main__", fromlist=["main"]).main()),
    "21": ("dots_and_boxes", lambda: __import__("paper_games.dots_and_boxes.__main__", fromlist=["main"]).main()),
    "22": ("hangman", lambda: __import__("paper_games.hangman.__main__", fromlist=["main"]).main()),
    "23": ("nim", lambda: __import__("paper_games.nim.__main__", fromlist=["main"]).main()),
    "24": ("sudoku", lambda: __import__("paper_games.sudoku.__main__", fromlist=["main"]).main()),
    "25": ("mancala", lambda: __import__("paper_games.mancala.__main__", fromlist=["main"]).main()),
    "26": ("craps", lambda: __import__("dice_games.craps.__main__", fromlist=["main"]).main()),
    "27": ("bunco", lambda: __import__("dice_games.bunco.__main__", fromlist=["main"]).main()),
    "28": ("liars_dice", lambda: __import__("dice_games.liars_dice.__main__", fromlist=["main"]).main()),
    "29": ("unscramble", lambda: __import__("word_games.unscramble.__main__", fromlist=["main"]).main()),
    "30": ("wordle", lambda: __import__("word_games.wordle.__main__", fromlist=["main"]).main()),
    "31": ("mastermind", lambda: __import__("logic_games.mastermind.__main__", fromlist=["main"]).main()),
    "32": ("codebreaker", lambda: __import__("logic_games.codebreaker.__main__", fromlist=["main"]).main()),
    "33": ("pinochle", lambda: __import__("card_games.pinochle.__main__", fromlist=["main"]).main()),
}

SLUG_TO_ENTRY = {value[0]: value for value in GAME_MAP.values()}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for automation and smoke tests."""

    parser = argparse.ArgumentParser(description="Games Collection launcher")
    parser.add_argument("--game", help="Game identifier (menu number or slug, e.g., dots_and_boxes).")
    parser.add_argument(
        "--gui-framework",
        choices=["tkinter", "pyqt5"],
        help="Preferred GUI framework when launching programmatically.",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run a non-interactive smoke test (used by CI to validate bundles).",
    )
    parser.add_argument("--profile", help="Select a profile identifier before launching games.")
    parser.add_argument(
        "--profile-display-name",
        help="Display name to use when creating or renaming profiles (defaults to title-cased identifier).",
    )
    parser.add_argument("--profile-summary", action="store_true", help="Print the active profile summary.")
    parser.add_argument("--profile-reset", action="store_true", help="Reset the active profile before launching.")
    parser.add_argument("--profile-rename", help="Rename the active profile to the provided identifier.")
    return parser.parse_args()


def get_game_entry(identifier: str) -> tuple[str, Callable[[], None]] | None:
    """Return the launcher entry for a menu choice or slug."""

    key = identifier.strip().lower()
    if key in GAME_MAP:
        return GAME_MAP[key]

    normalized_key = key.replace("-", "_")
    return SLUG_TO_ENTRY.get(normalized_key)


def run_pyqt_smoke_test(game_slug: str) -> int:
    """Launch a PyQt5 GUI briefly to ensure resources are bundled."""

    try:
        from PyQt5.QtCore import QTimer
        from PyQt5.QtWidgets import QApplication
    except ImportError as exc:  # pragma: no cover - PyInstaller smoke tests only
        raise RuntimeError("PyQt5 is required for PyQt5 smoke tests") from exc

    app = QApplication.instance() or QApplication([])

    if game_slug == "dots_and_boxes":
        from paper_games.dots_and_boxes.gui_pyqt import DotsAndBoxesGUI

        window = DotsAndBoxesGUI(size=2, show_hints=False)
    elif game_slug == "go_fish":
        from card_games.go_fish.game import GoFishGame
        from card_games.go_fish.gui_pyqt import GoFishGUI

        window = GoFishGUI(GoFishGame(num_players=2))
    else:  # pragma: no cover - only called with supported games
        raise ValueError(f"Unsupported PyQt5 smoke test for '{game_slug}'")

    window.show()
    QTimer.singleShot(0, window.close)
    QTimer.singleShot(0, app.quit)
    return app.exec()


def run_smoke_test(game_identifier: str, gui_framework: str | None) -> int:
    """Run the CI smoke test for the requested game and framework."""

    entry = get_game_entry(game_identifier)
    if entry is None:
        raise ValueError(f"Unknown game identifier '{game_identifier}'")

    game_slug, _ = entry
    if gui_framework == "pyqt5":
        return run_pyqt_smoke_test(game_slug)

    return 0


def print_header(service: ProfileService, scheduler: DailyChallengeScheduler) -> None:
    """Print the launcher header."""
    profile = service.active_profile
    profile_line = f"Active Profile: {profile.display_name} (Level {profile.level})"
    xp_line = f"XP: {profile.experience} | Next Level: {profile.experience_to_next_level()} XP"
    selection = scheduler.get_challenge_for_date()
    progress = profile.daily_challenge_progress
    completed = progress.is_completed(selection.target_date)
    status_label = "Completed" if completed else "Available"
    streak_line = (
        f"Streak: {progress.current_streak} (Best {progress.best_streak})"
        f" | Total Completed: {progress.total_completed}"
    )
    summary_line = f"Daily Challenge: {selection.summary()} [{status_label}]"
    if HAS_COLORAMA:
        status_color = Fore.GREEN if completed else Fore.YELLOW
    else:
        status_color = ""
    if HAS_COLORAMA:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 60}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'GAMES COLLECTION':^60}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}\n")
        print(f"{Fore.MAGENTA}{profile_line}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{xp_line}{Style.RESET_ALL}\n")
        print(f"{status_color}{summary_line}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{streak_line}{Style.RESET_ALL}\n")
    else:
        print("\n" + "=" * 60)
        print(f"{'GAMES COLLECTION':^60}")
        print("=" * 60 + "\n")
        print(profile_line)
        print(xp_line)
        print(summary_line)
        print(streak_line + "\n")


def print_menu(service: ProfileService) -> None:
    """Print the main menu."""
    categories = {
        "Card Games": [
            ("1", "Poker (Texas Hold'em)"),
            ("2", "Blackjack"),
            ("3", "Uno"),
            ("4", "Hearts"),
            ("5", "Spades"),
            ("6", "Bridge"),
            ("7", "Gin Rummy"),
            ("8", "Solitaire"),
            ("9", "Bluff"),
            ("10", "War"),
            ("11", "Go Fish"),
            ("12", "Crazy Eights"),
            ("13", "Cribbage"),
            ("14", "Euchre"),
            ("15", "Rummy 500"),
        ],
        "Paper Games": [
            ("16", "Tic-Tac-Toe"),
            ("17", "Battleship"),
            ("18", "Checkers"),
            ("19", "Connect Four"),
            ("20", "Othello"),
            ("21", "Dots and Boxes"),
            ("22", "Hangman"),
            ("23", "Nim"),
            ("24", "Sudoku"),
            ("25", "Mancala"),
        ],
        "Dice Games": [
            ("26", "Craps"),
            ("27", "Bunco"),
            ("28", "Liar's Dice"),
        ],
        "Word Games": [
            ("29", "Unscramble"),
            ("30", "Wordle"),
        ],
        "Logic Games": [
            ("31", "Mastermind"),
            ("32", "Codebreaker"),
        ],
        "Educational Tools": [
            ("T", "Tutorial catalogue"),
        ],
    }

    if HAS_COLORAMA:
        print(f"{Fore.CYAN}Daily Activities:{Style.RESET_ALL}")
    else:
        print("Daily Activities:")
    print("  D. Play today's daily challenge\n")

    if HAS_COLORAMA:
        print(f"{Fore.GREEN}Profile Options:{Style.RESET_ALL}")
    else:
        print("Profile Options:")
    print("  P. View profile summary")
    print("  L. List available profiles")
    print("  S. Switch profile")
    print("  R. Rename active profile")
    print("  X. Reset active profile\n")

    for category, games in categories.items():
        if HAS_COLORAMA:
            print(f"{Fore.YELLOW}{Style.BRIGHT}{category}:{Style.RESET_ALL}")
        else:
            print(f"\n{category}:")
        for num, name in games:
            print(f"  {num}. {name}")
        print()

    if HAS_COLORAMA:
        print(f"{Fore.RED}0. Exit{Style.RESET_ALL}\n")
    else:
        print("0. Exit\n")


def _print_profile_list(service: ProfileService) -> None:
    """Display the identifiers of profiles stored on disk."""

    print("\nAvailable profiles:")
    for identifier in service.list_profiles():
        marker = "*" if identifier == service.active_profile.player_id else "-"
        print(f"  {marker} {identifier}")


def _handle_profile_summary(service: ProfileService) -> None:
    print("\n" + service.summary() + "\n")
    input("Press Enter to return to the menu…")


def _handle_profile_list(service: ProfileService) -> None:
    _print_profile_list(service)
    input("\nPress Enter to return to the menu…")


def _handle_profile_switch(service: ProfileService) -> None:
    _print_profile_list(service)
    selection = input("\nEnter profile identifier to activate (blank to cancel): ").strip()
    if not selection:
        return
    display = input("Display name [leave blank to keep default]: ").strip() or None
    try:
        service.select_profile(selection, display)
        message = f"Switched to profile '{service.active_profile.display_name}'."
        if HAS_COLORAMA:
            print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")
        else:
            print(message)
    except ProfileServiceError as exc:
        if HAS_COLORAMA:
            print(f"{Fore.RED}Error: {exc}{Style.RESET_ALL}")
        else:
            print(f"Error: {exc}")
    input("Press Enter to return to the menu…")


def _handle_profile_rename(service: ProfileService) -> None:
    new_identifier = input("Enter new profile identifier (blank to cancel): ").strip()
    if not new_identifier:
        return
    new_display_name = input("Display name [leave blank to keep current]: ").strip() or None
    try:
        service.rename_active_profile(new_identifier, new_display_name)
        message = f"Profile renamed to '{service.active_profile.display_name}'."
        if HAS_COLORAMA:
            print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")
        else:
            print(message)
    except ProfileServiceError as exc:
        if HAS_COLORAMA:
            print(f"{Fore.RED}Error: {exc}{Style.RESET_ALL}")
        else:
            print(f"Error: {exc}")
    input("Press Enter to return to the menu…")


def _handle_profile_reset(service: ProfileService) -> None:
    confirmation = input("Type 'RESET' to confirm wiping all progress: ").strip()
    if confirmation.lower() != "reset":
        return
    service.reset_active_profile()
    message = "Profile progress cleared."
    if HAS_COLORAMA:
        print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")
    else:
        print(message)
    input("Press Enter to return to the menu…")


def _format_metadata_summary(metadata: TutorialMetadata) -> str:
    """Return a formatted summary for display."""

    summary_lines = [
        f"Game: {metadata.display_name}",
        f"Module: {metadata.game_key}",
        f"Category: {metadata.category}",
        f"Rules reference: {metadata.doc_path}",
        "",
        metadata.summary,
    ]
    return "\n".join(summary_lines)


def _run_tutorial_session(session: TutorialSession, metadata: TutorialMetadata) -> None:
    """Interactive loop for a tutorial session."""

    def _print_help() -> None:
        print(
            "\nCommands:\n"
            "  status       Show the current tutorial step and progress estimate\n"
            "  hint         Display the hint for the current step\n"
            "  tip [level]  Show a strategy tip (levels: beginner/intermediate/advanced)\n"
            "  probability  Estimate success probability based on game state\n"
            "  auto         Perform an automatic valid move (if available)\n"
            "  reset        Restart the tutorial session\n"
            "  help         Show this help text\n"
            "  quit         Return to the launcher\n"
        )

    print("\nTutorial session started. Type 'help' for commands.")
    _print_help()

    while True:
        step = session.get_current_step()
        if step is None:
            print("Tutorial completed. Great work!")
            break
        prompt = f"tutorial[{metadata.display_name}]> "
        command = input(prompt).strip()
        if not command:
            continue
        lowered = command.lower()
        if lowered in {"quit", "exit", "q"}:
            break
        if lowered == "help":
            _print_help()
            continue
        if lowered == "status":
            print(f"\nCurrent step: {step.title}\n{step.description}")
            probability = session.estimate_progress()
            if probability:
                print(f"Estimated success probability: {probability}")
            continue
        if lowered == "hint":
            hint = session.get_hint()
            if hint:
                print(f"Hint: {hint}")
            else:
                print("No hint available for this step.")
            continue
        if lowered.startswith("tip"):
            parts = lowered.split()
            difficulty = parts[1] if len(parts) > 1 else None
            tip = session.request_strategy_tip(difficulty)
            if tip is None:
                print("No tips available.")
            else:
                print(f"{tip.title} ({tip.difficulty})\n{tip.description}")
                if tip.applies_to:
                    print(f"Applies to: {tip.applies_to}")
            continue
        if lowered == "probability":
            probability = session.estimate_progress()
            if probability:
                print(f"Estimated success probability: {probability}")
            else:
                print("Probability calculator unavailable for this game.")
            continue
        if lowered == "reset":
            session.reset()
            print("Session reset. Back to the first step.")
            continue
        if lowered == "auto":
            get_moves = getattr(session.game, "get_valid_moves", None)
            if not callable(get_moves):
                print("This game does not expose valid moves for automation.")
                continue
            try:
                moves = get_moves()
            except Exception as exc:  # pragma: no cover - defensive
                print(f"Could not obtain valid moves: {exc}")
                continue
            if not moves:
                print("No valid moves available—perhaps the game is already over?")
                continue
            move = moves[0]
            success, feedback = session.apply_move(move)
            for message in feedback.messages:
                print(message)
            if feedback.tutorial_completed:
                break
            continue

        print("Unknown command. Type 'help' to view available options.")


def launch_tutorial_browser(service: ProfileService) -> None:
    """Interactive tutorial browser."""

    registry = GLOBAL_TUTORIAL_REGISTRY
    game_keys = registry.available_games()
    if not game_keys:
        print("No tutorials available.")
        input("Press Enter to return to the menu…")
        return

    lookup: Dict[str, str] = {}
    for index, game_key in enumerate(game_keys, start=1):
        lookup[str(index)] = game_key

    while True:
        print("\nTutorial catalogue:")
        for index, game_key in enumerate(game_keys, start=1):
            metadata = registry.get_metadata(game_key)
            print(f"  {index}. {metadata.display_name} ({metadata.category})")
        print("  B. Back to main menu\n")

        selection = input("Select a tutorial (number or B to return): ").strip()
        if not selection:
            continue
        if selection.lower() in {"b", "back"}:
            return
        if selection not in lookup:
            print("Invalid selection. Please try again.")
            continue

        game_key = lookup[selection]
        metadata = registry.get_metadata(game_key)
        print("\n" + _format_metadata_summary(metadata) + "\n")

        difficulties = list(metadata.difficulty_notes.keys())
        difficulty_prompt = (
            "Choose difficulty "
            + f"({', '.join(difficulties)}). Press Enter for default [{metadata.default_difficulty}]: "
        )
        difficulty = input(difficulty_prompt).strip().lower()
        if difficulty and difficulty not in difficulties:
            print(f"Unknown difficulty '{difficulty}', defaulting to {metadata.default_difficulty}.")
            difficulty = metadata.default_difficulty
        elif not difficulty:
            difficulty = metadata.default_difficulty

        learning_goal_keys = list(metadata.learning_goals.keys())
        learning_goal: Optional[str] = None
        if learning_goal_keys:
            goal_prompt = (
                "Focus area "
                + f"({', '.join(learning_goal_keys)}). Press Enter to skip: "
            )
            goal_input = input(goal_prompt).strip().lower()
            if goal_input in learning_goal_keys:
                learning_goal = goal_input

        tutorial_cls = registry.get_tutorial_class(game_key)
        tutorial = tutorial_cls(difficulty=difficulty, learning_goal=learning_goal)
        strategy_provider = registry.get_strategy_provider(game_key)
        probability_calculator = registry.get_probability_calculator(game_key)

        engine_class = metadata.engine_class
        if engine_class is None:
            print(
                "This tutorial relies on external game launchers. Use the documentation reference "
                "to start the game manually, then follow the steps listed above."
            )
            step = tutorial.get_current_step()
            while step is not None:
                print(f"- {step.title}: {step.description}")
                tutorial.advance_step()
                step = tutorial.get_current_step()
            tutorial.reset()
            input("\nPress Enter to return to the tutorial list…")
            continue

        try:
            game = engine_class()  # type: ignore[call-arg]
        except TypeError:
            print(
                "This game's engine requires additional parameters. Launch the standard game "
                "and consult the tutorial steps for guidance."
            )
            step = tutorial.get_current_step()
            while step is not None:
                print(f"- {step.title}: {step.description}")
                tutorial.advance_step()
                step = tutorial.get_current_step()
            tutorial.reset()
            input("\nPress Enter to return to the tutorial list…")
            continue

        session = TutorialSession(
            game,
            tutorial,
            strategy_provider=strategy_provider,
            probability_calculator=probability_calculator,
        )
        launch_message = f"Starting interactive tutorial for {metadata.display_name}."
        if HAS_COLORAMA:
            print(f"{Fore.GREEN}{launch_message}{Style.RESET_ALL}")
        else:
            print(launch_message)
        _run_tutorial_session(session, metadata)


def _print_completion_message(unlocked: List[str]) -> None:
    """Display confirmation for recording a daily challenge completion."""

    message = "Daily challenge completion recorded!"
    if HAS_COLORAMA:
        print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")
    else:
        print(message)

    if not unlocked:
        return

    badge_line = "Unlocked achievements: " + ", ".join(unlocked)
    if HAS_COLORAMA:
        print(f"{Fore.MAGENTA}{badge_line}{Style.RESET_ALL}")
    else:
        print(badge_line)


def _run_sudoku_daily_challenge(
    service: ProfileService,
    selection: DailyChallengeSelection,
) -> None:
    """Launch the Sudoku CLI configured for the selected challenge."""

    challenge = selection.challenge
    builder = challenge.metadata.get("build_puzzle")
    if not callable(builder):
        print("This Sudoku challenge is missing puzzle configuration.")
        return

    puzzle = builder()
    try:
        from paper_games.sudoku.sudoku import SudokuCLI, SudokuPuzzle
    except ImportError as exc:  # pragma: no cover - optional dependency guard
        print(f"Unable to load Sudoku CLI: {exc}")
        return

    def _on_complete(puzzle_obj: SudokuPuzzle) -> None:
        is_valid = True
        if challenge.validate:
            try:
                is_valid = bool(challenge.validate(puzzle_obj))
            except Exception as exc:  # pragma: no cover - defensive path
                print(f"Validation error: {exc}")
                is_valid = False
        if not is_valid:
            print("Completion could not be validated; progress not recorded.")
            return
        unlocked = service.record_daily_challenge_completion(challenge.id, when=selection.target_date)
        _print_completion_message(unlocked)

    SudokuCLI(puzzle=puzzle, on_complete=_on_complete).run()


def _handle_daily_challenge(service: ProfileService, scheduler: DailyChallengeScheduler) -> None:
    """Display information about today's daily challenge and offer to launch it."""

    selection = scheduler.get_challenge_for_date()
    challenge = selection.challenge
    pack = selection.pack
    progress = service.active_profile.daily_challenge_progress
    completed = progress.is_completed(selection.target_date)

    difficulty = challenge.difficulty.value.title()
    header = f"\nDaily Challenge – {selection.target_date.isoformat()}"
    details = [
        header,
        "-" * len(header),
        f"Pack: {pack.name}",
        f"Difficulty: {difficulty}",
        f"Title: {challenge.title}",
        "",
        challenge.description,
        "",
        f"Goal: {challenge.goal}",
    ]
    print("\n".join(details))

    if completed:
        print("\nYou've already completed today's challenge. Great job!")
        input("Press Enter to return to the menu…")
        return

    game_id = challenge.metadata.get("game_id")
    if game_id == "sudoku":
        _run_sudoku_daily_challenge(service, selection)
        input("\nPress Enter to return to the menu…")
        return

    print("\nPlay the corresponding game and return here when finished.")
    confirm = input("Mark this challenge as completed? [y/N]: ").strip().lower()
    if confirm == "y":
        unlocked = service.record_daily_challenge_completion(challenge.id, when=selection.target_date)
        _print_completion_message(unlocked)
    else:
        print("Progress not recorded. You can come back later today.")
    input("Press Enter to return to the menu…")


def launch_game(choice: str, service: ProfileService, scheduler: DailyChallengeScheduler) -> bool:
    """Launch the selected game.

    Args:
        choice: The menu choice number
        scheduler: Daily challenge scheduler for handling special entries

    Returns:
        True to continue, False to exit
    """
    normalized = choice.strip().lower()

    if normalized in {"0", "exit"}:
        return False

    if normalized == "p":
        _handle_profile_summary(service)
        return True
    if normalized == "l":
        _handle_profile_list(service)
        return True
    if normalized == "s":
        _handle_profile_switch(service)
        return True
    if normalized == "r":
        _handle_profile_rename(service)
        return True
    if normalized == "x":
        _handle_profile_reset(service)
        return True
    if normalized == "t":
        launch_tutorial_browser(service)
        return True
    if normalized == "d":
        _handle_daily_challenge(service, scheduler)
        return True

    if normalized in GAME_MAP:
        game_name, launcher = GAME_MAP[normalized]
        if HAS_COLORAMA:
            print(f"\n{Fore.GREEN}Launching {game_name}...{Style.RESET_ALL}\n")
        else:
            print(f"\nLaunching {game_name}...\n")
        try:
            launcher()
        except Exception as e:
            if HAS_COLORAMA:
                print(f"\n{Fore.RED}Error launching game: {e}{Style.RESET_ALL}")
            else:
                print(f"\nError launching game: {e}")
        return True
    else:
        if HAS_COLORAMA:
            print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
        else:
            print("Invalid choice. Please try again.")
        return True


def main() -> None:
    """Main launcher loop."""
    args = parse_args()

    profile_service = get_profile_service()
    challenge_manager = get_default_challenge_manager()
    schedule_path = profile_service.profile_dir.parent / "daily_challenges.json"
    scheduler = DailyChallengeScheduler(challenge_manager, storage_path=schedule_path)

    try:
        if args.profile:
            profile_service.select_profile(args.profile, args.profile_display_name)
        if args.profile_rename:
            profile_service.rename_active_profile(args.profile_rename, args.profile_display_name)
        if args.profile_reset:
            profile_service.reset_active_profile()
    except ProfileServiceError as exc:
        print(f"Profile error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.smoke_test:
        if args.game is None:
            print("Smoke tests require --game to be specified.", file=sys.stderr)
            profile_service.save_active_profile()
            sys.exit(1)

        exit_code = run_smoke_test(args.game, args.gui_framework)
        profile_service.save_active_profile()
        sys.exit(exit_code)

    if args.game:
        entry = get_game_entry(args.game)
        if entry is None:
            print(f"Unknown game identifier '{args.game}'.", file=sys.stderr)
            profile_service.save_active_profile()
            sys.exit(1)

        game_slug, launcher = entry
        if args.gui_framework == "pyqt5":
            exit_code = run_pyqt_smoke_test(game_slug)
            profile_service.save_active_profile()
            sys.exit(exit_code)

        launcher()
        if args.profile_summary:
            print(profile_service.summary())
        profile_service.save_active_profile()
        return

    if args.profile_summary:
        print(profile_service.summary())
        if not args.game:
            profile_service.save_active_profile()
            return

    while True:
        print_header(profile_service, scheduler)
        print_menu(profile_service)

        try:
            choice = input("Enter your choice: ").strip()
            if not launch_game(choice, profile_service, scheduler):
                if HAS_COLORAMA:
                    print(f"\n{Fore.CYAN}Thank you for playing!{Style.RESET_ALL}\n")
                else:
                    print("\nThank you for playing!\n")
                profile_service.save_active_profile()
                break
        except KeyboardInterrupt:
            if HAS_COLORAMA:
                print(f"\n\n{Fore.CYAN}Thank you for playing!{Style.RESET_ALL}\n")
            else:
                print("\n\nThank you for playing!\n")
            profile_service.save_active_profile()
            break
        except EOFError:
            profile_service.save_active_profile()
            break


if __name__ == "__main__":
    main()
