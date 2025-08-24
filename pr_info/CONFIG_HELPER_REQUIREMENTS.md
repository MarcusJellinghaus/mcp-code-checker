# MCP Configuration Helper - Simplified Requirements

## Overview

A simple configuration tool that automates MCP server setup for different clients (starting with Claude Desktop). Focus on solving the real user pain point: manual JSON configuration.

## Core Problem

Users struggle with:
- Manual JSON editing with absolute paths
- Cross-platform path issues (Windows/Mac/Linux)
- Complex Claude Desktop configuration syntax

## Goals

1. **Automate MCP server configuration** - No more manual JSON editing
2. **Support multiple servers** - Import server configs from other packages
3. **Support multiple clients** - Claude Desktop now, others later
4. **Keep it simple** - Minimal complexity, maximum utility

## Architecture - Simplified

### Package Structure
```
src/
├── config/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── servers.py           # Server registry (simple dict)
│   ├── clients.py           # Client handlers (Claude Desktop, others)
│   └── utils.py             # Path detection, JSON utils
tests/
├── test_config/
│   ├── test_servers.py
│   ├── test_clients.py
│   └── test_utils.py
```

### Server Definition - Flexible Parameters

```python
@dataclass
class ParameterDef:
    name: str                   # CLI parameter name (e.g., "project-dir") 
    arg_name: str              # Server argument (e.g., "--project-dir")
    required: bool = False     # Whether required
    default: any = None        # Default value
    help: str = ""            # Help text for CLI

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
                args.extend([param.arg_name, str(value)])
        
        return args
    
    def get_required_params(self) -> list[str]:
        """Get list of required parameter names."""
        return [p.name for p in self.parameters if p.required]
    
    def validate_project(self, project_dir: Path) -> bool:
        """Check if project is compatible (server-specific logic)."""
        pass
```

### Server Registry - Simple Dict

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

# Built-in servers
registry = ServerRegistry()

# MCP Code Checker built-in config
MCP_CODE_CHECKER = ServerConfig(
    name="mcp-code-checker",
    display_name="MCP Code Checker", 
    main_module="src/main.py",
    parameters=[
        ParameterDef("project-dir", "--project-dir", required=True, 
                    help="Target project directory for code checking"),
        ParameterDef("python-exe", "--python-executable", 
                    help="Python executable path (auto-detected)"),
        ParameterDef("venv-path", "--venv-path", 
                    help="Virtual environment path (auto-detected)"),
        ParameterDef("log-level", "--log-level", default="INFO",
                    help="Logging level"),
        ParameterDef("test-folder", "--test-folder", default="tests",
                    help="Test directory path"),
        ParameterDef("log-file", "--log-file",
                    help="Custom log file path"),
        ParameterDef("console-only", "--console-only", 
                    help="Disable file logging (flag)"),
        ParameterDef("keep-temp-files", "--keep-temp-files",
                    help="Preserve temporary files for debugging (flag)")
    ]
)
registry.register(MCP_CODE_CHECKER)
```

### Client Interface - Safe Config Management

```python
# src/config/clients.py
class ClientHandler:
    def setup_server(self, server_name: str, server_config: dict) -> bool:
        """Add server to client config - only touch our server entries."""
        pass
    
    def remove_server(self, server_name: str) -> bool:
        """Remove server from client config - preserve all other servers."""
        pass
    
    def list_managed_servers(self) -> list:
        """List only servers managed by this tool."""
        pass
    
    def list_all_servers(self) -> list:
        """List all servers in config (managed + external)."""
        pass

