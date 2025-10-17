"""Test suite for MCP config loader utility.

This module tests the mcp_config_loader utility functions and classes.
"""

from __future__ import annotations

import json
import pathlib
import tempfile

import pytest

from common.mcp_config_loader import MCPConfig, MCPServerConfig, load_default_mcp_config, validate_mcp_config_file


class TestMCPServerConfig:
    """Tests for MCPServerConfig class."""

    def test_valid_server_config(self):
        """Test creating a valid server configuration."""
        config = MCPServerConfig(
            name="test_server",
            type="http",
            url="https://example.com/mcp",
            tools=["*"],
            headers={"Accept": "application/json"},
        )

        assert config.is_valid()
        assert len(config.validate()) == 0

    def test_invalid_server_type(self):
        """Test that invalid server type is caught."""
        config = MCPServerConfig(
            name="test_server",
            type="invalid",
            url="https://example.com/mcp",
            tools=["*"],
            headers={"Accept": "application/json"},
        )

        assert not config.is_valid()
        errors = config.validate()
        assert any("type must be 'http'" in error for error in errors)

    def test_invalid_url_scheme(self):
        """Test that invalid URL scheme is caught."""
        config = MCPServerConfig(
            name="test_server",
            type="http",
            url="ftp://example.com/mcp",
            tools=["*"],
            headers={"Accept": "application/json"},
        )

        assert not config.is_valid()
        errors = config.validate()
        assert any("must use http or https scheme" in error for error in errors)

    def test_missing_url_host(self):
        """Test that missing URL host is caught."""
        config = MCPServerConfig(
            name="test_server",
            type="http",
            url="https://",
            tools=["*"],
            headers={"Accept": "application/json"},
        )

        assert not config.is_valid()
        errors = config.validate()
        assert any("must have a valid host" in error for error in errors)

    def test_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "type": "http",
            "url": "https://example.com/mcp",
            "tools": ["*"],
            "headers": {"Accept": "application/json"},
        }

        config = MCPServerConfig.from_dict("test_server", config_dict)

        assert config.name == "test_server"
        assert config.type == "http"
        assert config.url == "https://example.com/mcp"
        assert config.tools == ["*"]
        assert config.headers == {"Accept": "application/json"}


