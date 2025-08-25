"""Client handlers for managing MCP server configurations in various clients.

This module provides abstract base class and implementations for managing
MCP server configurations in different client applications.
"""

import json
import os
import platform
import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any


class ClientHandler(ABC):
    """Abstract base class for MCP client handlers."""

    @abstractmethod
    def get_config_path(self) -> Path:
        """Get the path to the client's configuration file."""
        pass

    @abstractmethod
    def setup_server(self, server_name: str, server_config: dict[str, Any]) -> bool:
        """Add server to client config - only touch our server entries."""
        pass

    @abstractmethod
    def remove_server(self, server_name: str) -> bool:
        """Remove server from client config - preserve all other servers."""
        pass

    @abstractmethod
    def list_managed_servers(self) -> list[dict[str, Any]]:
        """List only servers managed by this tool."""
        pass

    @abstractmethod
    def list_all_servers(self) -> list[dict[str, Any]]:
        """List all servers in config (managed + external)."""
        pass


class ClaudeDesktopHandler(ClientHandler):
    """Handler for Claude Desktop client configuration."""

    MANAGED_SERVER_MARKER = "mcp-config-managed"

    def get_config_path(self) -> Path:
        """Get Claude Desktop config file path based on platform."""
        # Get home directory as string first to avoid Path type issues
        home_str = str(Path.home())

        if os.name == "nt":  # Windows
            return (
                Path(home_str)
                / "AppData"
                / "Roaming"
                / "Claude"
                / "claude_desktop_config.json"
            )
        elif os.name == "posix":
            if platform.system() == "Darwin":  # macOS
                return (
                    Path(home_str)
                    / "Library"
                    / "Application Support"
                    / "Claude"
                    / "claude_desktop_config.json"
                )
            else:  # Linux
                return (
                    Path(home_str) / ".config" / "claude" / "claude_desktop_config.json"
                )
        else:
            raise OSError(f"Unsupported operating system: {os.name}")

    def load_config(self) -> dict[str, Any]:
        """Load existing Claude Desktop configuration.

        Returns:
            Configuration dictionary, defaulting to {"mcpServers": {}} if not found
        """
        config_path = self.get_config_path()

        # Default configuration structure
        default_config: dict[str, Any] = {"mcpServers": {}}

        if not config_path.exists():
            return default_config

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config: dict[str, Any] = json.load(f)

            # Ensure mcpServers section exists
            if "mcpServers" not in config:
                config["mcpServers"] = {}

            return config

        except (json.JSONDecodeError, IOError) as e:
            # If there's an error reading/parsing, return default
            # but log warning if needed in production
            print(f"Warning: Error loading config from {config_path}: {e}")
            return default_config

    def save_config(self, config: dict[str, Any]) -> None:
        """Save Claude Desktop configuration with proper formatting.

        Args:
            config: Configuration dictionary to save
        """
        config_path = self.get_config_path()

        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to a temporary file first (atomic write)
        temp_path = config_path.with_suffix(".tmp")

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                f.write("\n")  # Add trailing newline

            # Replace the original file atomically
            temp_path.replace(config_path)

        except Exception:
            # Clean up temp file if something went wrong
            if temp_path.exists():
                temp_path.unlink()
            raise

    def setup_server(self, server_name: str, server_config: dict[str, Any]) -> bool:
        """Safely update Claude Desktop config.

        Args:
            server_name: Name for the server instance
            server_config: Server configuration dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup before modification
            self.backup_config()

            # Load existing configuration
            config = self.load_config()

            # Add our management markers
            server_config["_managed_by"] = self.MANAGED_SERVER_MARKER
            if "_server_type" not in server_config:
                server_config["_server_type"] = "mcp-server"

            # Update only our specific server entry
            config["mcpServers"][server_name] = server_config

            # Save the updated configuration
            self.save_config(config)

            return True

        except Exception as e:
            print(f"Error setting up server '{server_name}': {e}")
            return False

    def remove_server(self, server_name: str) -> bool:
        """Remove only if it's managed by us.

        Args:
            server_name: Name of the server to remove

        Returns:
            True if removed successfully, False otherwise
        """
        try:
            config = self.load_config()

            # Check if server exists
            if server_name not in config.get("mcpServers", {}):
                print(f"Server '{server_name}' not found in configuration")
                return False

            # Check if it's managed by us
            server_entry = config["mcpServers"][server_name]
            if server_entry.get("_managed_by") != self.MANAGED_SERVER_MARKER:
                print(
                    f"Server '{server_name}' is not managed by this tool. "
                    "Cannot remove external servers."
                )
                return False

            # Create backup before modification
            self.backup_config()

            # Remove the server
            del config["mcpServers"][server_name]

            # Save the updated configuration
            self.save_config(config)

            return True

        except Exception as e:
            print(f"Error removing server '{server_name}': {e}")
            return False

    def list_managed_servers(self) -> list[dict[str, Any]]:
        """List only servers we manage.

        Returns:
            List of dictionaries with server information
        """
        config = self.load_config()
        servers = []

        for name, server_config in config.get("mcpServers", {}).items():
            if server_config.get("_managed_by") == self.MANAGED_SERVER_MARKER:
                servers.append(
                    {
                        "name": name,
                        "type": server_config.get("_server_type", "unknown"),
                        "command": server_config.get("command", ""),
                        "args": server_config.get("args", []),
                        "env": server_config.get("env", {}),
                    }
                )

        return servers

    def list_all_servers(self) -> list[dict[str, Any]]:
        """List all servers, mark which ones we manage.

        Returns:
            List of dictionaries with server information
        """
        config = self.load_config()
        servers = []

        for name, server_config in config.get("mcpServers", {}).items():
            is_managed = server_config.get("_managed_by") == self.MANAGED_SERVER_MARKER

            servers.append(
                {
                    "name": name,
                    "managed": is_managed,
                    "type": server_config.get("_server_type", "unknown"),
                    "command": server_config.get("command", ""),
                    "args": server_config.get("args", []),
                    "env": server_config.get("env", {}),
                }
            )

        return servers

    def backup_config(self) -> Path:
        """Create a backup of the current configuration.

        Returns:
            Path to the backup file
        """
        config_path = self.get_config_path()

        if not config_path.exists():
            # Nothing to backup
            return config_path

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"claude_desktop_config_backup_{timestamp}.json"
        backup_path = config_path.parent / backup_name

        # Copy the configuration file
        shutil.copy2(config_path, backup_path)

        return backup_path

    def validate_config(self) -> list[str]:
        """Validate current configuration for basic correctness.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        try:
            config = self.load_config()

            # Check mcpServers section (config is always a dict from load_config)
            if "mcpServers" not in config:
                errors.append("Configuration missing 'mcpServers' section")
            elif not isinstance(config["mcpServers"], dict):
                errors.append("'mcpServers' must be an object")
            else:
                # Validate each server entry only if mcpServers is valid
                for name, server_config in config["mcpServers"].items():
                    if not isinstance(server_config, dict):
                        errors.append(
                            f"Server '{name}' configuration must be an object"
                        )
                        continue

                    # Check required fields
                    if "command" not in server_config:
                        errors.append(
                            f"Server '{name}' missing required 'command' field"
                        )

                    if "args" in server_config and not isinstance(
                        server_config["args"], list
                    ):
                        errors.append(f"Server '{name}' 'args' field must be an array")

                    if "env" in server_config and not isinstance(
                        server_config["env"], dict
                    ):
                        errors.append(f"Server '{name}' 'env' field must be an object")

        except Exception as e:
            errors.append(f"Error reading configuration: {e}")

        return errors


# Client registry
CLIENT_HANDLERS = {
    "claude-desktop": ClaudeDesktopHandler,
    # Future clients can be added here
}


def get_client_handler(client_name: str) -> ClientHandler:
    """Get client handler by name.

    Args:
        client_name: Name of the client

    Returns:
        ClientHandler instance

    Raises:
        ValueError: If client name is not recognized
    """
    if client_name not in CLIENT_HANDLERS:
        raise ValueError(
            f"Unknown client: {client_name}. Available: {list(CLIENT_HANDLERS.keys())}"
        )

    return CLIENT_HANDLERS[client_name]()
