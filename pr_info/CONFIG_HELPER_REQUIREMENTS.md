# MCP Configuration Helper - Requirements for Code Checker

## Overview

A configuration tool that automates MCP server setup specifically for the MCP Code Checker, with support for extending to other MCP servers. Focus on solving the real user pain point: manual JSON configuration for Claude Desktop and other MCP clients.

## Core Problem

Users struggle with:
- Manual JSON editing with absolute paths for Claude Desktop configuration
- Cross-platform path issues (Windows/Mac/Linux)
- Complex Claude Desktop configuration syntax
- Remembering all available parameters for MCP Code Checker
- Setting up multiple instances of the same server for different projects

## Goals

1. **Automate MCP Code Checker configuration** - No more manual JSON editing
2. **Support multiple server instances** - Multiple projects, different configurations
3. **Support multiple clients** - Claude Desktop now, VS Code/others later
4. **Extensible design** - Support other MCP servers via plugin system
5. **Keep it practical** - Solve real configuration problems

## Architecture

### Package Structure
```
src/
├── config/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── servers.py           # Server registry and definitions
│   ├── clients.py           # Client handlers (Claude Desktop, others)
│   ├── discovery.py         # External server discovery via entry points
│   └── utils.py             # Path detection, JSON utils, validation
tests/
├── test_config/
│   ├── test_servers.py
│   ├── test_clients.py
│   ├── test_discovery.py
│   └── test_utils.py
```

### Server Definition - Complete Parameter Support

```python
@dataclass
class ParameterDef:
    name: str                   # CLI parameter name (e.g., "project-dir") 
    arg_name: str              # Server argument (e.g., "--project-dir")
    param_type: str            # "string", "boolean", "choice", "path"
    required: bool = False     # Whether required
    default: any = None        # Default value
    choices: list = None       # For choice parameters
    help: str = ""            # Help text for CLI
    is_flag: bool = False      # True for boolean flags (action="store_true")

@dataclass
class ServerConfig:
    name: str                    # "mcp-code-checker"
    display_name: str           # "MCP Code Checker"
    main_module: str            # "src/main.py"  
    parameters: list[ParameterDef]  # All possible parameters
    
    def generate_args(self, user_params: dict) -> list:
        """Generate command line args from user parameters."""
        args = [self.main_module]  # Always start with main module
        
        for param in self.parameters:
            value = user_params.get(param.name, param.default)
            if value is not None:
                if param.is_flag and value:
                    # For boolean flags, just add the flag if True
                    args.append(param.arg_name)
                elif not param.is_flag:
                    # For regular parameters, add name and value
                    args.extend([param.arg_name, str(value)])
        
        return args
    
    def get_required_params(self) -> list[str]:
        """Get list of required parameter names."""
        return [p.name for p in self.parameters if p.required]
    
    def validate_project(self, project_dir: Path) -> bool:
        """Check if project is compatible (server-specific logic)."""
        # For mcp-code-checker, check for src/main.py
        main_py = project_dir / "src" / "main.py"
        return main_py.exists()
    
    def get_parameter_by_name(self, name: str) -> Optional[ParameterDef]:
        """Get parameter definition by name."""
        return next((p for p in self.parameters if p.name == name), None)
```

### MCP Code Checker Server Definition - Complete Parameters

