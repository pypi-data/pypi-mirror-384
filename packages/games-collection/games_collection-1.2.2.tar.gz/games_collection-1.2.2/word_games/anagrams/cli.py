"""CLI for Anagrams."""

from __future__ import annotations

from .anagrams import AnagramsGame


def main() -> None:
    """Run Anagrams game."""
    print("ANAGRAMS".center(50, "="))
    print("\nRearrange letters to form words!")

    game = AnagramsGame(num_rounds=5)
    game.state = game.state.IN_PROGRESS

    while not game.is_game_over():
        scrambled = game.get_current_scrambled()
        print(f"\nRound {game.current_round + 1}/{len(game.pairs)}")
        print(f"Scrambled: {scrambled.upper()}")

        guess = input("Your answer: ").strip()
        game.make_move(guess)

    print(f"\nFinal Score: {game.score}/{len(game.pairs)}")


if __name__ == "__main__":
    main()
