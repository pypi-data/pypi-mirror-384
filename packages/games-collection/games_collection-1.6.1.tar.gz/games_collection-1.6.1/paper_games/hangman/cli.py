"""Command-line interface for playing Hangman.

This module provides the terminal-based interactive experience for playing
Hangman with ASCII art and word guessing.
"""

from __future__ import annotations

from typing import Iterable, List

from common.cli_utils import ASCIIArt, InteractiveMenu, RichText, Theme, clear_screen
from common.profile_service import get_profile_service

from .hangman import HANGMAN_ART_STYLES, HangmanGame, load_themed_words, load_words_by_difficulty

# Create a theme for consistent colors
CLI_THEME = Theme()


def _get_difficulty() -> str:
    """Prompt user to select difficulty level."""
    options = [
        "Easy (6+ letter words)",
        "Medium (4-5 letter words)",
        "Hard (3 letter words)",
        "All difficulties",
    ]
    menu = InteractiveMenu("Select Difficulty", options, theme=CLI_THEME)
    selection = menu.display()

    difficulty_map = {0: "easy", 1: "medium", 2: "hard", 3: "all"}
    return difficulty_map.get(selection, "all")


def _get_theme() -> str | None:
    """Prompt user to select a theme."""
    themes = load_themed_words()
    if not themes:
        return None

    options = ["No theme (standard words)"]
    theme_list = sorted(themes.keys())
    options.extend([theme.capitalize() for theme in theme_list])

    menu = InteractiveMenu("Select Theme", options, theme=CLI_THEME)
    selection = menu.display()

    if selection == 0:
        return None

    return theme_list[selection - 1] if 0 < selection <= len(theme_list) else None


def _get_art_style() -> str:
    """Prompt user to select ASCII art style."""
    styles = sorted(HANGMAN_ART_STYLES.keys())
    options = [style.capitalize() for style in styles]

    menu = InteractiveMenu("Select ASCII Art Style", options, theme=CLI_THEME)
    selection = menu.display()

    return styles[selection] if 0 <= selection < len(styles) else "classic"


def _get_game_mode() -> str:
    """Prompt user to select game mode."""
    options = ["Single Player", "Multiplayer (take turns choosing words)"]

    menu = InteractiveMenu("Select Game Mode", options, theme=CLI_THEME)
    selection = menu.display()

    return "multiplayer" if selection == 1 else "single"


def _play_multiplayer() -> None:
    """Run multiplayer mode where players take turns."""
    clear_screen()
    print(ASCIIArt.banner("MULTIPLAYER", CLI_THEME.primary, width=60))
    print(RichText.info("Players will take turns choosing words for each other to guess.", CLI_THEME))
    print()

    num_players = 2
    try:
        num_input = input("How many players? (2-4, default 2): ").strip()
        if num_input:
            num_players = max(2, min(4, int(num_input)))
    except ValueError:
        num_players = 2

    players = []
    for i in range(num_players):
        name = input(f"Enter name for Player {i + 1}: ").strip()
        if not name:
            name = f"Player {i + 1}"
        players.append({"name": name, "score": 0})

    rounds_input = input("\nHow many rounds per player? (default 1): ").strip()
    try:
        rounds = max(1, int(rounds_input)) if rounds_input else 1
    except ValueError:
        rounds = 1

    total_rounds = rounds * num_players
    current_round = 0

    # Get art style once for the game
    art_style = _get_art_style()

    while current_round < total_rounds:
        choosing_player_idx = current_round % num_players
        guessing_player_idx = (current_round + 1) % num_players

        choosing_player = players[choosing_player_idx]
        guessing_player = players[guessing_player_idx]

        print(f"\n{'='*60}")
        print(f"Round {current_round + 1}/{total_rounds}")
        print(f"{choosing_player['name']} will choose a word for {guessing_player['name']} to guess.")
        print(f"{'='*60}")

        # Choosing player enters a secret word
        while True:
            word = input(f"\n{choosing_player['name']}, enter a secret word (letters only): ").strip().lower()
            if word and word.isalpha():
                break
            print("Please enter a valid word with letters only.")

        # Clear screen (print newlines)
        print("\n" * 50)

        # Guessing player plays
        print(f"\n{guessing_player['name']}'s turn to guess!")
        game = HangmanGame([word], max_attempts=6, hints_enabled=True, art_style=art_style)

        while not (game.is_won() or game.is_lost()):
            print()
            for line in game.status_lines():
                print(line)

            guess = input("Enter a letter, 'hint' for a hint, or guess the word: ").strip().lower()

            if guess == "hint":
                hint = game.get_hint()
                if hint:
                    print(f"Hint! The letter '{hint}' has been revealed.")
                else:
                    print("No hints available!")
                continue

            try:
                correct = game.guess(guess)
            except ValueError as exc:
                print(exc)
                continue

            if correct:
                if len(guess) == 1:
                    print("Good guess!")
                else:
                    print("Incredible! You solved the word outright.")
            else:
                if len(guess) == 1:
                    print("Nope, that letter isn't in the word.")
                else:
                    print("That's not the word. The gallows creak ominously...")

        if game.is_won():
            print(f"\n✓ {guessing_player['name']} guessed '{game.secret_word}' correctly!")
            guessing_player["score"] += 1
        else:
            print(f"\n✗ {guessing_player['name']} didn't guess the word: '{game.secret_word}'")

        current_round += 1

        # Show scores
        print("\n--- Current Scores ---")
        for player in players:
            print(f"{player['name']}: {player['score']}")

    # Final results
    print(f"\n{'='*60}")
    print("GAME OVER - Final Scores:")
    print(f"{'='*60}")
    sorted_players = sorted(players, key=lambda p: p["score"], reverse=True)
    for idx, player in enumerate(sorted_players, 1):
        print(f"{idx}. {player['name']}: {player['score']} points")

    winner = sorted_players[0]
    if sorted_players[0]["score"] > sorted_players[1]["score"]:
        print(f"\n🎉 {winner['name']} wins! Congratulations!")
    else:
        print("\n🤝 It's a tie!")


