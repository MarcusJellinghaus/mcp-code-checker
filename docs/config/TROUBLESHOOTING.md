# MCP Configuration Helper - Troubleshooting Guide

## Common Issues

### CLI Command Issues

#### "mcp-code-checker: command not found"

**Symptoms:**
- Running `mcp-code-checker` returns "command not found"
- Config tool falls back to Python module mode

**Solutions:**

1. **Check if package is installed:**
   ```bash
   pip list | grep mcp-code-checker
   ```

2. **Reinstall with CLI command:**
   ```bash
   pip uninstall mcp-code-checker
   pip install mcp-code-checker
   # Or for development:
   pip install -e .
   ```

3. **Verify command installation:**
   ```bash
   # Unix/macOS
   which mcp-code-checker
   
   # Windows
   where mcp-code-checker
   ```

4. **Check PATH environment variable:**
   ```bash
   # Ensure pip's scripts directory is in PATH
   python -m site --user-base
   # Add the 'Scripts' (Windows) or 'bin' (Unix) subdirectory to PATH
   ```

5. **Use Python module fallback:**
   ```bash
   python -m mcp_code_checker --project-dir /path/to/project
   ```

#### "Multiple installation modes detected"

**Symptoms:**
- Both CLI command and development files exist
- Confusion about which version is being used

**Solution:**
```bash
# Check what's being used
mcp-config validate "your-server" --verbose

# Clean up duplicate installations
pip uninstall mcp-code-checker
rm -rf src/__pycache__ *.egg-info  # Clean development files
pip install mcp-code-checker  # Fresh install
```

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

### Installation Mode Validation

#### Understanding Installation Modes

MCP Code Checker can be installed in three modes. Use validation to check:

```bash
mcp-config validate "your-server-name"
```

**Output explanations:**

1. **"✓ CLI command 'mcp-code-checker' is available"**
   - Best mode - using installed command
   - Config uses: `"command": "mcp-code-checker"`

2. **"⚠ Package installed but CLI command not found"**
   - Package is installed but command isn't available
   - Fix: `pip install --force-reinstall mcp-code-checker`

3. **"ℹ Running in development mode"**
   - Using source files directly
   - Make sure you're in the correct directory

4. **"✗ MCP Code Checker not properly installed"**
   - Not installed at all
   - Install using: `pip install mcp-code-checker`

#### Quick Diagnostic Commands

```bash
# Full diagnostic
python -c "
import shutil
import importlib.util
from pathlib import Path

print('CLI command:', 'Yes' if shutil.which('mcp-code-checker') else 'No')
try:
    importlib.util.find_spec('mcp_code_checker')
    print('Package installed: Yes')
except:
    print('Package installed: No')
print('Development mode:', 'Yes' if Path('src/main.py').exists() else 'No')
"
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

#### Windows-Specific CLI Command Issues

##### PowerShell Execution Policy
If the `mcp-code-checker` command doesn't work in PowerShell:

```powershell
# Check execution policy
Get-ExecutionPolicy

# If restricted, you can:
# Option 1: Use cmd.exe instead
cmd
mcp-code-checker --help

# Option 2: Use Python module directly
python -m mcp_code_checker --help

# Option 3: Set execution policy (requires admin)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

##### Windows PATH Issues
```batch
REM Check if Python Scripts is in PATH
echo %PATH%

REM Find Python Scripts directory
python -c "import site; print(site.USER_BASE)"

REM Add to PATH (replace with your actual path)
setx PATH "%PATH%;C:\Users\YourName\AppData\Roaming\Python\Python311\Scripts"

REM Restart terminal and try again
mcp-code-checker --help
```

### Virtual Environment Issues

#### CLI Command in Virtual Environments

**Issue:** Command not available in activated venv

**Solution:**
```bash
# Activate your virtual environment
source .venv/bin/activate  # Unix/macOS
# or
.venv\Scripts\activate  # Windows

# Install in the venv
pip install mcp-code-checker

# Verify it's using venv version
which mcp-code-checker  # Should show .venv/... path

# Configure with venv
mcp-config setup mcp-code-checker "project" \
  --project-dir . \
  --venv-path .venv
```

**Issue:** Config uses wrong Python after venv deactivation

**Solution:**
The generated configuration captures the Python path, so it works even when venv is not activated. If you need to update:

```bash
# Reconfigure with new Python
mcp-config remove "project"
mcp-config setup mcp-code-checker "project" \
  --project-dir . \
  --python-executable /path/to/venv/bin/python
```

### Fallback Strategies

If you can't get the CLI command working, you have several fallback options:

#### Option 1: Use Python Module
```bash
# Instead of: mcp-code-checker --project-dir .
python -m mcp_code_checker --project-dir .
```

#### Option 2: Use Direct Script (Development)
```bash
cd /path/to/mcp-code-checker
python src/main.py --project-dir /path/to/project
```

#### Option 3: Manual Configuration
Edit your client config directly:

```json
{
  "command": "python",
  "args": [
    "-m",
    "mcp_code_checker",
    "--project-dir",
    "/path/to/project"
  ]
}
```

#### Option 4: Create Custom Wrapper
Create a batch/shell script:

**Windows (mcp-check.bat):**
```batch
@echo off
python -m mcp_code_checker %*
```

**Unix (mcp-check.sh):**
```bash
#!/bin/bash
python -m mcp_code_checker "$@"
```

Then use this wrapper in your configuration.

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

# Try CLI command first
mcp-code-checker --help
mcp-code-checker --project-dir . --log-level DEBUG

# Fallback to Python module
python -m mcp_code_checker --help
python -m mcp_code_checker --project-dir . --log-level DEBUG

# Or development mode
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

## VSCode Issues

### VSCode Version Requirements

**Problem:** MCP servers not loading in VSCode

**Solution:** Ensure VSCode 1.102 or later is installed:
1. Check version: Help → About
2. Update if needed: Help → Check for Updates

### GitHub Copilot Requirements

**Problem:** MCP servers not available in Copilot

**Solution:** 
1. Ensure GitHub Copilot extension is installed
2. For organizations: Check that "MCP servers in Copilot" policy is enabled
3. Sign in to GitHub Copilot

### Configuration Not Loading

**Problem:** VSCode doesn't recognize MCP configuration

**Solutions:**
1. Restart VSCode after configuration changes
2. Check file location:
   - Workspace: `.vscode/mcp.json`
   - User: Check correct path for your OS
3. Validate JSON syntax:
   ```bash
   mcp-config validate --client vscode
   ```

### Workspace vs User Profile

**Problem:** Unsure which configuration to use

**Guidelines:**
- **Workspace** (`.vscode/mcp.json`):
  - Team projects
  - Project-specific settings
  - Shareable via git
- **User Profile**:
  - Personal projects
  - Global settings
  - Not shared

### Path Resolution Issues

**Problem:** Server fails to start with path errors

**Solutions:**
1. Use relative paths for workspace configs:
   ```json
   "args": ["--project-dir", "."]
   ```
2. Use absolute paths for user configs:
   ```json
   "args": ["--project-dir", "/home/user/projects"]
   ```

### Multiple Configurations

**Problem:** Both workspace and user configs exist

**Note:** Workspace configuration takes precedence over user profile configuration.

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
