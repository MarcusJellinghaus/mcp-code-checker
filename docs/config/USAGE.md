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
