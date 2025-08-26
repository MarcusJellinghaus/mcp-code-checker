# Step 3: Integration and Path Handling

## Objective
Update the integration layer to properly handle VSCode-specific requirements, including proper Python module invocation and path handling.

## Background
VSCode MCP expects servers to be invoked as Python modules when possible (e.g., `python -m mcp_code_checker`) rather than direct script paths. This ensures better compatibility and module resolution.

## Requirements

### 1. Update Integration Logic
Modify `src/config/integration.py` to:
- Handle VSCode-specific command generation
- Use module invocation for installed packages
- Fall back to script paths for local development

### 2. Path Normalization
Ensure paths work correctly for:
- Workspace configurations (relative paths preferred)
- User profile configurations (absolute paths required)
- Cross-platform compatibility

### 3. Server Detection
Improve detection of whether MCP Code Checker is installed as a package or running from source.

## Implementation

### In `src/config/integration.py`:

```python
from pathlib import Path
from typing import Any
import sys
import importlib.util

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

def generate_vscode_command(
    server_type: str,
    server_config: dict[str, Any],
    workspace: bool = True
) -> dict[str, Any]:
    """Generate VSCode-compatible server configuration.
    
    Args:
        server_type: Type of server (e.g., "mcp-code-checker")
        server_config: Raw server configuration
        workspace: Whether this is for workspace config
    
    Returns:
        VSCode-formatted server configuration
    """
    config = {}
    
    # Determine if we should use module invocation
    if server_type == "mcp-code-checker":
        if is_package_installed("mcp_code_checker"):
            # Installed as package - use module invocation
            config["command"] = sys.executable
            config["args"] = ["-m", "mcp_code_checker"] + server_config.get("args", [])[1:]
        else:
            # Running from source - use direct path
            config["command"] = server_config.get("command", sys.executable)
            config["args"] = server_config.get("args", [])
    else:
        # Other server types - use as-is
        config["command"] = server_config.get("command")
        config["args"] = server_config.get("args", [])
    
    # Handle environment variables
    if "env" in server_config and server_config["env"]:
        config["env"] = server_config["env"]
    
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
    
    # Check if command is a path and make relative if possible
    if "command" in updated:
        try:
            command_path = Path(updated["command"])
            if command_path.is_absolute():
                try:
                    rel_path = command_path.relative_to(base_path)
                    if not str(rel_path).startswith(".."):
                        updated["command"] = str(rel_path)
                except ValueError:
                    pass  # Keep absolute if not relative to base
        except (ValueError, OSError):
            pass  # Not a path, keep as-is
    
    # Process arguments
    if "args" in updated:
        updated_args = []
        skip_next = False
        
        for i, arg in enumerate(updated["args"]):
            if skip_next:
                skip_next = False
                updated_args.append(arg)
                continue
            
            # Check for path-related arguments
            if arg in ["--project-dir", "--python-executable", "--venv-path", "--log-file"]:
                skip_next = True
                updated_args.append(arg)
                if i + 1 < len(updated["args"]):
                    path_value = updated["args"][i + 1]
                    try:
                        path_obj = Path(path_value)
                        if path_obj.is_absolute():
                            try:
                                rel_path = path_obj.relative_to(base_path)
                                if not str(rel_path).startswith(".."):
                                    # Skip the original and add relative version
                                    continue
                            except ValueError:
                                pass
                    except (ValueError, OSError):
                        pass
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
    
    # Make command absolute if it's a relative path
    if "command" in updated:
        try:
            command_path = Path(updated["command"])
            if not command_path.is_absolute():
                updated["command"] = str(command_path.resolve())
        except (ValueError, OSError):
            pass  # Not a path or system command
    
    # Process arguments
    if "args" in updated:
        updated_args = []
        skip_next = False
        
        for i, arg in enumerate(updated["args"]):
            if skip_next:
                skip_next = False
                updated_args.append(arg)
                continue
            
            # Check for path-related arguments
            if arg in ["--project-dir", "--python-executable", "--venv-path", "--log-file"]:
                skip_next = True
                updated_args.append(arg)
                if i + 1 < len(updated["args"]):
                    path_value = updated["args"][i + 1]
                    try:
                        path_obj = Path(path_value)
                        if not path_obj.is_absolute():
                            updated_args.append(str(path_obj.resolve()))
                            skip_next = False
                            continue
                    except (ValueError, OSError):
                        pass
            else:
                updated_args.append(arg)
        
        updated["args"] = updated_args
    
    return updated

def setup_server(
    handler: Any,
    server_type: str,
    server_name: str,
    project_dir: Path,
    dry_run: bool = False,
    **params: Any
) -> bool:
    """Setup a server with the given handler.
    
    Args:
        handler: Client handler instance
        server_type: Type of server
        server_name: Name for this server instance
        project_dir: Project directory
        dry_run: Preview mode
        **params: Additional parameters
    
    Returns:
        True if successful
    """
    from src.config.servers import registry
    
    # Get server configuration
    server_config = registry.get(server_type)
    if not server_config:
        print(f"Unknown server type: {server_type}")
        return False
    
    # Generate base configuration
    base_config = {
        "command": sys.executable,
        "args": server_config.generate_args({"project_dir": str(project_dir), **params}),
        "_server_type": server_type
    }
    
    # Add environment if needed
    env = {}
    if project_dir:
        env["PYTHONPATH"] = str(project_dir)
    if env:
        base_config["env"] = env
    
    # Special handling for VSCode
    handler_class = handler.__class__.__name__
    if handler_class == "VSCodeHandler":
        # Determine if workspace or user config
        workspace = getattr(handler, "workspace", True)
        final_config = generate_vscode_command(server_type, base_config, workspace)
    else:
        final_config = base_config
    
    if dry_run:
        import json
        print(f"Would create configuration for '{server_name}':")
        print(json.dumps(final_config, indent=2))
        return True
    
    return handler.setup_server(server_name, final_config)
```

