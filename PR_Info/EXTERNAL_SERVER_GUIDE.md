# External Server Configuration Guide

This guide explains how external MCP packages can register their server configurations with the MCP Configuration Helper tool.

## Overview

External MCP packages can expose their server configurations via Python entry points, allowing the MCP Configuration Helper to discover and manage them automatically.

## Setup in pyproject.toml

Add your server configuration to the `mcp.server_configs` entry point group:

```toml
[project.entry-points."mcp.server_configs"]
# Single server
my_server = "my_package.config:SERVER_CONFIG"

# Multiple servers
filesystem = "mcp_filesystem.config:FILESYSTEM_CONFIG"
database = "mcp_filesystem.config:DATABASE_CONFIG"
```

## Configuration Definition

Create a configuration module that exports a `ServerConfig` object:

```python
# In my_package/config.py
from mcp_config.servers import ServerConfig, ParameterDef

SERVER_CONFIG = ServerConfig(
    name="my-mcp-server",
    display_name="My MCP Server",
    main_module="src/main.py",  # Path relative to package root
    parameters=[
        ParameterDef(
            name="api-key",
            arg_name="--api-key",
            param_type="string",
            required=True,
            help="API key for authentication"
        ),
        ParameterDef(
            name="endpoint",
            arg_name="--endpoint",
            param_type="string",
            default="https://api.example.com",
            help="API endpoint URL"
        ),
        ParameterDef(
            name="verbose",
            arg_name="--verbose",
            param_type="boolean",
            is_flag=True,
            help="Enable verbose logging"
        ),
        ParameterDef(
            name="cache-dir",
            arg_name="--cache-dir",
            param_type="path",
            auto_detect=True,
            help="Directory for caching (auto-detected if not specified)"
        ),
        ParameterDef(
            name="mode",
            arg_name="--mode",
            param_type="choice",
            choices=["development", "production"],
            default="production",
            help="Operating mode"
        )
    ]
)
```

## Parameter Types

### String Parameters
Basic text input parameters:
```python
ParameterDef(
    name="api-key",
    arg_name="--api-key",
    param_type="string",
    required=True,
    help="API key for authentication"
)
```

### Boolean Flags
Boolean parameters that act as flags:
```python
ParameterDef(
    name="debug",
    arg_name="--debug",
    param_type="boolean",
    is_flag=True,  # Important for boolean flags
    help="Enable debug mode"
)
```

### Path Parameters
File or directory paths (automatically normalized):
```python
ParameterDef(
    name="config-file",
    arg_name="--config-file",
    param_type="path",
    help="Configuration file path"
)
```

### Choice Parameters
Parameters with predefined valid values:
```python
ParameterDef(
    name="log-level",
    arg_name="--log-level",
    param_type="choice",
    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    default="INFO",
    help="Logging level"
)
```

## Advanced Features

### Auto-Detection
Mark parameters that can be automatically detected:
```python
ParameterDef(
    name="python-executable",
    arg_name="--python-executable",
    param_type="path",
    auto_detect=True,  # Will be auto-detected if not provided
    help="Python interpreter path (auto-detected if not specified)"
)
```

### Custom Validators
Add validation functions for parameters:
```python
def validate_port(value: Any, param_name: str) -> List[str]:
    """Validate port number."""
    errors = []
    try:
        port = int(value)
        if port < 1 or port > 65535:
            errors.append(f"{param_name}: Port must be between 1 and 65535")
    except ValueError:
        errors.append(f"{param_name}: Must be a valid integer")
    return errors

ParameterDef(
    name="port",
    arg_name="--port",
    param_type="string",
    default="8080",
    validator=validate_port,
    help="Server port number"
)
```

## Complete Example: Filesystem Server

