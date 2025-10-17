#!/usr/bin/env python3
"""Bump version script for automated releases.

This script automatically increments the version number in both pyproject.toml
and scripts/__init__.py, ensuring consistency across the package.

Usage:
    python scripts/bump_version.py [--part {major,minor,patch}] [--dry-run]

Examples:
    # Bump patch version (1.0.1 -> 1.0.2)
    python scripts/bump_version.py

    # Bump minor version (1.0.1 -> 1.1.0)
    python scripts/bump_version.py --part minor

    # Bump major version (1.0.1 -> 2.0.0)
    python scripts/bump_version.py --part major

    # Preview changes without writing
    python scripts/bump_version.py --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Tuple

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse a semantic version string into components.

    Args:
        version: Version string in format "MAJOR.MINOR.PATCH"

    Returns:
        Tuple of (major, minor, patch) as integers

    Raises:
        ValueError: If version format is invalid
    """
    parts = version.split(".")
    if len(parts) < 3:
        raise ValueError(f"Version must have at least 3 parts (MAJOR.MINOR.PATCH), got: {version}")

    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError as e:
        raise ValueError(f"Version parts must be integers, got: {version}") from e

    return major, minor, patch


def bump_version(version: str, part: str = "patch") -> str:
    """Bump a semantic version.

    Args:
        version: Current version string
        part: Which part to bump (major, minor, or patch)

    Returns:
        New version string

    Raises:
        ValueError: If part is invalid or version format is invalid
    """
    major, minor, patch = parse_version(version)

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid part: {part}. Must be 'major', 'minor', or 'patch'")

    return f"{major}.{minor}.{patch}"


def get_current_version(pyproject_path: Path) -> str:
    """Get current version from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml

    Returns:
        Current version string

    Raises:
        FileNotFoundError: If pyproject.toml doesn't exist
        KeyError: If version field is missing
    """
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    return data["project"]["version"]


def update_pyproject_toml(pyproject_path: Path, new_version: str) -> None:
    """Update version in pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml
        new_version: New version string

    Raises:
        FileNotFoundError: If pyproject.toml doesn't exist
    """
    with open(pyproject_path) as f:
        content = f.read()

    # Use regex to replace version while preserving formatting
    # Match: version = "1.0.1" or version="1.0.1"
    pattern = r'(version\s*=\s*["\'])([^"\']+)(["\'])'
    replacement = rf"\g<1>{new_version}\g<3>"

    new_content = re.sub(pattern, replacement, content, count=1)

    if new_content == content:
        raise ValueError("Could not find version field in pyproject.toml")

    with open(pyproject_path, "w") as f:
        f.write(new_content)


def update_scripts_init(scripts_init_path: Path, new_version: str) -> None:
    """Update version in scripts/__init__.py.

    Args:
        scripts_init_path: Path to scripts/__init__.py
        new_version: New version string

    Raises:
        FileNotFoundError: If scripts/__init__.py doesn't exist
    """
    with open(scripts_init_path) as f:
        content = f.read()

    # Use regex to replace __version__
    # Match: __version__ = "1.0.1" or __version__="1.0.1"
    pattern = r'(__version__\s*=\s*["\'])([^"\']+)(["\'])'
    replacement = rf"\g<1>{new_version}\g<3>"

    new_content = re.sub(pattern, replacement, content, count=1)

    if new_content == content:
        raise ValueError("Could not find __version__ in scripts/__init__.py")

    with open(scripts_init_path, "w") as f:
        f.write(new_content)


def main() -> int:
    """Main entry point for version bump script.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Bump version in pyproject.toml and scripts/__init__.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--part",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Which version part to bump (default: patch)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without actually changing files",
    )

    args = parser.parse_args()

    # Get repository root
    repo_root = Path(__file__).parent.parent
    pyproject_path = repo_root / "pyproject.toml"
    scripts_init_path = repo_root / "scripts" / "__init__.py"

    try:
        # Get current version
        current_version = get_current_version(pyproject_path)
        print(f"Current version: {current_version}")

        # Calculate new version
        new_version = bump_version(current_version, args.part)
        print(f"New version: {new_version}")

        if args.dry_run:
            print("\nDry run - no files were modified")
            print(f"Would update pyproject.toml: {pyproject_path}")
            print(f"Would update scripts/__init__.py: {scripts_init_path}")
            return 0

        # Update files
        update_pyproject_toml(pyproject_path, new_version)
        print(f"✓ Updated {pyproject_path}")

        update_scripts_init(scripts_init_path, new_version)
        print(f"✓ Updated {scripts_init_path}")

        # Output new version for GitHub Actions to capture
        print(f"\n::set-output name=version::{new_version}")
        print(f"::set-output name=tag::v{new_version}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
