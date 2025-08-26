"""
Manual Testing Checklist for VSCode Support
===========================================

This file contains manual testing procedures to verify VSCode support works correctly.

## Prerequisites
- VSCode 1.102 or later installed
- Python 3.11+ installed  
- MCP Code Checker project available
- Git for version control (optional)

## 1. Basic Setup Testing

### 1.1 Workspace Configuration
```bash
# Navigate to a test project
cd /path/to/test/project

# Setup VSCode workspace configuration
mcp-config setup mcp-code-checker "test-project" --client vscode --project-dir .

# Verify files created
ls -la .vscode/
# Should see: mcp.json and .mcp-config-metadata.json

# Check the configuration
cat .vscode/mcp.json

# Expected output structure:
# {
#   "servers": {
#     "test-project": {
#       "command": "python",
#       "args": ["-m", "mcp_code_checker", "--project-dir", "."],
#       "env": {"PYTHONPATH": "."}
#     }
#   }
# }
```

### 1.2 User Profile Configuration
```bash
# Setup VSCode user profile configuration
mcp-config setup mcp-code-checker "global-checker" --client vscode --user --project-dir ~/projects

# Verify file location based on OS:
# Linux: ~/.config/Code/User/mcp.json
# macOS: ~/Library/Application Support/Code/User/mcp.json
# Windows: %APPDATA%\Code\User\mcp.json

# Check the configuration
# Linux/macOS:
cat ~/.config/Code/User/mcp.json
# Windows:
type %APPDATA%\Code\User\mcp.json
```

## 2. Client Alias Testing

### 2.1 Test all client aliases work
```bash
# These should all work:
mcp-config list --client vscode
mcp-config list --client vscode-workspace  
mcp-config list --client vscode-user
```

## 3. List Operations Testing

### 3.1 List all servers
```bash
# List workspace servers
mcp-config list --client vscode

# List user profile servers
mcp-config list --client vscode --user

# List with details
mcp-config list --client vscode --detailed
```

### 3.2 Test mixed server listing
```bash
# Manually add an external server to .vscode/mcp.json
# Edit the file to add:
{
  "servers": {
    "test-project": {
      "command": "python",
      "args": ["-m", "mcp_code_checker"]
    },
    "external-server": {
      "command": "node",
      "args": ["server.js"]
    }
  }
}

# List should show both servers
mcp-config list --client vscode

# Only test-project should be marked as managed
```

## 4. Remove Operations Testing

### 4.1 Remove managed server
```bash
# Setup a test server
mcp-config setup mcp-code-checker "temp-server" --client vscode --project-dir .

# Remove it
mcp-config remove "temp-server" --client vscode

# Verify it's gone
mcp-config list --client vscode
cat .vscode/mcp.json
```

### 4.2 Try to remove external server (should fail)
```bash
# Try to remove the external server added earlier
mcp-config remove "external-server" --client vscode

# Should see error message about external server
# External server should still be in config
cat .vscode/mcp.json
```

## 5. Validation Testing

### 5.1 Validate valid configuration
```bash
mcp-config validate "test-project" --client vscode
# Should report configuration is valid
```

### 5.2 Test invalid configuration
```bash
# Manually corrupt .vscode/mcp.json
# Remove the "command" field from a server

# Run validation
mcp-config validate "test-project" --client vscode
# Should report error about missing command field
```

## 6. Dry Run Testing

### 6.1 Test dry run mode
```bash
# Clean workspace
rm -rf .vscode/

# Run setup with dry-run
mcp-config setup mcp-code-checker "dry-test" --client vscode --project-dir . --dry-run

# Should see output about what would be done
# But no files should be created
ls -la .vscode/
# Should not exist or be empty
```

## 7. Advanced Parameter Testing

### 7.1 Test all parameters
```bash
mcp-config setup mcp-code-checker "full-test" \
  --client vscode \
  --project-dir . \
  --venv-path .venv \
  --log-file debug.log \
  --log-level DEBUG \
  --workspace

# Check configuration includes all parameters
cat .vscode/mcp.json
```

## 8. Path Handling Testing

### 8.1 Relative path handling (workspace)
```bash
# Setup with absolute path
mcp-config setup mcp-code-checker "abs-test" --client vscode --project-dir $(pwd)

# Check that paths are relative in workspace config
cat .vscode/mcp.json
# Project dir should be "." or relative path
```

### 8.2 Absolute path handling (user profile)
```bash
# Setup with relative path
mcp-config setup mcp-code-checker "user-test" --client vscode --user --project-dir .

# Check that paths are absolute in user config
# Paths should be fully qualified
```

## 9. Cross-Platform Testing

### 9.1 Windows Testing
```powershell
# On Windows, test with PowerShell
mcp-config setup mcp-code-checker "win-test" --client vscode --project-dir .

# Check Windows paths work correctly
type .vscode\mcp.json

# Test user profile location
mcp-config setup mcp-code-checker "win-user" --client vscode --user --project-dir %CD%
type %APPDATA%\Code\User\mcp.json
```

### 9.2 macOS Testing
```bash
# On macOS, test with standard paths
mcp-config setup mcp-code-checker "mac-test" --client vscode --project-dir .

# Test user profile location (different from Linux)
mcp-config setup mcp-code-checker "mac-user" --client vscode --user --project-dir .
cat ~/Library/Application\ Support/Code/User/mcp.json
```

## 10. VSCode Integration Testing

### 10.1 Test in VSCode
1. Open VSCode
2. Open the project with .vscode/mcp.json
3. Open Command Palette (Ctrl/Cmd+Shift+P)
4. Look for MCP-related commands
5. Restart VSCode if needed
6. Check if GitHub Copilot can see the MCP servers

### 10.2 Test with VSCode Insiders
```bash
# Setup for VSCode Insiders (if installed)
# Note: Path might be different
mcp-config setup mcp-code-checker "insiders-test" --client vscode --project-dir .

# The config path might be:
# Linux: ~/.config/Code - Insiders/User/mcp.json
# macOS: ~/Library/Application Support/Code - Insiders/User/mcp.json
# Windows: %APPDATA%\Code - Insiders\User\mcp.json
```

## 11. Package vs Source Testing

### 11.1 Test with package installation
```bash
# Install mcp-code-checker as package
pip install -e .

# Setup should use module invocation
mcp-config setup mcp-code-checker "pkg-test" --client vscode --project-dir .
cat .vscode/mcp.json
# Should see: "args": ["-m", "mcp_code_checker", ...]
```

### 11.2 Test without package installation
```bash
# Uninstall package
pip uninstall mcp-code-checker

# Setup should use direct script
mcp-config setup mcp-code-checker "src-test" --client vscode --project-dir .
cat .vscode/mcp.json
# Should see: "args": ["src/main.py", ...]
```

## 12. Error Handling Testing

### 12.1 Test permission errors
```bash
# Make .vscode read-only
chmod 444 .vscode/

# Try to setup (should fail gracefully)
mcp-config setup mcp-code-checker "perm-test" --client vscode --project-dir .

# Reset permissions
chmod 755 .vscode/
```

### 12.2 Test malformed JSON
```bash
# Corrupt .vscode/mcp.json
echo "{ invalid json }" > .vscode/mcp.json

# Try to list (should handle error)
mcp-config list --client vscode

# Try to validate (should report JSON error)
mcp-config validate "test" --client vscode
```

## 13. Backup Testing

### 13.1 Test backup creation
```bash
# Setup initial server
mcp-config setup mcp-code-checker "backup-test" --client vscode --project-dir .

# Modify the server (should create backup)
mcp-config setup mcp-code-checker "backup-test" --client vscode --project-dir . --log-level DEBUG

# Check for backup files
ls -la .vscode/mcp_backup_*.json
```

## 14. Help System Testing

### 14.1 Test help includes VSCode options
```bash
# Check main help
mcp-config --help
# Should mention VSCode support

# Check setup help
mcp-config setup --help
# Should explain --client vscode options

# Check for workspace/user flags
mcp-config setup --help | grep -E "(workspace|user)"
```

## Expected Results Summary

✅ All tests should pass with:
- Correct file creation in expected locations
- Proper JSON structure in configuration files
- Metadata tracking for managed servers
- External servers preserved during operations
- Error messages for invalid operations
- Cross-platform path handling
- VSCode can load and use the configurations

❌ Common issues to watch for:
- Permission errors on file creation
- Incorrect path separators on Windows
- Missing directories (.vscode not created)
- JSON formatting issues
- Module vs script invocation problems

## Reporting Issues

If any test fails:
1. Note the exact command that failed
2. Capture the error message
3. Check the generated files
4. Include OS and VSCode version
5. Report in GitHub issue or PR comments
"""