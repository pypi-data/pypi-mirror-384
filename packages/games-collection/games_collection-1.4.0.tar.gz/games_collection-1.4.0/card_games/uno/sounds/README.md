# Uno Sound Files

This directory should contain `.wav` audio files for game sound effects.

## Required Sound Files

Place the following `.wav` files in this directory to enable sound effects:

- `card_play.wav` - Played when a regular card is placed
- `wild.wav` - Played when a wild card is played
- `skip.wav` - Played when a skip card is played
- `reverse.wav` - Played when a reverse card is played
- `draw_penalty.wav` - Played when a +2 or +4 card is played
- `uno.wav` - Played when a player declares UNO
- `win.wav` - Played when a player wins the game
- `swap.wav` - Played when hands are swapped (7 card with 7-0 rule)
- `rotate.wav` - Played when hands rotate (0 card with 7-0 rule)
- `draw.wav` - Played when a card is drawn from the deck

## Audio Format

- **Format**: WAV (uncompressed PCM)
- **Sample Rate**: 44100 Hz recommended
- **Bit Depth**: 16-bit recommended
- **Channels**: Mono or stereo

## Finding or Creating Sounds

### Free Sound Resources

1. **Freesound.org** - https://freesound.org/

   - Search for terms like "card shuffle", "card flip", "game win", "beep"
   - Make sure to check the license (CC0 or CC-BY recommended)

1. **OpenGameArt.org** - https://opengameart.org/

   - Browse game sound effects
   - Filter by license (Public Domain or CC0)

1. **Zapsplat.com** - https://www.zapsplat.com/

   - Free sound effects library
   - Requires attribution for free tier

### Creating Your Own Sounds

You can record or generate sounds using:

- **Audacity** (free, open-source audio editor)
- **LMMS** (free music production software)
- **Bfxr/Sfxr** (retro game sound effect generators)

### Example Sound Effects

- **card_play**: A soft "snap" or card flip sound
- **wild**: A magical "shimmer" or "sparkle" sound
- **skip**: A quick "whoosh" or "swish" sound
- **reverse**: A "rewind" or "turnaround" sound
- **draw_penalty**: A dramatic "warning" or "alarm" beep
- **uno**: An excited "ding" or voice saying "UNO!"
- **win**: A triumphant fanfare or celebration sound
- **swap**: A "switch" or "exchange" sound
- **rotate**: A "spinning" or "circular motion" sound
- **draw**: A soft card draw or shuffle sound

## Installation

1. Install pygame (required for sound playback):

   ```bash
   pip install pygame
   ```

1. Place sound files in this directory

1. Launch the game with GUI mode (use `--gui pyqt` for the PyQt5 interface or omit the value for Tkinter):

   ```bash
   python -m card_games.uno --gui pyqt
   ```

1. Sounds will play automatically during gameplay

## Troubleshooting

### No Sound Playing

- **Check pygame installation**: `python -c "import pygame; print('OK')"`
- **Verify sound files exist**: Look for `.wav` files in this directory
- **Check file names**: Files must match the exact names listed above
- **Test pygame mixer**:
  ```python
  import pygame
  pygame.mixer.init()
  sound = pygame.mixer.Sound("card_play.wav")
  sound.play()
  ```

### Sound Quality Issues

- Convert audio files to 44100 Hz, 16-bit WAV format
- Keep sound files short (0.5-2 seconds) for responsiveness
- Normalize volume levels across all sound files

## License

Sound files you add to this directory should be:

- Public domain
- Licensed under Creative Commons (CC0 or CC-BY preferred)
- Created by you with appropriate rights

Always provide attribution for sound effects that require it!
