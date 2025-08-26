# VSCode Support Release Notes

## Version 1.x.x - VSCode Integration

### New Features

#### Native VSCode Support
- Full support for VSCode 1.102+ with native MCP integration
- Works with GitHub Copilot and other MCP-compatible extensions
- No VSCode extension required - uses built-in MCP support

#### Flexible Configuration Options
- **Workspace Configuration** (`.vscode/mcp.json`)
  - Team-shareable via version control
  - Project-specific settings
  - Relative path support
- **User Profile Configuration**
  - Global/personal settings
  - Cross-project usage
  - Platform-specific paths handled automatically

#### Enhanced CLI
- New `--client` option for all commands
- Client aliases: `vscode`, `vscode-workspace`, `vscode-user`
- Backward compatible - Claude Desktop remains default

#### Smart Command Generation
- Automatic detection of package vs source installation
- Uses `python -m mcp_code_checker` for packages
- Uses `python src/main.py` for source
- Intelligent path resolution (relative/absolute)

### Usage Examples

```bash
# Configure for VSCode workspace (team projects)
mcp-config setup mcp-code-checker "project" --client vscode --project-dir .

# Configure for VSCode user profile (personal)
mcp-config setup mcp-code-checker "global" --client vscode-user --project-dir ~/projects

# List VSCode servers
mcp-config list --client vscode --detailed

# Remove from VSCode
mcp-config remove "project" --client vscode
```

### Requirements

- VSCode 1.102 or later
- Python 3.11+
- GitHub Copilot (optional, for Copilot integration)

### Migration Guide

Existing Claude Desktop configurations are unaffected. To add VSCode support:

1. Run setup with `--client vscode` option
2. Restart VSCode
3. MCP servers will be available in GitHub Copilot

### Technical Details

- Cross-platform support (Windows, macOS, Linux)
- Comprehensive test coverage
- Performance optimized for large configurations
- Thread-safe operations
- Automatic backup creation

### Breaking Changes

None - all changes are additive and backward compatible.

### Known Issues

- VSCode requires restart after configuration changes
- Workspace config takes precedence over user profile

### Documentation

- Updated README with VSCode sections
- Enhanced USER_GUIDE with client options
- New TROUBLESHOOTING section for VSCode
- Complete API documentation

### Contributors

- Implementation follows MCP protocol standards
- Tested on Windows, macOS, and Linux
- Performance validated with 100+ server configurations
