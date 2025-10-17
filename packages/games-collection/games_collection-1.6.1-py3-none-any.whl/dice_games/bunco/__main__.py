"""Entry point for the Bunco game package.

This module allows the Bunco command-line interface to be executed directly
by running the package as a script:

    python -m dice_games.bunco

This is enabled by the `if __name__ == "__main__"` block, which calls the `main`
function from the `cli` module.
"""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    main()
