# Sokoban

Sokoban is the classic warehouse puzzle where a lone worker must push heavy crates onto designated storage goals. This
implementation ships with a realistic ruleset, handcrafted levels, undo support, and a command-line interface for
playing through the puzzles.

## How to Play

- `@` – warehouse worker
- `$` – crate on a floor tile
- `.` – storage goal
- `*` – crate placed on a goal
- `+` – worker standing on a goal
- `#` – wall tiles that block movement

Crates can only be pushed (never pulled) and only one crate may be pushed at a time. A level is solved once every goal
tile is occupied by either the worker (`+`) or a crate (`*`).

## Controls

When running the CLI you can use the following commands:

| Command | Action |
| ------------------ | ----------------------------------- |
| `u`, `d`, `l`, `r` | Move up, down, left, or right |
| `undo` | Revert the previous move |
| `restart` | Reset the current level |
| `next`, `prev` | Cycle through the curated level set |
| `help` | Display the command reference |
| `quit` | Exit the game |

The interface also tracks both total moves and the number of pushes so you can challenge yourself to optimise your
solution.

## Running

```bash
python -m logic_games.sokoban
```