def play(words: Iterable[str] | None = None, max_attempts: int = 6) -> None:
    """Run an interactive hangman session in the terminal."""
    # If words are provided directly, use them (for backward compatibility)
    if words is not None:
        game = HangmanGame(words, max_attempts=max_attempts)
        print("Welcome to Hangman! Guess letters or attempt the entire word.")
        _play_single_game(game)
        return

    # Otherwise, show the full interactive menu
    clear_screen()
    print(ASCIIArt.banner("HANGMAN", CLI_THEME.primary, width=60))
    print(RichText.info("Guess letters or attempt the entire word!", CLI_THEME))
    print()

    mode = _get_game_mode()

    if mode == "multiplayer":
        _play_multiplayer()
        return

    # Single player mode
    difficulty = _get_difficulty()
    theme = _get_theme()
    art_style = _get_art_style()

    # Load words based on selections
    if theme:
        word_list = load_themed_words(theme)
        theme_display = theme
    else:
        word_list = load_words_by_difficulty(difficulty)
        theme_display = None

    game = HangmanGame(word_list, max_attempts=max_attempts, theme=theme_display, hints_enabled=True, art_style=art_style)

    print()
    print(RichText.info(f"Starting game with {len(word_list)} possible words.", CLI_THEME))
    print(RichText.highlight("Type 'hint' at any time to reveal a letter (3 hints available).", CLI_THEME))
    print(RichText.success("Good luck!", CLI_THEME))
    print()

    _play_single_game(game)


def _play_single_game(game: HangmanGame) -> None:
    """Play a single game of hangman."""
    profile_service = get_profile_service()
    session = profile_service.start_session("hangman")

    while not (game.is_won() or game.is_lost()):
        print()
        for line in game.status_lines():
            print(line)

        guess = input("Enter a letter, 'hint' for a hint, or guess the word: ").strip().lower()

        if guess == "hint":
            hint = game.get_hint()
            if hint:
                print(RichText.info(f"Hint! The letter '{hint}' has been revealed.", CLI_THEME))
            else:
                print(RichText.warning("No hints available!", CLI_THEME))
            continue

        try:
            correct = game.guess(guess)
        except ValueError as exc:
            print(RichText.error(str(exc), CLI_THEME))
            continue

        if correct:
            if len(guess) == 1:
                print(RichText.success("Good guess!", CLI_THEME))
            else:
                print(RichText.success("Incredible! You solved the word outright.", CLI_THEME))
        else:
            if len(guess) == 1:
                print(RichText.error("Nope, that letter isn't in the word.", CLI_THEME))
            else:
                print(RichText.error("That's not the word. The gallows creak ominously...", CLI_THEME))

    if game.is_won():
        print()
        print(RichText.success(f"✓ Congratulations! You guessed '{game.secret_word}'.", CLI_THEME))
    else:
        print()
        print(RichText.error(f"✗ Game over! The word was '{game.secret_word}'.", CLI_THEME))

    result = "win" if game.is_won() else "loss"
    experience = 150 if result == "win" else 60
    metadata = {
        "word_length": len(game.secret_word),
        "wrong_guesses": len(game.wrong_guesses),
        "hints_used": game.hints_used,
        "theme": game.theme or "standard",
    }
    if result == "win" and not game.wrong_guesses:
        metadata["perfect_game"] = True

    unlocked = session.complete(result=result, experience=experience, metadata=metadata)
    if unlocked:
        manager = profile_service.active_profile.achievement_manager
        print()
        print(RichText.highlight("New achievements unlocked!", CLI_THEME))
        lines: List[str] = []
        for achievement_id in unlocked:
            achievement = manager.achievements.get(achievement_id)
            if achievement is not None:
                lines.append(f"  • {achievement.name} (+{achievement.points} pts)")
            else:
                lines.append(f"  • {achievement_id}")
        for line in lines:
            print(RichText.info(line, CLI_THEME))
