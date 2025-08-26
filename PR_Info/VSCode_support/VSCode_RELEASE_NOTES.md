# VSCode Support Release Notes

## Overview

Added full support for VSCode's native MCP functionality (available in VSCode 1.102+).

## New Features

### 1. VSCode Client Handler
- New `VSCodeHandler` class for managing VSCode MCP configurations
- Support for both workspace (`.vscode/mcp.json`) and user profile configurations
- Cross-platform path handling for Windows, macOS, and Linux

### 2. CLI Enhancements
- New client options: `vscode`, `vscode-workspace`, `vscode-user`
- `--workspace/--user` flag for VSCode configuration location
- Updated help text with VSCode examples

### 3. Intelligent Command Generation
- Automatic detection of package vs source installation
- Module invocation (`python -m mcp_code_checker`) for installed packages
- Direct script execution for development setups
- Path normalization (relative for workspace, absolute for user configs)

## Usage Examples

### Basic VSCode Setup
```bash
# Workspace configuration (recommended)
mcp-config setup mcp-code-checker "my-project" --client vscode --project-dir .

# User profile configuration
mcp-config setup mcp-code-checker "global" --client vscode --user --project-dir ~/projects
```

### List VSCode Servers
```bash
# All VSCode servers
mcp-config list --client vscode

# Workspace servers only
mcp-config list --client vscode-workspace

# User profile servers only
mcp-config list --client vscode-user
```

### Remove VSCode Server
```bash
# Remove from workspace
mcp-config remove "my-project" --client vscode

# Remove from user profile
mcp-config remove "global" --client vscode-user
```

## Technical Details

### Configuration Format
VSCode uses a simpler format than Claude Desktop:
```json
{
  "servers": {
    "server-name": {
      "command": "python",
      "args": ["-m", "mcp_code_checker", "--project-dir", "/path"],
      "env": {"PYTHONPATH": "/path"}
    }
  }
}
```

### Metadata Tracking
Like Claude Desktop, uses `.mcp-config-metadata.json` to track managed servers, ensuring external servers are never modified.

### Path Handling
- **Workspace configs:** Prefer relative paths for portability
- **User configs:** Use absolute paths for reliability
- **Cross-platform:** Automatic path normalization for each OS

## Migration Guide

### For Existing Users
No changes required for Claude Desktop users. VSCode support is additive.

### For VSCode Users
1. Ensure VSCode 1.102+ is installed
2. Run setup command with `--client vscode`
3. Restart VSCode to load configuration
4. Use with GitHub Copilot or other MCP-compatible extensions

## Testing Coverage

### Unit Tests Added
- `test_vscode_handler.py` - Handler functionality
- `test_vscode_cli.py` - CLI integration
- `test_integration.py` - VSCode-specific integration

### Platforms Tested
- ✅ Windows 10/11
- ✅ macOS 12+
- ✅ Ubuntu 22.04
- ✅ VSCode stable and Insiders editions

## Backward Compatibility
- All existing Claude Desktop functionality unchanged
- Existing configurations remain valid
- CLI maintains backward compatibility

## Known Limitations
1. VSCode must be restarted after configuration changes
2. GitHub Copilot organization policy may need adjustment
3. VSCode 1.102+ required (earlier versions lack MCP support)

## Future Enhancements
- Auto-detect VSCode installation and version
- Support for VSCode workspace settings inheritance
- Integration with VSCode's multi-root workspace feature
- Support for Cursor and other VSCode forks