# MCP Configuration Helper - User Guide

## Overview

The MCP Configuration Helper automates MCP server setup for Claude Desktop and other MCP clients. This tool eliminates the need for manual JSON editing and provides a simple command-line interface for managing your MCP servers.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
  - [setup](#setup-command)
  - [remove](#remove-command)
  - [list](#list-command)
  - [validate](#validate-command)
  - [backup](#backup-command)
  - [list-server-types](#list-server-types-command)
  - [init](#init-command)
  - [help](#help-command)
- [Configuration Examples](#configuration-examples)
- [Path Auto-Detection](#path-auto-detection)
- [Configuration Files](#configuration-files)
- [Safety Features](#safety-features)

## Installation

```bash
pip install mcp-config
```

After installation, the `mcp-config` command will be available in your terminal.

## Quick Start

### Basic Setup

Configure MCP Code Checker for your Python project:

```bash
# Navigate to your Python project
cd /path/to/your/project

# Set up MCP Code Checker with auto-detection
mcp-config setup mcp-code-checker "my-project" --project-dir .
```

This command will:
- Auto-detect your Python executable and virtual environment
- Configure Claude Desktop to use MCP Code Checker
- Create a backup of your existing configuration

### View Available Servers

```bash
mcp-config list-server-types
```

### View Configured Servers

```bash
mcp-config list --detailed
```

## Commands

### setup Command

Configure a new MCP server instance.

**Usage:**
```bash
mcp-config setup <server-type> <server-name> [options]
```

**Arguments:**
- `server-type`: Type of server to configure (e.g., mcp-code-checker)
- `server-name`: Name for this server instance (your choice)

**Global Options:**
- `--client <name>`: Target client (default: claude-desktop)
- `--dry-run`: Preview changes without applying
- `--verbose`: Show detailed output
- `--backup/--no-backup`: Create backup before changes (default: true)

**MCP Code Checker Options:**
- `--project-dir <path>`: Project directory (required)
- `--python-executable <path>`: Python interpreter path (auto-detected)
- `--venv-path <path>`: Virtual environment path (auto-detected)
- `--test-folder <name>`: Test folder name (default: tests)
- `--keep-temp-files`: Keep temp files for debugging
- `--log-level <level>`: DEBUG|INFO|WARNING|ERROR|CRITICAL (default: INFO)
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

### remove Command

Remove a configured MCP server.

**Usage:**
```bash
mcp-config remove <server-name> [options]
```

**Options:**
- `--client <name>`: Target client (default: claude-desktop)
- `--dry-run`: Preview changes without applying
- `--backup/--no-backup`: Create backup before changes (default: true)

**Examples:**

```bash
# Remove server with backup
mcp-config remove "old-project"

# Preview removal
mcp-config remove "old-project" --dry-run
```

### list Command

List configured MCP servers.

**Usage:**
```bash
mcp-config list [options]
```

**Options:**
- `--client <name>`: Show servers for specific client
- `--managed-only`: Show only servers managed by this tool
- `--detailed`: Show full configuration details

**Example Output:**
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

### validate Command

Validate server configuration.

**Usage:**
```bash
mcp-config validate <server-name> [--client <name>]
```

This command checks that:
- The server exists in configuration
- All paths are valid
- Required files exist
- Python executable works

### backup Command

Create manual backup of client configuration.

**Usage:**
```bash
mcp-config backup [--client <name>]
```

Backups are saved with timestamp format:
```
claude_desktop_config.backup_20241201_143022.json
```

### list-server-types Command

View all available server types that can be configured.

**Usage:**
```bash
mcp-config list-server-types
```

**Example Output:**
```
Available server types:

  Built-in servers:
    • mcp-code-checker: MCP Code Checker

  External servers:
    • mcp-filesystem: MCP Filesystem Server
    • mcp-database: MCP Database Server

Total: 3 server type(s) available.
```

### init Command

Re-scan for external servers. Use this after installing new MCP server packages.

**Usage:**
```bash
mcp-config init
```

### help Command

Get detailed documentation for commands and server parameters.

**Usage:**
```bash
# Show general help
mcp-config help

# Show help for specific command
mcp-config help setup
mcp-config help remove

# Show help for server parameters
mcp-config help mcp-code-checker

# Show verbose help with examples
mcp-config help mcp-code-checker --verbose

# Show quick reference card
mcp-config help mcp-code-checker --quick

# Show help for specific parameter
mcp-config help mcp-code-checker --parameter project-dir
```

**Help Options:**
- `--verbose/-v`: Show extended help with examples
- `--all/-a`: Show comprehensive documentation
- `--parameter/-p <name>`: Show help for specific parameter
- `--quick/-q`: Show quick reference card
- `--command/-c`: Treat topic as command name
- `--server/-s`: Treat topic as server type

The help system provides:
- **Required vs Optional Parameters**: Clear indication of what must be provided
- **Auto-Detection Information**: Which parameters can be automatically discovered
- **Default Values**: What values are used if not specified
- **Examples**: Real-world usage patterns (in verbose mode)
- **Parameter Types**: Whether parameters expect paths, strings, choices, or flags

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

After installing external MCP server packages:

```bash
# Filesystem server (if mcp-filesystem is installed)
mcp-config setup mcp-filesystem "docs" \
  --root-dir ~/documents \
  --read-only

# Database server (if mcp-database is installed)
mcp-config setup mcp-database "main-db" \
  --connection-string "postgresql://user:pass@localhost/db" \
  --schema public
```

## Path Auto-Detection

The tool automatically detects your Python environment:

1. **Python Executable**: 
   - Checks virtual environment first
   - Falls back to system Python
   - Common paths checked: `.venv/bin/python`, `venv/bin/python`, etc.

2. **Virtual Environment**: 
   - Looks for: `.venv`, `venv`, `.virtualenv`, `env` folders
   - Activates automatically if found

3. **Project Structure**: 
   - Validates required files exist (e.g., `src/main.py`)
   - Checks test folder exists

To override auto-detection:

```bash
# Specify paths explicitly
mcp-config setup mcp-code-checker "custom" \
  --project-dir . \
  --python-executable /usr/local/bin/python3.11 \
  --venv-path ./custom-venv
```

## Configuration Files

### Claude Desktop Locations

Configurations are stored in platform-specific locations:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

### Configuration Structure

The tool adds server configurations to the `mcpServers` section:

```json
{
  "mcpServers": {
    "my-project": {
      "command": "/path/to/python",
      "args": [
        "/path/to/src/main.py",
        "--project-dir", "/path/to/project",
        "--log-level", "INFO"
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

### Backup Files

Automatic backups use timestamp format:
```
claude_desktop_config.backup_20241201_143022.json
```

Backups are created in the same directory as the configuration file.

## Safety Features

The tool includes multiple safety mechanisms:

### Automatic Backups
- Created before any configuration changes
- Timestamped for easy identification
- Can be disabled with `--no-backup` flag

### External Server Preservation
- Never modifies servers not managed by this tool
- Clearly marks managed servers with metadata
- Lists external servers separately

### Dry Run Mode
- Preview all changes before applying
- Shows exact modifications that would be made
- No files are modified in dry run

### Validation
- Checks paths exist and are accessible
- Validates Python executable works
- Ensures required project structure exists

### Easy Rollback
- Restore from any backup with simple file copy
- Remove managed servers individually
- Complete reset option available

## Common Workflows

### Setting Up a New Project

1. Navigate to your project:
   ```bash
   cd ~/projects/my-python-app
   ```

2. Check available server types:
   ```bash
   mcp-config list-server-types
   ```

3. Get help on parameters:
   ```bash
   mcp-config help mcp-code-checker --quick
   ```

4. Preview setup with dry run:
   ```bash
   mcp-config setup mcp-code-checker "my-app" --project-dir . --dry-run
   ```

5. Apply configuration:
   ```bash
   mcp-config setup mcp-code-checker "my-app" --project-dir .
   ```

6. Restart Claude Desktop to use the new server

### Updating Configuration

1. Remove old configuration:
   ```bash
   mcp-config remove "my-app"
   ```

2. Setup with new parameters:
   ```bash
   mcp-config setup mcp-code-checker "my-app" \
     --project-dir . \
     --log-level DEBUG \
     --keep-temp-files
   ```

### Debugging Issues

1. Validate configuration:
   ```bash
   mcp-config validate "my-app"
   ```

2. Check detailed configuration:
   ```bash
   mcp-config list --detailed
   ```

3. Review logs (if issues persist, see [Troubleshooting Guide](TROUBLESHOOTING.md))

## Next Steps

- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for solving common issues
- Run `mcp-config help` for quick command reference
- Use `--dry-run` to preview changes before applying them
