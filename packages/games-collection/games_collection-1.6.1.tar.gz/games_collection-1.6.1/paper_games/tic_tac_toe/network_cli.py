"""Command-line interface for network multiplayer Tic-Tac-Toe.

This module provides the user interface for hosting or joining a network-based
Tic-Tac-Toe game. It allows players to choose whether to act as a server (host)
or a client (join), and it handles the interaction for setting up the game
and playing it over the network.

The CLI uses the `NetworkTicTacToeServer` and `NetworkTicTacToeClient` classes
from the `network` module to manage the underlying network communication and
game logic.

Functions:
    play_network_server(): Runs the game loop for the server (host).
    play_network_client(): Runs the game loop for the client (joiner).
    play_network(): The main entry point that prompts the user to choose
                    between hosting and joining a game.
"""

from __future__ import annotations

from .network import NetworkConfig, NetworkTicTacToeClient, NetworkTicTacToeServer


def play_network_server() -> None:
    """Runs the game as a server (host) for network play.

    This function prompts the user for the port and board size, then starts
    a server and waits for a client to connect. Once connected, it manages
    the game loop, alternating turns between the server and the client.
    """
    print("=== Tic-Tac-Toe Network Play (Server) ===")

    # Get the desired port and board size from the user.
    port_input = input("Port to listen on [5555]: ").strip()
    port = int(port_input) if port_input else 5555

    board_size_input = input("Board size (3, 4, or 5) [3]: ").strip()
    board_size = int(board_size_input) if board_size_input in {"3", "4", "5"} else 3

    # Configure and start the server.
    config = NetworkConfig(host="0.0.0.0", port=port, board_size=board_size)
    server = NetworkTicTacToeServer(config)

    try:
        server.start()
        game = server.game

        if not game:
            print("Failed to initialize game.")
            return

        print("\nYou are X (goes first)")
        print(game.render(show_reference=True))

        # The main game loop continues until there is a winner or a draw.
        while not game.winner() and not game.is_draw():
            if game.current_turn == "X":
                # It's the server's turn (Player X).
                move_str = input("\nYour move (e.g., A1, B2): ").strip()
                try:
                    position = game.parse_coordinate(move_str)
                except ValueError as e:
                    print(e)
                    continue

                if not game.make_move(position, "X"):
                    print("Invalid move. Try again.")
                    continue

                server.send_move(position)
                print(f"\nYou played {move_str}")
            else:
                # It's the opponent's turn (Player O).
                print("\nWaiting for opponent...")
                position = server.receive_move()

                if position is None:
                    print("Connection lost.")
                    return

                game.make_move(position, "O")
                coords_map = game._generate_coordinates()
                print(f"Opponent played {coords_map[position]}")

            print("\n" + game.render())

            if not game.winner() and not game.is_draw():
                game.swap_turn()

        # Announce the final result of the game.
        winner = game.winner()
        if winner == "X":
            print("\nYou win!")
        elif winner == "O":
            print("\nOpponent wins!")
        else:
            print("\nIt's a draw!")

    finally:
        # Ensure the server connection is closed.
        server.close()


def play_network_client() -> None:
    """Runs the game as a client (joiner) for network play.

    This function prompts the user for the server's address and port, then
    connects to the server. Once connected, it manages the game loop,
    alternating turns with the server.
    """
    print("=== Tic-Tac-Toe Network Play (Client) ===")

    # Get the server's address and port from the user.
    host = input("Server address [localhost]: ").strip() or "localhost"
    port_input = input("Server port [5555]: ").strip()
    port = int(port_input) if port_input else 5555

    # Configure and connect the client.
    client = NetworkTicTacToeClient(host, port)

    try:
        if not client.connect():
            return

        game = client.game
        if not game:
            print("Failed to initialize game.")
            return

        print(f"\nYou are {client.my_symbol} (goes second)")
        print(game.render(show_reference=True))

        # The main game loop continues until there is a winner or a draw.
        while not game.winner() and not game.is_draw():
            if game.current_turn == client.opponent_symbol:
                # It's the opponent's turn (the server).
                print("\nWaiting for opponent...")
                position = client.receive_move()

                if position is None:
                    print("Connection lost.")
                    return

                game.make_move(position, client.opponent_symbol)
                coords_map = game._generate_coordinates()
                print(f"Opponent played {coords_map[position]}")
            else:
                # It's the client's turn.
                move_str = input("\nYour move (e.g., A1, B2): ").strip()
                try:
                    position = game.parse_coordinate(move_str)
                except ValueError as e:
                    print(e)
                    continue

                if not game.make_move(position, client.my_symbol):
                    print("Invalid move. Try again.")
                    continue

                client.send_move(position)
                print(f"\nYou played {move_str}")

            print("\n" + game.render())

            if not game.winner() and not game.is_draw():
                game.swap_turn()

        # Announce the final result of the game.
        winner = game.winner()
        if winner == client.my_symbol:
            print("\nYou win!")
        elif winner == client.opponent_symbol:
            print("\nOpponent wins!")
        else:
            print("\nIt's a draw!")

    finally:
        # Ensure the client connection is closed.
        client.close()


def play_network() -> None:
    """The main entry point for network play.

    This function prompts the user to choose whether they want to host a game
    (act as a server) or join a game (act as a client), and then calls the
    appropriate function to start the game.
    """
    print("=== Tic-Tac-Toe Network Multiplayer ===")
    print("1. Host a game (server)")
    print("2. Join a game (client)")

    choice = input("\nYour choice [1]: ").strip() or "1"

    if choice == "1":
        play_network_server()
    elif choice == "2":
        play_network_client()
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    # This allows the script to be run directly to start network play.
    play_network()