```python
# In mcp_filesystem/config.py
from typing import Any, List
from mcp_config.servers import ServerConfig, ParameterDef

def validate_max_file_size(value: Any, param_name: str) -> List[str]:
    """Validate max file size format."""
    errors = []
    valid_units = ["B", "KB", "MB", "GB"]
    
    if not isinstance(value, str):
        errors.append(f"{param_name}: Must be a string")
        return errors
    
    # Check format (e.g., "10MB")
    import re
    pattern = r'^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB)$'
    if not re.match(pattern, value, re.IGNORECASE):
        errors.append(
            f"{param_name}: Invalid format. Use format like '10MB', '1.5GB'"
        )
    
    return errors

FILESYSTEM_CONFIG = ServerConfig(
    name="mcp-filesystem",
    display_name="MCP Filesystem Server",
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
            help="Enable read-only mode (no write operations allowed)"
        ),
        ParameterDef(
            name="max-file-size",
            arg_name="--max-file-size",
            param_type="string",
            default="10MB",
            validator=validate_max_file_size,
            help="Maximum file size to read (e.g., '10MB', '1GB')"
        ),
        ParameterDef(
            name="allowed-extensions",
            arg_name="--allowed-extensions",
            param_type="string",
            default=".txt,.md,.json,.py",
            help="Comma-separated list of allowed file extensions"
        ),
        ParameterDef(
            name="follow-symlinks",
            arg_name="--follow-symlinks",
            param_type="boolean",
            is_flag=True,
            help="Follow symbolic links when traversing directories"
        ),
        ParameterDef(
            name="log-level",
            arg_name="--log-level",
            param_type="choice",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="Logging verbosity level"
        )
    ]
)
```

## Usage After Installation

Once your package is installed, the MCP Configuration Helper will automatically discover it:

```bash
# List all available server types (including yours)
mcp-config list-server-types

# Your server will appear in the list:
#   Built-in servers:
#     • mcp-code-checker: MCP Code Checker
#   
#   External servers:
#     • mcp-filesystem: MCP Filesystem Server

# Setup your server
mcp-config setup mcp-filesystem "my-fs" \
    --root-dir /path/to/files \
    --read-only \
    --max-file-size 50MB

# List configured servers
mcp-config list

# Remove your server
mcp-config remove my-fs
```

## Best Practices

1. **Naming Convention**: Use kebab-case for server names (e.g., `mcp-my-server`)
2. **Display Names**: Use clear, descriptive display names
3. **Help Text**: Provide comprehensive help text for all parameters
4. **Defaults**: Set sensible defaults where appropriate
5. **Validation**: Add validators for complex parameters
6. **Documentation**: Document all parameters in your package README

## Validation Rules

Your server configuration must pass these validation checks:

1. **Required Fields**:
   - `name`: Non-empty, unique server identifier
   - `display_name`: Human-readable name
   - `main_module`: Path to main Python module
   - `parameters`: List (can be empty)

2. **Name Format**:
   - Only letters, numbers, hyphens, and underscores
   - Cannot conflict with built-in server names

3. **Parameter Types**:
   - Must be one of: `string`, `boolean`, `choice`, `path`
   - Choice parameters must have a `choices` list

## Troubleshooting

### Server Not Discovered

1. Check entry point is correctly defined in `pyproject.toml`
2. Ensure package is installed (`pip list | grep your-package`)
3. Run `mcp-config init --verbose` to see discovery details
4. Check for validation errors in verbose output

### Validation Errors

Run with `--verbose` to see detailed error messages:
```bash
mcp-config init --verbose
```

Common issues:
- Missing required fields in `ServerConfig`
- Invalid parameter types
- Name conflicts with built-in servers
- Malformed entry point definitions

## Testing Your Configuration

Test your configuration before publishing:

```python
# test_config.py
from mcp_config.servers import ServerConfig
from mcp_config.discovery import ExternalServerValidator
from my_package.config import SERVER_CONFIG

def test_server_config():
    validator = ExternalServerValidator()
    is_valid, errors = validator.validate_server_config(
        SERVER_CONFIG, 
        "my_package"
    )
    
    if not is_valid:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")
    
    # Test parameter generation
    test_params = {
        "api_key": "test-key",
        "verbose": True
    }
    
    args = SERVER_CONFIG.generate_args(test_params)
    print(f"Generated args: {args}")

if __name__ == "__main__":
    test_server_config()
```

## Support

For issues or questions about external server configuration:
1. Check this guide and the troubleshooting section
2. Review the built-in `mcp-code-checker` configuration as an example
3. File an issue on the MCP Configuration Helper repository
