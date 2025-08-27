"""Integration between ServerConfig and ClientHandler.

This module provides high-level functions that bridge server configurations
and client handlers for setting up MCP servers.
"""

import importlib.util
import shutil
import sys
from pathlib import Path
from typing import Any

from src.config.clients import ClientHandler, VSCodeHandler
from src.config.servers import ServerConfig
from src.config.utils import (
    normalize_path_parameter,
    validate_parameter_value,
    validate_required_parameters,
)


def is_command_available(command: str) -> bool:
    """Check if a command is available in the system PATH.
    
    Args:
        command: Command name to check
        
    Returns:
        True if command is available in PATH
    """
    return shutil.which(command) is not None


def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed.

    Args:
        package_name: Name of the package to check

    Returns:
        True if package is installed and importable
    """
    try:
        spec = importlib.util.find_spec(package_name)
        return spec is not None
    except (ImportError, ModuleNotFoundError):
        return False


def get_mcp_code_checker_command_mode() -> str:
    """Determine the best command mode for MCP Code Checker.
    
    Returns:
        One of: 'cli_command', 'python_module', 'development', 'not_available'
    """
    # First check for CLI command
    if is_command_available("mcp-code-checker"):
        return "cli_command"
    
    # Check if package is installed
    if is_package_installed("mcp_code_checker"):
        return "python_module"
    
    # Check if we're in development mode (src/main.py exists)
    if Path("src/main.py").exists():
        return "development"
    
    return "not_available"


def generate_vscode_command(
    server_type: str, server_config: dict[str, Any], workspace: bool = True
) -> dict[str, Any]:
    """Generate VSCode-compatible server configuration.

    Args:
        server_type: Type of server (e.g., "mcp-code-checker")
        server_config: Raw server configuration
        workspace: Whether this is for workspace config

    Returns:
        VSCode-formatted server configuration
    """
    config: dict[str, Any] = {}

    # Determine command mode for mcp-code-checker
    if server_type == "mcp-code-checker":
        mode = get_mcp_code_checker_command_mode()
        
        if mode == "cli_command":
            # Use the CLI command directly
            config["command"] = "mcp-code-checker"
            # Skip the first arg (script path) if present
            original_args = server_config.get("args", [])
            if original_args and original_args[0].endswith(("main.py", "server.py")):
                config["args"] = original_args[1:]  # Skip the script path
            else:
                config["args"] = original_args
                
        elif mode == "python_module":
            # Use package module invocation
            config["command"] = sys.executable
            original_args = server_config.get("args", [])
            if original_args and original_args[0].endswith(("main.py", "server.py")):
                config["args"] = ["-m", "mcp_code_checker"] + original_args[1:]
            else:
                config["args"] = ["-m", "mcp_code_checker"] + original_args
                
        else:  # development or not_available
            # Use direct path (existing behavior)
            config["command"] = server_config.get("command", sys.executable)
            config["args"] = server_config.get("args", [])
    else:
        # Other server types - use as-is
        config["command"] = server_config.get("command")
        config["args"] = server_config.get("args", [])

    # Handle environment variables
    if "env" in server_config and server_config["env"]:
        config["env"] = server_config["env"]

    # Preserve metadata field for internal use
    if "_server_type" in server_config:
        config["_server_type"] = server_config["_server_type"]

    # Normalize paths based on workspace vs user config
    if workspace:
        # For workspace configs, prefer relative paths where possible
        config = make_paths_relative(config, Path.cwd())
    else:
        # For user configs, ensure absolute paths
        config = make_paths_absolute(config)

    return config


def make_paths_relative(config: dict[str, Any], base_path: Path) -> dict[str, Any]:
    """Convert absolute paths to relative where possible.

    Args:
        config: Server configuration
        base_path: Base path to make paths relative to

    Returns:
        Configuration with relative paths
    """
    updated = config.copy()

    # Process arguments
    if "args" in updated:
        updated_args = []
        skip_next = False

        for i, arg in enumerate(updated["args"]):
            if skip_next:
                skip_next = False
                # This is the value for a path argument
                try:
                    path_obj = Path(arg)
                    if path_obj.is_absolute():
                        try:
                            rel_path = path_obj.relative_to(base_path)
                            # Only use relative path if it doesn't go up directories
                            if not str(rel_path).startswith(".."):
                                updated_args.append(str(rel_path).replace("\\", "/"))
                            else:
                                updated_args.append(arg)
                        except ValueError:
                            # Path is not relative to base, keep absolute
                            updated_args.append(arg)
                    else:
                        updated_args.append(arg)
                except (ValueError, OSError):
                    updated_args.append(arg)
            elif arg in [
                "--project-dir",
                "--python-executable",
                "--venv-path",
                "--log-file",
            ]:
                skip_next = True
                updated_args.append(arg)
            else:
                updated_args.append(arg)

        updated["args"] = updated_args

    return updated


def make_paths_absolute(config: dict[str, Any]) -> dict[str, Any]:
    """Ensure all paths are absolute.

    Args:
        config: Server configuration

    Returns:
        Configuration with absolute paths
    """
    updated = config.copy()

    # Process arguments
    if "args" in updated:
        updated_args = []
        skip_next = False

        for i, arg in enumerate(updated["args"]):
            if skip_next:
                skip_next = False
                # This is the value for a path argument
                try:
                    path_obj = Path(arg)
                    if not path_obj.is_absolute():
                        updated_args.append(str(path_obj.resolve()))
                    else:
                        updated_args.append(arg)
                except (ValueError, OSError):
                    updated_args.append(arg)
            elif arg in [
                "--project-dir",
                "--python-executable",
                "--venv-path",
                "--log-file",
            ]:
                skip_next = True
                updated_args.append(arg)
            else:
                updated_args.append(arg)

        updated["args"] = updated_args

    return updated


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

    # Determine command mode
    config: dict[str, Any]
    if server_config.name == "mcp-code-checker":
        mode = get_mcp_code_checker_command_mode()
        
        if mode == "cli_command":
            # Generate args for CLI command (without script path)
            args = server_config.generate_args(normalized_params, use_cli_command=True)
            config = {
                "command": "mcp-code-checker",
                "args": args,
            }
        elif mode == "python_module":
            # Generate args for module invocation
            args = server_config.generate_args(normalized_params, use_cli_command=True)
            config = {
                "command": python_executable or sys.executable,
                "args": ["-m", "mcp_code_checker"] + args,
            }
        else:
            # Development/fallback mode
            args = server_config.generate_args(normalized_params)
            config = {
                "command": python_executable or sys.executable,
                "args": args,
            }
    else:
        # Other servers
        args = server_config.generate_args(normalized_params)
        config = {
            "command": python_executable or sys.executable,
            "args": args,
        }

    # Add environment if needed
    if "project_dir" in normalized_params:
        pythonpath = str(normalized_params["project_dir"])
        # Ensure trailing separator on Windows
        if sys.platform == "win32" and not pythonpath.endswith("\\"):
            pythonpath += "\\"
        config["env"] = {"PYTHONPATH": pythonpath}

    return config


def generate_client_config(
    server_config: ServerConfig,
    server_name: str,
    user_params: dict[str, Any],
    python_executable: str | None = None,
    client_handler: ClientHandler | None = None,
) -> dict[str, Any]:
    """Generate client configuration from server config and user parameters.

    Args:
        server_config: Server configuration definition
        server_name: User-provided server instance name
        user_params: User-provided parameter values (with underscores)
        python_executable: Path to Python executable to use (auto-detect if None)
        client_handler: Client handler instance for client-specific formatting

    Returns:
        Client configuration dictionary ready for JSON serialization

    Raises:
        ValueError: If required parameters are missing or invalid
    """
    # Validate required parameters
    # Note: user_params already has underscore format from argparse
    errors = validate_required_parameters(server_config, user_params)
    if errors:
        raise ValueError(f"Parameter validation failed: {', '.join(errors)}")

    # Validate individual parameter values
    for param in server_config.parameters:
        # Convert parameter name to underscore format to match user_params
        param_key = param.name.replace("-", "_")
        if param_key in user_params:
            value = user_params[param_key]
            param_errors = validate_parameter_value(param, value)
            if param_errors:
                errors.extend(param_errors)

    if errors:
        raise ValueError(f"Parameter validation failed: {', '.join(errors)}")

    # Get project directory (required for path normalization)
    project_dir = Path(user_params.get("project_dir", ".")).resolve()

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

    # Determine command mode for mcp-code-checker
    client_config: dict[str, Any]
    if server_config.name == "mcp-code-checker":
        mode = get_mcp_code_checker_command_mode()
        
        if mode == "cli_command":
            args = server_config.generate_args(normalized_params, use_cli_command=True)
            client_config = {
                "command": "mcp-code-checker",
                "args": args,
            }
        elif mode == "python_module":
            args = server_config.generate_args(normalized_params, use_cli_command=True)
            client_config = {
                "command": python_executable or sys.executable,
                "args": ["-m", "mcp_code_checker"] + args,
            }
        else:
            args = server_config.generate_args(normalized_params)
            client_config = {
                "command": python_executable or sys.executable,
                "args": args,
            }
    else:
        # Other servers
        args = server_config.generate_args(normalized_params)
        client_config = {
            "command": python_executable or sys.executable,
            "args": args,
        }

    # Store metadata separately (will be handled by ClientHandler)
    # The _server_type will be passed through setup_server and extracted there
    client_config["_server_type"] = server_config.name

    # Add environment variables if needed
    env = {}

    # Add PYTHONPATH to include the project directory
    if "project_dir" in normalized_params:
        pythonpath = normalized_params["project_dir"]
        # Ensure trailing separator on Windows
        if sys.platform == "win32" and not pythonpath.endswith("\\"):
            pythonpath += "\\"
        env["PYTHONPATH"] = pythonpath

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
                # Only update command if not using CLI command
                if client_config["command"] != "mcp-code-checker":
                    client_config["command"] = str(venv_python)

    if env:
        client_config["env"] = env

    # Apply VSCode-specific formatting if needed
    if client_handler and isinstance(client_handler, VSCodeHandler):
        workspace = getattr(client_handler, "workspace", True)
        client_config = generate_vscode_command(
            server_config.name, client_config, workspace
        )

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
            server_config, server_name, user_params, python_executable, client_handler
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
