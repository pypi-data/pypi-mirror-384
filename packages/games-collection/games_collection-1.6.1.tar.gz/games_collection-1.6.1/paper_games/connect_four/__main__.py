"""Command line interface for Connect Four."""

from __future__ import annotations

from .connect_four import ConnectFourCLI


def main() -> None:
    """Run the Connect Four command line interface."""
    ConnectFourCLI().run()


if __name__ == "__main__":
    main()
