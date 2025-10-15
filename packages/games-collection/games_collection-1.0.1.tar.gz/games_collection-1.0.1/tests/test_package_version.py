"""Test package version consistency.

This module tests that version numbers are consistent across the package.
"""

from __future__ import annotations

import tomllib
from pathlib import Path


def test_version_consistency():
    """Test that version in pyproject.toml matches version in scripts/__init__.py."""
    # Get project root
    repo_root = Path(__file__).parent.parent

    # Read version from pyproject.toml
    pyproject_path = repo_root / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    pyproject_version = pyproject_data["project"]["version"]

    # Read version from scripts/__init__.py
    scripts_init_path = repo_root / "scripts" / "__init__.py"
    with open(scripts_init_path) as f:
        content = f.read()
        # Extract version from __version__ = "x.y.z"
        for line in content.split("\n"):
            if line.startswith("__version__"):
                scripts_version = line.split("=")[1].strip().strip('"').strip("'")
                break
        else:
            raise ValueError("Could not find __version__ in scripts/__init__.py")

    # Verify they match
    assert (
        pyproject_version == scripts_version
    ), f"Version mismatch: pyproject.toml has {pyproject_version} but scripts/__init__.py has {scripts_version}"


def test_version_format():
    """Test that version follows semantic versioning format."""
    repo_root = Path(__file__).parent.parent
    pyproject_path = repo_root / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    version = pyproject_data["project"]["version"]

    # Check basic semantic versioning format: MAJOR.MINOR.PATCH
    parts = version.split(".")
    assert len(parts) >= 3, f"Version {version} should have at least 3 parts (MAJOR.MINOR.PATCH)"

    # Check that MAJOR, MINOR, and PATCH are numeric
    for i, part in enumerate(parts[:3]):
        assert part.isdigit(), f"Version part {i} ({part}) should be numeric in version {version}"
