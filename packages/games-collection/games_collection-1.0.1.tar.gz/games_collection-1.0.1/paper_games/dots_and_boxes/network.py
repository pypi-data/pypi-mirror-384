"""Network multiplayer mode for Dots and Boxes.

This module provides basic network multiplayer functionality using sockets.
One player hosts a game, and another connects to play.
"""

from __future__ import annotations

import json
import socket
import sys
from typing import Optional

from .dots_and_boxes import DotsAndBoxes


class NetworkGame:
    """Base class for network multiplayer games."""

    def __init__(self, size: int = 2, player_name: str = "Player") -> None:
        """Initialize network game.

        Args:
            size: Board size
            player_name: Name of the local player
        """
        self.size = size
        self.player_name = player_name
        self.opponent_name = "Opponent"
        self.sock: Optional[socket.socket] = None
        self.conn: Optional[socket.socket] = None

    def send_message(self, message: dict) -> None:
        """Send a JSON message over the network."""
        if self.conn:
            data = json.dumps(message).encode("utf-8")
            self.conn.sendall(len(data).to_bytes(4, "big"))
            self.conn.sendall(data)

    def receive_message(self) -> Optional[dict]:
        """Receive a JSON message from the network."""
        if not self.conn:
            return None

        try:
            # Receive message length
            length_bytes = self.conn.recv(4)
            if not length_bytes:
                return None
            length = int.from_bytes(length_bytes, "big")

            # Receive message data
            data = b""
            while len(data) < length:
                chunk = self.conn.recv(length - len(data))
                if not chunk:
                    return None
                data += chunk

            return json.loads(data.decode("utf-8"))
        except (ConnectionError, json.JSONDecodeError):
            return None

    def close(self) -> None:
        """Close the network connection."""
        if self.conn:
            self.conn.close()
        if self.sock:
            self.sock.close()


class NetworkHost(NetworkGame):
    """Host a network multiplayer game."""

    def __init__(self, size: int = 2, player_name: str = "Host", port: int = 5555) -> None:
        """Initialize host.

        Args:
            size: Board size
            player_name: Name of the host player
            port: Port to listen on
        """
        super().__init__(size=size, player_name=player_name)
        self.port = port

    def wait_for_connection(self) -> bool:
        """Wait for a client to connect.

        Returns:
            True if connection was successful, False otherwise
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(("", self.port))
            self.sock.listen(1)

            print(f"Waiting for opponent to connect on port {self.port}...")
            self.conn, addr = self.sock.accept()
            print(f"Connected to {addr}")

            # Send initial game info
            self.send_message({"type": "init", "size": self.size, "host_name": self.player_name})

            # Receive opponent info
            msg = self.receive_message()
            if msg and msg.get("type") == "init_response":
                self.opponent_name = msg.get("client_name", "Opponent")
                return True

            return False
        except (OSError, ConnectionError) as e:
            print(f"Error setting up host: {e}", file=sys.stderr)
            return False


class NetworkClient(NetworkGame):
    """Connect to a network multiplayer game."""

    def __init__(self, size: int = 2, player_name: str = "Client", host: str = "localhost", port: int = 5555) -> None:
        """Initialize client.

        Args:
            size: Expected board size
            player_name: Name of the client player
            host: Host address to connect to
            port: Port to connect to
        """
        super().__init__(size=size, player_name=player_name)
        self.host = host
        self.port = port

    def connect(self) -> bool:
        """Connect to the host.

        Returns:
            True if connection was successful, False otherwise
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn = self.sock
            print(f"Connecting to {self.host}:{self.port}...")
            self.sock.connect((self.host, self.port))
            print("Connected!")

            # Receive initial game info
            msg = self.receive_message()
            if msg and msg.get("type") == "init":
                self.size = msg.get("size", self.size)
                self.opponent_name = msg.get("host_name", "Host")

                # Send response
                self.send_message({"type": "init_response", "client_name": self.player_name})
                return True

            return False
        except (OSError, ConnectionError) as e:
            print(f"Error connecting to host: {e}", file=sys.stderr)
            return False