```python
# src/config/servers.py
class ServerRegistry:
    def __init__(self):
        self._servers = {}
    
    def register(self, config: ServerConfig):
        self._servers[config.name] = config
    
    def get(self, name: str) -> ServerConfig:
        return self._servers.get(name)
    
    def list_servers(self) -> list:
        return list(self._servers.keys())
    
    def get_all_configs(self) -> dict[str, ServerConfig]:
        return self._servers.copy()

# Built-in servers
registry = ServerRegistry()

# MCP Code Checker built-in config - COMPLETE PARAMETER SET
MCP_CODE_CHECKER = ServerConfig(
    name="mcp-code-checker",
    display_name="MCP Code Checker", 
    main_module="src/main.py",
    parameters=[
        # Required parameters
        ParameterDef(
            name="project-dir", 
            arg_name="--project-dir", 
            param_type="path",
            required=True, 
            help="Base directory for code checking operations (required)"
        ),
        
        # Python execution parameters
        ParameterDef(
            name="python-executable", 
            arg_name="--python-executable", 
            param_type="path",
            help="Path to Python interpreter to use for running tests. If not specified, defaults to the current Python interpreter (sys.executable)"
        ),
        ParameterDef(
            name="venv-path", 
            arg_name="--venv-path", 
            param_type="path",
            help="Path to virtual environment to activate for running tests. When specified, the Python executable from this venv will be used instead of python-executable"
        ),
        
        # Test configuration parameters
        ParameterDef(
            name="test-folder", 
            arg_name="--test-folder", 
            param_type="string",
            default="tests",
            help="Path to the test folder (relative to project_dir). Defaults to 'tests'"
        ),
        ParameterDef(
            name="keep-temp-files", 
            arg_name="--keep-temp-files", 
            param_type="boolean",
            is_flag=True,
            help="Keep temporary files after test execution. Useful for debugging when tests fail"
        ),
        
        # Logging parameters
        ParameterDef(
            name="log-level", 
            arg_name="--log-level", 
            param_type="choice",
            default="INFO",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="Set logging level (default: INFO)"
        ),
        ParameterDef(
            name="log-file", 
            arg_name="--log-file", 
            param_type="path",
            help="Path for structured JSON logs (default: mcp_code_checker_{timestamp}.log in project_dir/logs/)"
        ),
        ParameterDef(
            name="console-only", 
            arg_name="--console-only", 
            param_type="boolean",
            is_flag=True,
            help="Log only to console, ignore --log-file parameter"
        )
    ]
)
registry.register(MCP_CODE_CHECKER)
```

### Client Interface - Safe Config Management

```python
# src/config/clients.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

class ClientHandler(ABC):
    """Abstract base class for MCP client handlers."""
    
    @abstractmethod
    def get_config_path(self) -> Path:
        """Get the path to the client's configuration file."""
        pass
    
    @abstractmethod
    def setup_server(self, server_name: str, server_config: dict) -> bool:
        """Add server to client config - only touch our server entries."""
        pass
    
    @abstractmethod
    def remove_server(self, server_name: str) -> bool:
        """Remove server from client config - preserve all other servers."""
        pass
    
    @abstractmethod
    def list_managed_servers(self) -> list:
        """List only servers managed by this tool."""
        pass
    
    @abstractmethod
    def list_all_servers(self) -> list:
        """List all servers in config (managed + external)."""
        pass

class ClaudeDesktopHandler(ClientHandler):
    """Handler for Claude Desktop client configuration."""
    
    MANAGED_SERVER_MARKER = "mcp-config-managed"
    
    def get_config_path(self) -> Path:
        """Get Claude Desktop config file path."""
        import os
        if os.name == 'nt':  # Windows
            return Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json"
        elif os.name == 'posix':
            import platform
            if platform.system() == 'Darwin':  # macOS
                return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
            else:  # Linux
                return Path.home() / ".config/claude/claude_desktop_config.json"
        else:
            raise OSError(f"Unsupported operating system: {os.name}")
    
    def load_config(self) -> dict:
        """Load existing Claude Desktop configuration."""
        import json
        config_path = self.get_config_path()
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {"mcpServers": {}}
    
    def save_config(self, config: dict) -> None:
        """Save Claude Desktop configuration."""
        import json
        config_path = self.get_config_path()
        
        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save with proper formatting
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def setup_server(self, server_name: str, server_config: dict) -> bool:
        """
        Safely update Claude Desktop config:
        1. Load existing config 
        2. Preserve ALL other servers (filesystem, calculator, etc.)
        3. Only add/update our specific server entry
        4. Mark our entries for identification
        """
        config = self.load_config()
        
        # Ensure mcpServers section exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # Add marker to identify our managed servers
        server_config["_managed_by"] = self.MANAGED_SERVER_MARKER
        
        # Only update our server, preserve everything else
        config["mcpServers"][server_name] = server_config
        
        self.save_config(config)
        return True
    
    def remove_server(self, server_name: str) -> bool:
        """Remove only if it's managed by us."""
        config = self.load_config()
        
        server = config.get("mcpServers", {}).get(server_name)
        if server and server.get("_managed_by") == self.MANAGED_SERVER_MARKER:
            del config["mcpServers"][server_name]
            self.save_config(config)
            return True
        elif server:
            raise ValueError(f"Server '{server_name}' is not managed by mcp-config (cannot remove external servers)")
        else:
            raise ValueError(f"Server '{server_name}' not found in configuration")
    
    def list_managed_servers(self) -> list:
        """List only servers we manage."""
        config = self.load_config()
        managed = []
        
        for name, server_config in config.get("mcpServers", {}).items():
            if server_config.get("_managed_by") == self.MANAGED_SERVER_MARKER:
                managed.append({
                    "name": name,
                    "type": server_config.get("_server_type", "mcp-code-checker"),
                    "managed": True,
                    "command": server_config.get("command"),
                    "args": server_config.get("args", [])
                })
        
        return managed
    
    def list_all_servers(self) -> list:
        """List all servers, mark which ones we manage."""
        config = self.load_config()
        all_servers = []
        
        for name, server_config in config.get("mcpServers", {}).items():
            is_managed = server_config.get("_managed_by") == self.MANAGED_SERVER_MARKER
            all_servers.append({
                "name": name,
                "type": server_config.get("_server_type", "external" if not is_managed else "mcp-code-checker"),
                "managed": is_managed,
                "command": server_config.get("command"),
                "args": server_config.get("args", [])
            })
        
        return all_servers
    
    def backup_config(self) -> Path:
        """Create a backup of the current configuration."""
        import shutil
        from datetime import datetime
        
        config_path = self.get_config_path()
        if not config_path.exists():
            raise FileNotFoundError(f"No configuration file to backup: {config_path}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = config_path.with_suffix(f".backup_{timestamp}.json")
        
        shutil.copy2(config_path, backup_path)
        return backup_path

# Client registry
CLIENT_HANDLERS = {
    "claude-desktop": ClaudeDesktopHandler,
    # Future clients can be added here
    # "vscode": VSCodeHandler,
    # "cursor": CursorHandler,
}

def get_client_handler(client_name: str) -> ClientHandler:
    """Get client handler by name."""
    if client_name not in CLIENT_HANDLERS:
        raise ValueError(f"Unknown client: {client_name}. Available: {list(CLIENT_HANDLERS.keys())}")
    
    return CLIENT_HANDLERS[client_name]()
```

