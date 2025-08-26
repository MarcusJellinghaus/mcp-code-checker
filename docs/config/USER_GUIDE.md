# MCP Configuration Helper - User Guide

## Overview

The MCP Configuration Helper automates MCP server setup for Claude Desktop and other MCP clients, eliminating manual JSON editing through a simple command-line interface.

## Quick Start

```bash
# Install the tool
pip install mcp-config

# Navigate to your project
cd /path/to/your/project

# Set up for Claude Desktop (default)
mcp-config setup mcp-code-checker "my-project" --project-dir .

# Set up for VSCode workspace
mcp-config setup mcp-code-checker "my-project" --client vscode --project-dir .

# Set up for VSCode user profile
mcp-config setup mcp-code-checker "global" --client vscode-user --project-dir .

# View configured servers
mcp-config list --detailed
```

## Commands

### setup

Configure a new MCP server instance.

```bash
mcp-config setup <server-type> <server-name> [options]
```

**Arguments:**
- `server-type`: Type of server (e.g., mcp-code-checker)
- `server-name`: Name for this instance

**Options:**
- `--client <type>`: Client type (claude/vscode/vscode-workspace/vscode-user)
- `--project-dir <path>`: Project directory (required)
- `--python-executable <path>`: Python path (auto-detected)
- `--venv-path <path>`: Virtual environment (auto-detected)
- `--log-level <level>`: DEBUG|INFO|WARNING|ERROR|CRITICAL
- `--dry-run`: Preview changes without applying
- `--backup/--no-backup`: Create backup (default: true)

**Client Types:**
- `claude` (default): Configure for Claude Desktop
- `vscode` or `vscode-workspace`: Configure for VSCode workspace (.vscode/mcp.json)
- `vscode-user`: Configure for VSCode user profile

**Examples:**

```bash
# Claude Desktop (default)
mcp-config setup mcp-code-checker "webapp" --project-dir .

# VSCode workspace (team sharing via git)
mcp-config setup mcp-code-checker "webapp" --client vscode --project-dir .

# VSCode user profile (personal/global)
mcp-config setup mcp-code-checker "global" --client vscode-user --project-dir ~/projects

# Debug configuration for VSCode
mcp-config setup mcp-code-checker "debug" \
  --client vscode \
  --project-dir . \
  --log-level DEBUG

# Custom Python
mcp-config setup mcp-code-checker "custom" \
  --project-dir . \
  --python-executable /usr/bin/python3.11
```

### remove

Remove a configured server.

```bash
mcp-config remove <server-name> [options]
```

**Options:**
- `--client <type>`: Client type (claude/vscode/vscode-workspace/vscode-user)
- `--dry-run`: Preview changes
- `--backup/--no-backup`: Create backup

**Examples:**

```bash
# Remove from Claude Desktop (default)
mcp-config remove "old-project"

# Remove from VSCode workspace
mcp-config remove "old-project" --client vscode

# Preview removal from VSCode user profile
mcp-config remove "global" --client vscode-user --dry-run
```

### list

List configured servers.

```bash
mcp-config list [options]
```

**Options:**
- `--client <type>`: Client type (claude/vscode/vscode-workspace/vscode-user)
- `--detailed`: Show full configuration
- `--managed-only`: Show only managed servers

**Examples:**

```bash
# List Claude Desktop servers (default)
mcp-config list

# List VSCode workspace servers
mcp-config list --client vscode --detailed

# List VSCode user profile servers
mcp-config list --client vscode-user
```

**Example Output:**
```
Managed Servers:
├── webapp (mcp-code-checker)
│   ├── Project: /home/user/webapp
│   └── Python: /home/user/webapp/.venv/bin/python

External Servers:
└── calculator (external)
```

### validate

Validate server configuration and discover available server types.

```bash
mcp-config validate [server-name] [options]
```

**Usage:**
- Without arguments: Shows available server types
- With server name: Validates specific server

**Examples:**

```bash
# Show available servers
mcp-config validate

# Validate specific server
mcp-config validate "webapp"

# Verbose validation
mcp-config validate "webapp" --verbose
```

### help

Get command and parameter documentation.

```bash
mcp-config help [topic] [options]
```

**Examples:**

```bash
# General help
mcp-config help

# Command help
mcp-config help setup

# Server parameters
mcp-config help mcp-code-checker

# Quick reference
mcp-config help mcp-code-checker --quick
```

## Auto-Detection

The tool automatically detects:

1. **Python Executable**: Checks virtual environments first, then system Python
2. **Virtual Environment**: Looks for `.venv`, `venv`, etc.
3. **Project Structure**: Validates required files exist

Override auto-detection by specifying paths explicitly.

## Configuration Storage

Configurations are stored in platform-specific locations:

### Claude Desktop
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

### VSCode Workspace
- **All platforms**: `.vscode/mcp.json` in project root
- Shareable via version control
- Takes precedence over user profile

### VSCode User Profile
- **Windows**: `%APPDATA%\Code\User\mcp.json`
- **macOS**: `~/Library/Application Support/Code/User/mcp.json`
- **Linux**: `~/.config/Code/User/mcp.json`

## Safety Features

- **Automatic Backups**: Before any changes (disable with `--no-backup`)
- **External Server Preservation**: Never modifies unmanaged servers
- **Dry Run Mode**: Preview changes with `--dry-run`
- **Validation**: Checks paths and executables before saving

## Common Workflows

### Claude Desktop Setup

```bash
cd ~/projects/my-app
mcp-config setup mcp-code-checker "my-app" --project-dir .
# Restart Claude Desktop
```

### VSCode Team Project

```bash
cd ~/projects/team-project
mcp-config setup mcp-code-checker "team-project" --client vscode --project-dir .
git add .vscode/mcp.json
git commit -m "Add MCP configuration for team"
# Team members: pull and restart VSCode
```

### VSCode Personal Setup

```bash
# Configure globally for all projects
mcp-config setup mcp-code-checker "personal" \
  --client vscode-user \
  --project-dir ~/projects
# Restart VSCode
```

### Multi-Client Setup

```bash
# Same project in both Claude and VSCode
mcp-config setup mcp-code-checker "webapp" --project-dir .
mcp-config setup mcp-code-checker "webapp" --client vscode --project-dir .
```

### Update Configuration

```bash
mcp-config remove "my-app"
mcp-config setup mcp-code-checker "my-app" \
  --project-dir . --log-level DEBUG
```

### Troubleshooting

```bash
# Validate configuration
mcp-config validate "my-app"

# Check detailed config
mcp-config list --detailed
```

## Next Steps

- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Use `--dry-run` to preview changes safely
- Run `mcp-config help` for quick reference
