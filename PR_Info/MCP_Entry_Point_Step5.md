# Step 5: Complete Integration Module Updates

## Objective
Finalize the integration module with all CLI command detection and generation logic.

## Files to Modify
- `src/config/integration.py` - Complete implementation

## Full Implementation

### Complete Updated integration.py Code

```python
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
        config = make_paths_relative(config, Path.cwd())
    else:
        config = make_paths_absolute(config)

    return config


def build_server_config(
    server_config: ServerConfig,
    user_params: dict[str, Any],
    python_executable: str | None = None,
) -> dict[str, Any]:
    """Build server configuration for preview/dry-run.

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
    if server_config.name == "mcp-code-checker":
        mode = get_mcp_code_checker_command_mode()
        
        if mode == "cli_command":
            # Generate args for CLI command (without script path)
            args = server_config.generate_args(normalized_params, use_cli_command=True)
            config: dict[str, Any] = {
                "command": "mcp-code-checker",
                "args": args,
            }
        elif mode == "python_module":
            # Generate args for module invocation
            args = server_config.generate_args(normalized_params, use_cli_command=True)
            config: dict[str, Any] = {
                "command": python_executable or sys.executable,
                "args": ["-m", "mcp_code_checker"] + args,
            }
        else:
            # Development/fallback mode
            args = server_config.generate_args(normalized_params)
            config: dict[str, Any] = {
                "command": python_executable or sys.executable,
                "args": args,
            }
    else:
        # Other servers
        args = server_config.generate_args(normalized_params)
        config: dict[str, Any] = {
            "command": python_executable or sys.executable,
            "args": args,
        }

    # Add environment if needed
    if "project_dir" in normalized_params:
        pythonpath = str(normalized_params["project_dir"])
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
    errors = validate_required_parameters(server_config, user_params)
    if errors:
        raise ValueError(f"Parameter validation failed: {', '.join(errors)}")

    # Validate individual parameter values
    for param in server_config.parameters:
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

    # Normalize path parameters
    normalized_params = {}
    for param in server_config.parameters:
        param_key = param.name.replace("-", "_")
        if param_key in user_params:
            value = user_params[param_key]
            if param.param_type == "path" and value is not None:
                normalized_params[param_key] = normalize_path_parameter(
                    value, project_dir
                )
            else:
                normalized_params[param_key] = value

    # Use provided Python executable or default to current
    if python_executable is None:
        python_executable = sys.executable

    # Determine command mode for mcp-code-checker
    if server_config.name == "mcp-code-checker":
        mode = get_mcp_code_checker_command_mode()
        
        if mode == "cli_command":
            args = server_config.generate_args(normalized_params, use_cli_command=True)
            client_config: dict[str, Any] = {
                "command": "mcp-code-checker",
                "args": args,
            }
        elif mode == "python_module":
            args = server_config.generate_args(normalized_params, use_cli_command=True)
            client_config: dict[str, Any] = {
                "command": python_executable,
                "args": ["-m", "mcp_code_checker"] + args,
            }
        else:
            args = server_config.generate_args(normalized_params)
            client_config: dict[str, Any] = {
                "command": python_executable,
                "args": args,
            }
    else:
        # Other servers
        args = server_config.generate_args(normalized_params)
        client_config: dict[str, Any] = {
            "command": python_executable,
            "args": args,
        }

    # Store metadata separately
    client_config["_server_type"] = server_config.name

    # Add environment variables if needed
    env = {}

    # Add PYTHONPATH to include the project directory
    if "project_dir" in normalized_params:
        pythonpath = normalized_params["project_dir"]
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


# Keep existing helper functions (make_paths_relative, make_paths_absolute, etc.)
# ... rest of the file remains the same ...
```

## Key Changes Explained

1. **Added `is_command_available()`**: Checks if a command exists in PATH
2. **Added `get_mcp_code_checker_command_mode()`**: Determines best command mode
3. **Updated all config generation**: Now checks command mode and generates appropriate config
4. **Smart fallback**: CLI command → Python module → Development mode
5. **Preserves venv handling**: Still respects virtual environment settings

## Testing the Implementation

```bash
# Test 1: With CLI command installed
pip install -e .
mcp-config setup mcp-code-checker "test1" --project-dir . --dry-run
# Expected: "command": "mcp-code-checker"

# Test 2: Simulate module-only installation
# (temporarily rename the command entry point and reinstall)
mcp-config setup mcp-code-checker "test2" --project-dir . --dry-run  
# Expected: "command": "python", "args": ["-m", "mcp_code_checker", ...]

# Test 3: Development mode
# (in fresh environment without installation)
cd /path/to/mcp-code-checker
python -m src.config.main setup mcp-code-checker "test3" --project-dir . --dry-run
# Expected: "command": "python", "args": ["src/main.py", ...]
```

## Next Step
Proceed to Step 6 to update the server registry with the new methods.
