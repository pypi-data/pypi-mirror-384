"""Main entry point for the Tic-Tac-Toe game."""

import sys

from . import play
from .network_cli import play_network
from .ultimate_cli import play_ultimate

# This script allows the game to be run directly from the command line.
if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--ultimate", "-u"]:
            play_ultimate()
        elif sys.argv[1] in ["--network", "-n"]:
            play_network()
        else:
            print("Unknown option. Available options:")
            print("  --ultimate, -u  : Play Ultimate Tic-Tac-Toe")
            print("  --network, -n   : Play network multiplayer")
    else:
        # Show available options
        print("Tic-Tac-Toe - Multiple game modes available:")
        print("  Run with --ultimate (-u) for Ultimate Tic-Tac-Toe")
        print("  Run with --network (-n) for network multiplayer\n")
        play()