### Update `src/config/utils.py`:

```python
def detect_mcp_installation(project_dir: Path) -> dict[str, Any]:
    """Detect MCP Code Checker installation details.
    
    Args:
        project_dir: Project directory to check
    
    Returns:
        Dictionary with installation information
    """
    info = {
        "installed_as_package": False,
        "source_path": None,
        "module_name": None,
        "version": None
    }
    
    # Check if installed as package
    try:
        import mcp_code_checker
        info["installed_as_package"] = True
        info["module_name"] = "mcp_code_checker"
        
        # Try to get version
        if hasattr(mcp_code_checker, "__version__"):
            info["version"] = mcp_code_checker.__version__
    except ImportError:
        pass
    
    # Check for source installation
    main_py = project_dir / "src" / "main.py"
    if main_py.exists():
        info["source_path"] = str(main_py)
        
        # Check if this looks like MCP Code Checker
        try:
            with open(main_py, "r") as f:
                content = f.read(1000)  # Read first 1000 chars
                if "mcp" in content.lower() and "code" in content.lower():
                    info["likely_mcp_code_checker"] = True
        except:
            pass
    
    return info

def recommend_command_format(
    client: str,
    server_type: str,
    installation_info: dict[str, Any]
) -> str:
    """Recommend the best command format for the given client and server.
    
    Args:
        client: Client type (vscode, claude-desktop, etc.)
        server_type: Server type
        installation_info: Installation detection results
    
    Returns:
        Recommended command format description
    """
    if client.startswith("vscode"):
        if installation_info.get("installed_as_package"):
            return "Module invocation (python -m mcp_code_checker)"
        else:
            return "Direct script execution (python src/main.py)"
    elif client == "claude-desktop":
        return "Direct script execution with full paths"
    
    return "Default command format"
```

## Testing Checklist
- [ ] Test package detection for installed MCP Code Checker
- [ ] Test source detection for development setup
- [ ] Test module invocation format for VSCode
- [ ] Test relative paths in workspace config
- [ ] Test absolute paths in user profile config
- [ ] Test path normalization on Windows/Mac/Linux
- [ ] Test dry-run shows correct VSCode format

## Success Criteria
- VSCode configs use `python -m` format when package is installed
- Workspace configs use relative paths where possible
- User configs use absolute paths
- Path handling works cross-platform
- Backward compatibility maintained for Claude Desktop