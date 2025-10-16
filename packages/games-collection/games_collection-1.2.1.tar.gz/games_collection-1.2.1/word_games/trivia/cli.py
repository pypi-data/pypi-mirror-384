"""CLI for Trivia."""

from __future__ import annotations

from .trivia import TriviaGame


def main() -> None:
    """Run Trivia game."""
    print("TRIVIA QUIZ".center(50, "="))
    print("\nAnswer multiple choice questions!")

    game = TriviaGame(num_questions=5)
    game.state = game.state.IN_PROGRESS

    while not game.is_game_over():
        q = game.get_current_question()
        print(f"\nQuestion {game.current_question_idx + 1}/{len(game.questions)}")
        print(q["question"])

        for i, opt in enumerate(q["options"]):
            print(f"  {i + 1}. {opt}")

        while True:
            try:
                answer = int(input("\nYour answer (1-4): ")) - 1
                if game.make_move(answer):
                    break
                print("Invalid answer!")
            except ValueError:
                print("Enter a number 1-4")

    print(f"\n{'='*50}")
    print(f"Final Score: {game.score}/{len(game.questions)}")
    percent = (game.score / len(game.questions)) * 100
    print(f"Percentage: {percent:.1f}%")


if __name__ == "__main__":
    main()
