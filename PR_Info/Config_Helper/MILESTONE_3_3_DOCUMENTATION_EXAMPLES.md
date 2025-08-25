# Milestone 3.3: Documentation & Examples Implementation

## Context
You are implementing Phase 3, Milestone 3.3 of the MCP Configuration Helper tool. Previous milestones have completed:
- Phase 1: Core foundation with basic ServerConfig, ClaudeDesktopHandler, and CLI  
- Phase 2: Complete parameter support, advanced CLI features, and cross-platform polish
- Phase 3.1: Server Registry with built-in MCP Code Checker configuration
- Phase 3.2: External Server Support with entry point discovery

This final milestone focuses on creating comprehensive documentation and examples to make the tool production-ready and user-friendly.

## Objective
Create complete documentation that:
1. Provides clear usage examples for all functionality
2. Includes troubleshooting guides for common issues
3. Shows integration examples for external server authors
4. Documents the complete API and CLI interface
5. Enables users to successfully configure MCP servers without additional support

## Requirements

### 1. Main Usage Documentation
Create `docs/USAGE.md`:

```markdown
# MCP Configuration Helper - Usage Guide

## Overview
The MCP Configuration Helper automates MCP server setup for Claude Desktop and other MCP clients. No more manual JSON editing!

## Installation

```bash
pip install mcp-config
```

## Quick Start

### Basic Setup
Configure MCP Code Checker for your project:

```bash
# Navigate to your Python project
cd /path/to/your/project

# Set up MCP Code Checker with auto-detection
mcp-config setup mcp-code-checker "my-project" --project-dir .
```

This will:
- Auto-detect your Python executable and virtual environment
- Configure Claude Desktop to use MCP Code Checker
- Create a backup of your existing configuration

### View Available Server Types

```bash
mcp-config list-server-types
```

Output:
```
Available server types:

  Built-in servers:
    • mcp-code-checker: MCP Code Checker

  External servers:
    • mcp-filesystem: MCP Filesystem Server
    • mcp-database: MCP Database Server

Total: 3 server type(s) available.
```

### View Configured Servers

```bash
mcp-config list --detailed
```

Output:
```
Managed Servers for claude-desktop:
├── my-project (mcp-code-checker)
│   ├── Project: /home/user/myproject
│   ├── Python: /home/user/myproject/.venv/bin/python
│   ├── Test Folder: tests
│   └── Log Level: INFO

External Servers:
├── calculator (external) - not managed by mcp-config
└── weather-api (external) - not managed by mcp-config
```

## Complete CLI Reference

### setup
Configure a new MCP server instance.

```bash
mcp-config setup <server-type> <server-name> [options]
```

**Global Options:**
- `--client <n>`: Target client (default: claude-desktop)
- `--dry-run`: Preview changes without applying
- `--verbose`: Show detailed output
- `--backup`: Create backup before changes (default: true)

**MCP Code Checker Options:**
- `--project-dir <path>`: Project directory (required)
- `--python-executable <path>`: Python interpreter path
- `--venv-path <path>`: Virtual environment path  
- `--test-folder <n>`: Test folder name (default: tests)
- `--keep-temp-files`: Keep temp files for debugging
- `--log-level <level>`: DEBUG|INFO|WARNING|ERROR|CRITICAL
- `--log-file <path>`: Custom log file path
- `--console-only`: Log to console only

**Examples:**

```bash
# Basic setup with auto-detection
mcp-config setup mcp-code-checker "main-project" --project-dir .

# Custom Python and virtual environment
mcp-config setup mcp-code-checker "py311-project" \
  --project-dir . \
  --python-executable /usr/bin/python3.11 \
  --venv-path ./.venv

# Debug configuration
mcp-config setup mcp-code-checker "debug-project" \
  --project-dir . \
  --log-level DEBUG \
  --keep-temp-files \
  --console-only

# Dry run to preview changes
mcp-config setup mcp-code-checker "test-setup" \
  --project-dir . --dry-run
