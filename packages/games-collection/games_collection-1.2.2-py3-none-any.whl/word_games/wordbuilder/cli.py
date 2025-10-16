"""CLI for WordBuilder."""

from __future__ import annotations

from .wordbuilder import WordBuilderGame


def main() -> None:
    """Run WordBuilder game."""
    print("WORDBUILDER".center(50, "="))
    print("\nBuild words from letter tiles!")

    game = WordBuilderGame()
    game.state = game.state.IN_PROGRESS

    while not game.is_game_over():
        print(f"\nTurn {game.turns + 1}/10")
        print(f"Score: {game.score}")
        print(f"Hand: {' '.join(sorted(game.hand))}")

        word = input("\nEnter word: ").strip()

        if game.make_move(word):
            points = sum(game.TILE_VALUES.get(letter, 0) for letter in word.upper())
            print(f"✓ {word.upper()} = {points} points!")
        else:
            print("✗ Invalid word or letters not available")

    print(f"\nGame Over! Final Score: {game.score}")


if __name__ == "__main__":
    main()
