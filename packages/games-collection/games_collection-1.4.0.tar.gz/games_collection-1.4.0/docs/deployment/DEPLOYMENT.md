# Deployment Guide

This guide covers different deployment methods for the Games Collection.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation from PyPI](#installation-from-pypi)
- [Standalone Executables](#standalone-executables)
- [Docker Deployment](#docker-deployment)
- [Building from Source](#building-from-source)
- [Cross-Platform Compatibility](#cross-platform-compatibility)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Minimum Requirements

- Python 3.9 or higher (for source installation)
- 50 MB disk space (100 MB recommended)
- Terminal/Command Prompt access

### Recommended

- Python 3.11 or higher
- 100 MB disk space
- 2 GB RAM

### Platform Support

✅ **Fully Supported:**

- Linux (Ubuntu 20.04+, Debian 11+, Fedora 35+)
- macOS (10.15 Catalina or later)
- Windows (10/11)

✅ **Tested Python Versions:**

- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12

## Release Validation

All PyPI releases are gated by an automated smoke test that runs in GitHub Actions whenever a release is published or the workflow is dispatched manually. The workflow builds the source and wheel distributions, installs the generated wheel into an isolated virtual environment, and verifies two representative entry points: `games-collection --help` and `python -m card_games.go_fish --gui-framework pyqt5 --help`. The PyPI upload proceeds only if these commands succeed, ensuring that the published artifacts are installable and expose their CLI help correctly.

## Installation from PyPI

### Standard Installation

```bash
pip install games-collection
```

### With GUI Support

```bash
pip install games-collection[gui]
```

### Development Installation

```bash
pip install games-collection[dev]
```

### Running Games

After installation, you can run games using the `games-*` commands:

```bash
# Card games
games-poker
games-blackjack
games-uno
games-war

# Paper games
games-tic-tac-toe
games-battleship
games-checkers

# Dice games
games-craps
games-bunco

# See all available games
pip show games-collection
```

## Standalone Executables

Standalone executables bundle all dependencies, requiring no Python installation.

### Downloading Pre-built Executables

1. Go to the [Releases page](https://github.com/saint2706/Games/releases)
1. Download the executable for your platform:
   - **Linux**: `games-collection-linux`
   - **macOS**: `games-collection-macos`
   - **Windows**: `games-collection-windows.exe`

### Running the Executable

#### Linux/macOS

```bash
# Make executable
chmod +x games-collection-linux

# Run
./games-collection-linux
```

#### Windows

```cmd
games-collection-windows.exe
```

### Building Your Own Executable

#### Using PyInstaller

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller build_configs/pyinstaller/games.spec --clean

# Find executable in dist/
```

#### Using Nuitka

```bash
# Install Nuitka
pip install nuitka

# Build executable
python build_configs/nuitka/build.py

# Find executable in dist/nuitka/
```

#### Using Build Script

```bash
# Build with PyInstaller (default)
./scripts/build_executable.sh pyinstaller

# Or build with Nuitka
./scripts/build_executable.sh nuitka
```

## Docker Deployment

### Quick Start

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access the container
docker-compose exec games bash

# Run a game
python -m card_games.war
```

### Using Docker Directly

```bash
# Build the image
docker build -t games-collection .

# Run interactively
docker run -it games-collection

# Run with persistent statistics
docker run -it -v $(pwd)/game_stats:/home/games/.game_stats games-collection
```

### Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild image
docker-compose build --no-cache

# Remove everything
docker-compose down -v
```

## Building from Source

### Clone Repository

```bash
git clone https://github.com/saint2706/Games.git
cd Games
```

### Install in Development Mode

```bash
# Install with pip
pip install -e .

# Or with development dependencies
pip install -e .[dev]
```

### Run Games Directly

```bash
# Using Python module syntax
python -m card_games.war
python -m paper_games.tic_tac_toe

# Or using the launcher
python scripts/launcher.py
```

## Cross-Platform Compatibility

### Platform-Specific Considerations

#### Linux

- **GUI Games**: Requires Tkinter (usually pre-installed)

  ```bash
  # Ubuntu/Debian
  sudo apt-get install python3-tk

  # Fedora
  sudo dnf install python3-tkinter
  ```

- **Terminal**: Most games work in any terminal

- **Colors**: Requires terminal with ANSI color support

#### macOS

- **Python**: Use Python from python.org or Homebrew

  ```bash
  brew install python@3.11
  ```

- **Tkinter**: Included with official Python installers

- **Terminal**: Use Terminal.app or iTerm2

#### Windows

- **Python**: Download from python.org
- **Terminal**: Use Windows Terminal (recommended) or Command Prompt
- **Colors**: Enable ANSI colors in Windows Terminal settings
- **Tkinter**: Included with official Python installers

### Testing Your Installation

```bash
# Test basic import
python -c "from card_games.war import WarGame; print('Success!')"

# Test crash reporter
python -c "from common.crash_reporter import CrashReporter; print('Success!')"

# Test launcher
python scripts/launcher.py
```

## Troubleshooting

### Common Issues

#### "No module named 'colorama'"

```bash
pip install colorama
```

#### "No module named 'tkinter'"

See platform-specific instructions above for installing Tkinter.

#### Executable Won't Run (Linux/macOS)

```bash
# Make sure it's executable
chmod +x games-collection-linux

# Check if it's 64-bit (most systems)
file games-collection-linux
```

#### Windows Defender Blocks Executable

1. This is common with PyInstaller executables
1. Right-click → Properties → Unblock
1. Or add exception in Windows Defender

### Error Reporting

If you encounter errors:

1. **Check Logs**: Located in `~/.game_logs/`
1. **Crash Reports**: Located in `~/.game_logs/crashes/`
1. **Report Issues**: [GitHub Issues](https://github.com/saint2706/Games/issues)

### Getting Help

- **Documentation**: [GitHub Repository](https://github.com/saint2706/Games)
- **Issues**: [Report a Bug](https://github.com/saint2706/Games/issues/new)
- **Discussions**: [GitHub Discussions](https://github.com/saint2706/Games/discussions)

## Advanced Configuration

### Environment Variables

```bash
# Disable crash reporting
export GAMES_NO_CRASH_REPORT=1

# Enable telemetry (opt-in)
export GAMES_TELEMETRY=1

# Custom statistics directory
export GAMES_STATS_DIR=/custom/path
```

### Custom Build Options

#### PyInstaller

Edit `build_configs/pyinstaller/games.spec` to customize:

- Icon
- Console vs. windowed mode
- Additional data files
- Excluded modules

#### Nuitka

Edit `build_configs/nuitka/build.py` to customize:

- Output filename
- Optimization level
- Plugin options
- Icon

### Performance Tuning

```bash
# Use Nuitka for better performance
python build_configs/nuitka/build.py

# Or use PyInstaller with UPX compression
pyinstaller --upx-dir=/path/to/upx build_configs/pyinstaller/games.spec
```

## Uninstallation

### PyPI Installation

```bash
pip uninstall games-collection
```

### Remove User Data

```bash
# Remove statistics
rm -rf ~/.game_stats

# Remove logs
rm -rf ~/.game_logs
```

### Docker

```bash
# Remove containers and volumes
docker-compose down -v

# Remove image
docker rmi games-collection
```

## Security Considerations

- **Crash Reports**: May contain system information (opt-in)
- **Telemetry**: Disabled by default (opt-in only)
- **Statistics**: Stored locally in `~/.game_stats/`
- **Logs**: Stored locally in `~/.game_logs/`

All data is stored locally by default. No data is sent to external servers unless explicitly enabled.

## License

MIT License - See [LICENSE](../LICENSE) for details.