```

### remove
Remove a configured MCP server.

```bash
mcp-config remove <server-name> [options]
```

**Options:**
- `--client <n>`: Target client (default: claude-desktop)
- `--dry-run`: Preview changes without applying
- `--backup`: Create backup before changes (default: true)

**Examples:**

```bash
# Remove server with backup
mcp-config remove "old-project"

# Preview removal
mcp-config remove "old-project" --dry-run
```

### list
List configured MCP servers.

```bash
mcp-config list [options]
```

**Options:**
- `--client <n>`: Show servers for specific client
- `--managed-only`: Show only servers managed by this tool
- `--detailed`: Show full configuration details

### validate
Validate server configuration.

```bash
mcp-config validate <server-name> [--client <n>]
```

### backup
Create manual backup of client configuration.

```bash
mcp-config backup [--client <n>]
```

### init
Re-scan for external servers.

```bash
mcp-config init
```

## Configuration Examples

### Multiple Project Setup

```bash
# Web application project
mcp-config setup mcp-code-checker "webapp" \
  --project-dir ~/projects/webapp \
  --log-level INFO

# Machine learning project with custom test folder
mcp-config setup mcp-code-checker "ml-model" \
  --project-dir ~/projects/ml-model \
  --test-folder unit_tests \
  --log-level DEBUG

# Legacy project with specific Python version
mcp-config setup mcp-code-checker "legacy" \
  --project-dir ~/projects/legacy \
  --python-executable /usr/bin/python3.8 \
  --test-folder legacy_tests
```

### External Server Usage

```bash
# After installing mcp-filesystem package
mcp-config setup mcp-filesystem "docs" \
  --root-dir ~/documents \
  --read-only

# Database server setup
mcp-config setup mcp-database "main-db" \
  --connection-string "postgresql://user:pass@localhost/db" \
  --schema public
```

## Path Auto-Detection

The tool automatically detects:

1. **Python Executable**: Checks virtual environment first, falls back to system Python
2. **Virtual Environment**: Looks for `.venv`, `venv`, `.virtualenv`, `env` folders
3. **Project Structure**: Validates required files exist (e.g., `src/main.py`)

Manual specification overrides auto-detection:

```bash
# Override auto-detection
mcp-config setup mcp-code-checker "custom" \
  --project-dir . \
  --python-executable /usr/local/bin/python3.11 \
  --venv-path ./custom-venv
```

## Configuration Files

### Claude Desktop
Configurations are stored in platform-specific locations:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

### Backup Files
Automatic backups use timestamp format:
```
claude_desktop_config.backup_20241201_143022.json
```

## Safety Features

- **Automatic Backups**: Created before any changes
- **External Server Preservation**: Never modifies servers not managed by this tool
- **Dry Run Mode**: Preview all changes before applying
- **Validation**: Checks paths and configuration validity
- **Rollback**: Easy restoration from backups

## Next Steps

- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- See [INTEGRATION.md](INTEGRATION.md) for external server development
- See [API.md](API.md) for programmatic usage
```

### 2. Troubleshooting Guide
Create `docs/TROUBLESHOOTING.md`:

```markdown
# MCP Configuration Helper - Troubleshooting Guide

## Common Issues

### Installation Issues

#### "mcp-config command not found"

**Problem**: Command not available after installation.

**Solutions**:
```bash
# Verify installation
pip show mcp-config

# Reinstall with explicit scripts
pip install --force-reinstall mcp-config

# Check PATH includes Python scripts directory
python -m pip show mcp-config

# Use module execution as alternative
python -m src.config.main --help
```

#### "Permission denied" when running mcp-config

**Problem**: Insufficient permissions to modify configuration files.

**Solutions**:
```bash
# Check config directory permissions
ls -la ~/.config/claude/ # Linux
ls -la ~/Library/Application\ Support/Claude/ # macOS

# Fix permissions if needed
chmod 755 ~/.config/claude/
chmod 644 ~/.config/claude/claude_desktop_config.json
```

### Configuration Issues

#### "Project directory validation failed"

**Problem**: MCP Code Checker project validation fails.

**Diagnosis**:
```bash
# Check project structure
ls -la your-project/src/main.py

