"""Integration tests for Uno online multiplayer support."""

from __future__ import annotations

import asyncio
import random
from typing import Dict, Mapping

from card_games.uno import (
    HouseRules,
    NetworkGameInterface,
    UnoCard,
    UnoGame,
    UnoNetworkClient,
    UnoNetworkServer,
    UnoPlayer,
)


async def _scripted_client(client: UnoNetworkClient, prompts: Mapping[str, Mapping[str, object]]) -> None:
    """Consume server messages and respond according to a scripted prompt map."""

    while True:
        message = await client.read()
        msg_type = message.get("type")
        if msg_type == "prompt":
            prompt = str(message.get("prompt"))
            response: Dict[str, object] = {"prompt": prompt}
            response.update(prompts.get(prompt, {}))
            await client.respond(response)
        elif msg_type == "game_over":
            break


async def _run_network_game() -> str:
    loop = asyncio.get_running_loop()
    players = [UnoPlayer("Alice", is_human=True), UnoPlayer("Bob", is_human=True)]
    interface = NetworkGameInterface(players, loop)
    game = UnoGame(players=players, interface=interface, house_rules=HouseRules(), rng=random.Random(11))
    server = UnoNetworkServer(host="127.0.0.1", port=0, game=game)

    await server.start()
    # Configure a deterministic game state: Alice wins by playing her only card.
    players[0].hand = [UnoCard("red", "5")]
    players[1].hand = [UnoCard("blue", "9"), UnoCard("red", "7")]
    players[0].pending_uno = False
    players[1].pending_uno = False
    game.discard_pile = [UnoCard("red", "0")]
    game.active_color = "red"
    game.active_value = "0"
    game.current_index = 0
    interface.update_status(game)

    client_one = UnoNetworkClient("127.0.0.1", server.port)
    client_two = UnoNetworkClient("127.0.0.1", server.port)

    await client_one.connect()
    await client_two.connect()
    await asyncio.gather(client_one.ready(), client_two.ready())

    client_one_task = asyncio.create_task(
        _scripted_client(
            client_one,
            {
                "choose_action": {"action": "play", "card_index": 0, "declare_uno": True},
                "handle_drawn_card": {"action": "skip"},
                "choose_color": {"color": "red"},
                "prompt_jump_in": {"jump_in": False},
            },
        )
    )
    client_two_task = asyncio.create_task(
        _scripted_client(
            client_two,
            {
                "choose_action": {"action": "draw"},
                "handle_drawn_card": {"action": "skip"},
                "choose_color": {"color": "red"},
                "prompt_jump_in": {"jump_in": False},
            },
        )
    )

    winner = await server.wait_for_game_end()

    await asyncio.gather(client_one_task, client_two_task)
    await asyncio.gather(client_one.close(), client_two.close())
    await server.stop()
    return winner


def test_network_server_handles_simple_game() -> None:
    """Verify that the network server drives a simple Uno game to completion."""

    winner = asyncio.run(_run_network_game())
    assert winner == "Alice"