## CLI Design - Complete Parameter Support

### Command Structure
```
mcp-config <command> [arguments] [options]
```

### Commands

#### setup
```bash
mcp-config setup <server-type> <server-name> [options]
```

**Required:**
- `<server-type>`: Server type (currently only `mcp-code-checker` supported)
- `<server-name>`: User-provided name for this server instance

**Global Options:**
- `--client <name>`: MCP client to configure (default: `claude-desktop`)
- `--dry-run`: Preview changes without applying them
- `--verbose`: Show detailed output
- `--backup`: Create backup before making changes (default: true)

**MCP Code Checker Specific Options:**
- `--project-dir <path>`: Base directory for code checking operations (**required**)
- `--python-executable <path>`: Path to Python interpreter to use for running tests (auto-detected if not specified)
- `--venv-path <path>`: Path to virtual environment to activate for running tests (auto-detected if not specified)
- `--test-folder <path>`: Path to the test folder (relative to project_dir). Defaults to 'tests'
- `--keep-temp-files`: Keep temporary files after test execution (flag)
- `--log-level <level>`: Set logging level - choices: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- `--log-file <path>`: Path for structured JSON logs (default: auto-generated in project_dir/logs/)
- `--console-only`: Log only to console, ignore --log-file parameter (flag)

#### remove
```bash
mcp-config remove <server-name> [options]
```

**Required:**
- `<server-name>`: Name of server to remove

**Options:**
- `--client <name>`: MCP client to modify (default: `claude-desktop`)
- `--dry-run`: Preview changes without applying them
- `--verbose`: Show detailed output
- `--backup`: Create backup before making changes (default: true)

#### list
```bash
mcp-config list [options]
```

**Options:**
- `--client <name>`: Show servers for specific client (default: all clients)
- `--type <server-type>`: Filter by server type
- `--managed-only`: Show only servers managed by this tool
- `--detailed`: Show full configuration details including all parameters

#### list-server-types
```bash
mcp-config list-server-types
```
Shows all available server types (built-in + discovered from other packages)

#### validate
```bash
mcp-config validate <server-name> [--client <name>]
```
Validate that a configured server can actually run (check paths, permissions, etc.)

#### backup
```bash
mcp-config backup [--client <name>]
```
Create a backup of client configuration files

### Usage Examples

