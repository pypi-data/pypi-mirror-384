# Documentation

This directory contains comprehensive documentation for the Card & Paper Games project, including Sphinx documentation,
architecture guides, development resources, and planning documents.

## Quick Start

Welcome to the Games documentation! This guide will help you navigate all available resources.

### 📚 Documentation Overview

#### 📖 Game Catalog

- **[GAMES.md](../GAMES.md)** - Complete catalog of all 49 available games with features and usage

#### 📐 Architecture & Design

- **[architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)** - Comprehensive architecture guide
  - Plugin system for third-party games
  - Event-driven architecture patterns
  - Save/load system
  - Unified settings management
  - Replay/undo functionality
  - Observer pattern for GUI synchronization
  - Game engine abstraction

#### 💻 Development Resources

- **[development/CODE_QUALITY.md](development/CODE_QUALITY.md)** - Code quality standards

  - Pre-commit hooks configuration
  - Linting and formatting (Black, Ruff)
  - Type checking (mypy)
  - Complexity analysis
  - Best practices

- **[development/TESTING.md](development/TESTING.md)** - Testing guide

  - Running tests (pytest)
  - Coverage requirements (90%+)
  - Writing tests
  - GUI testing
  - Performance benchmarking
  - Mutation testing

- **[development/IMPLEMENTATION_NOTES.md](development/IMPLEMENTATION_NOTES.md)** - Implementation details

  - Code quality improvements
  - Documentation system
  - Testing infrastructure
  - Architecture system
  - CLI enhancements
  - Five new card games implementation

- **[development/ENHANCEMENTS_APPLIED.md](development/ENHANCEMENTS_APPLIED.md)** - Applied enhancements

  - Infrastructure enhancements
  - Save/load functionality
  - Replay/undo functionality
  - CLI enhancements

#### 🎨 GUI Development

- **[gui/README.md](gui/README.md)** - GUI framework documentation hub
- **[gui/FRAMEWORKS.md](gui/FRAMEWORKS.md)** - Framework overview and guidelines
- **[gui/MIGRATION_GUIDE.md](gui/MIGRATION_GUIDE.md)** - tkinter to PyQt5 migration guide
- **[gui/PYQT5_IMPLEMENTATION.md](gui/PYQT5_IMPLEMENTATION.md)** - PyQt5 implementation summary
- **[gui/GUI_ENHANCEMENTS.md](gui/GUI_ENHANCEMENTS.md)** - GUI enhancements and improvements

#### 🔄 GitHub Actions Workflows

- **[workflows/README.md](workflows/README.md)** - Workflow documentation hub
- **[workflows/VALIDATION_REPORT.md](workflows/VALIDATION_REPORT.md)** - Workflow validation results
- **[workflows/VALIDATION_SUMMARY.md](workflows/VALIDATION_SUMMARY.md)** - Validation implementation summary
- **[workflows/DEBUG_REPORT.md](workflows/DEBUG_REPORT.md)** - Workflow debugging and failure analysis
- **[workflows/FIX_SUMMARY.md](workflows/FIX_SUMMARY.md)** - Workflow fixes and resolutions
- **[development/LOCAL_WORKFLOWS.md](development/LOCAL_WORKFLOWS.md)** - Local workflow testing with act
- **[development/WORKFLOW_TESTING_QUICKSTART.md](development/WORKFLOW_TESTING_QUICKSTART.md)** - Workflow testing quick start
- **[development/WORKFLOW_VALIDATION.md](development/WORKFLOW_VALIDATION.md)** - Workflow validation guide

#### 📊 Status Tracking

- **[status/README.md](status/README.md)** - Status tracking hub
- **[status/GUI_MIGRATION_STATUS.md](status/GUI_MIGRATION_STATUS.md)** - GUI migration progress tracking

#### 🗺️ Planning & Roadmap

- **[planning/TODO.md](planning/TODO.md)** - Future plans and roadmap
  - Planned new games
  - Feature enhancements
  - Technical improvements

#### 📘 Sphinx Documentation (source/)

**For Players:**

