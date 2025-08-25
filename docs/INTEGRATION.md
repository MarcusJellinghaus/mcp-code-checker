# External Server Integration Guide

This guide shows how to make your MCP server package compatible with the MCP Configuration Helper.

## Overview

The MCP Configuration Helper discovers external servers through Python entry points. Your package needs to:

1. Define a `ServerConfig` object with all parameters
2. Expose it via an entry point in `pyproject.toml`
3. Follow the parameter definition conventions

## Quick Start

### 1. Add Dependency

```toml
[project]
dependencies = [
    "mcp-config>=1.0.0",
    # your other dependencies
]
```

### 2. Create Configuration

Create a `config.py` file in your package:

```python
# src/your_package/config.py
from mcp_config.servers import ServerConfig, ParameterDef

YOUR_SERVER_CONFIG = ServerConfig(
    name="your-server-name",
    display_name="Your Server Display Name",
    main_module="src/main.py",  # Relative to project directory
    parameters=[
        ParameterDef(
            name="required-param",
            arg_name="--required-param",
            param_type="path",
            required=True,
            help="Description of required parameter"
        ),
        ParameterDef(
            name="optional-param",
            arg_name="--optional-param",
            param_type="string",
            default="default-value",
            help="Description of optional parameter"
        ),
        # Add more parameters as needed
    ]
)
```

### 3. Register Entry Point

Add to your `pyproject.toml`:

```toml
[project.entry-points."mcp.server_configs"]
your-server-name = "your_package.config:YOUR_SERVER_CONFIG"
```

### 4. Test Integration

```bash
# Install your package in development mode
pip install -e .

# Re-scan for servers
mcp-config init

# Verify your server is discovered
mcp-config list-server-types

# Test setup
mcp-config setup your-server-name "test-instance" --required-param /path/to/something
```

## Parameter Types and Examples

### String Parameters
```python
ParameterDef(
    name="connection-string",
    arg_name="--connection-string", 
    param_type="string",
    required=True,
    help="Database connection string"
)
```

Usage: `--connection-string "postgresql://user:pass@localhost/db"`

### Path Parameters
```python
ParameterDef(
    name="root-directory",
    arg_name="--root-dir",
    param_type="path",
    required=True,
    help="Root directory for file operations"
)
```

Usage: `--root-directory /path/to/directory`

### Boolean Flags
```python
ParameterDef(
    name="read-only",
    arg_name="--read-only",
    param_type="boolean",
    is_flag=True,
    help="Enable read-only mode"
)
```

Usage: `--read-only` (no value, just the flag)

### Choice Parameters
```python
ParameterDef(
    name="log-level",
    arg_name="--log-level",
    param_type="choice",
    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    default="INFO",
    help="Set logging level"
)
```

Usage: `--log-level DEBUG`

### Optional Parameters with Defaults
```python
ParameterDef(
    name="timeout",
    arg_name="--timeout",
    param_type="string",
    default="30s",
    help="Request timeout duration"
)
```

## Complete Example: Filesystem Server

```python
# mcp_filesystem/config.py
from mcp_config.servers import ServerConfig, ParameterDef

FILESYSTEM_CONFIG = ServerConfig(
    name="mcp-filesystem",
    display_name="MCP Filesystem Server",
    main_module="src/main.py",
    parameters=[
        # Required parameters
        ParameterDef(
            name="root-dir",
            arg_name="--root-dir",
            param_type="path",
            required=True,
            help="Root directory for filesystem access"
        ),
        
        # Security parameters
        ParameterDef(
            name="read-only",
            arg_name="--read-only",
            param_type="boolean",
            is_flag=True,
            help="Enable read-only mode (no write operations)"
        ),
        
        # Size limits
        ParameterDef(
            name="max-file-size",
            arg_name="--max-file-size",
            param_type="string",
            default="10MB",
            help="Maximum file size to read (e.g., '10MB', '1GB')"
        ),
        
        # Filtering
        ParameterDef(
            name="ignore-patterns",
            arg_name="--ignore-patterns",
            param_type="string",
            help="Comma-separated glob patterns to ignore (e.g., '*.log,temp/*')"
        ),
        
        # Behavior options
        ParameterDef(
            name="follow-symlinks",
            arg_name="--follow-symlinks",
            param_type="boolean",
            is_flag=True,
            help="Follow symbolic links"
        ),
        
        # Logging
        ParameterDef(
            name="log-level",
            arg_name="--log-level",
            param_type="choice",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="Set logging level"
        )
    ]
)
```

### pyproject.toml
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mcp-filesystem"
version = "1.0.0"
description = "MCP Filesystem Server"
dependencies = [
    "mcp-config>=1.0.0"
]

[project.entry-points."mcp.server_configs"]
mcp-filesystem = "mcp_filesystem.config:FILESYSTEM_CONFIG"

