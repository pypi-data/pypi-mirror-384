"""CLI for Lights Out."""

from __future__ import annotations

from statistics import mean

from .lights_out import LightBulb, LightsOutGame

_BRIGHTNESS_CHARS: tuple[tuple[float, str], ...] = (
    (0.05, " "),
    (0.15, "."),
    (0.3, ":"),
    (0.5, "*"),
    (0.75, "O"),
    (0.9, "@"),
    (1.01, "#"),
)


def _render_bulb(bulb: LightBulb) -> str:
    """Convert a bulb brightness into an ASCII representation."""

    for threshold, char in _BRIGHTNESS_CHARS:
        if bulb.brightness < threshold:
            return char
    return _BRIGHTNESS_CHARS[-1][1]


def _prompt_for_integer(
    message: str,
    *,
    minimum: int,
    maximum: int,
    default: int,
) -> int:
    """Prompt the user for an integer within a range."""

    while True:
        raw = input(message).strip()
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError:
            print("Please enter a whole number.")
            continue

        if value < minimum or value > maximum:
            print(f"Please choose a value between {minimum} and {maximum}.")
            continue

        return value


def _render_board(game: LightsOutGame) -> None:
    """Print the current board with brightness-aware glyphs."""

    header = "    " + " ".join(str(i) for i in range(game.size))
    print(header)
    for r, row in enumerate(game.grid):
        cells = " ".join(_render_bulb(bulb) for bulb in row)
        print(f"  {r} {cells}")


def _print_telemetry(game: LightsOutGame) -> None:
    """Display realistic telemetry about the lighting state."""

    brightness = game.calculate_room_brightness()
    power_draw = game.calculate_power_draw()
    toggles = [bulb.toggle_count for row in game.grid for bulb in row]
    avg_toggles = mean(toggles) if toggles else 0
    max_toggles = max(toggles) if toggles else 0

    print(f"Room brightness: {brightness:.1f} lux")
    print(f"Instant power draw: {power_draw:.1f} W")
    print(f"Energy consumed so far: {game.total_energy_kwh:.4f} kWh")
    print(f"Average toggles per bulb: {avg_toggles:.1f} (max {max_toggles})")


def main() -> None:
    """Run Lights Out."""

    print("LIGHTS OUT".center(60, "="))
    print("\nTurn all lights off by toggling fixtures. Brighter symbols indicate\n" "bulbs that are glowing or receiving light bleed from neighbours.")
    print("\nBrightness scale: " + " ".join(char for _, char in _BRIGHTNESS_CHARS))

    size = _prompt_for_integer(
        "\nChoose board size (default 5, range 3-9): ",
        minimum=3,
        maximum=9,
        default=5,
    )
    game = LightsOutGame(size=size)

    while not game.is_game_over():
        print("\n" + "-" * 60)
        print(f"Move {game.moves + 1}")
        _render_board(game)
        _print_telemetry(game)

        row = _prompt_for_integer(
            "Row to toggle (0-indexed): ",
            minimum=0,
            maximum=game.size - 1,
            default=0,
        )
        col = _prompt_for_integer(
            "Column to toggle (0-indexed): ",
            minimum=0,
            maximum=game.size - 1,
            default=0,
        )

        if not game.make_move((row, col)):
            print("That fixture cannot be toggled right now.")

    print("\n" + "=" * 60)
    print(f"Puzzle solved in {game.moves} moves!")
    print(f"Total simulated time: {game.total_time_seconds:.1f} seconds")
    print(f"Total energy consumed: {game.total_energy_kwh:.4f} kWh")
    print(f"Final room brightness: {game.calculate_room_brightness():.1f} lux")


if __name__ == "__main__":
    main()
