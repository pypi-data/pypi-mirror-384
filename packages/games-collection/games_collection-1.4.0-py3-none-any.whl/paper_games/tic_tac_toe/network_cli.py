"""Command-line interface for network multiplayer tic-tac-toe."""

from __future__ import annotations

from .network import NetworkConfig, NetworkTicTacToeClient, NetworkTicTacToeServer


def play_network_server() -> None:
    """Run as server (host) for network play."""
    print("=== Tic-Tac-Toe Network Play (Server) ===")

    # Get configuration
    port_input = input("Port to listen on [5555]: ").strip()
    port = int(port_input) if port_input else 5555

    board_size_input = input("Board size (3, 4, or 5) [3]: ").strip()
    board_size = int(board_size_input) if board_size_input in {"3", "4", "5"} else 3

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

        # Game loop
        while not game.winner() and not game.is_draw():
            if game.current_turn == "X":
                # Server's turn (X)
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
                # Opponent's turn (O)
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

        # Announce result
        winner = game.winner()
        if winner == "X":
            print("\nYou win!")
        elif winner == "O":
            print("\nOpponent wins!")
        else:
            print("\nIt's a draw!")

    finally:
        server.close()


def play_network_client() -> None:
    """Run as client (join) for network play."""
    print("=== Tic-Tac-Toe Network Play (Client) ===")

    # Get server details
    host = input("Server address [localhost]: ").strip() or "localhost"
    port_input = input("Server port [5555]: ").strip()
    port = int(port_input) if port_input else 5555

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

        # Game loop
        while not game.winner() and not game.is_draw():
            if game.current_turn == client.opponent_symbol:
                # Opponent's turn
                print("\nWaiting for opponent...")
                position = client.receive_move()

                if position is None:
                    print("Connection lost.")
                    return

                game.make_move(position, client.opponent_symbol)
                coords_map = game._generate_coordinates()
                print(f"Opponent played {coords_map[position]}")
            else:
                # Client's turn
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

        # Announce result
        winner = game.winner()
        if winner == client.my_symbol:
            print("\nYou win!")
        elif winner == client.opponent_symbol:
            print("\nOpponent wins!")
        else:
            print("\nIt's a draw!")

    finally:
        client.close()


def play_network() -> None:
    """Main entry point for network play."""
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
    play_network()