class ClaudeDesktopHandler(ClientHandler):
    MANAGED_SERVER_MARKER = "# Managed by mcp-config"
    
    def setup_server(self, server_name: str, server_config: dict) -> bool:
        """
        Safely update Claude Desktop config:
        1. Load existing config 
        2. Preserve ALL other servers (filesystem, calculator, etc.)
        3. Only add/update our specific server entry
        4. Mark our entries for identification
        """
        config = self.load_config()
        
        # Add marker to identify our managed servers
        server_config["_managed_by"] = "mcp-config"
        
        # Only update our server, preserve everything else
        config["mcpServers"][server_name] = server_config
        
        self.save_config(config)
    
    def remove_server(self, server_name: str) -> bool:
        """Remove only if it's managed by us."""
        config = self.load_config()
        
        server = config.get("mcpServers", {}).get(server_name)
        if server and server.get("_managed_by") == "mcp-config":
            del config["mcpServers"][server_name]
            self.save_config(config)
            return True
        else:
            raise ValueError(f"Server '{server_name}' not managed by mcp-config")
    
    def list_managed_servers(self) -> list:
        """List only servers we manage."""
        config = self.load_config()
        managed = []
        
        for name, server_config in config.get("mcpServers", {}).items():
            if server_config.get("_managed_by") == "mcp-config":
                managed.append({
                    "name": name,
                    "type": server_config.get("_server_type", "unknown"),
                    "managed": True
                })
        
        return managed
    
    def list_all_servers(self) -> list:
        """List all servers, mark which ones we manage."""
        config = self.load_config()
        all_servers = []
        
        for name, server_config in config.get("mcpServers", {}).items():
            is_managed = server_config.get("_managed_by") == "mcp-config"
            all_servers.append({
                "name": name,
                "type": server_config.get("_server_type", "external"),
                "managed": is_managed
            })
        
        return all_servers
```

## CLI Design - Simplified

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
- `<server-type>`: Server type (e.g., `mcp-code-checker`)
- `<server-name>`: User-provided name for this server instance

**Global Options:**
- `--client <n>`: MCP client to configure (default: `claude-desktop`)
- `--dry-run`: Preview changes without applying them
- `--verbose`: Show detailed output

**Server-Specific Options:**
- `--project-dir <path>`: Target project directory (required for mcp-code-checker)
- `--python-exe <path>`: Python executable (auto-detected if not specified)
- `--venv-path <path>`: Virtual environment path (auto-detected if not specified)
- `--log-level <level>`: Logging level (default: INFO)
- `--test-folder <path>`: Test directory (default: tests)
- `--log-file <path>`: Custom log file path (optional)
- `--console-only`: Disable file logging
- `--keep-temp-files`: Preserve temporary files for debugging

#### remove
```bash
mcp-config remove <server-name> [options]
```

**Required:**
- `<server-name>`: Name of server to remove

**Options:**
- `--client <n>`: MCP client to modify (default: `claude-desktop`)
- `--dry-run`: Preview changes without applying them
- `--verbose`: Show detailed output

#### list
```bash
mcp-config list [options]
```

**Options:**
- `--client <n>`: Show servers for specific client (default: all clients)
- `--type <server-type>`: Filter by server type
- `--detailed`: Show full configuration details

#### list-server-types
```bash
mcp-config list-server-types
```
Shows all available server types (built-in + discovered from other packages)

### Usage Examples

```bash
# Basic setup with minimal options
mcp-config setup mcp-code-checker "my-checker" --project-dir .

# Setup with custom parameters
mcp-config setup mcp-code-checker "debug-checker" \
  --project-dir . --log-level DEBUG --test-folder custom-tests

# Setup for different client (future)
mcp-config setup mcp-code-checker "vscode-checker" \
  --client vscode --project-dir .

# Dry run to preview
mcp-config setup mcp-code-checker "test-name" --project-dir . --dry-run

# Remove server
mcp-config remove "my-checker"

# Remove with dry run
mcp-config remove "my-checker" --dry-run

# List all servers (managed + external)
mcp-config list --all

# List only servers managed by this tool
mcp-config list

# Output example:
# Managed Servers:
# my-checker (mcp-code-checker) [claude-desktop] ✓
# docs-fs (mcp-filesystem) [claude-desktop] ✓
# 
# External Servers: 
# calculator [claude-desktop] (not managed)
# weather-api [claude-desktop] (not managed)

