# Milestone 2.2: Advanced CLI Features

## Overview
Implement advanced CLI features including configuration validation, dry-run support, and enhanced output formatting. This milestone focuses on improving user experience and safety through better feedback and preview capabilities.

## Prerequisites
- Milestone 2.1 completed (complete parameter support)
- All 8 MCP Code Checker parameters working
- Dynamic CLI generation implemented
- Basic `setup`, `remove`, `list` commands functional

## Goals
1. Implement `validate` command for configuration verification
2. Add `--dry-run` support across all commands
3. Implement detailed output formatting with clear status indicators
4. Add comprehensive error handling and user feedback
5. Provide actionable error messages and suggestions

## Detailed Requirements

### 1. Validate Command

Implement a comprehensive validation command that checks if a configured server can actually run:

```bash
mcp-config validate <server-name> [--client <client>]
```

#### Validation Checks:
1. **Configuration Existence:** Server exists in client configuration
2. **Path Validation:** All specified paths exist and are accessible
3. **Python Executable:** Specified Python interpreter is valid and executable
4. **Virtual Environment:** If specified, venv exists and contains valid Python
5. **Project Structure:** Required files exist (e.g., src/main.py for MCP Code Checker)
6. **Permissions:** User has necessary read/write permissions
7. **Dependencies:** Basic dependency checking (optional)

#### Output Format:
```
Validating server 'my-checker' configuration...

✓ Configuration found in claude-desktop
✓ Project directory exists: /home/user/myproject
✓ Project directory is readable and writable
✓ Python executable found: /home/user/myproject/.venv/bin/python
✓ Python executable is valid and runnable
✓ Virtual environment is valid: /home/user/myproject/.venv
✓ Main module exists: /home/user/myproject/src/main.py
✓ Test folder exists: /home/user/myproject/tests
✓ Test folder is readable: /home/user/myproject/tests
✓ Log directory exists: /home/user/myproject/logs
✓ Log directory is writable: /home/user/myproject/logs

✅ Server 'my-checker' configuration is valid and ready to use

Configuration Details:
├── Server Type: mcp-code-checker
├── Project Directory: /home/user/myproject
├── Python Executable: /home/user/myproject/.venv/bin/python (venv)
├── Test Folder: tests (relative to project)
├── Log Level: INFO
├── Log File: /home/user/myproject/logs/mcp_code_checker_20241201_143022.log
└── Keep Temp Files: No
```

#### Error Output Example:
```
Validating server 'broken-checker' configuration...

✓ Configuration found in claude-desktop
✗ Project directory does not exist: /invalid/path
✗ Python executable not found: /usr/bin/python3.12
✗ Test folder not found: /home/user/myproject/custom-tests

❌ Server 'broken-checker' configuration has errors

Suggestions:
• Create project directory: mkdir -p /invalid/path
• Install Python 3.12 or update --python-executable parameter
• Create test folder: mkdir -p /home/user/myproject/custom-tests
• Run: mcp-config setup mcp-code-checker broken-checker --project-dir /home/user/myproject
```

### 2. Dry-Run Support

Implement `--dry-run` flag for all commands that modify configuration:

#### Setup Command Dry-Run:
```bash
mcp-config setup mcp-code-checker "test-checker" --project-dir . --dry-run
```

**Output:**
```
🔍 DRY RUN: No changes will be applied

Auto-detected parameters:
├── Python Executable: /home/user/myproject/.venv/bin/python (from venv)
├── Virtual Environment: /home/user/myproject/.venv (detected)
├── Test Folder: tests (default)
├── Log Level: INFO (default)
└── Log File: /home/user/myproject/logs/mcp_code_checker_20241201_143022.log (auto-generated)

Would add server 'test-checker' to claude-desktop configuration:
{
  "command": "/home/user/myproject/.venv/bin/python",
  "args": [
    "/home/user/myproject/src/main.py",
    "--project-dir", "/home/user/myproject",
    "--test-folder", "tests",
    "--log-level", "INFO"
  ],
  "env": {
    "PYTHONPATH": "/home/user/myproject"
  },
  "_managed_by": "mcp-config-managed",
  "_server_type": "mcp-code-checker"
}

Configuration file: /home/user/.config/claude/claude_desktop_config.json
Backup would be created: /home/user/.config/claude/claude_desktop_config.backup_20241201_143022.json

✅ Configuration is valid. Run without --dry-run to apply changes.
```