[project.scripts]
mcp-filesystem = "mcp_filesystem.main:main"
```

### Usage After Installation
```bash
# Install the package
pip install mcp-filesystem

# Discover the new server
mcp-config init

# Use the server
mcp-config setup mcp-filesystem "docs-reader" \
  --root-dir ~/Documents \
  --read-only \
  --max-file-size 5MB \
  --ignore-patterns "*.log,temp/*"
```

## Best Practices

### Parameter Naming
- Use kebab-case for parameter names: `max-file-size`, `connection-string`
- Match CLI argument names: `name="log-level"` → `arg_name="--log-level"`
- Use descriptive, unambiguous names

### Parameter Types
- Use `path` for file/directory parameters (enables path validation)
- Use `choice` for enumerated values (provides CLI validation)
- Use `boolean` with `is_flag=True` for feature toggles
- Use `string` for free-form text inputs

### Help Text
- Write clear, concise help text
- Include examples for complex parameters
- Mention defaults where applicable
- Explain the impact of the parameter

### Project Validation
Optionally implement custom project validation:

```python
def validate_project(self, project_dir: Path) -> bool:
    """Check if project is compatible with your server."""
    if self.name == "your-server-name":
        # Check for required files/structure
        config_file = project_dir / "your-config.yml"
        return config_file.exists()
    
    return True  # Default: any directory is valid
```

### Error Handling
Your server configuration will be validated automatically:
- Missing required fields will be caught
- Invalid parameter types will be rejected
- Name conflicts with built-in servers will be prevented

## Testing Your Integration

### 1. Unit Tests
```python
# test_config.py
import pytest
from your_package.config import YOUR_SERVER_CONFIG

def test_server_config_validity():
    """Test server configuration is valid."""
    assert YOUR_SERVER_CONFIG.name
    assert YOUR_SERVER_CONFIG.display_name
    assert YOUR_SERVER_CONFIG.main_module
    assert isinstance(YOUR_SERVER_CONFIG.parameters, list)

def test_required_parameters():
    """Test required parameters are identified."""
    required = YOUR_SERVER_CONFIG.get_required_params()
    assert "required-param" in required

def test_argument_generation():
    """Test CLI argument generation."""
    user_params = {
        "required-param": "/path/to/something",
        "optional-param": "value"
    }
    args = YOUR_SERVER_CONFIG.generate_args(user_params)
    
    assert YOUR_SERVER_CONFIG.main_module in args
    assert "--required-param" in args
    assert "/path/to/something" in args
```

### 2. Integration Tests
```python
def test_entry_point_registration():
    """Test entry point is registered correctly."""
    from importlib.metadata import entry_points
    
    eps = entry_points()
    if hasattr(eps, 'select'):
        mcp_eps = list(eps.select(group='mcp.server_configs'))
    else:
        mcp_eps = eps.get('mcp.server_configs', [])
    
    found = False
    for ep in mcp_eps:
        if ep.name == "your-server-name":
            config = ep.load()
            assert config.name == "your-server-name"
            found = True
            break
    
    assert found, "Entry point not registered"

def test_mcp_config_integration():
    """Test integration with mcp-config tool."""
    import subprocess
    
    # Test discovery
    result = subprocess.run(
        ["mcp-config", "list-server-types"],
        capture_output=True, text=True
    )
    assert "your-server-name" in result.stdout
    
    # Test dry run setup
    result = subprocess.run([
        "mcp-config", "setup", "your-server-name", "test",
        "--required-param", "/tmp",
        "--dry-run"
    ], capture_output=True, text=True)
    assert result.returncode == 0
```

## Deployment Checklist

- [ ] ServerConfig properly defined with all parameters
- [ ] Entry point registered in pyproject.toml
- [ ] All required parameters marked as required=True
- [ ] Help text provided for all parameters
- [ ] Parameter types correctly specified
- [ ] Default values provided where appropriate
- [ ] Configuration tested with mcp-config tool
- [ ] Integration tests passing
- [ ] Documentation updated with usage examples

## Troubleshooting

### "Server not discovered"
1. Check entry point registration in pyproject.toml
2. Reinstall package: `pip install -e .`
3. Force re-discovery: `mcp-config init`

### "Invalid server configuration"  
1. Check ServerConfig fields are all present
2. Verify parameter definitions are complete
3. Run mcp-config init with verbose output: `mcp-config init --verbose`

### "Name conflicts"
1. Ensure server name doesn't conflict with built-in servers
2. Use unique, descriptive names
3. Check existing servers: `mcp-config list-server-types`

## Support

- Include examples in your package documentation
- Provide troubleshooting guides specific to your server
- Reference this integration guide in your README
- Consider providing configuration templates

Your external server integration makes the MCP ecosystem more powerful and user-friendly!
