"""Online multiplayer exploration utilities for word games."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncIterator, Dict, List


@dataclass
class WordPlayEvent:
    """Event emitted during a multiplayer word-play session."""

    type: str
    player: str
    payload: Dict[str, object]


class WordPlaySession:
    """Synchronous cooperative or versus session tracker."""

    def __init__(self, name: str, *, cooperative: bool = True) -> None:
        self.name = name
        self.cooperative = cooperative
        self.players: List[str] = []
        self.history: List[WordPlayEvent] = []

    def join(self, player: str) -> None:
        """Register a player with the session."""

        if player not in self.players:
            self.players.append(player)
            self.history.append(WordPlayEvent("join", player, {"cooperative": self.cooperative}))

    def record_move(self, player: str, word: str, score: int) -> None:
        """Store a move for post-game analytics."""

        self.history.append(WordPlayEvent("move", player, {"word": word, "score": score}))


class AsyncWordPlaySession:
    """Asynchronous session wrapper leveraging asyncio queues."""

    def __init__(self, name: str, *, cooperative: bool = True) -> None:
        self._session = WordPlaySession(name, cooperative=cooperative)
        self._queue: asyncio.Queue[WordPlayEvent] = asyncio.Queue()

    async def join(self, player: str) -> None:
        """Register a player asynchronously."""

        self._session.join(player)
        await self._queue.put(WordPlayEvent("join", player, {"cooperative": self._session.cooperative}))

    async def record_move(self, player: str, word: str, score: int) -> None:
        """Log a move asynchronously and broadcast to listeners."""

        self._session.record_move(player, word, score)
        await self._queue.put(WordPlayEvent("move", player, {"word": word, "score": score}))

    async def stream(self) -> AsyncIterator[WordPlayEvent]:
        """Yield events as they are recorded."""

        while True:
            event = await self._queue.get()
            yield event

    def export_history(self) -> List[WordPlayEvent]:
        """Expose the accumulated synchronous history."""

        return list(self._session.history)
