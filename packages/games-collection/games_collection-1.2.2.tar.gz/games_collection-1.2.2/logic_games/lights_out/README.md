# Lights Out

Simulation-driven take on the classic toggle puzzle. Each fixture behaves like a physical light bulb with brightness,
energy consumption and wiring wear that changes as you play.

## Features

- Physically inspired light bulbs that track on/off state, brightness and wear
- Scrambled boards are always solvable because they are generated from a solved grid using real moves
- Ambient light bleed lets neighbouring bulbs glow faintly when a nearby light is on, giving the board a more natural
  appearance
- Telemetry readouts show instantaneous power usage, accumulated energy and an estimate of room brightness
- Configurable board size directly from the CLI (3×3 through 9×9)

## Running

```bash
python -m logic_games.lights_out
```

At runtime you can choose the board size. Symbols with higher density represent brighter bulbs, ranging from dark spaces
for fully-off fixtures to `#` for a fully lit bulb.
