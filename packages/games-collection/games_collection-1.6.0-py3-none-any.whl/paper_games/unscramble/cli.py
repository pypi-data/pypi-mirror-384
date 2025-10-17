"""Command-line interface for playing Unscramble.

This module provides the terminal-based interactive experience for playing
the word unscrambling game.
"""

from __future__ import annotations

import pathlib
import time
from typing import Optional

from .stats import GameStats
from .unscramble import UnscrambleGame, list_themes, load_themed_words, load_words_by_difficulty

# Path to store statistics
STATS_FILE = pathlib.Path.home() / ".games" / "unscramble_stats.json"


def play(rounds: int = 5) -> None:
    """Run a multi-round unscramble session with mode selection."""
    print("=" * 60)
    print("UNSCRAMBLE - Word Scrambling Game")
    print("=" * 60)

    # Load statistics
    stats = GameStats.load(STATS_FILE)

    # Show statistics if there are any games played
    if stats.games_played > 0:
        show_stats = input("View your statistics? [y/N]: ").strip().lower()
        if show_stats in {"y", "yes"}:
            print("\n" + stats.summary() + "\n")

    # Choose game mode
    print("\nGame Modes:")
    print("  1. Classic Mode (no timer)")
    print("  2. Timed Mode (countdown per word)")
    print("  3. Multiplayer Mode (competitive)")

    mode_choice = input("\nSelect mode (1-3) [1]: ").strip() or "1"

    if mode_choice == "2":
        _play_timed(rounds, stats)
    elif mode_choice == "3":
        _play_multiplayer(stats)
    else:
        _play_classic(rounds, stats)

    # Record game completion and check for achievements
    stats.record_game()
    new_achievements = stats.check_achievements()
    if new_achievements:
        print("\n🎉 NEW ACHIEVEMENTS UNLOCKED! 🎉")
        for achievement in new_achievements:
            print(f"  🏆 {achievement}")

    # Save statistics
    stats.save(STATS_FILE)

    # Show updated statistics
    print("\n" + stats.summary())


def _get_game_setup() -> tuple[Optional[str], Optional[str], list[str]]:
    """Get difficulty and theme selection from user.

    Returns:
        Tuple of (difficulty, theme, words)
    """
    # Choose difficulty
    print("\nDifficulty Levels:")
    print("  1. Easy (6+ letter words)")
    print("  2. Medium (4-5 letter words)")
    print("  3. Hard (3 letter words)")
    print("  4. Mixed (all difficulties)")

    diff_choice = input("\nSelect difficulty (1-4) [4]: ").strip() or "4"
    difficulty_map = {"1": "easy", "2": "medium", "3": "hard", "4": "all"}
    difficulty = difficulty_map.get(diff_choice, "all")

    # Choose theme
    use_theme = input("\nUse a themed word pack? [y/N]: ").strip().lower()
    theme = None

    if use_theme in {"y", "yes"}:
        print("\n" + list_themes())
        theme_input = input("\nChoose a theme (or press Enter to skip): ").strip().lower()
        if theme_input:
            try:
                words = load_themed_words(theme_input)
                theme = theme_input
                print(f"\nUsing {theme} theme with {len(words)} words!")
                return difficulty, theme, words
            except ValueError as e:
                print(f"Error: {e}")
                print("Continuing without theme...")

    # Load words by difficulty
    words = load_words_by_difficulty(difficulty if difficulty != "all" else "all")
    print(f"\nUsing {difficulty} difficulty with {len(words)} words!")

    return difficulty if difficulty != "all" else None, theme, words


def _play_classic(rounds: int, stats: GameStats) -> None:
    """Run classic mode without timer."""
    difficulty, theme, words = _get_game_setup()

    game = UnscrambleGame(words=words, difficulty=difficulty, theme=theme)
    print("\n" + "=" * 60)
    print("CLASSIC MODE - Unscramble the letters to reveal the word!")
    print("=" * 60)

    score = 0
    for round_number in range(1, rounds + 1):
        scrambled = game.new_round()
        print(f"\nRound {round_number}/{rounds}: {scrambled}")
        print(f"Letters: {len(game.secret_word)}")

        start_time = time.time()
        guess = input("Your guess: ")
        time_taken = time.time() - start_time

        if game.guess(guess):
            print("✓ Correct!")
            score += 1
            stats.record_word(True, difficulty=difficulty, theme=theme, time_taken=time_taken)
        else:
            print(f"✗ Close, but the word was '{game.secret_word}'.")
            stats.record_word(False, difficulty=difficulty, theme=theme, time_taken=time_taken)

    print(f"\n{'=' * 60}")
    print(f"GAME OVER - You solved {score} out of {rounds} words!")
    print(f"{'=' * 60}")


