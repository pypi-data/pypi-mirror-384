"""Network multiplayer support for tic-tac-toe.

This module provides client/server functionality for playing tic-tac-toe
over the network between two human players.
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Optional

from .tic_tac_toe import TicTacToeGame


@dataclass
class NetworkConfig:
    """Configuration for network game."""

    host: str = "localhost"
    port: int = 5555
    board_size: int = 3
    win_length: Optional[int] = None


class NetworkTicTacToeServer:
    """Server for hosting a network tic-tac-toe game."""

    def __init__(self, config: NetworkConfig) -> None:
        """Initialize the server.

        Args:
            config: Network configuration.
        """
        self.config = config
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.game: Optional[TicTacToeGame] = None

    def start(self) -> None:
        """Start the server and wait for a client to connect."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.config.host, self.config.port))
        self.server_socket.listen(1)

        print(f"Server listening on {self.config.host}:{self.config.port}")
        print("Waiting for opponent to connect...")

        self.client_socket, address = self.server_socket.accept()
        print(f"Connected to {address}")

        # Initialize the game
        self.game = TicTacToeGame(
            human_symbol="X",
            computer_symbol="O",
            starting_symbol="X",
            board_size=self.config.board_size,
            win_length=self.config.win_length or self.config.board_size,
        )

        # Send game config to client
        self._send_message(
            {
                "type": "config",
                "board_size": self.config.board_size,
                "win_length": self.game.win_length,
                "your_symbol": "O",
                "opponent_symbol": "X",
            }
        )

    def send_move(self, position: int) -> bool:
        """Send a move to the opponent.

        Args:
            position: The position to play.

        Returns:
            True if the move was sent successfully.
        """
        if not self.game or not self.client_socket:
            return False

        self._send_message(
            {
                "type": "move",
                "position": position,
                "symbol": "X",
            }
        )
        return True

    def receive_move(self) -> Optional[int]:
        """Receive a move from the opponent.

        Returns:
            The position played by the opponent, or None if connection lost.
        """
        if not self.client_socket:
            return None

        try:
            message = self._receive_message()
            if message and message.get("type") == "move":
                return message.get("position")
        except (ConnectionResetError, BrokenPipeError):
            return None

        return None

    def close(self) -> None:
        """Close the server connection."""
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()

    def _send_message(self, message: dict) -> None:
        """Send a JSON message to the client."""
        if not self.client_socket:
            return
        data = json.dumps(message).encode("utf-8")
        self.client_socket.sendall(data + b"\n")

    def _receive_message(self) -> Optional[dict]:
        """Receive a JSON message from the client."""
        if not self.client_socket:
            return None

        buffer = b""
        while b"\n" not in buffer:
            chunk = self.client_socket.recv(1024)
            if not chunk:
                return None
            buffer += chunk

        data = buffer.split(b"\n")[0]
        return json.loads(data.decode("utf-8"))


class NetworkTicTacToeClient:
    """Client for connecting to a network tic-tac-toe game."""

    def __init__(self, host: str = "localhost", port: int = 5555) -> None:
        """Initialize the client.

        Args:
            host: Server hostname or IP address.
            port: Server port number.
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.game: Optional[TicTacToeGame] = None
        self.my_symbol: Optional[str] = None
        self.opponent_symbol: Optional[str] = None

    def connect(self) -> bool:
        """Connect to the server.

        Returns:
            True if connection was successful.
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to {self.host}:{self.port}")

            # Receive game config
            config = self._receive_message()
            if config and config.get("type") == "config":
                board_size = config.get("board_size", 3)
                win_length = config.get("win_length", board_size)
                self.my_symbol = config.get("your_symbol", "O")
                self.opponent_symbol = config.get("opponent_symbol", "X")

                self.game = TicTacToeGame(
                    human_symbol=self.my_symbol,
                    computer_symbol=self.opponent_symbol,
                    starting_symbol="X",
                    board_size=board_size,
                    win_length=win_length,
                )
                return True
        except (ConnectionRefusedError, socket.timeout):
            print("Could not connect to server.")
            return False

        return False

    def send_move(self, position: int) -> bool:
        """Send a move to the opponent.

        Args:
            position: The position to play.

        Returns:
            True if the move was sent successfully.
        """
        if not self.socket:
            return False

        self._send_message(
            {
                "type": "move",
                "position": position,
                "symbol": self.my_symbol,
            }
        )
        return True

    def receive_move(self) -> Optional[int]:
        """Receive a move from the opponent.

        Returns:
            The position played by the opponent, or None if connection lost.
        """
        if not self.socket:
            return None

        try:
            message = self._receive_message()
            if message and message.get("type") == "move":
                return message.get("position")
        except (ConnectionResetError, BrokenPipeError):
            return None

        return None

    def close(self) -> None:
        """Close the client connection."""
        if self.socket:
            self.socket.close()

    def _send_message(self, message: dict) -> None:
        """Send a JSON message to the server."""
        if not self.socket:
            return
        data = json.dumps(message).encode("utf-8")
        self.socket.sendall(data + b"\n")

    def _receive_message(self) -> Optional[dict]:
        """Receive a JSON message from the server."""
        if not self.socket:
            return None

        buffer = b""
        while b"\n" not in buffer:
            chunk = self.socket.recv(1024)
            if not chunk:
                return None
            buffer += chunk

        data = buffer.split(b"\n")[0]
        return json.loads(data.decode("utf-8"))
