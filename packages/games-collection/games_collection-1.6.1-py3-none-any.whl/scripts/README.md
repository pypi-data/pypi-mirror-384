# Scripts Directory

This directory contains utility scripts for development, testing, building, and workflow management.

## Overview

| Script | Purpose | Usage |
| ------------------------------- | -------------------------------------------------- | ------------------------------------------- |
| `bump_version.py` | Automated version bumping for releases | `python bump_version.py` |
| `check_complexity.sh` | Check code complexity with Radon | `./check_complexity.sh` |
| `check_version_consistency.py` | Check for version consistency across files | `python check_version_consistency.py` |
| `build_executable.sh` | Build standalone executables | `./build_executable.sh` |
| `debug_workflow.py` | Debug GitHub Actions workflow execution | `python debug_workflow.py <workflow>` |
| `launcher.py` | Launch games from command line | `python launcher.py` |
| `run_tests.sh` | Run test suite with various options | `./run_tests.sh all` |
| `run_workflow.sh` | Run GitHub Actions workflows locally | `./run_workflow.sh ci` |
| `setup_act.sh` | Install act for local workflow testing | `./setup_act.sh` |
| `test_gui.py` | Test GUI applications | `python test_gui.py` |
| `test_mcp_servers.py` | Test MCP server configurations | `python test_mcp_servers.py` |
| `validate_mcp_config.py` | Validate MCP configuration files | `python validate_mcp_config.py` |
| `validate_pyqt5.py` | Validate the PyQt5 GUI implementation | `python validate_pyqt5.py` |
| `validate_workflows.py` | Validate GitHub Actions workflow files | `python validate_workflows.py` |
| `workflow_info.py` | Display workflow information | `python workflow_info.py` |

---

## Release Management Scripts

### `bump_version.py`

Automatically bump version numbers in `pyproject.toml` and `scripts/__init__.py` for releases.

**Usage:**

```bash
# Bump patch version (e.g., 1.0.1 -> 1.0.2)
python scripts/bump_version.py

# Bump minor version (e.g., 1.0.1 -> 1.1.0)
python scripts/bump_version.py --part minor

# Bump major version (e.g., 1.0.1 -> 2.0.0)
python scripts/bump_version.py --part major
```

### `check_version_consistency.py`

Validates that version numbers are consistent across `pyproject.toml`, `scripts/__init__.py`, and Git tags.

**Usage:**

```bash
# Check version consistency
python scripts/check_version_consistency.py

# Check consistency with a Git tag
python scripts/check_version_consistency.py --tag v1.2.3
```

---

## Workflow and CI/CD Scripts

### `setup_act.sh`

Installs `act`, a tool for running GitHub Actions workflows locally. This is essential for testing CI/CD changes without pushing to the repository.

**Usage:**

```bash
./scripts/setup_act.sh
```

### `run_workflow.sh`

Run GitHub Actions workflows locally with `act` for testing and debugging.

**Usage:**

```bash
# Run the CI workflow
./scripts/run_workflow.sh ci

# Run a specific job from the workflow
./scripts/run_workflow.sh ci --job lint

# List all available workflows
./scripts/run_workflow.sh all
```

### `validate_workflows.py`

A comprehensive validation tool for GitHub Actions workflow files. It checks for YAML syntax, structural integrity, and script references.

**Usage:**

```bash
python scripts/validate_workflows.py
```

### `workflow_info.py`

Displays detailed information about GitHub Actions workflows, including triggers, jobs, permissions, and dependencies.

**Usage:**

```bash
# Get info for a specific workflow
python scripts/workflow_info.py ci.yml

# List all workflows
python scripts/workflow_info.py --all
```

### `debug_workflow.py`

Helps debug why a GitHub Actions workflow or job may be skipped by analyzing its trigger conditions and event types.

**Usage:**

```bash
# Analyze a workflow's conditions
python scripts/debug_workflow.py build-executables.yml

# Simulate a push event to the main branch
python scripts/debug_workflow.py ci.yml --simulate push --ref refs/heads/main
```

---

## Testing and Validation Scripts

### `run_tests.sh`

Runs the test suite with various configurations, allowing you to target specific test types like unit, integration, or GUI tests.

**Usage:**

```bash
# Run all tests
./scripts/run_tests.sh all

# Run only unit tests
./scripts/run_tests.sh unit

# Run tests with a coverage report
./scripts/run_tests.sh coverage
```

### `check_complexity.sh`

Analyzes code complexity using `radon` to ensure that functions remain maintainable and below established complexity thresholds.

**Usage:**

```bash
./scripts/check_complexity.sh
```

### `validate_pyqt5.py`

Validates the project's PyQt5 GUI implementation to ensure that all modules, classes, and methods are correctly defined.

**Usage:**

```bash
python scripts/validate_pyqt5.py
```

### `test_gui.py`

A utility for testing GUI applications with different frameworks (Tkinter and PyQt5) to ensure consistency.

**Usage:**

```bash
# List all games with GUI support
python scripts/test_gui.py --list

# Check framework availability
python scripts/test_gui.py --check-framework all
```

---

## Build and Launcher Scripts

### `build_executable.sh`

Builds a standalone executable of the game collection using either PyInstaller or Nuitka.

**Usage:**

```bash
# Build with the default tool (PyInstaller)
./scripts/build_executable.sh

# Build with Nuitka for a potentially smaller/faster executable
./scripts/build_executable.sh nuitka
```

### `launcher.py`

An interactive launcher for all games in the collection. This is the main entry point for the executable.

**Usage:**

```bash
# Run the interactive launcher
python scripts/launcher.py

# Launch a specific game directly
python scripts/launcher.py --game dots_and_boxes
```

---

## MCP Scripts

### `validate_mcp_config.py`

Validates the MCP (Model-View-Controller-Presenter) configuration file for correctness.

**Usage:**

```bash
python scripts/validate_mcp_config.py
```

### `test_mcp_servers.py`

Tests the MCP server configurations and their connectivity.

**Usage:**

```bash
python scripts/test_mcp_servers.py
```

---

For more detailed information on a specific script, refer to its internal documentation or run it with the `--help` flag.