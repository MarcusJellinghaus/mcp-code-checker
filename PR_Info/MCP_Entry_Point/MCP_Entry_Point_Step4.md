# Step 4: Add Validation for CLI Command

## Objective
Update validation module to check if `mcp-code-checker` command is properly installed and provide helpful messages.

## Files to Modify
- `src/config/validation.py` - Add CLI command validation

## Implementation

### 1. Add CLI Command Validation Function
Add a new validation function to check command availability:

```python
def validate_cli_command(command: str) -> list[str]:
    """Validate that a CLI command is available.
    
    Args:
        command: Command name to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    import shutil
    
    errors = []
    
    if not shutil.which(command):
        errors.append(
            f"Command '{command}' not found. "
            f"Please install the package with 'pip install mcp-code-checker' "
            f"or 'pip install -e .' in development mode."
        )
    
    return errors
```

### 2. Update validate_server_configuration Function
Add CLI command validation to the main validation function:

```python
def validate_server_configuration(
    server_name: str,
    server_type: str,
    params: dict[str, Any],
    client_handler: ClientHandler | None = None,
) -> dict[str, Any]:
    """Comprehensive validation of server configuration.

    Args:
        server_name: Name of the server instance
        server_type: Type of server (e.g., 'mcp-code-checker')
        params: Server parameters to validate
        client_handler: Optional client handler for context

    Returns:
        Dictionary with validation results including success status and any errors
    """
    result = {
        "success": True,
        "server_name": server_name,
        "server_type": server_type,
        "checks": {},
        "errors": [],
        "warnings": [],
    }

    # Add CLI command check for mcp-code-checker
    if server_type == "mcp-code-checker":
        import shutil
        
        # Check if CLI command is available
        if shutil.which("mcp-code-checker"):
            result["checks"]["cli_command"] = {
                "status": "✓",
                "message": "CLI command 'mcp-code-checker' is available",
            }
            result["installation_mode"] = "cli_command"
        else:
            # Check if package is installed
            try:
                import mcp_code_checker
                result["checks"]["cli_command"] = {
                    "status": "⚠",
                    "message": "Package installed but CLI command not found. Run 'pip install -e .' to install command.",
                }
                result["warnings"].append(
                    "CLI command 'mcp-code-checker' not available. "
                    "Using Python module fallback."
                )
                result["installation_mode"] = "python_module"
            except ImportError:
                # Development mode - check for source files
                project_dir = Path(params.get("project_dir", "."))
                main_path = project_dir / "src" / "main.py"
                if main_path.exists():
                    result["checks"]["cli_command"] = {
                        "status": "ℹ",
                        "message": "Running in development mode (source files)",
                    }
                    result["installation_mode"] = "development"
                else:
                    result["checks"]["cli_command"] = {
                        "status": "✗",
                        "message": "MCP Code Checker not properly installed",
                    }
                    result["errors"].append(
                        "MCP Code Checker is not installed. "
                        "Please run 'pip install mcp-code-checker' or 'pip install -e .' in the project directory."
                    )
                    result["success"] = False
                    result["installation_mode"] = "not_installed"

    # Rest of validation continues...
    # Check project directory
    if "project_dir" in params:
        project_dir = Path(params["project_dir"])
        if project_dir.exists() and project_dir.is_dir():
            result["checks"]["project_dir"] = {
                "status": "✓",
                "message": f"Project directory exists: {project_dir}",
            }
        else:
            result["checks"]["project_dir"] = {
                "status": "✗",
                "message": f"Project directory not found: {project_dir}",
            }
            result["errors"].append(f"Project directory does not exist: {project_dir}")
            result["success"] = False
    
    # Continue with other validations...
    
    return result
```

### 3. Add Helper Message Function
Add a function to provide installation instructions:

```python
def get_installation_instructions(server_type: str, mode: str) -> str:
    """Get installation instructions based on server type and current mode.
    
    Args:
        server_type: Type of server
        mode: Current installation mode
        
    Returns:
        Helpful installation instructions
    """
    if server_type == "mcp-code-checker":
        if mode == "not_installed":
            return (
                "To install MCP Code Checker:\n"
                "  1. From PyPI: pip install mcp-code-checker\n"
                "  2. From source: git clone <repo> && cd mcp-code-checker && pip install -e .\n"
                "  3. Development: cd /path/to/mcp-code-checker && pip install -e ."
            )
        elif mode == "python_module":
            return (
                "CLI command not available. To enable it:\n"
                "  1. Reinstall: pip install --force-reinstall mcp-code-checker\n"
                "  2. Or in development: pip install -e .\n"
                "  3. Then verify: which mcp-code-checker (or 'where' on Windows)"
            )
        elif mode == "development":
            return (
                "Running in development mode. To install CLI command:\n"
                "  1. Navigate to project: cd /path/to/mcp-code-checker\n"
                "  2. Install in editable mode: pip install -e .\n"
                "  3. Verify: mcp-code-checker --help"
            )
    
    return "Please check the documentation for installation instructions."
```

### 4. Update Output Formatting
In `src/config/output.py`, add formatting for installation mode:

```python
@staticmethod
def print_validation_results(validation_result: dict[str, Any]) -> None:
    """Print validation results in a formatted way.
    
    Args:
        validation_result: Validation result dictionary
    """
    server_name = validation_result.get("server_name", "Unknown")
    server_type = validation_result.get("server_type", "Unknown")
    
    print(f"\n{'='*60}")
    print(f"Validation Results for '{server_name}' ({server_type})")
    print(f"{'='*60}\n")
    
    # Show installation mode if available
    if "installation_mode" in validation_result:
        mode = validation_result["installation_mode"]
        mode_display = {
            "cli_command": "✓ CLI Command",
            "python_module": "⚠ Python Module", 
            "development": "ℹ Development Mode",
            "not_installed": "✗ Not Installed"
        }.get(mode, mode)
        print(f"Installation Mode: {mode_display}\n")
    
    # Show checks
    if validation_result.get("checks"):
        print("Validation Checks:")
        for check_name, check_result in validation_result["checks"].items():
            status = check_result.get("status", "?")
            message = check_result.get("message", "")
            print(f"  {status} {check_name}: {message}")
        print()
    
    # Continue with errors and warnings...
```

## Testing Scenarios

### Test 1: CLI Command Installed
```bash
pip install -e .
mcp-config validate "test-server"
# Should show: "✓ CLI command 'mcp-code-checker' is available"
```

### Test 2: Package Without CLI
```python
# Simulate by temporarily removing command
mcp-config validate "test-server"
# Should show: "⚠ Package installed but CLI command not found"
```

### Test 3: Development Mode
```bash
# In fresh environment without installation
cd /path/to/mcp-code-checker
mcp-config validate "test-server" 
# Should show: "ℹ Running in development mode"
```

### Test 4: Not Installed
```bash
# In environment without package
mcp-config validate "test-server"
# Should show: "✗ MCP Code Checker not properly installed"
```

## Next Step
Proceed to Step 5 to update the integration module with the new validation.
