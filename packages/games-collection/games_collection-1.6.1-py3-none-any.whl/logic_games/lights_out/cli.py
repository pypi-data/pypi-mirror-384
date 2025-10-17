"""Command-line interface for the Lights Out game.

This module provides a rich CLI experience for the Lights Out puzzle,
featuring a board with physically-inspired light bulbs that have varying
brightness levels. It includes telemetry readouts for power usage, energy
consumption, and room brightness, offering a more immersive gameplay
experience.

The main loop handles user input for board size and move coordinates,
updates the game state, and renders the board and telemetry data after
each move until the puzzle is solved.
"""

from statistics import mean

from .lights_out import LightBulb, LightsOutGame

# Brightness-to-character mapping for rendering the game board.
# Each tuple defines a brightness threshold and the corresponding character
# to display. The characters are ordered from darkest to brightest.
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
    """Convert a light bulb's brightness into an ASCII character representation.

    Args:
        bulb: The LightBulb instance to render.

    Returns:
        A single character representing the bulb's brightness.
    """
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
    """Prompt the user for an integer within a specified range.

    This function repeatedly prompts the user until a valid integer is
    entered. It provides feedback for invalid or out-of-range inputs.

    Args:
        message: The prompt message to display to the user.
        minimum: The minimum acceptable value for the integer.
        maximum: The maximum acceptable value for the integer.
        default: The default value to return if the user enters nothing.

    Returns:
        The validated integer entered by the user.
    """
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
    """Print the current game board to the console.

    The board is rendered with brightness-aware glyphs that represent
    the state of each light bulb.

    Args:
        game: The LightsOutGame instance containing the board state.
    """
    header = "    " + " ".join(str(i) for i in range(game.size))
    print(header)
    for r, row in enumerate(game.grid):
        cells = " ".join(_render_bulb(bulb) for bulb in row)
        print(f"  {r} {cells}")


def _print_telemetry(game: LightsOutGame) -> None:
    """Display real-time telemetry about the lighting grid.

    This includes metrics such as estimated room brightness, instantaneous
    power draw, total energy consumed, and bulb toggle statistics.

    Args:
        game: The LightsOutGame instance from which to pull telemetry data.
    """
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
    """Run the main game loop for the Lights Out CLI.

    This function initializes the game, prompts the user for the board size,
    and then enters a loop to accept player moves. The loop continues until

    the puzzle is solved, at which point it prints the final statistics.
    """
    # Print a welcome banner and instructions.
    print("LIGHTS OUT".center(60, "="))
    print("\nTurn all lights off by toggling fixtures. Brighter symbols indicate\n" "bulbs that are glowing or receiving light bleed from neighbours.")
    print("\nBrightness scale: " + " ".join(char for _, char in _BRIGHTNESS_CHARS))

    # Prompt the user for the desired board size and initialize the game.
    size = _prompt_for_integer(
        "\nChoose board size (default 5, range 3-9): ",
        minimum=3,
        maximum=9,
        default=5,
    )
    game = LightsOutGame(size=size)

    # Main game loop. Continues until all lights are off.
    while not game.is_game_over():
        print("\n" + "-" * 60)
        print(f"Move {game.moves + 1}")

        # Render the current state of the board and telemetry.
        _render_board(game)
        _print_telemetry(game)

        # Prompt the player for their next move.
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

        # Apply the move and check for errors.
        if not game.make_move((row, col)):
            print("That fixture cannot be toggled right now.")

    # Once the game is over, print the final results.
    print("\n" + "=" * 60)
    print(f"Puzzle solved in {game.moves} moves!")
    print(f"Total simulated time: {game.total_time_seconds:.1f} seconds")
    print(f"Total energy consumed: {game.total_energy_kwh:.4f} kWh")
    print(f"Final room brightness: {game.calculate_room_brightness():.1f} lux")


if __name__ == "__main__":
    main()
