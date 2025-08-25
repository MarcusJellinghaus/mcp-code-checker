# Milestone 1.2: Claude Desktop Handler Implementation

## Overview
Implement the Claude Desktop configuration handler that safely manages MCP server configurations in Claude Desktop's JSON configuration file. This milestone focuses on reading, writing, and safely updating the configuration while preserving external servers.

## Context
You are working on an MCP configuration helper tool. The full requirements are in `CONFIG_HELPER_REQUIREMENTS.md` in the same directory. This milestone builds on Milestone 1.1's data model to create the client configuration handler. You should have `src/config/servers.py` and `src/config/utils.py` implemented from the previous milestone.

## Implementation Requirements

### 1. Client Interface

#### File: `src/config/clients.py`

Create the abstract base class and Claude Desktop implementation:

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import os
import platform
import shutil
from datetime import datetime

class ClientHandler(ABC):
    """Abstract base class for MCP client handlers."""
    
    @abstractmethod
    def get_config_path(self) -> Path:
        """Get the path to the client's configuration file."""
        pass
    
    @abstractmethod
    def setup_server(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Add server to client config - only touch our server entries."""
        pass
    
    @abstractmethod
    def remove_server(self, server_name: str) -> bool:
        """Remove server from client config - preserve all other servers."""
        pass
    
    @abstractmethod
    def list_managed_servers(self) -> List[Dict[str, Any]]:
        """List only servers managed by this tool."""
        pass
    
    @abstractmethod
    def list_all_servers(self) -> List[Dict[str, Any]]:
        """List all servers in config (managed + external)."""
        pass

class ClaudeDesktopHandler(ClientHandler):
    """Handler for Claude Desktop client configuration."""
    
    MANAGED_SERVER_MARKER = "mcp-config-managed"
    
    def get_config_path(self) -> Path:
        """Get Claude Desktop config file path based on platform."""
        # Implementation needed - handle Windows/Mac/Linux
        pass
    
    def load_config(self) -> Dict[str, Any]:
        """Load existing Claude Desktop configuration."""
        # Implementation needed
        pass
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save Claude Desktop configuration with proper formatting."""
        # Implementation needed
        pass
    
    def setup_server(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """
        Safely update Claude Desktop config:
        1. Load existing config 
        2. Preserve ALL other servers (filesystem, calculator, etc.)
        3. Only add/update our specific server entry
        4. Mark our entries for identification
        """
        # Implementation needed
        pass
    
    def remove_server(self, server_name: str) -> bool:
        """Remove only if it's managed by us."""
        # Implementation needed
        pass
    
    def list_managed_servers(self) -> List[Dict[str, Any]]:
        """List only servers we manage."""
        # Implementation needed
        pass
    
    def list_all_servers(self) -> List[Dict[str, Any]]:
        """List all servers, mark which ones we manage."""
        # Implementation needed
        pass
    
    def backup_config(self) -> Path:
        """Create a backup of the current configuration."""
        # Implementation needed
        pass
    
    def validate_config(self) -> List[str]:
        """Validate current configuration for basic correctness."""
        # Implementation needed
        pass

# Client registry
CLIENT_HANDLERS = {
    "claude-desktop": ClaudeDesktopHandler,
    # Future clients can be added here
}

def get_client_handler(client_name: str) -> ClientHandler:
    """Get client handler by name."""
    if client_name not in CLIENT_HANDLERS:
        raise ValueError(f"Unknown client: {client_name}. Available: {list(CLIENT_HANDLERS.keys())}")
    
    return CLIENT_HANDLERS[client_name]()
```

### 2. Configuration Path Detection

Implement platform-specific configuration path detection:

```python
def get_config_path(self) -> Path:
    """Get Claude Desktop config file path based on platform."""
    if os.name == 'nt':  # Windows
        return Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json"
    elif os.name == 'posix':
        if platform.system() == 'Darwin':  # macOS
            return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
        else:  # Linux
            return Path.home() / ".config/claude/claude_desktop_config.json"
    else:
        raise OSError(f"Unsupported operating system: {os.name}")
```

### 3. Safe Configuration Management

The handler must:
1. **Preserve External Servers:** Never modify servers not created by this tool
2. **Use Markers:** Add `_managed_by` field to identify our servers
3. **Atomic Updates:** Load → Modify → Save as atomic operation
4. **Backup Before Changes:** Always create backup before modifications
5. **Validate Structure:** Ensure JSON structure is valid

### 4. Server Configuration Format

Generate configurations in Claude Desktop format:

```json
{
  "mcpServers": {
    "my-checker": {
      "command": "/path/to/python",
      "args": [
        "/path/to/project/src/main.py",
        "--project-dir",
        "/path/to/project",
        "--log-level",
        "INFO"
      ],
      "env": {
        "PYTHONPATH": "/path/to/project"
      },
      "_managed_by": "mcp-config-managed",
      "_server_type": "mcp-code-checker"
    }
  }
}
```

### 5. Integration with ServerConfig

#### File: `src/config/integration.py`

Create integration functions that bridge ServerConfig and ClientHandler:

```python
from .servers import ServerConfig
from .clients import ClientHandler
from .utils import normalize_path_parameter
from typing import Dict, Any
from pathlib import Path

def generate_client_config(
    server_config: ServerConfig, 
    server_name: str, 
    user_params: Dict[str, Any], 
    python_executable: str
) -> Dict[str, Any]:
    """
    Generate client configuration from server config and user parameters.
    
    Args:
        server_config: Server configuration definition
        server_name: User-provided server instance name
        user_params: User-provided parameter values
        python_executable: Path to Python executable to use
        
    Returns:
        Client configuration dictionary ready for JSON serialization
    """
    # Implementation needed
    pass

def setup_mcp_server(
    client_handler: ClientHandler,
    server_config: ServerConfig,
    server_name: str,
    user_params: Dict[str, Any],
    python_executable: str = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    High-level function to set up an MCP server in a client.
    
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
    # Implementation needed
    pass

def remove_mcp_server(
    client_handler: ClientHandler,
    server_name: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Remove an MCP server from client configuration.
    
    Args:
        client_handler: Client handler instance
        server_name: Name of server to remove
        dry_run: If True, return what would be done without applying changes
        
    Returns:
        Dictionary with operation results
    """
    # Implementation needed
    pass
```

### 6. Path Auto-Detection

#### File: `src/config/detection.py`

Implement Python executable and environment detection:

```python
import sys
import os
from pathlib import Path
from typing import Optional, Tuple, List

def detect_python_environment(project_dir: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    Auto-detect Python executable and virtual environment.
    
    Args:
        project_dir: Project directory to search for virtual environments
        
    Returns:
        Tuple of (python_executable, venv_path)
    """
    # Implementation needed
    pass

def find_virtual_environments(project_dir: Path) -> List[Path]:
    """
    Find all potential virtual environments in project directory.
    
    Args:
        project_dir: Directory to search
        
    Returns:
        List of virtual environment paths found
    """
    # Implementation needed
    pass

def validate_python_executable(python_path: str) -> bool:
    """
    Validate that a Python executable path is valid and working.
    
    Args:
        python_path: Path to Python executable
        
    Returns:
        True if valid, False otherwise
    """
    # Implementation needed
    pass

def get_python_info(python_path: str) -> Dict[str, str]:
    """
    Get information about a Python executable.
    
    Args:
        python_path: Path to Python executable
        
    Returns:
        Dictionary with version, platform, etc.
    """
    # Implementation needed
    pass
```

## Implementation Details

### Configuration Loading
- Handle missing configuration files gracefully
- Default to `{"mcpServers": {}}` structure
- Proper UTF-8 encoding for international characters
- Validate JSON structure after loading

### Configuration Saving
- Create parent directories if they don't exist
- Use proper JSON formatting (2-space indentation)
- Atomic write operations (write to temp file, then rename)
- Preserve file permissions

### Server Management Safety
- Always check `_managed_by` marker before modifications
- Raise clear errors when trying to modify external servers
- Preserve all other configuration sections (not just mcpServers)
- Handle missing mcpServers section gracefully

### Backup Strategy
- Include timestamp in backup filenames
- Create backups in same directory as original
- Return backup path for user confirmation
- Clean up old backups (optional)

### Path Normalization
- Convert all paths to absolute paths
- Handle Windows drive letters correctly
- Resolve symbolic links if needed
- Validate path existence for critical paths

## Test Requirements

### File: `tests/test_config/test_clients.py`

Create comprehensive tests for:

1. **Path Detection Tests:**
   ```python
   def test_config_path_windows():
       # Mock Windows environment
       pass
   
   def test_config_path_macos():
       # Mock macOS environment
       pass
   
   def test_config_path_linux():
       # Mock Linux environment
       pass
   ```

2. **Configuration Management Tests:**
   ```python
   def test_load_missing_config():
       # Should return default structure
       pass
   
   def test_load_existing_config():
       # Should preserve existing content
       pass
   
   def test_save_config_creates_directories():
       # Should create parent directories
       pass
   
   def test_setup_server_preserves_external():
       # Should not modify external servers
       pass
   ```

3. **Server Management Tests:**
   ```python
   def test_setup_managed_server():
       # Should add server with markers
       pass
   
   def test_remove_managed_server():
       # Should only remove our servers
       pass
   
   def test_remove_external_server_fails():
       # Should raise error for external servers
       pass
   
   def test_list_managed_vs_all_servers():
       # Should distinguish managed from external
       pass
   ```

4. **Backup Tests:**
   ```python
   def test_backup_config():
       # Should create timestamped backup
       pass
   
   def test_backup_missing_config():
       # Should handle missing config gracefully
       pass
   ```

### File: `tests/test_config/test_integration.py`

Create tests for:
- Configuration generation from ServerConfig
- End-to-end server setup flow
- Parameter validation and normalization
- Dry-run functionality

### File: `tests/test_config/test_detection.py`

Create tests for:
- Python executable detection
- Virtual environment discovery
- Path validation
- Cross-platform compatibility

## Test Data Setup

### File: `tests/test_config/fixtures/`

Create test fixture files:
- `claude_config_empty.json` - Empty configuration
- `claude_config_with_external.json` - Config with external servers
- `claude_config_with_managed.json` - Config with managed servers
- `claude_config_mixed.json` - Mix of managed and external servers

## Acceptance Criteria

1. **Configuration Path Detection:**
   ```python
   handler = ClaudeDesktopHandler()
   path = handler.get_config_path()
   assert path.name == "claude_desktop_config.json"
   ```

2. **Safe Server Management:**
   ```python
   # Setup server doesn't affect external servers
   initial_external = handler.list_all_servers()
   handler.setup_server("test-server", test_config)
   final_all = handler.list_all_servers()
   # External servers should be unchanged
   ```

3. **Backup Functionality:**
   ```python
   backup_path = handler.backup_config()
   assert backup_path.exists()
   assert "backup_" in backup_path.name
   ```

4. **Integration Works:**
   ```python
   from src.config.servers import registry
   from src.config.integration import setup_mcp_server
   
   config = registry.get("mcp-code-checker")
   result = setup_mcp_server(
       handler, config, "test", 
       {"project-dir": "/test/project"}
   )
   assert result["success"] == True
   ```

5. **All Tests Pass:**
   ```bash
   pytest tests/test_config/test_clients.py -v
   pytest tests/test_config/test_integration.py -v  
   pytest tests/test_config/test_detection.py -v
   ```

## Next Steps
After completing this milestone, you'll have a working configuration handler that Milestone 1.3 (Basic CLI) can use to provide user-facing commands.
