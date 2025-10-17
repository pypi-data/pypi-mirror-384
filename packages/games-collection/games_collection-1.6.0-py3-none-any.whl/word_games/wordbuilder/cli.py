"""CLI for WordBuilder."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .multiplayer import AsyncWordPlaySession, WordPlaySession
from .wordbuilder import DEFAULT_DICTIONARY_PATH, DEFAULT_TILE_BAG, DictionaryValidator, WordBuilderGame


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI parser for WordBuilder."""

    parser = argparse.ArgumentParser(description="Play WordBuilder with configurable dictionaries and tile bags.")
    parser.add_argument("--dictionary", type=Path, default=None, help="Path to a newline-delimited dictionary file")
    parser.add_argument(
        "--tile-config",
        type=Path,
        default=None,
        help="JSON file describing letter counts for the tile bag",
    )
    parser.add_argument(
        "--session",
        choices=["none", "sync", "async"],
        default="none",
        help="Enable cooperative/versus online session tracking",
    )
    parser.add_argument(
        "--versus",
        action="store_true",
        help="Switch the multiplayer session to versus mode",
    )
    return parser


def load_tile_config(path: Path | None) -> dict[str, int]:
    """Load a tile bag configuration from JSON if provided."""

    if path is None:
        return dict(DEFAULT_TILE_BAG)
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {letter.upper(): int(count) for letter, count in data.items()}


def main() -> None:
    """Run WordBuilder game."""

    parser = build_parser()
    args = parser.parse_args()

    print("WORDBUILDER".center(50, "="))
    print("\nBuild words from letter tiles!")

    dictionary_path = args.dictionary if args.dictionary is not None else DEFAULT_DICTIONARY_PATH
    validator = DictionaryValidator(dictionary_path=dictionary_path)
    tile_config = load_tile_config(args.tile_config)

    game = WordBuilderGame(dictionary=validator, tile_bag_config=tile_config)
    game.state = game.state.IN_PROGRESS

    session_type = args.session
    sync_session: WordPlaySession | None = None
    async_session: AsyncWordPlaySession | None = None

    if session_type == "sync":
        sync_session = WordPlaySession("CLI Session", cooperative=not args.versus)
        sync_session.join("CLI_Player")
        print("\nSynchronous session tracking enabled.")
    elif session_type == "async":
        async_session = AsyncWordPlaySession("CLI Session", cooperative=not args.versus)

        async def _join() -> None:
            await async_session.join("CLI_Player")

        asyncio.run(_join())
        print("\nAsynchronous session tracking enabled.")

    while not game.is_game_over():
        print(f"\nTurn {game.turns + 1}/10")
        print(f"Score: {game.score}")
        print(f"Hand: {' '.join(sorted(game.hand))}")

        word = input("\nEnter word: ").strip()

        if game.make_move(word):
            points = sum(game.TILE_VALUES.get(letter, 0) for letter in word.upper())
            print(f"✓ {word.upper()} = {points} points!")
            if sync_session is not None:
                sync_session.record_move("CLI_Player", word.upper(), points)
            if async_session is not None:

                async def _record() -> None:
                    await async_session.record_move("CLI_Player", word.upper(), points)

                asyncio.run(_record())
        else:
            print("✗ Invalid word or letters not available")

        if game.tile_bag.remaining() == 0:
            print("No tiles remaining in the bag!")

    print(f"\nGame Over! Final Score: {game.score}")

    if sync_session is not None:
        print("\nSession summary (sync):")
        for event in sync_session.history:
            print(f"  - {event.type.upper()} :: {event.player} :: {event.payload}")
    if async_session is not None:
        print("\nSession summary (async):")
        for event in async_session.export_history():
            print(f"  - {event.type.upper()} :: {event.player} :: {event.payload}")


if __name__ == "__main__":
    main()