# Validate manually
mcp-config validate "your-server-name"
```

**Solutions**:
- Ensure `src/main.py` exists in project directory
- Use correct `--project-dir` path
- Check for typos in paths

#### "Python executable not found"

**Problem**: Auto-detection fails to find Python.

**Diagnosis**:
```bash
# Check what Python is available
which python
which python3
ls -la .venv/bin/python  # Check virtual environment

# Test manual specification
mcp-config setup mcp-code-checker "test" \
  --project-dir . \
  --python-executable $(which python3) \
  --dry-run
```

**Solutions**:
```bash
# Specify Python executable explicitly
mcp-config setup mcp-code-checker "project" \
  --project-dir . \
  --python-executable /usr/bin/python3

# Or specify virtual environment
mcp-config setup mcp-code-checker "project" \
  --project-dir . \
  --venv-path ./.venv
```

#### "Server name already exists"

**Problem**: Attempting to create server with existing name.

**Solutions**:
```bash
# Check existing servers
mcp-config list

# Remove existing server first
mcp-config remove "existing-name"

# Or use a different name
mcp-config setup mcp-code-checker "new-name" --project-dir .
```

### Claude Desktop Integration Issues

#### "Claude Desktop not recognizing server"

**Problem**: Configured server doesn't appear in Claude Desktop.

**Diagnosis**:
```bash
# Verify configuration was written
mcp-config list --detailed

# Check Claude Desktop config file directly
cat ~/.config/claude/claude_desktop_config.json  # Linux
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json  # macOS
type "%APPDATA%\Claude\claude_desktop_config.json"  # Windows
```

**Solutions**:
1. **Restart Claude Desktop** - Required after configuration changes
2. **Check JSON syntax** - Ensure config file is valid JSON
3. **Verify paths** - Ensure all paths in config are absolute and correct
4. **Check permissions** - Ensure Claude Desktop can read the config file

#### "Server fails to start in Claude Desktop"

**Problem**: Server appears in config but fails to start.

**Diagnosis**:
```bash
# Test server manually
cd /path/to/project
python src/main.py --project-dir . --log-level DEBUG

# Check Claude Desktop logs (if available)
# Logs location varies by platform
```

**Solutions**:
```bash
# Validate server configuration
mcp-config validate "server-name"

# Test with minimal configuration
mcp-config remove "server-name"
mcp-config setup mcp-code-checker "server-name" \
  --project-dir . \
  --console-only \
  --log-level DEBUG

# Check virtual environment activation
mcp-config setup mcp-code-checker "server-name" \
  --project-dir . \
  --venv-path ./.venv
```

### External Server Issues

#### "External server not discovered"

**Problem**: Installed external server package not showing up.

**Diagnosis**:
```bash
# Check if package is installed
pip list | grep mcp

# Force re-discovery
mcp-config init

# Check for entry points
python -c "
from importlib.metadata import entry_points
eps = entry_points()
if hasattr(eps, 'select'):
    mcp_eps = eps.select(group='mcp.server_configs')
else:
    mcp_eps = eps.get('mcp.server_configs', [])
for ep in mcp_eps:
    print(f'Found: {ep.name} -> {ep.value}')
"
```

**Solutions**:
1. **Reinstall external package** - May fix entry point registration
2. **Check package compatibility** - Ensure it uses correct entry point format
3. **Manual verification** - Try importing the config directly in Python

#### "External server validation failed"

**Problem**: External server config is invalid.

**Diagnosis**:
```bash
# Run with verbose output to see validation errors
mcp-config init --verbose
```

**Solutions**:
- Contact external package maintainer
- Report issue to external package repository
- Use built-in servers as alternative

### Performance Issues

#### "Slow startup or discovery"

**Problem**: Tool takes long time to start or discover servers.

**Solutions**:
```bash
# Skip external server discovery
export MCP_CONFIG_SKIP_EXTERNAL=1
mcp-config list-server-types