```bash
# Basic setup with minimal options (auto-detects Python executable)
mcp-config setup mcp-code-checker "my-checker" --project-dir .

# Setup with all custom parameters
mcp-config setup mcp-code-checker "debug-checker" \
  --project-dir . \
  --python-executable /usr/bin/python3.11 \
  --venv-path ./.venv \
  --test-folder custom-tests \
  --log-level DEBUG \
  --keep-temp-files \
  --log-file ./custom-logs/checker.log

# Setup without file logging
mcp-config setup mcp-code-checker "console-checker" \
  --project-dir . --console-only

# Setup for different client (future)
mcp-config setup mcp-code-checker "vscode-checker" \
  --client vscode --project-dir .

# Dry run to preview changes
mcp-config setup mcp-code-checker "test-name" --project-dir . --dry-run

# Remove server with backup
mcp-config remove "my-checker" --backup

# Remove with dry run (no backup needed)
mcp-config remove "my-checker" --dry-run

# List all servers (managed + external)
mcp-config list --detailed

# List only managed servers
mcp-config list --managed-only

# Output example:
# Managed Servers for claude-desktop:
# ├── my-checker (mcp-code-checker)
# │   ├── Project: /home/user/myproject
# │   ├── Python: /home/user/myproject/.venv/bin/python
# │   ├── Test Folder: tests
# │   └── Log Level: INFO
# ├── debug-checker (mcp-code-checker)
# │   ├── Project: /home/user/myproject
# │   ├── Python: /usr/bin/python3.11
# │   ├── Test Folder: custom-tests
# │   ├── Log Level: DEBUG
# │   ├── Keep Temp Files: Yes
# │   └── Custom Log File: ./custom-logs/checker.log
# 
# External Servers:
# ├── calculator (external) - not managed by mcp-config
# └── weather-api (external) - not managed by mcp-config

# Validate server configuration
mcp-config validate "my-checker"
# Output: ✓ Server 'my-checker' configuration is valid
#         ✓ Project directory exists: /home/user/myproject
#         ✓ Python executable found: /home/user/myproject/.venv/bin/python
#         ✓ Main module exists: /home/user/myproject/src/main.py
#         ✓ Test folder exists: /home/user/myproject/tests

# List available server types
mcp-config list-server-types
# Output: Available server types:
#         ├── mcp-code-checker (built-in) - MCP Code Checker
#         ├── mcp-filesystem (external) - MCP Filesystem
#         └── mcp-database (external) - MCP Database

# Create backup
mcp-config backup --client claude-desktop
# Output: Backup created: ~/.config/claude/claude_desktop_config.backup_20241201_143022.json
```

### Entry Point
```toml
[project.scripts]
mcp-config = "src.config.main:main"
```

## External Server Support

### Import from Other Packages
```python
# src/config/discovery.py
import pkg_resources
from typing import Dict, List
from .servers import ServerConfig, registry

def discover_external_servers() -> Dict[str, ServerConfig]:
    """Discover external MCP server configurations via entry points."""
    discovered = {}
    
    try:
        for entry_point in pkg_resources.iter_entry_points('mcp.server_configs'):
            try:
                config = entry_point.load()
                if isinstance(config, ServerConfig):
                    discovered[config.name] = config
                    registry.register(config)
                    print(f"Discovered external server: {config.display_name}")
                else:
                    print(f"Invalid server config from {entry_point.name}: not a ServerConfig instance")
            except Exception as e:
                print(f"Failed to load server config from {entry_point.name}: {e}")
    except Exception as e:
        print(f"Failed to discover external servers: {e}")
    
    return discovered

# Auto-discovery on startup
def initialize_servers():
    """Initialize built-in and external servers."""
    # Built-in servers are already registered in servers.py
    external_servers = discover_external_servers()
    return registry.get_all_configs()
```

### Example External Server Entry Point Configuration
```python
# In other MCP packages' setup.py/pyproject.toml:
[project.entry-points."mcp.server_configs"]
filesystem = "mcp_filesystem.config:FILESYSTEM_CONFIG"
database = "mcp_database.config:DATABASE_CONFIG"
```

### Example External Server Config
```python
# In mcp-filesystem package
from mcp_config.servers import ServerConfig, ParameterDef

FILESYSTEM_CONFIG = ServerConfig(
    name="mcp-filesystem",
    display_name="MCP Filesystem",
    main_module="src/main.py", 
    parameters=[
        ParameterDef(
            name="root-dir", 
            arg_name="--root-dir", 
            param_type="path",
            required=True,
            help="Root directory for filesystem access"
        ),
        ParameterDef(
            name="read-only", 
            arg_name="--read-only", 
            param_type="boolean",
            is_flag=True,
            help="Enable read-only mode"
        ),
        ParameterDef(
            name="max-file-size", 
            arg_name="--max-file-size", 
            param_type="string",
            default="10MB",
            help="Maximum file size to read"
        ),
        ParameterDef(
            name="ignore-patterns", 
            arg_name="--ignore-patterns", 
            param_type="string",
            help="Comma-separated glob patterns to ignore"
        )
    ]
)

# Usage would be:
# mcp-config setup mcp-filesystem "docs-fs" --root-dir ./docs --read-only
```