#### Remove Command Dry-Run:
```bash
mcp-config remove "test-checker" --dry-run
```

**Output:**
```
🔍 DRY RUN: No changes will be applied

Would remove server 'test-checker' from claude-desktop configuration.

Current configuration:
├── Server Type: mcp-code-checker
├── Project Directory: /home/user/myproject
└── Managed by: mcp-config

Other servers will be preserved:
├── calculator (external)
└── weather-api (external)

Configuration file: /home/user/.config/claude/claude_desktop_config.json
Backup would be created: /home/user/.config/claude/claude_desktop_config.backup_20241201_143022.json

✅ Removal is safe. Run without --dry-run to apply changes.
```

### 3. Enhanced Output Formatting

Implement consistent, user-friendly output formatting across all commands:

#### Design Principles:
1. **Visual Hierarchy:** Use symbols (✓, ✗, ⚠, 🔍, ✅, ❌) for status
2. **Tree Structure:** Use └── ├── for hierarchical data
3. **Color Coding:** Green for success, red for errors, yellow for warnings (if terminal supports)
4. **Actionable Messages:** Always provide next steps for errors
5. **Consistent Formatting:** Same style across all commands

#### List Command Enhanced Output:
```bash
mcp-config list --detailed
```

**Output:**
```
MCP Servers Configuration (claude-desktop)

Managed Servers (2):
├── my-checker (mcp-code-checker) ✅
│   ├── Project: /home/user/myproject
│   ├── Python: /home/user/myproject/.venv/bin/python (venv)
│   ├── Test Folder: tests
│   ├── Log Level: INFO
│   └── Status: Ready
└── debug-checker (mcp-code-checker) ⚠
    ├── Project: /home/user/project2
    ├── Python: /usr/bin/python3.11
    ├── Test Folder: custom-tests
    ├── Log Level: DEBUG
    ├── Keep Temp Files: Yes
    ├── Custom Log File: ./logs/debug.log
    └── Status: Warning - Log directory not found

External Servers (2):
├── calculator (external) - not managed by mcp-config
└── filesystem (external) - not managed by mcp-config

Configuration: /home/user/.config/claude/claude_desktop_config.json
Last Modified: 2024-12-01 14:30:22

Use 'mcp-config validate <server-name>' to check specific configurations.
```

#### Verbose Mode:
Add `--verbose` flag to show additional details:
- Auto-detection process
- File system operations
- Configuration parsing details
- Validation steps

### 4. Error Handling and User Feedback

Implement comprehensive error handling with actionable messages:

#### Error Categories:
1. **Configuration Errors:** Missing files, invalid JSON, permission issues
2. **Parameter Errors:** Invalid values, missing required parameters, type mismatches
3. **System Errors:** Missing executables, path issues, permission problems
4. **User Errors:** Non-existent servers, invalid commands, conflicting options

#### Error Message Format:
```
❌ Error: <Clear description of what went wrong>

Details:
<Specific technical details>

Suggestions:
• <Actionable step 1>
• <Actionable step 2>
• <Reference to help or documentation>
```

#### Examples:
```bash
# Missing required parameter
❌ Error: Required parameter --project-dir not specified

The --project-dir parameter is required for mcp-code-checker setup.

Suggestions:
• Run: mcp-config setup mcp-code-checker "my-checker" --project-dir .
• Use current directory: --project-dir .
• Specify project path: --project-dir /path/to/project

# Invalid server name for removal
❌ Error: Server 'nonexistent-server' not found in claude-desktop configuration

Available managed servers:
• my-checker (mcp-code-checker)
• debug-checker (mcp-code-checker)

Suggestions:
• List servers: mcp-config list
• Check server name spelling
• Use exact server name from list output

# Permission error
❌ Error: Cannot write to configuration file

Details:
Permission denied: /home/user/.config/claude/claude_desktop_config.json

Suggestions:
• Check file permissions: ls -la /home/user/.config/claude/
• Fix permissions: chmod 644 /home/user/.config/claude/claude_desktop_config.json
• Run with proper user permissions
```

