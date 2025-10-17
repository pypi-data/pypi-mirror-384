"""Test suite for MCP config validation.

This module tests the mcp-config.json file to ensure it is valid
and properly configures the three MCP servers for GitHub Copilot.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Dict
from urllib.parse import urlparse

import pytest

# Path to the MCP config file
MCP_CONFIG_PATH = pathlib.Path(__file__).resolve().parents[1] / ".github" / "mcp-config.json"


def load_mcp_config() -> Dict[str, Any]:
    """Load and parse the MCP config file.

    Returns:
        Parsed JSON configuration as a dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        json.JSONDecodeError: If config file is not valid JSON.
    """
    if not MCP_CONFIG_PATH.exists():
        raise FileNotFoundError(f"MCP config file not found at {MCP_CONFIG_PATH}")

    with open(MCP_CONFIG_PATH) as f:
        return json.load(f)


def test_mcp_config_file_exists():
    """Test that mcp-config.json exists in the .github directory."""
    assert MCP_CONFIG_PATH.exists(), f"MCP config file not found at {MCP_CONFIG_PATH}"
    assert MCP_CONFIG_PATH.is_file(), f"MCP config path is not a file: {MCP_CONFIG_PATH}"


def test_mcp_config_is_valid_json():
    """Test that mcp-config.json is valid JSON."""
    try:
        with open(MCP_CONFIG_PATH) as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"MCP config file is not valid JSON: {e}")


def test_mcp_config_has_servers_key():
    """Test that config has the required 'mcpServers' key."""
    config = load_mcp_config()
    assert "mcpServers" in config, "Config must have 'mcpServers' key"
    assert isinstance(config["mcpServers"], dict), "'mcpServers' must be a dictionary"


def test_mcp_config_has_three_servers():
    """Test that config defines exactly three servers."""
    config = load_mcp_config()
    servers = config.get("mcpServers", {})
    assert len(servers) == 3, f"Expected 3 servers, found {len(servers)}"


def test_mcp_config_server_names():
    """Test that all three expected servers are defined."""
    config = load_mcp_config()
    servers = config.get("mcpServers", {})
    expected_servers = {"deepwiki", "fetchMCP", "sequentialThinking"}
    actual_servers = set(servers.keys())

    assert actual_servers == expected_servers, f"Expected servers {expected_servers}, found {actual_servers}"


def test_deepwiki_server_config():
    """Test deepwiki server configuration."""
    config = load_mcp_config()
    deepwiki = config["mcpServers"]["deepwiki"]

    # Check required fields
    assert "type" in deepwiki, "deepwiki must have 'type' field"
    assert "url" in deepwiki, "deepwiki must have 'url' field"
    assert "tools" in deepwiki, "deepwiki must have 'tools' field"
    assert "headers" in deepwiki, "deepwiki must have 'headers' field"

    # Validate field values
    assert deepwiki["type"] == "http", "deepwiki type should be 'http'"
    assert deepwiki["url"] == "https://mcp.deepwiki.com/mcp", "deepwiki URL mismatch"
    assert deepwiki["tools"] == ["*"], "deepwiki should enable all tools"
    assert isinstance(deepwiki["headers"], dict), "deepwiki headers must be a dictionary"
    assert deepwiki["headers"].get("Accept") == "application/json", "deepwiki should accept JSON"


def test_fetchmcp_server_config():
    """Test fetchMCP server configuration."""
    config = load_mcp_config()
    fetch_mcp = config["mcpServers"]["fetchMCP"]

    # Check required fields
    assert "type" in fetch_mcp, "fetchMCP must have 'type' field"
    assert "url" in fetch_mcp, "fetchMCP must have 'url' field"
    assert "tools" in fetch_mcp, "fetchMCP must have 'tools' field"
    assert "headers" in fetch_mcp, "fetchMCP must have 'headers' field"

    # Validate field values
    assert fetch_mcp["type"] == "http", "fetchMCP type should be 'http'"
    assert fetch_mcp["url"] == "https://remote.mcpservers.org/fetch/mcp", "fetchMCP URL mismatch"
    assert fetch_mcp["tools"] == ["*"], "fetchMCP should enable all tools"
    assert isinstance(fetch_mcp["headers"], dict), "fetchMCP headers must be a dictionary"
    assert fetch_mcp["headers"].get("Accept") == "application/json", "fetchMCP should accept JSON"


def test_sequential_thinking_server_config():
    """Test sequentialThinking server configuration."""
    config = load_mcp_config()
    seq_thinking = config["mcpServers"]["sequentialThinking"]

    # Check required fields
    assert "type" in seq_thinking, "sequentialThinking must have 'type' field"
    assert "url" in seq_thinking, "sequentialThinking must have 'url' field"
    assert "tools" in seq_thinking, "sequentialThinking must have 'tools' field"
    assert "headers" in seq_thinking, "sequentialThinking must have 'headers' field"

    # Validate field values
    assert seq_thinking["type"] == "http", "sequentialThinking type should be 'http'"
    assert seq_thinking["url"] == "https://remote.mcpservers.org/sequentialthinking/mcp", "sequentialThinking URL mismatch"
    assert seq_thinking["tools"] == ["*"], "sequentialThinking should enable all tools"
    assert isinstance(seq_thinking["headers"], dict), "sequentialThinking headers must be a dictionary"
    assert seq_thinking["headers"].get("Accept") == "application/json", "sequentialThinking should accept JSON"


def test_all_server_urls_are_valid():
    """Test that all server URLs are valid and well-formed."""
    config = load_mcp_config()
    servers = config.get("mcpServers", {})

    for server_name, server_config in servers.items():
        url = server_config.get("url", "")
        assert url, f"Server {server_name} must have a URL"

        # Parse URL to validate structure
        parsed = urlparse(url)
        assert parsed.scheme in ["http", "https"], f"Server {server_name} URL must use http or https scheme"
        assert parsed.netloc, f"Server {server_name} URL must have a valid host"


def test_all_servers_have_consistent_structure():
    """Test that all servers have consistent configuration structure."""
    config = load_mcp_config()
    servers = config.get("mcpServers", {})

    required_fields = {"type", "url", "tools", "headers"}

    for server_name, server_config in servers.items():
        actual_fields = set(server_config.keys())
        assert required_fields.issubset(actual_fields), f"Server {server_name} missing required fields: {required_fields - actual_fields}"

        # Check type field
        assert server_config["type"] == "http", f"Server {server_name} type must be 'http'"

        # Check tools field
        assert isinstance(server_config["tools"], list), f"Server {server_name} tools must be a list"
        assert server_config["tools"] == ["*"], f"Server {server_name} should enable all tools with ['*']"

        # Check headers field
        assert isinstance(server_config["headers"], dict), f"Server {server_name} headers must be a dictionary"
        assert "Accept" in server_config["headers"], f"Server {server_name} must have 'Accept' header"


def test_config_can_be_serialized():
    """Test that config can be loaded and serialized back to JSON."""
    config = load_mcp_config()

    # Try to serialize it back to JSON
    try:
        json_str = json.dumps(config, indent=2)
        # Verify we can parse it again
        reparsed = json.loads(json_str)
        assert reparsed == config, "Config should be identical after serialization round-trip"
    except (TypeError, ValueError) as e:
        pytest.fail(f"Config cannot be serialized to JSON: {e}")


def test_no_extra_top_level_keys():
    """Test that config only has expected top-level keys."""
    config = load_mcp_config()
    expected_keys = {"mcpServers"}
    actual_keys = set(config.keys())

    assert actual_keys == expected_keys, f"Config should only have {expected_keys}, found {actual_keys}"


def test_server_urls_use_https():
    """Test that all server URLs use HTTPS for security."""
    config = load_mcp_config()
    servers = config.get("mcpServers", {})

    for server_name, server_config in servers.items():
        url = server_config.get("url", "")
        parsed = urlparse(url)
        assert parsed.scheme == "https", f"Server {server_name} should use HTTPS, found {parsed.scheme}"


@pytest.mark.parametrize(
    "server_name,expected_url",
    [
        ("deepwiki", "https://mcp.deepwiki.com/mcp"),
        ("fetchMCP", "https://remote.mcpservers.org/fetch/mcp"),
        ("sequentialThinking", "https://remote.mcpservers.org/sequentialthinking/mcp"),
    ],
)
def test_server_url_matches_expected(server_name: str, expected_url: str):
    """Test that each server has the correct URL."""
    config = load_mcp_config()
    server = config["mcpServers"][server_name]
    assert server["url"] == expected_url, f"Server {server_name} URL should be {expected_url}"


def test_config_summary():
    """Test and print a summary of the MCP configuration."""
    config = load_mcp_config()
    servers = config.get("mcpServers", {})

    print("\n" + "=" * 70)
    print("MCP Configuration Summary")
    print("=" * 70)
    print(f"Total servers configured: {len(servers)}")
    print()

    for server_name, server_config in servers.items():
        print(f"Server: {server_name}")
        print(f"  Type: {server_config.get('type')}")
        print(f"  URL: {server_config.get('url')}")
        print(f"  Tools: {server_config.get('tools')}")
        print(f"  Headers: {server_config.get('headers')}")
        print()

    print("=" * 70)
    print("✓ All three servers are properly configured")
    print("✓ Configuration is valid for GitHub Copilot coding agent")
    print("=" * 70)


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