### Dynamic CLI Parameter Generation

The CLI automatically generates server-specific options based on server definitions:

```python
# src/config/main.py
def build_setup_parser(server_config: ServerConfig) -> argparse.ArgumentParser:
    """Build setup command parser with server-specific parameters."""
    parser = argparse.ArgumentParser(
        description=f"Setup {server_config.display_name}",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add positional arguments
    parser.add_argument('server_type', help='Server type')
    parser.add_argument('server_name', help='Server instance name')
    
    # Add global options
    parser.add_argument('--client', default='claude-desktop', 
                       choices=['claude-desktop'], help='MCP client to configure')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without applying them')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed output')
    parser.add_argument('--backup', action='store_true', default=True,
                       help='Create backup before making changes')
    
    # Add server-specific options dynamically
    for param in server_config.parameters:
        option_name = f'--{param.name}'
        
        if param.param_type == "boolean" and param.is_flag:
            parser.add_argument(option_name, action='store_true', 
                              help=param.help, required=param.required)
        elif param.param_type == "choice":
            parser.add_argument(option_name, choices=param.choices,
                              default=param.default, help=param.help,
                              required=param.required)
        else:
            parser.add_argument(option_name, default=param.default,
                              help=param.help, required=param.required,
                              type=str if param.param_type != "path" else Path)
    
    return parser
```

This means:
- **mcp-code-checker** gets `--project-dir`, `--python-executable`, `--venv-path`, `--test-folder`, `--keep-temp-files`, `--log-level`, `--log-file`, `--console-only`
- **mcp-filesystem** gets `--root-dir`, `--read-only`, `--max-file-size`, `--ignore-patterns`
- **mcp-database** could get `--connection-string`, `--schema`, `--read-only`, etc.

Each server defines its own complete parameter set with proper types and validation!

## Auto-Detection and Smart Defaults

### Path Auto-Detection
```python
# src/config/utils.py
import sys
import os
from pathlib import Path
from typing import Optional, Tuple

def detect_python_environment(project_dir: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    Auto-detect Python executable and virtual environment.
    
    Returns:
        Tuple of (python_executable, venv_path)
    """
    # Check for common venv patterns in project directory
    venv_candidates = [
        project_dir / ".venv",
        project_dir / "venv", 
        project_dir / ".virtualenv",
        project_dir / "env"
    ]
    
    for venv_path in venv_candidates:
        if venv_path.exists() and venv_path.is_dir():
            # Check for Python executable in venv
            if os.name == 'nt':  # Windows
                python_exe = venv_path / "Scripts" / "python.exe"
            else:  # Unix-like
                python_exe = venv_path / "bin" / "python"
            
            if python_exe.exists():
                return str(python_exe), str(venv_path)
    
    # Fall back to current Python executable
    return sys.executable, None

def validate_project_structure(project_dir: Path, server_config: ServerConfig) -> list[str]:
    """
    Validate project structure for compatibility with server.
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if not project_dir.exists():
        errors.append(f"Project directory does not exist: {project_dir}")
        return errors
    
    if not project_dir.is_dir():
        errors.append(f"Project path is not a directory: {project_dir}")
        return errors
    
    # Server-specific validation
    if server_config.name == "mcp-code-checker":
        main_py = project_dir / "src" / "main.py"
        if not main_py.exists():
            errors.append(f"MCP Code Checker main module not found: {main_py}")
        
        # Check for typical Python project structure
        src_dir = project_dir / "src"
        if not src_dir.exists():
            errors.append(f"Source directory not found: {src_dir}")
    
    return errors

def normalize_paths(config: dict, project_dir: Path) -> dict:
    """
    Normalize all paths in configuration to absolute paths.
    """
    normalized = config.copy()
    
    # Convert relative paths to absolute
    path_keys = ['command', 'project_dir', 'python_executable', 'venv_path', 'log_file']
    
    for key, value in normalized.items():
        if key in path_keys and value:
            path = Path(value)
            if not path.is_absolute():
                normalized[key] = str((project_dir / path).absolute())
            else:
                normalized[key] = str(path.absolute())
        elif key == 'args' and isinstance(value, list):
            # Normalize paths in arguments list
            normalized_args = []
            for arg in value:
                if arg.startswith(('/', './', '../')) or (os.name == 'nt' and ':' in arg):
                    # Looks like a path
                    path = Path(arg)
                    if not path.is_absolute():
                        normalized_args.append(str((project_dir / path).absolute()))
                    else:
                        normalized_args.append(str(path.absolute()))
                else:
                    normalized_args.append(arg)
            normalized[key] = normalized_args
    
    return normalized
```

