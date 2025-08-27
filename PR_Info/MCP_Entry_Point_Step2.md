# Step 2: Update Config Tool to Detect mcp-code-checker Command

## Objective
Update the config tool to detect if `mcp-code-checker` is installed as a command and prefer it over the Python module approach when generating configurations.

## Files to Modify
- `src/config/integration.py` - Add command detection logic

## Implementation

### 1. Add Command Detection Function
Add a new function to check if `mcp-code-checker` command is available:

```python
def is_command_available(command: str) -> bool:
    """Check if a command is available in the system PATH.
    
    Args:
        command: Command name to check
        
    Returns:
        True if command is available in PATH
    """
    import shutil
    return shutil.which(command) is not None
```

### 2. Update `generate_vscode_command` Function
Modify the function to check for the CLI command first:

```python
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

    # Determine if we should use the CLI command or module invocation
    if server_type == "mcp-code-checker":
        # First check if mcp-code-checker command is available
        if is_command_available("mcp-code-checker"):
            # Use the CLI command directly
            config["command"] = "mcp-code-checker"
            # Skip the first arg (script path) if present, keep other args
            original_args = server_config.get("args", [])
            if original_args and original_args[0].endswith(("main.py", "server.py")):
                config["args"] = original_args[1:]  # Skip the script path
            else:
                config["args"] = original_args
        elif is_package_installed("mcp_code_checker"):
            # Fallback to package module invocation
            config["command"] = sys.executable
            original_args = server_config.get("args", [])
            if original_args and original_args[0].endswith(("main.py", "server.py")):
                config["args"] = ["-m", "mcp_code_checker"] + original_args[1:]
            else:
                config["args"] = ["-m", "mcp_code_checker"] + original_args
        else:
            # Running from source - use direct path
            config["command"] = server_config.get("command", sys.executable)
            config["args"] = server_config.get("args", [])
    else:
        # Other server types - use as-is
        config["command"] = server_config.get("command")
        config["args"] = server_config.get("args", [])

    # Rest of function remains the same...
```

### 3. Update `build_server_config` Function
Modify to use CLI command when available:

```python
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

    # Check if we should use the CLI command
    if server_config.name == "mcp-code-checker" and is_command_available("mcp-code-checker"):
        # Use CLI command, skip the script path from args if present
        if args and args[0].endswith(("main.py", "server.py")):
            args = args[1:]
        config: dict[str, Any] = {
            "command": "mcp-code-checker",
            "args": args,
        }
    else:
        # Use Python executable
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
```

### 4. Update `generate_client_config` Function
Similar updates to prefer CLI command when available:

```python
# In generate_client_config, after generating args:

    # Build the client configuration
    if server_config.name == "mcp-code-checker" and is_command_available("mcp-code-checker"):
        # Use CLI command
        if args and args[0].endswith(("main.py", "server.py")):
            args = args[1:]  # Skip script path
        client_config: dict[str, Any] = {
            "command": "mcp-code-checker",
            "args": args,
        }
    else:
        # Use Python executable (existing logic)
        client_config: dict[str, Any] = {
            "command": python_executable,
            "args": args,
        }
```

## Testing
After implementation, test:
1. With `mcp-code-checker` installed: Should use the command
2. Without command but with package: Should use `python -m mcp_code_checker`
3. In development mode: Should use direct script path

## Verification Commands
```bash
# Test dry-run with command available
mcp-config setup mcp-code-checker "test" --project-dir . --dry-run

# Should show:
# "command": "mcp-code-checker"
# Instead of:
# "command": "/path/to/python"
```

## Next Step
Proceed to Step 3 to update the server registry configuration.
