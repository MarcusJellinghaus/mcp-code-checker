# MCP Configuration Helper - API Documentation

## Overview
This document covers the programmatic API for the MCP Configuration Helper, useful for integration into other tools or custom automation.

## Core Classes

### ServerConfig
Main configuration class for MCP servers.

```python
from src.config.servers import ServerConfig, ParameterDef

config = ServerConfig(
    name="my-server",
    display_name="My Custom Server", 
    main_module="src/main.py",
    parameters=[...]
)
```

**Methods:**
- `generate_args(user_params: dict) -> list`: Generate command line arguments
- `get_required_params() -> list[str]`: Get required parameter names
- `validate_project(project_dir: Path) -> bool`: Validate project compatibility
- `get_parameter_by_name(name: str) -> Optional[ParameterDef]`: Find parameter by name

### ParameterDef
Parameter definition for server configuration.

```python
param = ParameterDef(
    name="param-name",
    arg_name="--param-name",
    param_type="string|boolean|choice|path",
    required=False,
    default=None,
    choices=None,  # For choice type
    help="Parameter description",
    is_flag=False  # For boolean flags
)
```

### ServerRegistry
Central registry for server configurations.

```python
from src.config.servers import registry

# Register a server
registry.register(server_config)

# Get a server
config = registry.get("server-name")

# List all servers
servers = registry.list_servers()
```

### ClientHandler (Abstract)
Base class for MCP client handlers.

```python
from src.config.clients import get_client_handler

handler = get_client_handler("claude-desktop")
handler.setup_server("server-name", server_config)
handler.remove_server("server-name") 
handler.list_managed_servers()
```

## Programmatic Usage Examples

### Basic Server Setup
```python
from src.config.servers import registry
from src.config.clients import get_client_handler
from pathlib import Path

# Get server configuration
server_config = registry.get("mcp-code-checker")
if not server_config:
    raise ValueError("Server type not found")

# Prepare parameters
user_params = {
    "project-dir": "/path/to/project",
    "log-level": "INFO"
}

# Validate required parameters
required = server_config.get_required_params()
missing = [p for p in required if p not in user_params]
if missing:
    raise ValueError(f"Missing required parameters: {missing}")

# Generate server configuration
args = server_config.generate_args(user_params)
server_instance_config = {
    "command": "/path/to/python",
    "args": args,
    "env": {"PYTHONPATH": "/path/to/project"},
    "_managed_by": "mcp-config-managed",
    "_server_type": server_config.name
}

# Setup with client
client_handler = get_client_handler("claude-desktop")
success = client_handler.setup_server("my-server", server_instance_config)
```

### Configuration Validation
```python
from src.config.utils import validate_project_structure
from pathlib import Path

project_dir = Path("/path/to/project")
server_config = registry.get("mcp-code-checker")

# Validate project structure
errors = validate_project_structure(project_dir, server_config)
if errors:
    print(f"Validation failed: {errors}")
else:
    print("Project structure is valid")

# Server-specific validation
is_compatible = server_config.validate_project(project_dir)
if not is_compatible:
    print("Project not compatible with server")
```

### External Server Discovery
```python
from src.config.discovery import discover_external_servers, initialize_external_servers

# Manual discovery
discovered = discover_external_servers()
print(f"Found {len(discovered)} external servers")

for name, (config, source) in discovered.items():
    print(f"  {config.display_name} from {source}")

# Full initialization (discovery + registration)
registered_count, errors = initialize_external_servers(verbose=True)
print(f"Registered {registered_count} external servers")

if errors:
    print("Errors occurred during discovery")
    for error in errors:
        print(f"  - {error}")
```

### Configuration Management
```python
from src.config.clients import get_client_handler

# Get client handler
handler = get_client_handler("claude-desktop")

# List managed servers
managed_servers = handler.list_managed_servers()
print(f"Found {len(managed_servers)} managed servers")

for server in managed_servers:
    print(f"  {server['name']}: {server['type']}")

# Create backup before changes
backup_path = handler.backup_config()
print(f"Configuration backed up to: {backup_path}")

# Remove a server
try:
    success = handler.remove_server("old-server")
    if success:
        print("Server removed successfully")
except ValueError as e:
    print(f"Failed to remove server: {e}")
```

## Error Handling

### Exception Types
```python
from src.config.errors import ServerDiscoveryError, ClientConfigError

try:
    # Discovery operations
    discovered = discover_external_servers()
except ServerDiscoveryError as e:
    print(f"Discovery failed: {e}")

try:
    # Client operations
    handler.setup_server("name", config)
except ClientConfigError as e:
    print(f"Client configuration failed: {e}")
```

### Validation Patterns
```python
from src.config.servers import registry
from pathlib import Path

def setup_server_safely(server_type: str, name: str, params: dict):
    """Setup server with comprehensive error handling."""
    
    # Validate server type
    server_config = registry.get(server_type)
    if not server_config:
        available = registry.list_servers()
        raise ValueError(f"Unknown server type '{server_type}'. Available: {available}")
    
    # Validate required parameters
    required = server_config.get_required_params()
    missing = [p for p in required if p not in params]
    if missing:
        raise ValueError(f"Missing required parameters: {missing}")
    
    # Validate project directory if specified
    project_dir = params.get("project-dir")
    if project_dir:
        project_path = Path(project_dir)
        if not project_path.exists():
            raise ValueError(f"Project directory does not exist: {project_dir}")
        
        if not server_config.validate_project(project_path):
            raise ValueError(f"Project directory is not compatible with {server_type}")
    
    # Generate and setup configuration
    args = server_config.generate_args(params)
    
    # ... rest of setup logic
```

## Custom Client Development