# Use specific operations only
mcp-config list --managed-only
```

### Path and Platform Issues

#### "Incorrect paths in configuration"

**Problem**: Generated paths don't work on your system.

**Diagnosis**:
```bash
# Check generated configuration
mcp-config setup mcp-code-checker "test" \
  --project-dir . \
  --dry-run \
  --verbose
```

**Solutions**:
```bash
# Use absolute paths explicitly
mcp-config setup mcp-code-checker "project" \
  --project-dir "$(pwd)" \
  --python-executable "$(which python3)"

# Check path normalization
python -c "
from pathlib import Path
print('Project dir:', Path('.').absolute())
print('Python exe:', Path('$(which python3)').absolute())
"
```

#### "Windows path issues"

**Problem**: Path separators or drive letters causing issues.

**Solutions**:
```cmd
REM Use forward slashes or double backslashes
mcp-config setup mcp-code-checker "project" --project-dir "C:/Projects/MyProject"

REM Or double backslashes
mcp-config setup mcp-code-checker "project" --project-dir "C:\\Projects\\MyProject"
```

## Debugging Steps

### 1. Basic Verification
```bash
# Verify tool installation
mcp-config --version
mcp-config --help

# Check available servers
mcp-config list-server-types

# Verify current configuration
mcp-config list --detailed
```

### 2. Configuration Testing
```bash
# Test with dry run
mcp-config setup mcp-code-checker "debug" \
  --project-dir . \
  --dry-run \
  --verbose

# Validate after setup
mcp-config validate "debug"
```

### 3. Manual Testing
```bash
# Test MCP Code Checker directly
cd your-project
python src/main.py --help
python src/main.py --project-dir . --log-level DEBUG
```

### 4. Log Analysis
```bash
# Enable verbose logging
mcp-config setup mcp-code-checker "debug" \
  --project-dir . \
  --log-level DEBUG \
  --verbose

# Check generated configuration
cat ~/.config/claude/claude_desktop_config.json | jq .mcpServers
```

## Getting Help

### Check Documentation
- [Usage Guide](USAGE.md)
- [Integration Guide](INTEGRATION.md)
- [API Documentation](API.md)

### Report Issues
1. **Gather information**:
   ```bash
   mcp-config --version
   python --version
   pip list | grep mcp
   ```

2. **Include configuration**:
   ```bash
   mcp-config list --detailed
   ```

3. **Test with minimal example**:
   ```bash
   mcp-config setup mcp-code-checker "test" --project-dir . --dry-run
   ```

4. **Report to appropriate repository**:
   - Main tool issues: [mcp-config repository]
   - External server issues: [specific server repository]

### Community Resources
- GitHub Discussions
- Stack Overflow (tag: mcp-config)
- Discord/Slack communities

## Recovery Procedures

### Restore from Backup
```bash
# List available backups
ls -la ~/.config/claude/claude_desktop_config.backup_*.json

# Restore specific backup
cp ~/.config/claude/claude_desktop_config.backup_20241201_143022.json \
   ~/.config/claude/claude_desktop_config.json

# Or remove all managed servers and start fresh
mcp-config list --managed-only  # Note server names
mcp-config remove "server1"
mcp-config remove "server2"
# etc.
```

### Complete Reset
```bash
# Backup current config
mcp-config backup

# Remove all managed servers
for server in $(mcp-config list --managed-only | grep '│' | cut -d' ' -f2); do
    mcp-config remove "$server"
done

# Start fresh
mcp-config setup mcp-code-checker "fresh-start" --project-dir .
```
```

### 3. Integration Guide for External Server Authors
Create `docs/INTEGRATION.md`:

```markdown
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
```

### 4. API Documentation
Create `docs/API.md`:

```markdown
# MCP Configuration Helper - API Documentation

## Overview
This document covers the programmatic API for the MCP Configuration Helper, useful for integration into other tools or custom automation.

## Core Classes

### ServerConfig
Main configuration class for MCP servers.

```python
from mcp_config.servers import ServerConfig, ParameterDef

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
from mcp_config.servers import registry

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
from mcp_config.clients import get_client_handler

