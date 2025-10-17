# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Documentation**: Updated `README.md`, `CONTRIBUTING.md`, and `GAMES.md` to ensure consistency and accuracy.

## [1.6.0] - 2025-10-16

### Fixed

- **Versioning**: Corrected versioning in `CHANGELOG.md` to reflect the current version of `1.6.0`.

## [1.1.0] - 2025-10-12

### Added - Q4 2025 Consolidation & Deployment

#### New Card Games (3)

- **Cribbage**: Full implementation with pegging, The Show, and crib scoring
- **Euchre**: Trump-based trick-taking with 24-card deck
- **Rummy 500**: Melding and laying off variant

#### Deployment Infrastructure

- **PyInstaller Build Configuration**: Create standalone executables
- **Nuitka Build Configuration**: Native compilation for better performance
- **Docker Support**: Complete containerization
- **Universal Launcher**: Menu-based game selector

#### Crash Reporting & Error Analytics

- **Crash Reporter Module**: Comprehensive error tracking

#### Cross-Platform Testing

- **GitHub Actions Workflow**: Multi-platform CI/CD

#### Documentation

- **Deployment Guide**: Complete deployment reference
- **Build Configs README**: Build tool documentation
- **Game READMEs**: Detailed rules for new games

### Changed

- Updated `TODO.md`: All Q4 2025 items marked complete (10/10)
- Updated `pyproject.toml`: Added entry points for new games
- Updated launcher: Integrated Cribbage, Euchre, and Rummy 500

### Fixed

- Launcher imports now use `__main__` modules correctly
- Docker image uses non-root user for security
- Cross-platform compatibility issues addressed

## [1.0.1] - 2025-10-15

### Fixed

- **PyPI Publishing**: Bumped version from 1.0.0 to 1.0.1 to resolve PyPI upload conflict.

### Changed

#### Packaging (2025-10-16)

- **PyInstaller configuration** now collects PyQt5 hidden imports and Qt plugin data.
- **build-executables workflow** installs the GUI extra and runs a PyQt5 smoke test.

#### Documentation Reorganization (2025-10-14)

- **Restructured documentation** for better organization and discoverability.
- **Root directory cleanup**: Reduced from 11 to 4 essential markdown files.
- **Improved navigation**: Each documentation area now has a README hub.

## [1.0.0] - 2025-10-12

### Added

#### Infrastructure & Framework

- **Achievement System**: Cross-game achievement framework.
- **Player Profile System**: Unified player profile with statistics and progression.

#### Card Games

- **Uno**: Complete jump-in rule implementation.

### Changed

- **Uno House Rules**: Updated documentation to reflect fully implemented jump-in rule.
- **PyPI Configuration**: Enhanced `pyproject.toml` with complete metadata, classifiers, and entry points.
- **Documentation**: Updated `TODO.md` to track Q4 2025 roadmap progress.

[Unreleased]: https://github.com/saint2706/Games/compare/v1.6.0...HEAD
[1.6.0]: https://github.com/saint2706/Games/releases/tag/v1.6.0
[1.1.0]: https://github.com/saint2706/Games/releases/tag/v1.1.0
[1.0.1]: https://github.com/saint2706/Games/releases/tag/v1.0.1
[1.0.0]: https://github.com/saint2706/Games/releases/tag/v1.0.0