"""Integration between ServerConfig and ClientHandler.

This module provides high-level functions that bridge server configurations
and client handlers for setting up MCP servers.
"""

import sys
from pathlib import Path
from typing import Any

from src.config.clients import ClientHandler
from src.config.servers import ServerConfig
from src.config.utils import (
    normalize_path_parameter,
    validate_parameter_value,
    validate_required_parameters,
)


def build_server_config(
    server_config: ServerConfig,
    user_params: dict[str, Any],
    python_executable: str | None = None,
) -> dict[str, Any]:
    """Build server configuration for preview/dry-run.

    This is a simplified version of generate_client_config for preview purposes.

    Args:
        server_config: Server configuration definition
        user_params: User-provided parameter values
        python_executable: Python executable to use

    Returns:
        Configuration dictionary for preview
    """
    # Get project directory
    project_dir = Path(user_params.get("project_dir", ".")).resolve()

    # Normalize parameters
    normalized_params = {}
    for key, value in user_params.items():
        if key in ["project_dir", "test_folder", "log_file", "venv_path"] and value:
            normalized_params[key] = str(
                Path(value).resolve()
                if Path(value).is_absolute()
                else project_dir / value
            )
        else:
            normalized_params[key] = value

    # Generate args
    args = server_config.generate_args(normalized_params)

    # Build config
    config: dict[str, Any] = {
        "command": python_executable or sys.executable,
        "args": args,
        "_managed_by": "mcp-config-managed",
        "_server_type": server_config.name,
    }

    # Add environment if needed
    if "project_dir" in normalized_params:
        config["env"] = {"PYTHONPATH": str(normalized_params["project_dir"])}

    return config


def generate_client_config(
    server_config: ServerConfig,
    server_name: str,
    user_params: dict[str, Any],
    python_executable: str | None = None,
) -> dict[str, Any]:
    """Generate client configuration from server config and user parameters.

    Args:
        server_config: Server configuration definition
        server_name: User-provided server instance name
        user_params: User-provided parameter values (with underscores)
        python_executable: Path to Python executable to use (auto-detect if None)

    Returns:
        Client configuration dictionary ready for JSON serialization

    Raises:
        ValueError: If required parameters are missing or invalid
    """
    # Convert user_params keys from underscore to hyphen format for validation
    # (they come from argparse with underscores, but ParameterDef uses hyphens)
    hyphen_params = {}
    for key, value in user_params.items():
        hyphen_key = key.replace("_", "-")
        hyphen_params[hyphen_key] = value

    # Validate required parameters
    errors = validate_required_parameters(server_config, hyphen_params)
    if errors:
        raise ValueError(f"Parameter validation failed: {', '.join(errors)}")

    # Validate individual parameter values
    for param in server_config.parameters:
        if param.name in hyphen_params:
            value = hyphen_params[param.name]
            param_errors = validate_parameter_value(param, value)
            if param_errors:
                errors.extend(param_errors)

    if errors:
        raise ValueError(f"Parameter validation failed: {', '.join(errors)}")

    # Get project directory (required for path normalization)
    project_dir = Path(hyphen_params.get("project-dir", ".")).resolve()

    # Normalize path parameters (convert back to underscore format for generate_args)
    normalized_params = {}
    for param in server_config.parameters:
        param_key = param.name.replace("-", "_")
        if param_key in user_params:
            value = user_params[param_key]
            if param.param_type == "path" and value is not None:
                # Normalize path relative to project directory
                normalized_params[param_key] = normalize_path_parameter(
                    value, project_dir
                )
            else:
                normalized_params[param_key] = value

    # Use provided Python executable or default to current
    if python_executable is None:
        python_executable = sys.executable

    # Generate command-line arguments
    args = server_config.generate_args(normalized_params)

    # Build the client configuration
    client_config: dict[str, Any] = {
        "command": python_executable,
        "args": args,
        "_server_type": server_config.name,
    }

    # Add environment variables if needed
    env = {}

    # Add PYTHONPATH to include the project directory
    if "project_dir" in normalized_params:
        env["PYTHONPATH"] = normalized_params["project_dir"]

    # Add virtual environment activation if specified
    if "venv_path" in normalized_params and normalized_params["venv_path"]:
        venv_path = Path(normalized_params["venv_path"])
        if venv_path.exists():
            # Update Python executable to use the one from venv
            if sys.platform == "win32":
                venv_python = venv_path / "Scripts" / "python.exe"
            else:
                venv_python = venv_path / "bin" / "python"

            if venv_python.exists():
                client_config["command"] = str(venv_python)

    if env:
        client_config["env"] = env

    return client_config