class TestMCPConfig:
    """Tests for MCPConfig class."""

    def test_load_from_valid_file(self):
        """Test loading configuration from a valid file."""
        config_data = {
            "mcpServers": {
                "server1": {
                    "type": "http",
                    "url": "https://example1.com/mcp",
                    "tools": ["*"],
                    "headers": {"Accept": "application/json"},
                },
                "server2": {
                    "type": "http",
                    "url": "https://example2.com/mcp",
                    "tools": ["*"],
                    "headers": {"Accept": "application/json"},
                },
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = pathlib.Path(f.name)

        try:
            config = MCPConfig.load_from_file(temp_path)
            assert len(config.servers) == 2
            assert "server1" in config.servers
            assert "server2" in config.servers
            assert config.is_valid()
        finally:
            temp_path.unlink()

    def test_load_from_missing_file(self):
        """Test that loading from missing file raises error."""
        with pytest.raises(FileNotFoundError):
            MCPConfig.load_from_file(pathlib.Path("/nonexistent/config.json"))

    def test_load_from_invalid_json(self):
        """Test that loading invalid JSON raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            temp_path = pathlib.Path(f.name)

        try:
            with pytest.raises(json.JSONDecodeError):
                MCPConfig.load_from_file(temp_path)
        finally:
            temp_path.unlink()

    def test_load_from_file_missing_servers_key(self):
        """Test that missing mcpServers key raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"other_key": {}}, f)
            temp_path = pathlib.Path(f.name)

        try:
            with pytest.raises(ValueError, match="must have 'mcpServers' key"):
                MCPConfig.load_from_file(temp_path)
        finally:
            temp_path.unlink()

    def test_get_server(self):
        """Test getting a specific server by name."""
        config = MCPConfig(
            servers={
                "server1": MCPServerConfig(
                    name="server1",
                    type="http",
                    url="https://example1.com/mcp",
                    tools=["*"],
                    headers={},
                )
            }
        )

        server = config.get_server("server1")
        assert server is not None
        assert server.name == "server1"

        missing = config.get_server("nonexistent")
        assert missing is None

    def test_get_server_names(self):
        """Test getting list of server names."""
        config = MCPConfig(
            servers={
                "server1": MCPServerConfig(
                    name="server1",
                    type="http",
                    url="https://example1.com/mcp",
                    tools=["*"],
                    headers={},
                ),
                "server2": MCPServerConfig(
                    name="server2",
                    type="http",
                    url="https://example2.com/mcp",
                    tools=["*"],
                    headers={},
                ),
            }
        )

        names = config.get_server_names()
        assert len(names) == 2
        assert "server1" in names
        assert "server2" in names

    def test_get_server_count(self):
        """Test getting server count."""
        config = MCPConfig(servers={})
        assert config.get_server_count() == 0

        config.servers["server1"] = MCPServerConfig(
            name="server1",
            type="http",
            url="https://example.com/mcp",
            tools=["*"],
            headers={},
        )
        assert config.get_server_count() == 1

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = MCPConfig(
            servers={
                "server1": MCPServerConfig(
                    name="server1",
                    type="http",
                    url="https://example.com/mcp",
                    tools=["*"],
                    headers={"Accept": "application/json"},
                )
            }
        )

        config_dict = config.to_dict()
        assert "mcpServers" in config_dict
        assert "server1" in config_dict["mcpServers"]
        assert config_dict["mcpServers"]["server1"]["url"] == "https://example.com/mcp"

    def test_save_and_load_roundtrip(self):
        """Test saving and loading configuration."""
        original_config = MCPConfig(
            servers={
                "server1": MCPServerConfig(
                    name="server1",
                    type="http",
                    url="https://example.com/mcp",
                    tools=["*"],
                    headers={"Accept": "application/json"},
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = pathlib.Path(tmpdir) / "config.json"
            original_config.save_to_file(temp_path)

            loaded_config = MCPConfig.load_from_file(temp_path)

            assert loaded_config.get_server_count() == original_config.get_server_count()
            assert loaded_config.get_server_names() == original_config.get_server_names()


def test_load_default_mcp_config():
    """Test loading the default MCP configuration."""
    config = load_default_mcp_config()

    # Should have exactly 3 servers
    assert config.get_server_count() == 3

    # Check expected server names
    server_names = config.get_server_names()
    assert "deepwiki" in server_names
    assert "fetchMCP" in server_names
    assert "sequentialThinking" in server_names

    # All servers should be valid
    assert config.is_valid()


def test_validate_mcp_config_file_valid():
    """Test validating a valid configuration file."""
    config_data = {
        "mcpServers": {
            "server1": {
                "type": "http",
                "url": "https://example.com/mcp",
                "tools": ["*"],
                "headers": {"Accept": "application/json"},
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        temp_path = pathlib.Path(f.name)

    try:
        is_valid, errors = validate_mcp_config_file(temp_path)
        assert is_valid
        assert len(errors) == 0
    finally:
        temp_path.unlink()


def test_validate_mcp_config_file_invalid():
    """Test validating an invalid configuration file."""
    config_data = {
        "mcpServers": {
            "server1": {
                "type": "invalid_type",
                "url": "ftp://invalid.com",
                "tools": ["*"],
                "headers": {},
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        temp_path = pathlib.Path(f.name)

    try:
        is_valid, errors = validate_mcp_config_file(temp_path)
        assert not is_valid
        assert len(errors) > 0
    finally:
        temp_path.unlink()


def test_validate_mcp_config_file_nonexistent():
    """Test validating a nonexistent configuration file."""
    is_valid, errors = validate_mcp_config_file(pathlib.Path("/nonexistent/config.json"))
    assert not is_valid
    assert len(errors) > 0
    assert any("not found" in error.lower() for error in errors)


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
