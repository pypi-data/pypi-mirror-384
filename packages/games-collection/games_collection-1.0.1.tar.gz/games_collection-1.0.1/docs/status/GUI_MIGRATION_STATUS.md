# GUI Migration Status: Tkinter → PyQt5

This document tracks the progress of migrating game GUIs from Tkinter to PyQt5.

## Overview

- **Total Games**: 14
- **Completed**: 3 (21%)
- **Remaining**: 11 (79%)

## Status by Category

### Paper Games (2/2 completed)

| Game | Status | GUI File | Notes |
| -------------- | ----------- | ---------------------------------------- | ----------------------------------------------- |
| Dots and Boxes | ✅ Complete | `paper_games/dots_and_boxes/gui_pyqt.py` | Proof of concept migration |
| Battleship | ✅ Complete | `paper_games/battleship/gui_pyqt.py` | Drag/preview placement and salvo support |

### Card Games (2/12 completed)

| Game | Status | GUI File | Notes |
| ------------ | ---------- | -------- | --------------------------------- |
| Blackjack | ✅ Complete | `card_games/blackjack/gui_pyqt.py` | PyQt table with betting and animations |
| Bluff | ⏳ Pending | - | 451 lines, multi-player |
| ------------ | ---------- | ------------------------------------------ | --------------------------------- |
| Blackjack | ⏳ Pending | - | 688 lines, table-based layout |
| Bluff | ✅ Complete | `card_games/bluff/gui_pyqt.py` | PyQt5 port with log, scoreboard, and challenge dialogs |
| Bridge | ⏳ Pending | - | 488 lines, complex bidding system |
| Crazy Eights | ✅ Complete | `card_games/crazy_eights/gui_pyqt.py` | Feature parity with Tkinter GUI |
| ------------ | ---------- | ------------------------------------------- | --------------------------------- |
| Blackjack | ⏳ Pending | - | 688 lines, table-based layout |
| Bluff | ⏳ Pending | - | 451 lines, multi-player |
| Bridge | ✅ Complete | `card_games/bridge/gui_pyqt.py` | PyQt port with automated bidding/play |
| Crazy Eights | ⏳ Pending | - | 465 lines |
| Gin Rummy | ✅ Complete | `card_games/gin_rummy/gui_pyqt.py` | 709 lines, melding system |
| Go Fish | ✅ Complete | `card_games/go_fish/gui_pyqt.py` | 425 lines, simplest card game GUI |
| Hearts | ✅ Complete | `card_games/hearts/gui_pyqt.py` | 610 lines, trick-taking |
| Poker | ⏳ Pending | - | 437 lines, betting interface |
| Solitaire | ✅ Complete | `card_games/solitaire/gui_pyqt.py` | 729 lines, most complex GUI |
| Spades | ⏳ Pending | - | 582 lines, bidding and tricks |
| Poker | ✅ Complete | `card_games/poker/gui_pyqt.py` | 437 lines, betting interface |
| Solitaire | ⏳ Pending | - | 729 lines, most complex GUI |
| Spades | ✅ Complete | `card_games/spades/gui_pyqt.py` | Bidding, trick display, and scoring migrated |
| Uno | ⏳ Pending | - | 524 lines, special cards |
| Spades | ⏳ Pending | - | 582 lines, bidding and tricks |
| Uno | ✅ Complete | `card_games/uno/gui_pyqt.py` | Mirrors Tk interface with PyQt widgets |
| War | ⏳ Pending | - | 622 lines, simple mechanics |
| Uno | ⏳ Pending | - | 524 lines, special cards |
| War | ✅ Complete | `card_games/war/gui_pyqt.py` | Flashing war canvas, Save/Load integration |

## Migration Guidelines

For detailed migration instructions, see:

- [GUI Migration Guide](../gui/MIGRATION_GUIDE.md)
- [PyQt5 Implementation Summary](../gui/PYQT5_IMPLEMENTATION.md)
- [GUI Frameworks Documentation](../gui/FRAMEWORKS.md)

### Quick Steps

1. Create `gui_pyqt.py` alongside existing `gui.py`
1. Import PyQt5 widgets and base class from `common.gui_base_pyqt`
1. Convert widget mappings (see migration guide)
1. Update event handlers from Tkinter to PyQt5 signals/slots
1. Convert layouts from pack/grid to QVBoxLayout/QHBoxLayout
1. Add tests in `tests/test_gui_pyqt.py`
1. Update this status file
1. Update documentation files

### Suggested Migration Order

Based on complexity (lines of code and features):

1. **Go Fish** (425 lines) - Simplest card game ✅ Complete
1. **Poker** (437 lines) - Moderate complexity
1. **Bluff** (451 lines) - Multi-player interaction
1. **Crazy Eights** (465 lines) - Special rules
1. **Bridge** (488 lines) - Completed PyQt migration
1. **Uno** (524 lines) - Special cards and colors
1. **Spades** (582 lines) - Trick-taking with bidding ✅ Complete
1. **Hearts** (610 lines) - Trick-taking, point avoidance
1. **Battleship** (617 lines) - Complex board interaction
1. **War** (622 lines) - Despite simple rules, has animations
1. **Blackjack** (688 lines) - Betting and dealer logic
1. **Gin Rummy** (709 lines) - Complex melding system
1. **Solitaire** (729 lines) - ✅ Completed with PyQt5 toolbar and canvas migration

## Testing

All PyQt5 GUIs must include:

- Import test in `tests/test_gui_pyqt.py`
- Initialization test (with display skip for CI)
- Widget creation verification
- Integration with existing game engine

## Dependencies

PyQt5 is installed as an optional dependency:

```bash
pip install -e ".[gui]"
```

Or directly:

```bash
pip install pyqt5>=5.15
```

## Progress Updates

When a game is migrated:

1. Update the status table above (✅ Complete, add GUI file path)
1. Update the completion counts at the top
1. Update documentation files:
   - `docs/gui/PYQT5_IMPLEMENTATION.md`
   - `docs/gui/FRAMEWORKS.md`
   - `docs/gui/MIGRATION_GUIDE.md`
1. Add the module to `tests/test_gui_pyqt.py`

## Related Resources

- [PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [Qt5 Documentation](https://doc.qt.io/qt-5/)
- [Base GUI Class](common/gui_base_pyqt.py)
- [Example Implementation](paper_games/dots_and_boxes/gui_pyqt.py)