def setup_mcp_server(
    client_handler: ClientHandler,
    server_config: ServerConfig,
    server_name: str,
    user_params: dict[str, Any],
    python_executable: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """High-level function to set up an MCP server in a client.

    Args:
        client_handler: Client handler instance
        server_config: Server configuration definition
        server_name: User-provided server instance name
        user_params: User-provided parameter values
        python_executable: Python executable to use (auto-detect if None)
        dry_run: If True, return what would be done without applying changes

    Returns:
        Dictionary with operation results and details
    """
    result = {
        "success": False,
        "server_name": server_name,
        "operation": "setup",
        "dry_run": dry_run,
    }

    try:
        # Generate the client configuration
        client_config = generate_client_config(
            server_config, server_name, user_params, python_executable
        )

        result["config"] = client_config
        result["config_path"] = str(client_handler.get_config_path())

        if dry_run:
            # Just return what would be done
            result["success"] = True
            result["message"] = f"Would set up server '{server_name}'"
            return result

        # Actually set up the server
        success = client_handler.setup_server(server_name, client_config)

        if success:
            result["success"] = True
            result["message"] = f"Successfully set up server '{server_name}'"

            # Get backup path if available
            try:
                # Try to get the most recent backup
                config_path = client_handler.get_config_path()
                backup_files = list(
                    config_path.parent.glob("claude_desktop_config_backup_*.json")
                )
                if backup_files:
                    # Sort by modification time and get the most recent
                    latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
                    result["backup_path"] = str(latest_backup)
            except Exception:
                pass  # Backup path is optional

        else:
            result["message"] = f"Failed to set up server '{server_name}'"

    except Exception as e:
        result["error"] = str(e)
        result["message"] = f"Error setting up server: {e}"

    return result


def remove_mcp_server(
    client_handler: ClientHandler,
    server_name: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Remove an MCP server from client configuration.

    Args:
        client_handler: Client handler instance
        server_name: Name of server to remove
        dry_run: If True, return what would be done without applying changes

    Returns:
        Dictionary with operation results
    """
    result = {
        "success": False,
        "server_name": server_name,
        "operation": "remove",
        "dry_run": dry_run,
    }

    try:
        # Check if server exists and is managed
        all_servers = client_handler.list_all_servers()
        server_info = None
        for server in all_servers:
            if server["name"] == server_name:
                server_info = server
                break

        if not server_info:
            result["message"] = f"Server '{server_name}' not found"
            return result

        if not server_info.get("managed", False):
            result["message"] = (
                f"Server '{server_name}' is not managed by this tool. "
                "Cannot remove external servers."
            )
            return result

        result["config_path"] = str(client_handler.get_config_path())

        if dry_run:
            result["success"] = True
            result["message"] = f"Would remove server '{server_name}'"
            return result

        # Actually remove the server
        success = client_handler.remove_server(server_name)

        if success:
            result["success"] = True
            result["message"] = f"Successfully removed server '{server_name}'"

            # Get backup path if available
            try:
                config_path = client_handler.get_config_path()
                backup_files = list(
                    config_path.parent.glob("claude_desktop_config_backup_*.json")
                )
                if backup_files:
                    latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
                    result["backup_path"] = str(latest_backup)
            except Exception:
                pass

        else:
            result["message"] = f"Failed to remove server '{server_name}'"

    except Exception as e:
        result["error"] = str(e)
        result["message"] = f"Error removing server: {e}"

    return result
