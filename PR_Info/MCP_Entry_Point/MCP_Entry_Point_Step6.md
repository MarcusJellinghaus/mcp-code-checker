# Step 6: Update Server Registry with CLI Support

## Objective
Complete the server registry updates to fully support CLI command mode.

## Files to Modify
- `src/config/servers.py` - Add CLI command support methods

## Implementation

### Add the Following Methods to ServerConfig Class

```python
# In src/config/servers.py, add these methods to the ServerConfig class:

def supports_cli_command(self) -> bool:
    """Check if this server supports CLI command mode.
    
    Returns:
        True if the server has a CLI command available
    """
    if self.name == "mcp-code-checker":
        import shutil
        return shutil.which("mcp-code-checker") is not None
    # Add other servers with CLI commands here in the future
    return False

def get_cli_command_name(self) -> str | None:
    """Get the CLI command name for this server.
    
    Returns:
        CLI command name if available, None otherwise
    """
    if self.name == "mcp-code-checker":
        return "mcp-code-checker"
    # Add other servers here
    return None

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

    # Initialize args based on mode
    if use_cli_command:
        # For CLI command mode, don't include the main module
        args = []
    else:
        # Get the absolute path to the main module
        if self.name == "mcp-code-checker" and "project_dir" in user_params:
            proj_dir = Path(user_params["project_dir"]).resolve()
            main_module_path = proj_dir / self.main_module
            args = [str(main_module_path.resolve())]
        else:
            args = [self.main_module]

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
                # Skip python-executable in CLI command mode
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

        # Skip python-executable in CLI command mode
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

def validate_project(self, project_dir: Path) -> bool:
    """Check if project is compatible (server-specific logic).

    For MCP Code Checker, validates based on installation mode.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if the project is valid for this server
    """
    if self.name == "mcp-code-checker":
        # If using CLI command, just verify directory exists
        if self.supports_cli_command():
            return project_dir.exists() and project_dir.is_dir()
        
        # Check if package is installed (module mode)
        try:
            import importlib.util
            spec = importlib.util.find_spec("mcp_code_checker")
            if spec is not None:
                # Package is installed, just need valid directory
                return project_dir.exists() and project_dir.is_dir()
        except (ImportError, ModuleNotFoundError):
            pass
        
        # Development mode - check for expected structure
        main_path = project_dir / self.main_module
        src_path = project_dir / "src"

        # Both the main module and src directory should exist
        return main_path.exists() and src_path.exists()

    # Default validation for other servers
    return True

def get_installation_mode(self) -> str:
    """Get the current installation mode for this server.
    
    Returns:
        One of: 'cli_command', 'python_module', 'development', 'not_available'
    """
    if self.name == "mcp-code-checker":
        import shutil
        import importlib.util
        
        # Check for CLI command
        if shutil.which("mcp-code-checker"):
            return "cli_command"
        
        # Check if package is installed
        try:
            spec = importlib.util.find_spec("mcp_code_checker")
            if spec is not None:
                return "python_module"
        except (ImportError, ModuleNotFoundError):
            pass
        
        # Check for development mode
        from pathlib import Path
        if Path("src/main.py").exists():
            return "development"
        
        return "not_available"
    
    # Default for other servers
    return "not_available"
```

## Update the MCP_CODE_CHECKER Configuration

No changes needed to the MCP_CODE_CHECKER definition itself, as the new methods handle everything dynamically.

## Benefits

1. **Encapsulation**: All CLI command logic is in the ServerConfig class
2. **Extensibility**: Easy to add CLI commands for other servers
3. **Consistency**: Same interface for all server types
4. **Smart detection**: Automatically determines best installation mode

## Testing

Create a test script to verify the implementation:

```python
# test_cli_command.py
from src.config.servers import registry

# Get the MCP Code Checker config
config = registry.get("mcp-code-checker")

# Test methods
print(f"Supports CLI command: {config.supports_cli_command()}")
print(f"CLI command name: {config.get_cli_command_name()}")
print(f"Installation mode: {config.get_installation_mode()}")

# Test argument generation
test_params = {
    "project_dir": ".",
    "log_level": "DEBUG"
}

print("\nArgs for CLI command mode:")
print(config.generate_args(test_params, use_cli_command=True))

print("\nArgs for module mode:")
print(config.generate_args(test_params, use_cli_command=False))
```

## Next Step
Proceed to Step 7 to update the README documentation.