## Implementation Tasks

### Task 1: Validate Command Implementation (8 hours)
1. Create validation framework with pluggable checks
2. Implement all validation checks for MCP Code Checker
3. Add comprehensive error reporting and suggestions
4. Write validation tests for various scenarios

**Expected Files:**
- `src/config/validation.py` (enhanced)
- `src/config/main.py` (updated with validate command)
- `tests/test_config/test_validation.py` (enhanced)

### Task 2: Dry-Run Support (6 hours)
1. Add dry-run logic to setup and remove commands
2. Implement configuration preview functionality
3. Add dry-run output formatting
4. Write tests for dry-run behavior

**Expected Files:**
- `src/config/main.py` (updated)
- `src/config/clients.py` (updated with dry-run methods)
- `tests/test_config/test_dry_run.py` (new)

### Task 3: Output Formatting System (6 hours)
1. Create output formatting utilities
2. Implement consistent styling across commands
3. Add color support (with fallback for non-color terminals)
4. Update all commands to use new formatting

**Expected Files:**
- `src/config/output.py` (new)
- `src/config/main.py` (updated)
- `tests/test_config/test_output.py` (new)

### Task 4: Enhanced Error Handling (4 hours)
1. Create error handling framework
2. Implement actionable error messages
3. Add error categorization and suggestions
4. Write error handling tests

**Expected Files:**
- `src/config/errors.py` (new)
- All command modules (updated with better error handling)
- `tests/test_config/test_errors.py` (new)

## Test Requirements

### Unit Tests
1. **Validation Tests:**
   - All validation checks work correctly
   - Proper error detection and reporting
   - Suggestion generation for common issues

2. **Dry-Run Tests:**
   - No actual changes made during dry-run
   - Accurate preview of changes
   - Proper dry-run output formatting

3. **Output Formatting Tests:**
   - Consistent formatting across commands
   - Proper tree structure rendering
   - Color support with fallbacks

4. **Error Handling Tests:**
   - All error categories properly handled
   - Actionable error messages generated
   - Graceful degradation for unexpected errors

### Integration Tests
1. **End-to-End Validation:**
   - Validate real server configurations
   - Test with various project structures
   - Handle edge cases gracefully

2. **Command Integration:**
   - All commands work with new output formatting
   - Dry-run mode works across all commands
   - Error handling consistent across commands

## Acceptance Criteria

### Must Have:
1. `mcp-config validate <server-name>` works with comprehensive checks
2. `--dry-run` flag works for setup and remove commands
3. All output uses consistent, user-friendly formatting
4. Error messages provide actionable suggestions
5. Commands gracefully handle all error conditions

### Should Have:
1. Verbose mode provides additional debugging information
2. Color output when terminal supports it
3. Progress indicators for long-running operations
4. Context-aware help and suggestions

### Test Coverage:
- Minimum 90% code coverage for new modules
- All validation scenarios tested
- All dry-run scenarios tested
- All error conditions tested

## Example Usage After Implementation

```bash
# Validate existing configuration
mcp-config validate "my-checker"
# Shows detailed validation results with ✓/✗ indicators

# Preview changes before applying
mcp-config setup mcp-code-checker "new-checker" --project-dir . --dry-run
# Shows exactly what would be changed without applying

# Detailed listing with status indicators
mcp-config list --detailed
# Shows all servers with visual status indicators

# Verbose output for debugging
mcp-config setup mcp-code-checker "debug-checker" --project-dir . --verbose
# Shows auto-detection process and detailed steps
```

## Deliverables

1. **Validate Command:** Comprehensive configuration validation with clear feedback
2. **Dry-Run Support:** Safe preview mode for all destructive operations  
3. **Enhanced Output:** Consistent, user-friendly formatting with visual indicators
4. **Error Handling:** Actionable error messages with specific suggestions
5. **Tests:** Complete test coverage for all new functionality
6. **Documentation:** Updated help text and usage examples

This milestone transforms the basic configuration tool into a polished, user-friendly CLI that provides excellent feedback and prevents user errors through validation and preview capabilities.
