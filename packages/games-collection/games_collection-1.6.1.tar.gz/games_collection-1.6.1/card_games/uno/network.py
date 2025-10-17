"""Async networking helpers for Uno online multiplayer."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence

from .uno import PlayerDecision, UnoCard, UnoGame, UnoInterface, UnoPlayer


class NetworkProtocolError(RuntimeError):
    """Raised when an invalid message is received over the network."""


@dataclass
class NetworkPlayerSession:
    """Represents a connected network player."""

    name: str
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    ready: bool = False
    task: Optional[asyncio.Task[Any]] = None


class NetworkGameInterface(UnoInterface):
    """Uno interface implementation that communicates with remote clients."""

    def __init__(self, players: Sequence[UnoPlayer], loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self._players = {player.name: player for player in players}
        self._responses: Dict[str, asyncio.Queue[Dict[str, Any]]] = {player.name: asyncio.Queue() for player in players}
        self._outgoing: Dict[str, asyncio.Queue[Dict[str, Any]]] = {player.name: asyncio.Queue() for player in players}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _is_loop_thread(loop: asyncio.AbstractEventLoop) -> bool:
        try:
            return asyncio.get_running_loop() is loop
        except RuntimeError:
            return False

    def get_outgoing_queue(self, player_name: str) -> asyncio.Queue[Dict[str, Any]]:
        """Return the outgoing queue for a specific player."""

        return self._outgoing[player_name]

    def submit_player_message(self, player_name: str, payload: Mapping[str, Any]) -> None:
        """Queue a response message from a remote player."""

        if player_name not in self._responses:
            raise NetworkProtocolError(f"Unknown player '{player_name}' in response.")
        queue = self._responses[player_name]
        message = dict(payload)
        if self._is_loop_thread(self.loop):
            queue.put_nowait(message)
        else:
            future = asyncio.run_coroutine_threadsafe(queue.put(message), self.loop)
            future.result()

    def _wait_for_prompt(self, player_name: str, prompt: str) -> Dict[str, Any]:
        """Wait synchronously for a response to a specific prompt."""

        queue = self._responses[player_name]
        while True:
            future = asyncio.run_coroutine_threadsafe(queue.get(), self.loop)
            response = future.result()
            if response.get("prompt") == prompt:
                return response

    def _send(self, message: Mapping[str, Any], *, target: Optional[str] = None) -> None:
        """Send a message to a specific player or broadcast to all players."""

        payload = dict(message)
        if target is None:
            targets = self._outgoing.values()
        else:
            targets = (self._outgoing[target],)
        in_loop_thread = self._is_loop_thread(self.loop)
        for queue in targets:
            if in_loop_thread:
                queue.put_nowait(dict(payload))
            else:
                future = asyncio.run_coroutine_threadsafe(queue.put(dict(payload)), self.loop)
                future.result()

    @staticmethod
    def _serialize_card(card: UnoCard) -> Dict[str, Any]:
        return {
            "color": card.color,
            "value": card.value,
            "label": card.label(),
            "effect": card.effect,
        }

    @staticmethod
    def _serialize_game(game: UnoGame) -> Dict[str, Any]:
        discard_top = game.discard_pile[-1] if game.discard_pile else None
        return {
            "active_color": game.active_color,
            "active_value": game.active_value,
            "direction": game.direction,
            "penalty_value": game.penalty_value,
            "penalty_amount": game.penalty_amount,
            "current_player": game.players[game.current_index].name,
            "discard_top": NetworkGameInterface._serialize_card(discard_top) if discard_top else None,
            "players": [
                {
                    "name": player.name,
                    "card_count": len(player.hand),
                    "is_human": player.is_human,
                    "team": player.team,
                }
                for player in game.players
            ],
            "available_colors": list(getattr(game, "available_colors", ())),
        }

    # ------------------------------------------------------------------
    # UnoInterface implementation
    # ------------------------------------------------------------------
    def show_heading(self, message: str) -> None:
        self._send({"type": "heading", "message": message})

    def show_message(self, message: str, *, color: str = "", style: str = "") -> None:
        self._send({"type": "message", "message": message, "color": color, "style": style})

    def show_hand(self, player: UnoPlayer, formatted_cards: Sequence[str]) -> None:
        self._send({"type": "hand", "cards": list(formatted_cards)}, target=player.name)

    def choose_action(
        self,
        game: UnoGame,
        player: UnoPlayer,
        playable: Sequence[int],
        penalty_active: bool,
    ) -> PlayerDecision:
        self._send(
            {
                "type": "prompt",
                "prompt": "choose_action",
                "playable": list(playable),
                "penalty_active": penalty_active,
                "hand": [self._serialize_card(card) for card in player.hand],
                "top_card": self._serialize_card(game.discard_pile[-1]),
            },
            target=player.name,
        )
        response = self._wait_for_prompt(player.name, "choose_action")
        return PlayerDecision(
            action=str(response.get("action", "draw")),
            card_index=response.get("card_index"),
            declare_uno=bool(response.get("declare_uno", False)),
            chosen_color=response.get("chosen_color"),
            swap_target=response.get("swap_target"),
        )

    def handle_drawn_card(self, game: UnoGame, player: UnoPlayer, card: UnoCard) -> PlayerDecision:
        self._send(
            {
                "type": "prompt",
                "prompt": "handle_drawn_card",
                "card": self._serialize_card(card),
            },
            target=player.name,
        )
        response = self._wait_for_prompt(player.name, "handle_drawn_card")
        return PlayerDecision(
            action=str(response.get("action", "skip")),
            card_index=response.get("card_index"),
            declare_uno=bool(response.get("declare_uno", False)),
            chosen_color=response.get("chosen_color"),
            swap_target=response.get("swap_target"),
        )

    def choose_color(self, player: UnoPlayer) -> str:
        available_colors = list(getattr(player, "available_colors", ()))
        self._send(
            {
                "type": "prompt",
                "prompt": "choose_color",
                "available_colors": available_colors,
            },
            target=player.name,
        )
        response = self._wait_for_prompt(player.name, "choose_color")
        chosen = str(response.get("color", ""))
        if chosen not in available_colors:
            raise NetworkProtocolError(f"Invalid color '{chosen}' returned by client.")
        return chosen

    def choose_swap_target(self, player: UnoPlayer, players: Sequence[UnoPlayer]) -> int:
        player_list = [p.name for p in players]
        self._send(
            {
                "type": "prompt",
                "prompt": "choose_swap_target",
                "players": player_list,
            },
            target=player.name,
        )
        response = self._wait_for_prompt(player.name, "choose_swap_target")
        return int(response.get("index", -1))

    def prompt_challenge(self, challenger: UnoPlayer, target: UnoPlayer, *, bluff_possible: bool) -> bool:
        self._send(
            {
                "type": "prompt",
                "prompt": "prompt_challenge",
                "target": target.name,
                "bluff_possible": bluff_possible,
            },
            target=challenger.name,
        )
        response = self._wait_for_prompt(challenger.name, "prompt_challenge")
        return bool(response.get("challenge", False))

    def notify_uno_called(self, player: UnoPlayer) -> None:
        self._send({"type": "event", "event": "uno_called", "player": player.name})

    def notify_uno_penalty(self, player: UnoPlayer) -> None:
        self._send({"type": "event", "event": "uno_penalty", "player": player.name})

    def announce_winner(self, winner: UnoPlayer) -> None:
        self._send({"type": "game_over", "winner": winner.name})

    def update_status(self, game: UnoGame) -> None:
        self._send({"type": "state", "state": self._serialize_game(game)})

    def render_card(self, card: UnoCard, *, emphasize: bool = False) -> str:
        return card.label()

    def render_color(self, color: str) -> str:
        return color

    def play_sound(self, sound_type: str) -> None:
        self._send({"type": "sound", "sound": sound_type})

    def prompt_jump_in(self, player: UnoPlayer, card: UnoCard) -> bool:
        self._send(
            {
                "type": "prompt",
                "prompt": "prompt_jump_in",
                "card": self._serialize_card(card),
            },
            target=player.name,
        )
        response = self._wait_for_prompt(player.name, "prompt_jump_in")
        return bool(response.get("jump_in", False))


class UnoNetworkServer:
    """Manage a networked Uno game over asyncio streams."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        game: UnoGame,
    ) -> None:
        self.host = host
        self.port = port
        self.game = game
        self.interface = game.interface
        if not isinstance(self.interface, NetworkGameInterface):
            raise TypeError("UnoNetworkServer requires a NetworkGameInterface.")
        self._server: Optional[asyncio.AbstractServer] = None
        self._sessions: Dict[str, NetworkPlayerSession] = {}
        self._ready: set[str] = set()
        self._game_task: Optional[asyncio.Task[str]] = None
        self._game_prepared = False
        self._game_started = asyncio.Event()

    async def start(self) -> None:
        """Start accepting player connections."""

        self._server = await asyncio.start_server(self._handle_client, self.host, self.port)
        sockets = self._server.sockets or []
        if sockets:
            sockname = sockets[0].getsockname()
            self.port = sockname[1]
        if not self._game_prepared:
            # Prepare the game but allow callers to override state first.
            self.game.setup()
            self.interface.update_status(self.game)
            self._game_prepared = True

    async def stop(self) -> None:
        """Stop the network server and disconnect clients."""

        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        for session in list(self._sessions.values()):
            if session.task:
                session.task.cancel()
            session.writer.close()
            try:
                await session.writer.wait_closed()
            except Exception:  # pragma: no cover - defensive cleanup
                pass
        self._sessions.clear()

    async def wait_for_game_end(self) -> str:
        """Wait for the game loop to complete and return the winner's name."""

        await self._game_started.wait()
        if self._game_task is None:
            raise RuntimeError("Game has not started yet.")
        return await self._game_task

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        player = self._assign_player(reader, writer)
        if player is None:
            await self._send_raw(writer, {"type": "error", "message": "No seats available."})
            writer.close()
            await writer.wait_closed()
            return

        session = self._sessions[player.name]
        await self._send_raw(
            writer,
            {
                "type": "assign",
                "player": player.name,
                "players": [p.name for p in self.game.players],
                "available_colors": list(getattr(self.game, "available_colors", ())),
            },
        )

        session.task = asyncio.create_task(self._outgoing_loop(player.name, writer))
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                try:
                    message = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError as exc:
                    raise NetworkProtocolError("Received invalid JSON from client.") from exc
                await self._handle_message(player, message)
        finally:
            if session.task:
                session.task.cancel()
            del self._sessions[player.name]
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:  # pragma: no cover - best effort
                pass

    def _assign_player(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> Optional[UnoPlayer]:
        assigned = set(self._sessions)
        for player in self.game.players:
            if player.name not in assigned:
                self._sessions[player.name] = NetworkPlayerSession(player.name, reader, writer)
                return player
        return None

    async def _outgoing_loop(self, player_name: str, writer: asyncio.StreamWriter) -> None:
        queue = self.interface.get_outgoing_queue(player_name)
        try:
            while True:
                message = await queue.get()
                await self._send_raw(writer, message)
        except asyncio.CancelledError:  # pragma: no cover - expected on shutdown
            return

    async def _handle_message(self, player: UnoPlayer, message: Mapping[str, Any]) -> None:
        msg_type = message.get("type")
        if msg_type == "ready":
            self._ready.add(player.name)
            if len(self._ready) == len(self.game.players) and self._game_task is None:
                self._game_task = asyncio.create_task(asyncio.to_thread(self._run_game))
                self._game_started.set()
        elif msg_type == "response":
            self.interface.submit_player_message(player.name, message)
        else:
            raise NetworkProtocolError(f"Unknown message type: {msg_type}")

    async def _send_raw(self, writer: asyncio.StreamWriter, payload: Mapping[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8") + b"\n"
        writer.write(data)
        await writer.drain()

    def _run_game(self) -> str:
        winner = self.game.play()
        return winner.name


class UnoNetworkClient:
    """Utility helper for connecting to an Uno network server."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.player: Optional[str] = None

    async def connect(self) -> Dict[str, Any]:
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        assign = await self._read()
        if assign.get("type") != "assign":
            raise NetworkProtocolError("Expected assignment handshake from server.")
        self.player = str(assign.get("player"))
        return assign

    async def ready(self) -> None:
        await self._send({"type": "ready"})

    async def read(self) -> Dict[str, Any]:
        return await self._read()

    async def respond(self, payload: Mapping[str, Any]) -> None:
        message = {"type": "response"}
        message.update(payload)
        await self._send(message)

    async def close(self) -> None:
        if self.writer:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except Exception:  # pragma: no cover - best effort
                pass
            self.writer = None
        self.reader = None

    async def _send(self, payload: Mapping[str, Any]) -> None:
        if not self.writer:
            raise NetworkProtocolError("Client is not connected.")
        data = json.dumps(payload).encode("utf-8") + b"\n"
        self.writer.write(data)
        await self.writer.drain()

    async def _read(self) -> Dict[str, Any]:
        if not self.reader:
            raise NetworkProtocolError("Client is not connected.")
        line = await self.reader.readline()
        if not line:
            raise NetworkProtocolError("Connection closed unexpectedly.")
        return json.loads(line.decode("utf-8"))