handler = get_client_handler("claude-desktop")
handler.setup_server("server-name", server_config)
handler.remove_server("server-name") 
handler.list_managed_servers()
```

## Programmatic Usage Examples

### Basic Server Setup
```python
from mcp_config.servers import registry
from mcp_config.clients import get_client_handler
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
from mcp_config.utils import validate_project_structure
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
from mcp_config.discovery import discover_external_servers, initialize_external_servers

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
from mcp_config.clients import get_client_handler

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
from mcp_config.discovery import ServerDiscoveryError
from mcp_config.clients import ClientConfigError

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
from mcp_config.servers import registry
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
from mcp_config.clients import ClientHandler
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
from mcp_config.clients import CLIENT_HANDLERS
CLIENT_HANDLERS["my-custom-client"] = MyCustomClientHandler
```

## Testing APIs

### Mock Configuration for Testing
```python
import pytest
from unittest.mock import Mock, patch
from mcp_config.servers import ServerConfig, ParameterDef, ServerRegistry

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
    from mcp_config.servers import registry
    from mcp_config.utils import detect_python_environment
    
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
    from mcp_config.servers import registry
    from mcp_config.clients import get_client_handler
    
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
```

## Testing Requirements

Create comprehensive tests in `tests/test_docs/`:

### Test Structure:
```python
# tests/test_docs/test_documentation.py

def test_all_documentation_files_exist():
    """Test that all required documentation files exist."""
    docs_dir = Path("docs")
    required_files = [
        "USAGE.md",
        "TROUBLESHOOTING.md", 
        "INTEGRATION.md",
        "API.md"
    ]
    
    for file in required_files:
        assert (docs_dir / file).exists(), f"Missing documentation file: {file}"

def test_documentation_examples_valid():
    """Test that code examples in documentation are valid Python syntax."""
    # Parse and validate code blocks from markdown files
    pass

def test_cli_examples_match_implementation():
    """Test that CLI examples in docs match actual CLI interface."""
    # Compare documented options with actual CLI options
    pass

def test_api_examples_work():
    """Test that API examples actually work."""
    # Run API examples from documentation
    pass
```

## Validation Criteria

### Functional Requirements:
- [ ] All documentation files created and complete
- [ ] Usage examples cover all major functionality  
- [ ] Troubleshooting guide addresses common issues
- [ ] Integration guide enables external server development
- [ ] API documentation covers all public interfaces

### Quality Requirements:
- [ ] Clear, consistent writing style
- [ ] Accurate code examples (syntax-checked)
- [ ] Complete CLI reference documentation
- [ ] Comprehensive troubleshooting scenarios
- [ ] Professional formatting and organization

### User Experience Requirements:
- [ ] New users can follow quick start guide successfully
- [ ] All CLI commands have usage examples
- [ ] Error scenarios have clear resolution steps
- [ ] External developers have complete integration guide
- [ ] API users have working code examples

## Expected Deliverables

1. **Complete Documentation Suite**
   - `docs/USAGE.md` with comprehensive usage guide
   - `docs/TROUBLESHOOTING.md` with common issues and solutions
   - `docs/INTEGRATION.md` for external server developers
   - `docs/API.md` with programmatic interface documentation

2. **Example Configurations**
   - Complete CLI usage examples
   - External server integration examples
   - API usage patterns
   - Configuration file examples

3. **Test Coverage**
   - Documentation validation tests
   - Example code verification
   - CLI reference accuracy tests

## Success Metrics

- Users can successfully configure MCP servers following the documentation
- External developers can create compatible server packages
- Common issues are resolved via troubleshooting guide
- Documentation is comprehensive enough to reduce support requests
- All code examples work correctly when executed
- Professional-quality documentation ready for public release

This milestone completes the MCP Configuration Helper with production-ready documentation that enables users and developers to successfully use and extend the tool.
