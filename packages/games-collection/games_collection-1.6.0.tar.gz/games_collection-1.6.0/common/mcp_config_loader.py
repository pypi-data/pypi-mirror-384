"""MCP configuration loader and validator.

This module provides utilities for loading and validating MCP (Model Context Protocol)
configuration files used by GitHub Copilot coding agent.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server.

    Attributes:
        name: Name of the server
        type: Server type (typically "http")
        url: Server endpoint URL
        tools: List of enabled tools (["*"] means all tools)
        headers: HTTP headers to include in requests
    """

    name: str
    type: str
    url: str
    tools: List[str]
    headers: Dict[str, str]

    def validate(self) -> List[str]:
        """Validate the server configuration.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        if not self.name:
            errors.append("Server name is required")

        if self.type != "http":
            errors.append(f"Server type must be 'http', got '{self.type}'")

        if not self.url:
            errors.append("Server URL is required")
        else:
            parsed = urlparse(self.url)
            if parsed.scheme not in ["http", "https"]:
                errors.append(f"Server URL must use http or https scheme, got '{parsed.scheme}'")
            if not parsed.netloc:
                errors.append("Server URL must have a valid host")

        if not isinstance(self.tools, list):
            errors.append(f"Tools must be a list, got {type(self.tools)}")

        if not isinstance(self.headers, dict):
            errors.append(f"Headers must be a dictionary, got {type(self.headers)}")

        return errors

    def is_valid(self) -> bool:
        """Check if the server configuration is valid.

        Returns:
            True if valid, False otherwise.
        """
        return len(self.validate()) == 0

    @classmethod
    def from_dict(cls, name: str, config: Dict[str, Any]) -> MCPServerConfig:
        """Create MCPServerConfig from a dictionary.

        Args:
            name: Server name
            config: Configuration dictionary

        Returns:
            MCPServerConfig instance
        """
        return cls(
            name=name,
            type=config.get("type", ""),
            url=config.get("url", ""),
            tools=config.get("tools", []),
            headers=config.get("headers", {}),
        )


@dataclass
class MCPConfig:
    """Complete MCP configuration with all servers.

    Attributes:
        servers: Dictionary of server configurations
    """

    servers: Dict[str, MCPServerConfig]

    @classmethod
    def load_from_file(cls, filepath: pathlib.Path) -> MCPConfig:
        """Load MCP configuration from a JSON file.

        Args:
            filepath: Path to the configuration file

        Returns:
            MCPConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is not valid JSON
            ValueError: If configuration is invalid
        """
        if not filepath.exists():
            raise FileNotFoundError(f"MCP config file not found at {filepath}")

        with open(filepath) as f:
            data = json.load(f)

        if "mcpServers" not in data:
            raise ValueError("Config must have 'mcpServers' key")

        servers_data = data["mcpServers"]
        if not isinstance(servers_data, dict):
            raise ValueError("'mcpServers' must be a dictionary")

        servers = {}
        for name, config in servers_data.items():
            servers[name] = MCPServerConfig.from_dict(name, config)

        return cls(servers=servers)

    def validate(self) -> List[str]:
        """Validate the complete configuration.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        if not self.servers:
            errors.append("Configuration must have at least one server")

        for server in self.servers.values():
            server_errors = server.validate()
            if server_errors:
                errors.extend([f"{server.name}: {error}" for error in server_errors])

        return errors

    def is_valid(self) -> bool:
        """Check if the configuration is valid.

        Returns:
            True if valid, False otherwise.
        """
        return len(self.validate()) == 0

    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get a specific server configuration by name.

        Args:
            name: Server name

        Returns:
            Server configuration or None if not found.
        """
        return self.servers.get(name)

    def get_server_names(self) -> List[str]:
        """Get list of all configured server names.

        Returns:
            List of server names.
        """
        return list(self.servers.keys())

    def get_server_count(self) -> int:
        """Get the number of configured servers.

        Returns:
            Number of servers.
        """
        return len(self.servers)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format.

        Returns:
            Dictionary representation suitable for JSON serialization.
        """
        return {
            "mcpServers": {
                name: {
                    "type": server.type,
                    "url": server.url,
                    "tools": server.tools,
                    "headers": server.headers,
                }
                for name, server in self.servers.items()
            }
        }

    def save_to_file(self, filepath: pathlib.Path) -> None:
        """Save configuration to a JSON file.

        Args:
            filepath: Path to save the configuration
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
            f.write("\n")  # Add trailing newline


def load_default_mcp_config() -> MCPConfig:
    """Load the default MCP configuration from .github/mcp-config.json.

    Returns:
        MCPConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is not valid JSON
        ValueError: If configuration is invalid
    """
    # Find the repository root (where .github directory is)
    current_file = pathlib.Path(__file__).resolve()
    repo_root = current_file.parents[1]  # Go up from common/ to repo root
    config_path = repo_root / ".github" / "mcp-config.json"

    return MCPConfig.load_from_file(config_path)


def validate_mcp_config_file(filepath: pathlib.Path) -> tuple[bool, List[str]]:
    """Validate an MCP configuration file.

    Args:
        filepath: Path to the configuration file

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    try:
        config = MCPConfig.load_from_file(filepath)
        errors = config.validate()
        return len(errors) == 0, errors
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        return False, [str(e)]