def _play_timed(rounds: int, stats: GameStats) -> None:
    """Run timed mode with countdown for each word."""
    difficulty, theme, words = _get_game_setup()

    # Get time limit
    print("\nTime Limits:")
    print("  1. Easy (30 seconds per word)")
    print("  2. Medium (20 seconds per word)")
    print("  3. Hard (10 seconds per word)")

    time_choice = input("\nSelect time limit (1-3) [2]: ").strip() or "2"
    time_limits = {"1": 30, "2": 20, "3": 10}
    time_limit = time_limits.get(time_choice, 20)

    game = UnscrambleGame(words=words, difficulty=difficulty, theme=theme)
    print("\n" + "=" * 60)
    print(f"TIMED MODE - You have {time_limit} seconds per word!")
    print("=" * 60)

    score = 0
    for round_number in range(1, rounds + 1):
        scrambled = game.new_round()
        print(f"\nRound {round_number}/{rounds}: {scrambled}")
        print(f"Letters: {len(game.secret_word)} | Time limit: {time_limit}s")
        print("GO! ", end="", flush=True)

        start_time = time.time()
        guess = input()
        time_taken = time.time() - start_time

        if time_taken > time_limit:
            print(f"⏱ Time's up! ({time_taken:.1f}s) The word was '{game.secret_word}'.")
            stats.record_word(False, difficulty=difficulty, theme=theme, time_taken=time_taken)
        elif game.guess(guess):
            print(f"✓ Correct! ({time_taken:.1f}s)")
            score += 1
            stats.record_word(True, difficulty=difficulty, theme=theme, time_taken=time_taken)
        else:
            print(f"✗ Wrong! The word was '{game.secret_word}'. ({time_taken:.1f}s)")
            stats.record_word(False, difficulty=difficulty, theme=theme, time_taken=time_taken)

    print(f"\n{'=' * 60}")
    print(f"GAME OVER - You solved {score} out of {rounds} words!")
    print(f"{'=' * 60}")


def _play_multiplayer(stats: GameStats) -> None:
    """Run multiplayer competitive mode."""
    print("\n" + "=" * 60)
    print("MULTIPLAYER MODE - Competitive Unscrambling!")
    print("=" * 60)

    # Get number of players
    num_players = 2
    try:
        num_input = input("How many players? (2-4, default 2): ").strip()
        if num_input:
            num_players = max(2, min(4, int(num_input)))
    except ValueError:
        num_players = 2

    # Get player names
    players = []
    for i in range(num_players):
        name = input(f"Enter name for Player {i + 1}: ").strip()
        if not name:
            name = f"Player {i + 1}"
        players.append({"name": name, "score": 0})

    # Get rounds
    rounds_input = input("\nHow many rounds? (default 5): ").strip()
    try:
        rounds = max(1, int(rounds_input)) if rounds_input else 5
    except ValueError:
        rounds = 5

    # Get game setup
    difficulty, theme, words = _get_game_setup()

    # Get timer option
    use_timer = input("\nUse timer? [y/N]: ").strip().lower()
    time_limit = None
    if use_timer in {"y", "yes"}:
        try:
            time_input = input("Time limit per word (seconds, default 20): ").strip()
            time_limit = int(time_input) if time_input else 20
        except ValueError:
            time_limit = 20

    game = UnscrambleGame(words=words, difficulty=difficulty, theme=theme)

    # Play rounds
    for round_number in range(1, rounds + 1):
        print(f"\n{'=' * 60}")
        print(f"ROUND {round_number}/{rounds}")
        print("=" * 60)

        scrambled = game.new_round()
        print(f"\nScrambled word: {scrambled}")
        print(f"Letters: {len(game.secret_word)}")

        if time_limit:
            print(f"Time limit: {time_limit}s")

        # Each player takes a turn
        round_solved = False
        for player in players:
            if round_solved:
                print(f"\n{player['name']}: (skipped - word already solved)")
                continue

            print(f"\n{player['name']}'s turn:")

            if time_limit:
                print("GO! ", end="", flush=True)
                start_time = time.time()
                guess = input()
                time_taken = time.time() - start_time

                if time_taken > time_limit:
                    print(f"⏱ Time's up! ({time_taken:.1f}s)")
                    continue
            else:
                guess = input("Your guess: ")
                time_taken = 0

            if game.guess(guess):
                if time_limit:
                    print(f"✓ Correct! ({time_taken:.1f}s)")
                else:
                    print("✓ Correct!")
                player["score"] += 1
                round_solved = True
                stats.record_word(True, difficulty=difficulty, theme=theme, time_taken=time_taken if time_limit else None)

        if not round_solved:
            print(f"\n💀 No one solved it! The word was '{game.secret_word}'.")
            stats.record_word(False, difficulty=difficulty, theme=theme)

        # Show current scores
        print("\nCurrent Scores:")
        for player in sorted(players, key=lambda p: p["score"], reverse=True):
            print(f"  {player['name']}: {player['score']}")

    # Final results
    print(f"\n{'=' * 60}")
    print("GAME OVER - Final Scores:")
    print("=" * 60)
    sorted_players = sorted(players, key=lambda p: p["score"], reverse=True)
    for idx, player in enumerate(sorted_players, 1):
        print(f"{idx}. {player['name']}: {player['score']} points")

    winner = sorted_players[0]
    if sorted_players[0]["score"] > sorted_players[1]["score"]:
        print(f"\n🎉 {winner['name']} wins! Congratulations!")
    else:
        print("\n🤝 It's a tie!")