## Implementation Plan

### Phase 1: Core Functionality (1 week)
1. **Server Registry & Configuration**
   - Complete ServerConfig with all MCP Code Checker parameters
   - ParameterDef with proper type system
   - Registry with built-in MCP Code Checker config

2. **Claude Desktop Client Handler**
   - Complete ClaudeDesktopHandler implementation
   - Config loading/saving with proper encoding
   - Backup functionality
   - Safe server management (managed vs external)

3. **Basic CLI Commands**
   - `setup` command with dynamic parameter generation
   - `remove` command with safety checks
   - `list` command with detailed output
   - Dry run support for all commands

4. **Path Auto-Detection**
   - Python executable detection
   - Virtual environment detection  
   - Project validation utilities

### Phase 2: Enhanced Functionality (1 week)
1. **External Server Discovery**
   - Entry point discovery system
   - Dynamic server registration
   - Error handling for invalid external servers

2. **Advanced CLI Features**
   - `validate` command for configuration checking
   - `backup` command for manual backups
   - `list-server-types` command
   - Verbose output modes

3. **Smart Defaults & Validation**
   - Complete parameter validation
   - Path normalization
   - Environment-specific defaults
   - Better error messages

### Phase 3: Polish & Documentation (3 days)
1. **Cross-Platform Testing**
   - Windows path handling
   - macOS config paths
   - Linux compatibility

2. **Documentation & Examples**
   - Complete usage examples
   - Troubleshooting guide
   - Integration examples

## Success Criteria

1. **Core Functionality**
   - `mcp-config setup mcp-code-checker "my-checker" --project-dir .` works with auto-detection
   - All 8 MCP Code Checker parameters are properly supported
   - `mcp-config remove "my-checker"` works safely (only removes managed servers)
   - Cross-platform path handling works correctly

2. **Safety & Reliability**
   - External servers in Claude config are never modified
   - Automatic backups before any changes
   - Clear distinction between managed and external servers
   - Validation prevents invalid configurations

3. **Extensibility**
   - External packages can register their server configs via entry points
   - Adding a new client takes <1 day of work
   - New parameters can be added to existing servers easily

4. **User Experience**
   - Auto-detection reduces required parameters to minimum
   - Clear error messages with actionable suggestions
   - Dry run mode for safe testing
   - Detailed listing shows all configuration details

## Configuration Output Format

### Generated Claude Desktop Configuration
```json
{
  "mcpServers": {
    "my-checker": {
      "command": "/home/user/myproject/.venv/bin/python",
      "args": [
        "/home/user/myproject/src/main.py",
        "--project-dir",
        "/home/user/myproject",
        "--test-folder", 
        "tests",
        "--log-level",
        "INFO"
      ],
      "env": {
        "PYTHONPATH": "/home/user/myproject"
      },
      "_managed_by": "mcp-config-managed",
      "_server_type": "mcp-code-checker"
    },
    "debug-checker": {
      "command": "/usr/bin/python3.11",
      "args": [
        "/home/user/myproject/src/main.py",
        "--project-dir",
        "/home/user/myproject", 
        "--python-executable",
        "/usr/bin/python3.11",
        "--venv-path",
        "/home/user/myproject/.venv",
        "--test-folder",
        "custom-tests",
        "--keep-temp-files",
        "--log-level",
        "DEBUG",
        "--log-file",
        "/home/user/myproject/custom-logs/checker.log"
      ],
      "env": {
        "PYTHONPATH": "/home/user/myproject"
      },
      "_managed_by": "mcp-config-managed",
      "_server_type": "mcp-code-checker"
    }
  }
}
```

The configuration tool generates complete, valid Claude Desktop configurations with all parameters properly formatted and paths normalized for the target platform.
