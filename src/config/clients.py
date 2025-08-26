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
from typing import Any, Callable, Union


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
    METADATA_FILE = ".mcp-config-metadata.json"

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

    def get_metadata_path(self) -> Path:
        """Get path to the metadata file for tracking managed servers."""
        config_path = self.get_config_path()
        return config_path.parent / self.METADATA_FILE

    def load_metadata(self) -> dict[str, Any]:
        """Load metadata about managed servers.
        
        Returns:
            Dictionary mapping server names to their metadata
        """
        metadata_path = self.get_metadata_path()
        
        if not metadata_path.exists():
            return {}
        
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, IOError):
            # If there's an error reading metadata, start fresh
            return {}

    def save_metadata(self, metadata: dict[str, Any]) -> None:
        """Save metadata about managed servers.
        
        Args:
            metadata: Dictionary mapping server names to their metadata
        """
        metadata_path = self.get_metadata_path()
        
        # Ensure parent directory exists
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write metadata
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            f.write("\n")

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

            # Extract metadata fields if present (for backward compatibility)
            metadata_fields = {}
            clean_config = server_config.copy()
            
            # Extract and remove metadata fields from the config
            if "_managed_by" in clean_config:
                metadata_fields["_managed_by"] = clean_config.pop("_managed_by")
            else:
                # Mark as managed by default
                metadata_fields["_managed_by"] = self.MANAGED_SERVER_MARKER
                
            if "_server_type" in clean_config:
                metadata_fields["_server_type"] = clean_config.pop("_server_type")
            else:
                metadata_fields["_server_type"] = "mcp-server"

            # Update only our specific server entry with clean config (no metadata)
            config["mcpServers"][server_name] = clean_config

            # Save the updated configuration
            self.save_config(config)
            
            # Update metadata separately
            metadata = self.load_metadata()
            metadata[server_name] = metadata_fields
            self.save_metadata(metadata)

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
            metadata = self.load_metadata()

            # Check if server exists
            if server_name not in config.get("mcpServers", {}):
                print(f"Server '{server_name}' not found in configuration")
                return False

            # Check if it's managed by us (check metadata)
            if server_name not in metadata or metadata[server_name].get("_managed_by") != self.MANAGED_SERVER_MARKER:
                print(
                    f"Server '{server_name}' is not managed by this tool. "
                    "Cannot remove external servers."
                )
                return False

            # Create backup before modification
            self.backup_config()

            # Remove the server from config
            del config["mcpServers"][server_name]

            # Save the updated configuration
            self.save_config(config)
            
            # Remove from metadata
            del metadata[server_name]
            self.save_metadata(metadata)

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
        metadata = self.load_metadata()
        servers = []

        for name, server_config in config.get("mcpServers", {}).items():
            # Check if this server is in our metadata
            if name in metadata and metadata[name].get("_managed_by") == self.MANAGED_SERVER_MARKER:
                servers.append(
                    {
                        "name": name,
                        "type": metadata[name].get("_server_type", "unknown"),
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
        metadata = self.load_metadata()
        servers = []

        for name, server_config in config.get("mcpServers", {}).items():
            # Check if this server is managed
            is_managed = (
                name in metadata and 
                metadata[name].get("_managed_by") == self.MANAGED_SERVER_MARKER
            )
            
            server_type = "unknown"
            if is_managed and name in metadata:
                server_type = metadata[name].get("_server_type", "unknown")

            servers.append(
                {
                    "name": name,
                    "managed": is_managed,
                    "type": server_type,
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

    def migrate_inline_metadata(self) -> bool:
        """Migrate any inline metadata fields to separate metadata file.
        
        This is for backward compatibility - removes _managed_by and _server_type
        fields from the main config and moves them to metadata file.
        
        Returns:
            True if migration was performed, False if not needed
        """
        try:
            config = self.load_config()
            metadata = self.load_metadata()
            modified = False
            
            for name, server_config in config.get("mcpServers", {}).items():
                if "_managed_by" in server_config or "_server_type" in server_config:
                    # Extract metadata fields
                    if name not in metadata:
                        metadata[name] = {}
                    
                    if "_managed_by" in server_config:
                        metadata[name]["_managed_by"] = server_config.pop("_managed_by")
                        modified = True
                    
                    if "_server_type" in server_config:
                        metadata[name]["_server_type"] = server_config.pop("_server_type")
                        modified = True
            
            if modified:
                # Save cleaned config and metadata
                self.save_config(config)
                self.save_metadata(metadata)
                return True
            
            return False
            
        except Exception:
            return False


class VSCodeHandler(ClientHandler):
    """Handler for VSCode native MCP configuration (VSCode 1.102+)."""
    
    MANAGED_SERVER_MARKER = "mcp-config-managed"
    METADATA_FILE = ".mcp-config-metadata.json"
    
    def __init__(self, workspace: bool = True):
        """Initialize VSCode handler.
        
        Args:
            workspace: If True, use workspace config (.vscode/mcp.json).
                      If False, use user profile config.
        """
        self.workspace = workspace
    
    def get_config_path(self) -> Path:
        """Get VSCode MCP config file path."""
        if self.workspace:
            # Workspace configuration in current directory
            return Path.cwd() / ".vscode" / "mcp.json"
        else:
            # User profile configuration
            home_str = str(Path.home())
            if os.name == "nt":  # Windows
                return Path(home_str) / "AppData" / "Roaming" / "Code" / "User" / "mcp.json"
            elif platform.system() == "Darwin":  # macOS
                return Path(home_str) / "Library" / "Application Support" / "Code" / "User" / "mcp.json"
            else:  # Linux
                return Path(home_str) / ".config" / "Code" / "User" / "mcp.json"
    
    def get_metadata_path(self) -> Path:
        """Get path to the metadata file for tracking managed servers."""
        config_path = self.get_config_path()
        return config_path.parent / self.METADATA_FILE
    
    def load_metadata(self) -> dict[str, Any]:
        """Load metadata about managed servers."""
        metadata_path = self.get_metadata_path()
        
        if not metadata_path.exists():
            return {}
        
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, IOError):
            return {}
    
    def save_metadata(self, metadata: dict[str, Any]) -> None:
        """Save metadata about managed servers."""
        metadata_path = self.get_metadata_path()
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            f.write("\n")
    
    def load_config(self) -> dict[str, Any]:
        """Load existing VSCode MCP configuration."""
        config_path = self.get_config_path()
        default_config: dict[str, Any] = {"servers": {}}
        
        if not config_path.exists():
            return default_config
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config: dict[str, Any] = json.load(f)
            
            if "servers" not in config:
                config["servers"] = {}
            
            return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Error loading config from {config_path}: {e}")
            return default_config
    
    def save_config(self, config: dict[str, Any]) -> None:
        """Save VSCode MCP configuration."""
        config_path = self.get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file first (atomic write)
        temp_path = config_path.with_suffix(".tmp")
        
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                f.write("\n")
            
            temp_path.replace(config_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise
    
    def setup_server(self, server_name: str, server_config: dict[str, Any]) -> bool:
        """Add server to VSCode MCP config."""
        try:
            self.backup_config()
            config = self.load_config()
            
            # Extract metadata fields
            metadata_fields = {
                "_managed_by": self.MANAGED_SERVER_MARKER,
                "_server_type": server_config.get("_server_type", "mcp-code-checker")
            }
            
            # Clean config for VSCode format (no metadata in main config)
            clean_config = {
                "command": server_config["command"],
                "args": server_config["args"]
            }
            if "env" in server_config and server_config["env"]:
                clean_config["env"] = server_config["env"]
            
            # Update server configuration
            config["servers"][server_name] = clean_config
            
            # Save config and metadata
            self.save_config(config)
            
            metadata = self.load_metadata()
            metadata[server_name] = metadata_fields
            self.save_metadata(metadata)
            
            return True
            
        except Exception as e:
            print(f"Error setting up server '{server_name}': {e}")
            return False
    
    def remove_server(self, server_name: str) -> bool:
        """Remove server from VSCode config if managed by us."""
        try:
            config = self.load_config()
            metadata = self.load_metadata()
            
            if server_name not in config.get("servers", {}):
                print(f"Server '{server_name}' not found in configuration")
                return False
            
            if server_name not in metadata or metadata[server_name].get("_managed_by") != self.MANAGED_SERVER_MARKER:
                print(f"Server '{server_name}' is not managed by this tool. Cannot remove external servers.")
                return False
            
            self.backup_config()
            
            del config["servers"][server_name]
            self.save_config(config)
            
            del metadata[server_name]
            self.save_metadata(metadata)
            
            return True
            
        except Exception as e:
            print(f"Error removing server '{server_name}': {e}")
            return False
    
    def list_managed_servers(self) -> list[dict[str, Any]]:
        """List only servers managed by this tool."""
        config = self.load_config()
        metadata = self.load_metadata()
        servers = []
        
        for name, server_config in config.get("servers", {}).items():
            if name in metadata and metadata[name].get("_managed_by") == self.MANAGED_SERVER_MARKER:
                servers.append({
                    "name": name,
                    "type": metadata[name].get("_server_type", "unknown"),
                    "command": server_config.get("command", ""),
                    "args": server_config.get("args", []),
                    "env": server_config.get("env", {})
                })
        
        return servers
    
    def list_all_servers(self) -> list[dict[str, Any]]:
        """List all servers in configuration."""
        config = self.load_config()
        metadata = self.load_metadata()
        servers = []
        
        for name, server_config in config.get("servers", {}).items():
            is_managed = (
                name in metadata and 
                metadata[name].get("_managed_by") == self.MANAGED_SERVER_MARKER
            )
            
            server_type = "unknown"
            if is_managed and name in metadata:
                server_type = metadata[name].get("_server_type", "unknown")
            
            servers.append({
                "name": name,
                "managed": is_managed,
                "type": server_type,
                "command": server_config.get("command", ""),
                "args": server_config.get("args", []),
                "env": server_config.get("env", {})
            })
        
        return servers
    
    def backup_config(self) -> Path:
        """Create a backup of the current configuration."""
        config_path = self.get_config_path()
        
        if not config_path.exists():
            return config_path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"mcp_backup_{timestamp}.json"
        backup_path = config_path.parent / backup_name
        
        shutil.copy2(config_path, backup_path)
        return backup_path
    
    def validate_config(self) -> list[str]:
        """Validate current configuration."""
        errors = []
        
        try:
            config = self.load_config()
            
            if "servers" not in config:
                errors.append("Configuration missing 'servers' section")
            elif not isinstance(config["servers"], dict):
                errors.append("'servers' must be an object")
            else:
                for name, server_config in config["servers"].items():
                    if not isinstance(server_config, dict):
                        errors.append(f"Server '{name}' configuration must be an object")
                        continue
                    
                    if "command" not in server_config:
                        errors.append(f"Server '{name}' missing required 'command' field")
                    
                    if "args" in server_config and not isinstance(server_config["args"], list):
                        errors.append(f"Server '{name}' 'args' field must be an array")
                    
                    if "env" in server_config and not isinstance(server_config["env"], dict):
                        errors.append(f"Server '{name}' 'env' field must be an object")
        
        except Exception as e:
            errors.append(f"Error reading configuration: {e}")
        
        return errors


# Client registry
# Type alias for handler factories
HandlerFactory = Union[type[ClientHandler], Callable[[], ClientHandler]]

CLIENT_HANDLERS: dict[str, HandlerFactory] = {
    "claude-desktop": ClaudeDesktopHandler,
    "vscode": lambda: VSCodeHandler(workspace=True),  # Default to workspace
    "vscode-workspace": lambda: VSCodeHandler(workspace=True),
    "vscode-user": lambda: VSCodeHandler(workspace=False),
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

    handler_factory = CLIENT_HANDLERS[client_name]
    # Check if it's a lambda/callable or a class
    if callable(handler_factory) and not isinstance(handler_factory, type):
        # It's a lambda or function, call it to get the handler instance
        handler = handler_factory()
    else:
        # It's a class, instantiate it
        handler = handler_factory()
    
    # If it's ClaudeDesktopHandler, try to migrate any inline metadata
    if isinstance(handler, ClaudeDesktopHandler):
        handler.migrate_inline_metadata()
    
    return handler
