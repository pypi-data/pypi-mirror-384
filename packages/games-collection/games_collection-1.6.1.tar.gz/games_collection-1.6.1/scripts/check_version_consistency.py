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


def _get_project_root() -> Path:
    """Find the project root by looking for pyproject.toml."""
    current_path = Path(__file__).resolve()
    for parent in [current_path, *current_path.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("Could not find project root containing pyproject.toml")


def get_version_from_pyproject(pyproject_path: Path) -> str | None:
    """Extract version from pyproject.toml."""
    try:
        content = pyproject_path.read_text()
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        return match.group(1) if match else None
    except Exception as e:
        print(f"Error reading {pyproject_path}: {e}", file=sys.stderr)
        return None


def get_version_from_init(init_path: Path) -> str | None:
    """Extract version from scripts/__init__.py."""
    try:
        content = init_path.read_text()
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        return match.group(1) if match else None
    except Exception as e:
        print(f"Error reading {init_path}: {e}", file=sys.stderr)
        return None


def normalize_version(version: str) -> str:
    """Normalize a version string by removing 'v' prefix."""
    return version.lstrip("v")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check version consistency across project files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--tag", help="Git tag to validate against (e.g., v1.2.3).")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root directory (auto-detected by default).",
    )
    args = parser.parse_args()

    try:
        repo_root = args.repo_root or _get_project_root()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

    pyproject_path = repo_root / "pyproject.toml"
    init_path = repo_root / "scripts" / "__init__.py"

    if not pyproject_path.exists() or not init_path.exists():
        print(f"❌ Error: Could not find pyproject.toml or scripts/__init__.py in {repo_root}", file=sys.stderr)
        return 1

    pyproject_version = get_version_from_pyproject(pyproject_path)
    init_version = get_version_from_init(init_path)

    if not pyproject_version or not init_version:
        print("❌ Error: Could not extract version from one or more files.", file=sys.stderr)
        return 1

    pyproject_version = normalize_version(pyproject_version)
    init_version = normalize_version(init_version)

    versions = {
        "pyproject.toml": pyproject_version,
        "scripts/__init__.py": init_version,
    }
    if args.tag:
        versions["Git tag"] = normalize_version(args.tag)

    print("Version Check Results:")
    for source, version in versions.items():
        print(f"  {source:<20}: {version}")

    unique_versions = set(versions.values())
    if len(unique_versions) > 1:
        print("\n❌ Version Consistency Check FAILED: Mismatched versions found.", file=sys.stderr)
        return 1

    print(f"\n✅ Version Consistency Check PASSED: All versions match {pyproject_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
