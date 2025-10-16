#!/usr/bin/env python3
"""Check version consistency across project files.

This script validates that version numbers are consistent across:
- pyproject.toml
- scripts/__init__.py
- Git tag (optional)

Used by CI/CD workflows to prevent version mismatches.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def get_version_from_pyproject(pyproject_path: Path) -> str | None:
    """Extract version from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml file.

    Returns:
        Version string or None if not found.
    """
    try:
        with open(pyproject_path) as f:
            content = f.read()

        # Match: version = "1.2.3"
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Error reading {pyproject_path}: {e}", file=sys.stderr)

    return None


def get_version_from_init(init_path: Path) -> str | None:
    """Extract version from scripts/__init__.py.

    Args:
        init_path: Path to scripts/__init__.py file.

    Returns:
        Version string or None if not found.
    """
    try:
        with open(init_path) as f:
            content = f.read()

        # Match: __version__ = "1.2.3"
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Error reading {init_path}: {e}", file=sys.stderr)

    return None


def normalize_version(version: str) -> str:
    """Normalize a version string by removing 'v' prefix.

    Args:
        version: Version string (may have 'v' prefix).

    Returns:
        Normalized version string.
    """
    return version.lstrip("v")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check version consistency across project files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check version consistency between pyproject.toml and scripts/__init__.py
  python scripts/check_version_consistency.py

  # Check that versions also match a specific tag
  python scripts/check_version_consistency.py --tag v1.2.3

  # Specify custom repository root
  python scripts/check_version_consistency.py --repo-root /path/to/repo
        """,
    )

    parser.add_argument("--tag", help="Git tag to validate against (e.g., v1.2.3)")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Repository root directory",
    )

    args = parser.parse_args()

    # Get file paths
    pyproject_path = args.repo_root / "pyproject.toml"
    init_path = args.repo_root / "scripts" / "__init__.py"

    # Check files exist
    if not pyproject_path.exists():
        print(f"❌ Error: {pyproject_path} not found", file=sys.stderr)
        return 1

    if not init_path.exists():
        print(f"❌ Error: {init_path} not found", file=sys.stderr)
        return 1

    # Extract versions
    pyproject_version = get_version_from_pyproject(pyproject_path)
    init_version = get_version_from_init(init_path)

    if not pyproject_version:
        print(f"❌ Error: Could not extract version from {pyproject_path}", file=sys.stderr)
        return 1

    if not init_version:
        print(f"❌ Error: Could not extract version from {init_path}", file=sys.stderr)
        return 1

    # Normalize versions
    pyproject_version = normalize_version(pyproject_version)
    init_version = normalize_version(init_version)

    # Compare versions
    print("Version Check Results:")
    print(f"  pyproject.toml: {pyproject_version}")
    print(f"  scripts/__init__.py: {init_version}")

    errors = []

    if pyproject_version != init_version:
        errors.append(f"Version mismatch: pyproject.toml ({pyproject_version}) != scripts/__init__.py ({init_version})")

    # Check tag if provided
    if args.tag:
        tag_version = normalize_version(args.tag)
        print(f"  Git tag: {tag_version}")

        if pyproject_version != tag_version:
            errors.append(f"Version mismatch: Git tag ({tag_version}) != pyproject.toml ({pyproject_version})")

        if init_version != tag_version:
            errors.append(f"Version mismatch: Git tag ({tag_version}) != scripts/__init__.py ({init_version})")

    # Report results
    if errors:
        print("\n❌ Version Consistency Check FAILED:")
        for error in errors:
            print(f"  • {error}")
        print("\nTo fix:")
        print("  1. Update version numbers to match in both files")
        print("  2. If using a git tag, ensure the tag name matches the version")
        print("  3. Run this script again to verify")
        print("\nExample fix:")
        print(f"  # Update both files to version {pyproject_version}")
        print(f'  sed -i \'s/version = ".*"/version = "{pyproject_version}"/\' pyproject.toml')
        print(f'  sed -i \'s/__version__ = ".*"/__version__ = "{pyproject_version}"/\' scripts/__init__.py')
        return 1

    print("\n✅ Version Consistency Check PASSED")
    print(f"   All versions match: {pyproject_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