### Implementing a New Client Handler
```python
from src.config.clients import ClientHandler
from pathlib import Path
import json

class MyCustomClientHandler(ClientHandler):
    """Handler for My Custom MCP Client."""
    
    def get_config_path(self) -> Path:
        """Get configuration file path for this client."""
        return Path.home() / ".config/myclient/config.json"
    
    def setup_server(self, server_name: str, server_config: dict) -> bool:
        """Add server to client configuration."""
        config = self.load_config()
        
        # Add server to configuration
        if "servers" not in config:
            config["servers"] = {}
        
        config["servers"][server_name] = server_config
        
        self.save_config(config)
        return True
    
    def remove_server(self, server_name: str) -> bool:
        """Remove server from client configuration."""
        config = self.load_config()
        
        if "servers" in config and server_name in config["servers"]:
            del config["servers"][server_name]
            self.save_config(config)
            return True
        
        return False
    
    def list_managed_servers(self) -> list:
        """List servers managed by this tool."""
        config = self.load_config()
        servers = []
        
        for name, server_config in config.get("servers", {}).items():
            if server_config.get("_managed_by") == "mcp-config-managed":
                servers.append({
                    "name": name,
                    "type": server_config.get("_server_type"),
                    "managed": True
                })
        
        return servers
    
    def list_all_servers(self) -> list:
        """List all servers in configuration."""
        config = self.load_config()
        servers = []
        
        for name, server_config in config.get("servers", {}).items():
            is_managed = server_config.get("_managed_by") == "mcp-config-managed"
            servers.append({
                "name": name,
                "type": server_config.get("_server_type", "external"),
                "managed": is_managed
            })
        
        return servers
    
    def load_config(self) -> dict:
        """Load client configuration from file."""
        config_path = self.get_config_path()
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            return {}
    
    def save_config(self, config: dict) -> None:
        """Save client configuration to file."""
        config_path = self.get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

# Register your custom handler
from src.config.clients import CLIENT_HANDLERS
CLIENT_HANDLERS["my-custom-client"] = MyCustomClientHandler
```

## Testing APIs

### Mock Configuration for Testing
```python
import pytest
from unittest.mock import Mock, patch
from src.config.servers import ServerConfig, ParameterDef, ServerRegistry

@pytest.fixture
def mock_server_config():
    """Create a mock server configuration for testing."""
    return ServerConfig(
        name="test-server",
        display_name="Test Server",
        main_module="test/main.py",
        parameters=[
            ParameterDef(
                name="test-param",
                arg_name="--test-param",
                param_type="string",
                required=True,
                help="Test parameter"
            )
        ]
    )

@pytest.fixture
def test_registry():
    """Create a test registry with mock server."""
    registry = ServerRegistry()
    mock_config = mock_server_config()
    registry.register(mock_config)
    return registry

def test_server_setup_api(mock_server_config):
    """Test server setup via API."""
    user_params = {"test-param": "test-value"}
    args = mock_server_config.generate_args(user_params)
    
    assert "test/main.py" in args
    assert "--test-param" in args
    assert "test-value" in args
```

## Integration Examples

### IDE Plugin Integration
```python
def create_mcp_server_for_project(project_path: str, server_type: str = "mcp-code-checker"):
    """Create MCP server configuration for IDE integration."""
    from src.config.servers import registry
    from src.config.utils import detect_python_environment
    
    project_dir = Path(project_path)
    server_config = registry.get(server_type)
    
    # Auto-detect Python environment
    python_exe, venv_path = detect_python_environment(project_dir)
    
    # Prepare parameters
    params = {
        "project-dir": str(project_dir),
        "python-executable": python_exe
    }
    
    if venv_path:
        params["venv-path"] = venv_path
    
    # Generate configuration
    args = server_config.generate_args(params)
    
    return {
        "name": f"{server_type}-{project_dir.name}",
        "command": python_exe,
        "args": args,
        "env": {"PYTHONPATH": str(project_dir)}
    }
```

### CI/CD Integration
```python
def setup_mcp_servers_from_config(config_file: str):
    """Setup multiple MCP servers from configuration file."""
    import yaml
    from src.config.servers import registry
    from src.config.clients import get_client_handler
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    client_handler = get_client_handler("claude-desktop")
    
    for server_def in config.get("servers", []):
        server_type = server_def["type"]
        server_name = server_def["name"]
        parameters = server_def.get("parameters", {})
        
        server_config = registry.get(server_type)
        if not server_config:
            print(f"Skipping unknown server type: {server_type}")
            continue
        
        # Generate configuration
        args = server_config.generate_args(parameters)
        server_instance_config = {
            "command": parameters.get("python-executable", "python"),
            "args": args,
            "_managed_by": "mcp-config-managed",
            "_server_type": server_type
        }
        
        # Setup server
        try:
            client_handler.setup_server(server_name, server_instance_config)
            print(f"✓ Configured {server_name} ({server_type})")
        except Exception as e:
            print(f"✗ Failed to configure {server_name}: {e}")
```

## Best Practices

### Error Handling
- Always validate inputs before processing
- Use specific exception types for different error categories
- Provide clear, actionable error messages
- Log errors appropriately for debugging

### Performance
- Cache server configurations when possible
- Avoid repeated file system access
- Use lazy loading for external server discovery
- Minimize configuration file writes

### Security
- Validate all file paths to prevent directory traversal
- Use absolute paths in generated configurations
- Sanitize user inputs before using in shell commands
- Preserve existing configuration permissions

### Compatibility
- Handle both old and new importlib.metadata APIs
- Support multiple Python versions (3.8+)
- Test across different operating systems
- Handle missing optional dependencies gracefully

This API enables powerful integration possibilities while maintaining the safety and reliability of the MCP Configuration Helper.
