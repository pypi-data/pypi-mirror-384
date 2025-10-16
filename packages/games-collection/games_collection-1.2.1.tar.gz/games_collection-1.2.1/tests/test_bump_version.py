"""Test version bump script.

This module tests the automated version bumping functionality.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from scripts.bump_version import (
    bump_version,
    get_current_version,
    parse_version,
    update_pyproject_toml,
    update_scripts_init,
)


def test_parse_version_valid():
    """Test parsing valid semantic version strings."""
    assert parse_version("1.0.0") == (1, 0, 0)
    assert parse_version("1.2.3") == (1, 2, 3)
    assert parse_version("10.20.30") == (10, 20, 30)
    assert parse_version("0.0.1") == (0, 0, 1)


def test_parse_version_invalid():
    """Test parsing invalid version strings raises ValueError."""
    with pytest.raises(ValueError, match="must have at least 3 parts"):
        parse_version("1.0")

    with pytest.raises(ValueError, match="must be integers"):
        parse_version("1.0.a")

    with pytest.raises(ValueError, match="must be integers"):
        parse_version("a.b.c")


def test_bump_version_patch():
    """Test bumping patch version."""
    assert bump_version("1.0.0", "patch") == "1.0.1"
    assert bump_version("1.0.9", "patch") == "1.0.10"
    assert bump_version("1.2.3", "patch") == "1.2.4"


def test_bump_version_minor():
    """Test bumping minor version resets patch."""
    assert bump_version("1.0.0", "minor") == "1.1.0"
    assert bump_version("1.0.9", "minor") == "1.1.0"
    assert bump_version("1.9.9", "minor") == "1.10.0"


def test_bump_version_major():
    """Test bumping major version resets minor and patch."""
    assert bump_version("1.0.0", "major") == "2.0.0"
    assert bump_version("1.9.9", "major") == "2.0.0"
    assert bump_version("9.9.9", "major") == "10.0.0"


def test_bump_version_invalid_part():
    """Test invalid bump part raises ValueError."""
    with pytest.raises(ValueError, match="Invalid part"):
        bump_version("1.0.0", "invalid")


def test_get_current_version():
    """Test reading version from pyproject.toml."""
    repo_root = Path(__file__).parent.parent
    pyproject_path = repo_root / "pyproject.toml"

    version = get_current_version(pyproject_path)
    assert isinstance(version, str)
    # Should be valid semantic version
    major, minor, patch = parse_version(version)
    assert major >= 0
    assert minor >= 0
    assert patch >= 0


def test_get_current_version_missing_file():
    """Test error when pyproject.toml doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent = Path(tmpdir) / "nonexistent.toml"
        with pytest.raises(FileNotFoundError):
            get_current_version(nonexistent)


def test_update_pyproject_toml():
    """Test updating version in pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "pyproject.toml"

        # Create test pyproject.toml
        content = """[project]
name = "test-package"
version = "1.0.0"
description = "Test package"
"""
        test_file.write_text(content)

        # Update version
        update_pyproject_toml(test_file, "1.0.1")

        # Verify update
        updated_content = test_file.read_text()
        assert 'version = "1.0.1"' in updated_content
        assert 'version = "1.0.0"' not in updated_content
        # Verify formatting is preserved
        assert 'name = "test-package"' in updated_content


def test_update_pyproject_toml_different_quotes():
    """Test updating version with different quote styles."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "pyproject.toml"

        # Test with single quotes
        content = """[project]
version = '1.0.0'
"""
        test_file.write_text(content)
        update_pyproject_toml(test_file, "2.0.0")
        assert "version = '2.0.0'" in test_file.read_text()


def test_update_pyproject_toml_no_spaces():
    """Test updating version without spaces around equals."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "pyproject.toml"

        content = """[project]
version="1.0.0"
"""
        test_file.write_text(content)
        update_pyproject_toml(test_file, "3.0.0")
        assert 'version="3.0.0"' in test_file.read_text()


def test_update_pyproject_toml_missing_version():
    """Test error when version field is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "pyproject.toml"

        content = """[project]
name = "test-package"
"""
        test_file.write_text(content)

        with pytest.raises(ValueError, match="Could not find version field"):
            update_pyproject_toml(test_file, "1.0.0")


def test_update_scripts_init():
    """Test updating version in scripts/__init__.py."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "__init__.py"

        # Create test __init__.py
        content = '''"""Scripts package."""

from __future__ import annotations

__version__ = "1.0.0"
'''
        test_file.write_text(content)

        # Update version
        update_scripts_init(test_file, "1.0.1")

        # Verify update
        updated_content = test_file.read_text()
        assert '__version__ = "1.0.1"' in updated_content
        assert '__version__ = "1.0.0"' not in updated_content
        # Verify other content is preserved
        assert "from __future__ import annotations" in updated_content


def test_update_scripts_init_different_quotes():
    """Test updating __version__ with different quote styles."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "__init__.py"

        content = "__version__ = '1.0.0'\n"
        test_file.write_text(content)
        update_scripts_init(test_file, "2.0.0")
        assert "__version__ = '2.0.0'" in test_file.read_text()


def test_update_scripts_init_missing_version():
    """Test error when __version__ is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "__init__.py"

        content = '"""Module without version."""\n'
        test_file.write_text(content)

        with pytest.raises(ValueError, match="Could not find __version__"):
            update_scripts_init(test_file, "1.0.0")


def test_version_consistency_after_bump():
    """Test that actual version files remain consistent after bump."""
    repo_root = Path(__file__).parent.parent
    pyproject_path = repo_root / "pyproject.toml"
    scripts_init_path = repo_root / "scripts" / "__init__.py"

    # Get current versions
    pyproject_version = get_current_version(pyproject_path)

    with open(scripts_init_path) as f:
        content = f.read()
        for line in content.split("\n"):
            if line.startswith("__version__"):
                scripts_version = line.split("=")[1].strip().strip('"').strip("'")
                break
        else:
            raise ValueError("Could not find __version__ in scripts/__init__.py")

    # Versions should match
    assert pyproject_version == scripts_version, "Versions should be consistent before test"