def play_network_game(game_obj: NetworkGame, is_host: bool) -> None:
    """Play a network multiplayer game.

    Args:
        game_obj: NetworkHost or NetworkClient instance
        is_host: True if this is the host (goes first), False if client
    """
    game = DotsAndBoxes(size=game_obj.size, human_name=game_obj.player_name, computer_name=game_obj.opponent_name)
    my_turn = is_host

    print(f"\nStarting game! You are: {game_obj.player_name}")
    print(f"Board size: {game_obj.size}x{game_obj.size}")
    print(f"You go {'first' if is_host else 'second'}.\n")

    try:
        while not game.is_finished():
            print("\n" + game.render())
            print(f"Score - {game_obj.player_name}: {game.scores[game_obj.player_name]} | " f"{game_obj.opponent_name}: {game.scores[game_obj.opponent_name]}")

            if my_turn:
                print("Your turn!")
                move = input("Your move (orientation row col): ").strip().split()
                if len(move) != 3:
                    print("Please enter orientation and coordinates like 'v 1 0'.")
                    continue

                orientation, row_str, col_str = move
                try:
                    row, col = int(row_str), int(col_str)
                    completed = game.claim_edge(orientation, row, col, player=game_obj.player_name)

                    # Send move to opponent
                    game_obj.send_message({"type": "move", "orientation": orientation, "row": row, "col": col})

                    if not completed:
                        my_turn = False
                        print("Turn passed to opponent.")

                except (ValueError, KeyError) as exc:
                    print(exc)
                    continue
            else:
                print("Waiting for opponent's move...")
                msg = game_obj.receive_message()
                if not msg or msg.get("type") != "move":
                    print("Connection lost or invalid message received.")
                    break

                orientation = msg["orientation"]
                row = msg["row"]
                col = msg["col"]

                try:
                    completed = game.claim_edge(orientation, row, col, player=game_obj.opponent_name)
                    print(f"Opponent plays: {orientation} {row} {col}")

                    if not completed:
                        my_turn = True
                        print("Your turn!")

                except (ValueError, KeyError) as exc:
                    print(f"Opponent made invalid move: {exc}")
                    break

        # Game finished
        print("\n" + game.render())
        my_score = game.scores[game_obj.player_name]
        opponent_score = game.scores[game_obj.opponent_name]

        print("\nGame Over!")
        print(f"{game_obj.player_name}: {my_score}")
        print(f"{game_obj.opponent_name}: {opponent_score}")

        if my_score > opponent_score:
            print("You win! 🎉")
        elif my_score < opponent_score:
            print("Opponent wins! 🤖")
        else:
            print("It's a tie! 🤝")

    finally:
        game_obj.close()


def host_game(size: int = 2, port: int = 5555, player_name: str = "Host") -> None:
    """Host a network multiplayer game.

    Args:
        size: Board size
        port: Port to listen on
        player_name: Name of the host player
    """
    host = NetworkHost(size=size, player_name=player_name, port=port)
    if host.wait_for_connection():
        play_network_game(host, is_host=True)
    else:
        print("Failed to establish connection.")


def join_game(host: str = "localhost", port: int = 5555, player_name: str = "Client") -> None:
    """Join a network multiplayer game.

    Args:
        host: Host address
        port: Port to connect to
        player_name: Name of the client player
    """
    client = NetworkClient(player_name=player_name, host=host, port=port)
    if client.connect():
        play_network_game(client, is_host=False)
    else:
        print("Failed to connect.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "host":
        host_game(size=2, port=5555, player_name="Host")
    elif len(sys.argv) > 1 and sys.argv[1] == "join":
        host_addr = sys.argv[2] if len(sys.argv) > 2 else "localhost"
        join_game(host=host_addr, port=5555, player_name="Client")
    else:
        print("Usage: python -m paper_games.dots_and_boxes.network [host|join [host_address]]")
