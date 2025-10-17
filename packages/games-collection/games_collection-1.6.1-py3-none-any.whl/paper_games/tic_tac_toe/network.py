"""Network multiplayer support for Tic-Tac-Toe.

This module provides the client and server functionality required for playing
Tic-Tac-Toe over a network between two human players. It uses standard
sockets for communication and JSON for message passing, allowing for a simple
and robust multiplayer experience.

The server hosts the game, waits for a client to connect, and manages the
game state. The client connects to the server and exchanges moves with it.
Both the server and client are designed to be used in a terminal-based
environment.

Classes:
    NetworkConfig: A dataclass for holding network game configuration.
    NetworkTicTacToeServer: The server for hosting a network game.
    NetworkTicTacToeClient: The client for connecting to a network game.
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Optional

from .tic_tac_toe import TicTacToeGame


@dataclass
class NetworkConfig:
    """Configuration for a network-based Tic-Tac-Toe game.

    Attributes:
        host (str): The hostname or IP address for the server.
        port (int): The port number for the network connection.
        board_size (int): The size of the game board.
        win_length (Optional[int]): The number of symbols in a row needed to win.
    """

    host: str = "localhost"
    port: int = 5555
    board_size: int = 3
    win_length: Optional[int] = None


class NetworkTicTacToeServer:
    """A server for hosting a network-based Tic-Tac-Toe game.

    This class manages the server-side logic, including waiting for a client
    connection, initializing the game, and exchanging moves with the client.
    The server is responsible for setting the game rules (board size, etc.)
    and enforcing them.
    """

    def __init__(self, config: NetworkConfig) -> None:
        """Initializes the server with the given network configuration.

        Args:
            config (NetworkConfig): The configuration for the network game,
                                    including host, port, and board size.
        """
        self.config = config
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.game: Optional[TicTacToeGame] = None

    def start(self) -> None:
        """Starts the server, binds to the specified host and port, and waits
        for a client to connect. Once a client connects, it initializes the
        game and sends the configuration to the client.
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.config.host, self.config.port))
        self.server_socket.listen(1)

        print(f"Server listening on {self.config.host}:{self.config.port}")
        print("Waiting for opponent to connect...")

        self.client_socket, address = self.server_socket.accept()
        print(f"Connected to {address}")

        # Initialize the game with the server's configuration.
        self.game = TicTacToeGame(
            human_symbol="X",  # The server is always 'X'.
            computer_symbol="O",  # The client is always 'O'.
            starting_symbol="X",
            board_size=self.config.board_size,
            win_length=self.config.win_length or self.config.board_size,
        )

        # Send the game configuration to the client so it can set up its own game instance.
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
        """Sends a move to the connected client.

        Args:
            position (int): The board index of the move to send.

        Returns:
            bool: True if the move was sent successfully, False otherwise.
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
        """Receives a move from the connected client.

        This method blocks until a move is received or the connection is lost.

        Returns:
            Optional[int]: The board index of the opponent's move, or None if the
                           connection was lost or an invalid message was received.
        """
        if not self.client_socket:
            return None

        try:
            message = self._receive_message()
            if message and message.get("type") == "move":
                return message.get("position")
        except (ConnectionResetError, BrokenPipeError):
            # Handle cases where the client disconnects abruptly.
            return None

        return None

    def close(self) -> None:
        """Closes the client and server sockets."""
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()

    def _send_message(self, message: dict) -> None:
        """Encodes and sends a JSON message to the client.

        Args:
            message (dict): The dictionary to be sent as a JSON message.
        """
        if not self.client_socket:
            return
        data = json.dumps(message).encode("utf-8")
        self.client_socket.sendall(data + b"\n")

    def _receive_message(self) -> Optional[dict]:
        """Receives and decodes a JSON message from the client.

        This method reads from the socket until a newline character is found,
        which indicates the end of a message.

        Returns:
            Optional[dict]: The received message as a dictionary, or None if the
                            connection was closed.
        """
        if not self.client_socket:
            return None

        buffer = b""
        while b"\n" not in buffer:
            chunk = self.client_socket.recv(1024)
            if not chunk:
                # The connection was closed by the client.
                return None
            buffer += chunk

        data = buffer.split(b"\n")[0]
        return json.loads(data.decode("utf-8"))


class NetworkTicTacToeClient:
    """A client for connecting to a network-based Tic-Tac-Toe game.

    This class manages the client-side logic, including connecting to the
    server, receiving the game configuration, and exchanging moves with the
    server.
    """

    def __init__(self, host: str = "localhost", port: int = 5555) -> None:
        """Initializes the client with the server's host and port.

        Args:
            host (str): The hostname or IP address of the server.
            port (int): The port number of the server.
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.game: Optional[TicTacToeGame] = None
        self.my_symbol: Optional[str] = None
        self.opponent_symbol: Optional[str] = None

    def connect(self) -> bool:
        """Connects to the server and receives the initial game configuration.

        Returns:
            bool: True if the connection and setup were successful, False otherwise.
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to {self.host}:{self.port}")

            # Receive the game configuration from the server.
            config = self._receive_message()
            if config and config.get("type") == "config":
                board_size = config.get("board_size", 3)
                win_length = config.get("win_length", board_size)
                self.my_symbol = config.get("your_symbol", "O")
                self.opponent_symbol = config.get("opponent_symbol", "X")

                # Initialize a local game instance with the server's settings.
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
        """Sends a move to the server.

        Args:
            position (int): The board index of the move to send.

        Returns:
            bool: True if the move was sent successfully, False otherwise.
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
        """Receives a move from the server.

        This method blocks until a move is received or the connection is lost.

        Returns:
            Optional[int]: The board index of the opponent's move, or None if the
                           connection was lost or an invalid message was received.
        """
        if not self.socket:
            return None

        try:
            message = self._receive_message()
            if message and message.get("type") == "move":
                return message.get("position")
        except (ConnectionResetError, BrokenPipeError):
            # Handle cases where the server disconnects abruptly.
            return None

        return None

    def close(self) -> None:
        """Closes the client socket."""
        if self.socket:
            self.socket.close()

    def _send_message(self, message: dict) -> None:
        """Encodes and sends a JSON message to the server.

        Args:
            message (dict): The dictionary to be sent as a JSON message.
        """
        if not self.socket:
            return
        data = json.dumps(message).encode("utf-8")
        self.socket.sendall(data + b"\n")

    def _receive_message(self) -> Optional[dict]:
        """Receives and decodes a JSON message from the server.

        This method reads from the socket until a newline character is found,
        which indicates the end of a message.

        Returns:
            Optional[dict]: The received message as a dictionary, or None if the
                            connection was closed.
        """
        if not self.socket:
            return None

        buffer = b""
        while b"\n" not in buffer:
            chunk = self.socket.recv(1024)
            if not chunk:
                # The connection was closed by the server.
                return None
            buffer += chunk

        data = buffer.split(b"\n")[0]
        return json.loads(data.decode("utf-8"))
