"""CLI for Trivia with online/offline selection."""

from __future__ import annotations

import argparse

from .trivia import TriviaGame


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(description="Play the Trivia quiz with optional online questions.")
    parser.add_argument("--questions", type=int, default=5, help="Number of questions to ask (default: 5)")
    parser.add_argument("--category", type=int, default=None, help="Numeric category identifier for the Open Trivia DB")
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default=None,
        help="Filter questions by difficulty",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Disable online fetching and rely on cached or bundled questions.",
    )
    return parser


def main() -> None:
    """Run Trivia game."""

    parser = build_parser()
    args = parser.parse_args()

    print("TRIVIA QUIZ".center(50, "="))
    print("\nAnswer multiple choice questions!")

    game = TriviaGame(
        num_questions=args.questions,
        category=args.category,
        difficulty=args.difficulty,
        enable_online=not args.offline,
    )
    game.state = game.state.IN_PROGRESS

    if args.offline:
        print("\nOffline mode enabled: using cached or bundled questions.")

    while not game.is_game_over():
        q = game.get_current_question()
        if q is None:
            break
        print(f"\nQuestion {game.current_question_idx + 1}/{len(game.questions)}")
        if q.get("category"):
            print(f"[{q['category']}] ({q.get('difficulty', 'unknown')})")
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
    total_questions = len(game.questions)
    print(f"Final Score: {game.score}/{total_questions}")
    percent = (game.score / total_questions) * 100 if total_questions else 0
    print(f"Percentage: {percent:.1f}%")


if __name__ == "__main__":
    main()