# List available server types
mcp-config list-server-types
```

### Entry Point
```toml
[project.scripts]
mcp-config = "src.config.main:main"
```

## External Server Support

### Import from Other Packages
```python
# Other MCP packages can provide their config
# In their setup.py/pyproject.toml:
[project.entry-points."mcp.server_configs"]
filesystem = "mcp_filesystem.config:FILESYSTEM_CONFIG"
database = "mcp_database.config:DATABASE_CONFIG"

# Auto-discovery on startup
def discover_servers():
    for entry_point in pkg_resources.iter_entry_points('mcp.server_configs'):
        config = entry_point.load()
        registry.register(config)
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
        ParameterDef("root-dir", "--root-dir", required=True,
                    help="Root directory for filesystem access"),
        ParameterDef("read-only", "--read-only", 
                    help="Enable read-only mode (flag)"),
        ParameterDef("max-file-size", "--max-file-size", default="10MB",
                    help="Maximum file size to read"),
        ParameterDef("ignore-patterns", "--ignore-patterns", 
                    help="Comma-separated glob patterns to ignore")
    ]
)

# Usage would be:
# mcp-config setup mcp-filesystem "docs-fs" --root-dir ./docs --read-only
```

### Dynamic CLI Parameter Generation

The CLI automatically generates server-specific options based on server definitions:

```python
# CLI dynamically adds parameters based on server config
def build_setup_parser(server_config: ServerConfig):
    parser = argparse.ArgumentParser()
    
    # Add global options
    parser.add_argument('--client', default='claude-desktop')
    parser.add_argument('--dry-run', action='store_true')
    
    # Add server-specific options dynamically
    for param in server_config.parameters:
        if param.help.endswith("(flag)"):
            parser.add_argument(f'--{param.name}', action='store_true', 
                              help=param.help)
        else:
            parser.add_argument(f'--{param.name}', default=param.default,
                              help=param.help, required=param.required)
    
    return parser
```

This means:
- **mcp-code-checker** gets `--project-dir`, `--log-level`, `--test-folder`, etc.
- **mcp-filesystem** gets `--root-dir`, `--read-only`, `--max-file-size`, etc.  
- **mcp-database** could get `--connection-string`, `--schema`, etc.

Each server defines its own parameters!

## Implementation Plan

### Phase 1: Core (1 week)
1. Basic CLI with setup/remove/list commands
2. Claude Desktop client handler
3. Simple server registry
4. MCP Code Checker built-in config
5. Path auto-detection utilities
6. Dry run support

### Phase 2: Extensibility (1 week)  
1. Entry point discovery for external servers
2. Second MCP client support
3. Better error handling and validation

### Success Criteria - Simplified
- `mcp-config setup mcp-code-checker "my-checker" --project-dir .` works
- `mcp-config remove "my-checker"` works
- External packages can register their server configs
- Adding a new client takes <1 day of work
- Cross-platform path handling works correctly

## Key Simplifications Made

### Removed Complexity
- ❌ Complex parameter type system (`ServerParameter` class)
- ❌ Abstract base classes with multiple inheritance
- ❌ Complex validation and metadata systems
- ❌ Auto-generated server names (user provides simple name)
- ❌ Multiple command patterns (just setup/remove/list)

### Kept Essential Features
- ✅ Server registry for extensibility
- ✅ Client abstraction for multiple MCP clients
- ✅ External server discovery via entry points
- ✅ Dry run support
- ✅ Cross-platform path handling
- ✅ User-provided server names (simple!)

## Why This Is Simpler

1. **User provides server name** - No complex naming logic
2. **Simple dataclass** instead of abstract inheritance
3. **Dict-based registry** instead of complex plugin system
4. **Entry points for discovery** - Standard Python approach
5. **Minimal CLI** - Just the essential commands
6. **One entry point** - `mcp-config` for everything

This approach gives you the extensibility you need for multiple servers and clients while keeping the implementation straightforward and maintainable.