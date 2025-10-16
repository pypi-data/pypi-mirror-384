"""Command line interface for 20 Questions."""

from __future__ import annotations

from .twenty_questions import TwentyQuestionsCLI


def main() -> None:
    """Run the 20 Questions command line interface."""
    TwentyQuestionsCLI().run()


if __name__ == "__main__":
    main()
