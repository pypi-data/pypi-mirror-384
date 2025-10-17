# Uno Game Features

This document provides an overview of the implemented features in the Uno game.

## Implemented Features

### House Rules

#### ✅ Stacking

**Status**: Fully Implemented

Players can stack +2 and +4 cards to increase the penalty for the next player. When a +2 or +4 is played, the next
player can either:

- Accept the penalty and draw the accumulated cards
- Stack another +2 or +4 to pass the penalty to the next player

Enable with: `--stacking` flag

**Implementation**: See `_execute_play()` and `_accept_penalty()` methods in `uno.py`

#### ✅ Jump-In

**Status**: Fully Implemented

The jump-in rule allows players to play a card that is identical (same color AND value) to the card just played, even if
it's not their turn. This interrupts the normal turn order.

Enable with: `--jump-in` flag

**How it works**:

1. After each non-wild card is played, the game checks all other players clockwise from the current player
1. Human players are prompted if they want to jump in with an identical card
1. Bot players decide probabilistically based on their personality, hand size, and whether it's an action card
1. The first player (in clockwise order) to accept jumps in and plays their identical card
1. Turn order is interrupted - the jump-in player becomes the current player

**Bot behavior**:

- Aggressive bots: 70% base probability to jump in
- Balanced bots: 50% base probability to jump in
- Easy bots: 30% base probability to jump in
- Probability increases with fewer cards in hand
- Probability increases for action cards (skip, reverse, +2)

**Implementation**: See `_check_jump_in()` and `_bot_should_jump_in()` methods in `uno.py`

#### ✅ 7-0 Swapping

**Status**: Fully Implemented

This house rule adds special effects when 7s and 0s are played:

- **7 card**: The player who played it swaps hands with another player of their choice
- **0 card**: All players pass their hands in the direction of play (clockwise or counter-clockwise)

Enable with: `--seven-zero` flag

**Implementation**: See `_swap_hands()`, `_rotate_hands()`, and the 7-0 handling in `_execute_play()` in `uno.py`

### Team Play Mode

#### ✅ 2v2 Team Mode

**Status**: Fully Implemented

Players are organized into two teams (Team 0 and Team 1) in a 4-player game. Team members work together to help each
other win.

- Players alternate between teams (Player 0 & 2 vs Player 1 & 3)
- Victory is achieved when any team member runs out of cards
- Team victory is announced with the team name

Enable with: `--team-mode` flag (requires exactly 4 players)

**Implementation**: See `build_players()` and team victory logic in `_execute_play()` in `uno.py`

### GUI Features

#### ✅ Card Animations

**Status**: Basic Implementation

Visual feedback when cards are played:

- Highlight animation with gold color
- Pulsing effect for 6 animation steps
- Non-blocking animation that doesn't interrupt gameplay

Enable with: `enable_animations=True` (default) in GUI initialization

**Implementation**: See `_animate_card_play()` in `gui.py`

**Future Enhancements**:

- Sliding animations from hand to discard pile
- Rotation/flip effects
- Fade-in/fade-out transitions
- Position-based animations

#### ✅ Sound Effects

**Status**: Infrastructure Complete, Implementation Optional

Sound effects are supported through a modular sound manager that uses pygame.mixer.

**Sound Types**:

- `card_play` - Regular card play
- `wild` - Wild card played
- `skip` - Skip action card
- `reverse` - Reverse action card
- `draw_penalty` - +2 or +4 card played
- `uno` - Player declares UNO
- `win` - Victory sound
- `swap` - Hands swapped (7 card)
- `rotate` - Hands rotated (0 card)
- `draw` - Card drawn from deck

Enable with: `enable_sounds=True` in GUI initialization

**Requirements**:

- `pygame` library: `pip install pygame`
- Sound files (.wav format) in `sounds/` directory

**Implementation**: See `sound_manager.py` and `play_sound()` in `gui.py`

**Note**: Sound effects gracefully degrade if pygame is not installed or sound files are missing.

## Not Implemented / Future Enhancements

### ❌ Online Multiplayer

**Status**: Documentation Only

Online multiplayer would require:

- WebSocket server implementation
- Client-side networking code
- Game state synchronization
- Player authentication
- Lobby system

**Reference**: See `MULTIPLAYER_GUIDE.md` for architecture guidelines

This feature is out of scope for the current implementation as it requires significant architectural changes.

### ❌ Custom Deck Designer

**Status**: Documentation Only

A custom deck designer would allow:

- Creating custom card types with special effects
- Defining new colors and values
- JSON-based deck definitions
- Deck validation and loading

**Reference**: See `CUSTOM_DECK_GUIDE.md` for implementation guidelines

This feature is out of scope for the current implementation as it requires:

- Extended card class with custom effects
- Custom effect handler
- Deck loader and validator
- Integration with game engine

## Usage Examples

Pass `--gui pyqt` to launch the new PyQt5 interface or omit the value/choose
`--gui tk` for the legacy Tkinter window.

### Enable All House Rules

```bash
python -m card_games.uno --gui pyqt --stacking --seven-zero --jump-in
```

### Team Mode with Stacking

```bash
python -m card_games.uno --gui pyqt --team-mode --stacking --players 4
```

### Play with Sound Effects (requires pygame)

```bash
pip install pygame
python -m card_games.uno --gui pyqt --seven-zero
# Sound effects will play if sound files are present in sounds/ directory
```

## Development Notes

### Adding Sound Files

1. Install pygame: `pip install pygame`
1. Create a `sounds/` directory in `card_games/uno/`
1. Add .wav files with the following names:
   - `card_play.wav`
   - `wild.wav`
   - `skip.wav`
   - `reverse.wav`
   - `draw_penalty.wav`
   - `uno.wav`
   - `win.wav`
   - `swap.wav`
   - `rotate.wav`
   - `draw.wav`

### Extending Animations

The `_animate_card_play()` method in `gui.py` can be extended to include more sophisticated animations. Consider using:

- Tkinter's canvas widget for custom drawing
- Coordinate-based position animations
- PIL/Pillow for image transformations
- Custom animation frameworks

## Testing

To test the implemented features:

1. **Stacking**: Play +2 or +4 cards in sequence
1. **7-0 Swapping**: Play 7 or 0 cards with the rule enabled
1. **Team Mode**: Start a 4-player game with team mode
1. **Animations**: Watch cards highlight when played in GUI
1. **Sound Effects**: Enable sounds and listen for audio feedback

## Contributing

When implementing new features:

1. Follow the existing code structure
1. Add appropriate error handling
1. Update this documentation
1. Consider backward compatibility
1. Test with both console and GUI interfaces
