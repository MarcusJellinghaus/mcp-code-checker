# Step 3: Update Server Registry Configuration

## Objective
Update the server configuration in `src/config/servers.py` to properly handle the new CLI command approach.

## Files to Modify
- `src/config/servers.py` - Update MCP_CODE_CHECKER configuration

## Implementation

### 1. Update ServerConfig.generate_args Method
Modify the `generate_args` method in `ServerConfig` class to handle CLI command mode:

```python
def generate_args(self, user_params: dict[str, Any], use_cli_command: bool = False) -> list[str]:
    """Generate command line args from user parameters.

    Args:
        user_params: Dictionary of parameter names to values
        use_cli_command: If True, generate args for CLI command (skip main module)

    Returns:
        List of command-line arguments
    """
    from src.config.validation import (
        auto_detect_python_executable,
        auto_detect_venv_path,
        normalize_path,
    )

    # For CLI command mode, don't include the main module
    if use_cli_command:
        args = []
    else:
        # Get the absolute path to the main module
        if self.name == "mcp-code-checker" and "project_dir" in user_params:
            proj_dir = Path(user_params["project_dir"]).resolve()
            main_module_path = proj_dir / self.main_module
            args = [str(main_module_path.resolve())]
        else:
            args = [self.main_module]

    # Rest of the method remains the same...
    # Process parameters with auto-detection
    processed_params = dict(user_params)

    # Auto-detect missing optional parameters
    project_dir: Path | None = None
    if "project_dir" in processed_params:
        project_dir = Path(processed_params["project_dir"])

    for param in self.parameters:
        param_key = param.name.replace("-", "_")

        # Skip if already has a value
        if (
            param_key in processed_params
            and processed_params[param_key] is not None
        ):
            continue

        # Auto-detect if possible
        if param.auto_detect and project_dir:
            if param.name == "python-executable":
                # Don't auto-detect python-executable in CLI command mode
                if not use_cli_command:
                    detected = auto_detect_python_executable(project_dir)
                    if detected:
                        processed_params[param_key] = str(detected)
            elif param.name == "venv-path":
                detected = auto_detect_venv_path(project_dir)
                if detected:
                    processed_params[param_key] = str(detected)

    # Generate arguments
    for param in self.parameters:
        param_key = param.name.replace("-", "_")

        # Get value from processed params or use default
        value = processed_params.get(param_key, param.default)

        # Skip if no value provided
        if value is None:
            continue

        # Skip python-executable in CLI command mode (not needed)
        if use_cli_command and param.name == "python-executable":
            continue

        # Handle boolean flags
        if param.is_flag:
            if value:  # Only add flag if True
                args.append(param.arg_name)
        else:
            # Normalize paths
            if param.param_type == "path" and project_dir:
                value = str(normalize_path(value, project_dir))

            # Add parameter and value
            args.append(param.arg_name)
            args.append(str(value))

    return args
```

### 2. Add Method to Check CLI Command Availability
Add a helper method to ServerConfig:

```python
def supports_cli_command(self) -> bool:
    """Check if this server supports CLI command mode.
    
    Returns:
        True if the server has a CLI command available
    """
    if self.name == "mcp-code-checker":
        import shutil
        return shutil.which("mcp-code-checker") is not None
    return False
```

### 3. Update validate_project Method
Enhance project validation to work with both modes:

```python
def validate_project(self, project_dir: Path) -> bool:
    """Check if project is compatible (server-specific logic).

    For MCP Code Checker, validates that the expected structure exists.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if the project is valid for this server
    """
    if self.name == "mcp-code-checker":
        # If using CLI command, just check that it's a valid directory
        if self.supports_cli_command():
            return project_dir.exists() and project_dir.is_dir()
        
        # For development mode, check for expected structure
        main_path = project_dir / self.main_module
        src_path = project_dir / "src"

        # Both the main module and src directory should exist
        return main_path.exists() and src_path.exists()

    # Default validation for other servers
    return True
```

### 4. Update Integration Code Usage
Back in `src/config/integration.py`, update calls to use the new parameter:

```python
# In build_server_config function:
    
    # Check if we should use CLI command mode
    use_cli = server_config.supports_cli_command()
    
    # Generate args with appropriate mode
    args = server_config.generate_args(normalized_params, use_cli_command=use_cli)
    
    # Build config based on mode
    if use_cli:
        config: dict[str, Any] = {
            "command": "mcp-code-checker",
            "args": args,
        }
    else:
        config: dict[str, Any] = {
            "command": python_executable or sys.executable,
            "args": args,
        }

# Similar updates in generate_client_config function
```

## Benefits of This Approach
1. **Clean separation**: CLI command mode vs development mode
2. **Backward compatible**: Existing logic preserved
3. **Smart detection**: Automatically uses best available method
4. **Flexible**: Easy to extend for other servers with CLI commands

## Testing
```bash
# Test with CLI command installed
pip install -e .
mcp-config setup mcp-code-checker "test" --project-dir . --dry-run
# Should show: "command": "mcp-code-checker"

# Test in development mode (without CLI command)
# Temporarily rename the command or test in fresh environment
mcp-config setup mcp-code-checker "test" --project-dir . --dry-run  
# Should show: "command": "/path/to/python", "args": ["src/main.py", ...]
```

## Next Step
Proceed to Step 4 to add validation for the CLI command.
