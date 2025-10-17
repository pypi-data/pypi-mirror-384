"""Entry point for the Farkle game package.

This module allows the Farkle command-line interface to be executed directly
by running the package as a script:

    python -m dice_games.farkle

This is enabled by the `if __name__ == "__main__"` block, which calls the `main`
function from the `cli` module.
"""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    main()