- **[Tutorial Series](source/tutorials/index.rst)** - Learn how to play each game
  - 🎮 [Poker Tutorial](source/tutorials/poker_tutorial.rst) - Texas Hold'em and Omaha
  - 🃏 [Bluff Tutorial](source/tutorials/bluff_tutorial.rst) - Master the art of deception
  - 🎰 [Blackjack Tutorial](source/tutorials/blackjack_tutorial.rst) - Beat the dealer
  - 🎴 [Uno Tutorial](source/tutorials/uno_tutorial.rst) - Classic card game
  - ✏️ [Paper Games Tutorial](source/tutorials/paper_games_tutorial.rst) - Tic-Tac-Toe, Battleship, and more

**For Developers:**

- **[Architecture Documentation](source/architecture/index.rst)** - Detailed design documentation

  - 🏗️ [Architecture Overview](source/architecture/index.rst) - Design patterns and principles
  - ♠️ [Poker Architecture](source/architecture/poker_architecture.rst) - Deep dive with diagrams
  - 🎭 [Bluff Architecture](source/architecture/bluff_architecture.rst) - Game mechanics and AI
  - 🤖 [AI Strategies](source/architecture/ai_strategies.rst) - Algorithms explained

- **[Code Examples](source/examples/index.rst)** - Learn by doing

  - 30+ practical code examples
  - Common patterns and best practices
  - Custom game creation
  - AI integration

- **[API Reference](source/api/)** - Complete module documentation

  - [Card Games API](source/api/card_games.rst)
  - [Paper Games API](source/api/paper_games.rst)

#### 📚 Specialized Guides

- **[development/ANALYTICS_INTEGRATION_GUIDE.md](development/ANALYTICS_INTEGRATION_GUIDE.md)** - Game analytics and statistics
- **[development/CLI_UTILS.md](development/CLI_UTILS.md)** - Enhanced CLI utilities
- **[development/EDUCATIONAL_FEATURES.md](development/EDUCATIONAL_FEATURES.md)** - Educational mode integration
- **[development/EDUCATIONAL_QUICKSTART.md](development/EDUCATIONAL_QUICKSTART.md)** - Quick start for educators
- **[development/NEW_GAMES_IMPLEMENTATION.md](development/NEW_GAMES_IMPLEMENTATION.md)** - Implementation of dice, word, and logic games
- **[deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md)** - Deployment and release guide

#### 🤝 Contributing

- **[../CONTRIBUTING.md](../CONTRIBUTING.md)** - Join the project
  - Code style guide
  - How to add new games
  - Testing requirements
  - Pull request process

## Building the Documentation

### Prerequisites

Install Sphinx and the required theme:

```bash
pip install sphinx sphinx_rtd_theme
```

### Building HTML Documentation

```bash
cd docs
make html
```

The generated HTML documentation will be in `build/html/`. Open `build/html/index.html` in a web browser.

### Building Other Formats

```bash
# PDF (requires LaTeX)
make latexpdf

# ePub
make epub

# Plain text
make text
```

### Cleaning Build Files

```bash
make clean
```

## Documentation Structure

```
docs/
├── architecture/                        # Architecture documentation
│   └── ARCHITECTURE.md                  # Comprehensive architecture guide
├── development/                         # Development resources
│   ├── CODE_QUALITY.md                 # Code quality standards and tools
│   ├── TESTING.md                      # Testing guide and best practices
│   ├── IMPLEMENTATION_NOTES.md         # Detailed implementation notes
│   ├── ENHANCEMENTS_APPLIED.md         # Infrastructure enhancements applied
│   ├── ANALYTICS_INTEGRATION_GUIDE.md  # Analytics integration guide
│   ├── CLI_UTILS.md                    # CLI utilities guide
│   ├── EDUCATIONAL_FEATURES.md         # Educational features
│   ├── EDUCATIONAL_QUICKSTART.md       # Quick start for educators
│   ├── NEW_GAMES_IMPLEMENTATION.md     # Implementation of dice, word, logic games
│   ├── LOCAL_WORKFLOWS.md              # Local workflow testing
│   ├── WORKFLOW_TESTING_QUICKSTART.md  # Workflow testing quick start
│   ├── WORKFLOW_VALIDATION.md          # Workflow validation guide
│   └── BUILD_EXECUTABLES_WORKFLOW.md   # Build executables workflow
├── deployment/                         # Deployment documentation
│   ├── DEPLOYMENT.md                   # Deployment and release guide
│   └── PYPI_RELEASE.md                 # PyPI release process
├── planning/                           # Planning and roadmap
│   └── TODO.md                         # Future plans and features
├── gui/                                # GUI framework documentation
│   ├── README.md                       # GUI documentation hub
│   ├── FRAMEWORKS.md                   # Framework overview
│   ├── MIGRATION_GUIDE.md              # tkinter to PyQt5 migration
│   ├── PYQT5_IMPLEMENTATION.md         # PyQt5 implementation details
│   └── GUI_ENHANCEMENTS.md             # GUI enhancements
├── workflows/                          # GitHub Actions workflow docs
│   ├── README.md                       # Workflow documentation hub
│   ├── VALIDATION_REPORT.md            # Workflow validation results
│   ├── VALIDATION_SUMMARY.md           # Validation implementation
│   ├── DEBUG_REPORT.md                 # Workflow debugging
│   └── FIX_SUMMARY.md                  # Workflow fixes
├── status/                             # Status tracking
│   ├── README.md                       # Status tracking hub
│   └── GUI_MIGRATION_STATUS.md         # GUI migration progress
├── images/                             # Documentation images
│   ├── battleship_gui_game.png         # Battleship gameplay screenshot
│   ├── battleship_gui_setup.png        # Battleship setup screenshot
│   └── hearts_gui_overview.svg         # Hearts GUI diagram
├── source/                             # Sphinx documentation
│   ├── index.rst                       # Main documentation index
│   ├── conf.py                         # Sphinx configuration
│   ├── tutorials/                      # Getting started guides
│   │   ├── index.rst
│   │   ├── poker_tutorial.rst
│   │   ├── bluff_tutorial.rst
│   │   ├── blackjack_tutorial.rst
│   │   ├── uno_tutorial.rst
│   │   └── paper_games_tutorial.rst
│   ├── architecture/                   # Sphinx architecture docs
│   │   ├── index.rst
│   │   ├── poker_architecture.rst
│   │   ├── bluff_architecture.rst
│   │   └── ai_strategies.rst
│   ├── examples/                       # Code examples
│   │   └── index.rst
│   ├── api/                           # API reference (auto-generated)
│   │   ├── card_games.rst
│   │   └── paper_games.rst
│   └── contributing.rst               # Contribution guidelines
├── ORGANIZATION_RATIONALE.md           # Repository organization rationale
├── Makefile                            # Build automation (Unix)
├── make.bat                            # Build automation (Windows)
└── README.md                           # This file
```

## Writing Documentation

### reStructuredText (RST) Basics

Documentation uses reStructuredText format:

```rst
Section Title
=============

Subsection
----------

**Bold text** and *italic text*

Code blocks:

.. code-block:: python

   def example():
       return "Hello"

Links:

`Link text <https://example.com>`_

Lists:

* Item 1
* Item 2
* Item 3
```

### Adding New Pages

1. Create a new `.rst` file in the appropriate directory
1. Add it to the `toctree` in the parent `index.rst`
1. Rebuild the documentation

### API Documentation

API documentation is automatically generated from docstrings using Sphinx autodoc.

To document a new module:

```rst
Module Name
===========

.. automodule:: package.module
   :members:
   :undoc-members:
   :show-inheritance:
```

## Contributing to Documentation

When contributing documentation:

1. Follow the existing style and structure
1. Use clear, concise language
1. Include code examples where appropriate
1. Test that the documentation builds without errors
1. Check for broken links and formatting issues

## Viewing Documentation Online

Once published, documentation will be available at:

- GitHub Pages: (to be configured)
- Read the Docs: (to be configured)

## Getting Help

For questions about documentation:

- Open an issue on GitHub
- Check Sphinx documentation: https://www.sphinx-doc.org/
- Review existing documentation files for examples
