# Step 9: Update Troubleshooting Guide

## Objective
Update the Troubleshooting guide (docs/config/TROUBLESHOOTING.md) to include issues related to the CLI command and installation modes.

## File to Modify
- `docs/config/TROUBLESHOOTING.md` - Add new troubleshooting scenarios

## Implementation Instructions

### 1. Add New Section for Command Issues

Add this section at the beginning of the troubleshooting guide:

```markdown
## CLI Command Issues

### Issue: "mcp-code-checker: command not found"

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

### Issue: "Multiple installation modes detected"

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
```

### 2. Update Existing "Server Not Found" Section

Add information about installation modes to the existing troubleshooting:

```markdown
### Issue: "Server 'mcp-code-checker' not found"

**Additional checks for mcp-code-checker:**

1. **Verify installation mode:**
   ```bash
   # Check if CLI command exists
   which mcp-code-checker || echo "CLI command not installed"
   
   # Check if package is installed
   python -c "import mcp_code_checker" || echo "Package not installed"
   
   # Check if in development mode
   ls src/main.py || echo "Not in development directory"
   ```

2. **Install based on your needs:**
   ```bash
   # For production use
   pip install mcp-code-checker
   
   # For development
   git clone <repository>
   cd mcp-code-checker
   pip install -e .
   ```
```

### 3. Add Installation Mode Validation Section

```markdown
## Installation Mode Validation

### Understanding Installation Modes

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

### Quick Diagnostic Commands

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
```

### 4. Update Platform-Specific Issues

Add Windows-specific command issues:

```markdown
### Windows-Specific Issues

#### PowerShell Execution Policy
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

#### Windows PATH Issues
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
```

### 5. Add Virtual Environment Section

```markdown
## Virtual Environment Issues

### CLI Command in Virtual Environments

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
```

### 6. Add Fallback Strategies Section

```markdown
## Fallback Strategies

If you can't get the CLI command working, you have several fallback options:

### Option 1: Use Python Module
```bash
# Instead of: mcp-code-checker --project-dir .
python -m mcp_code_checker --project-dir .
```

### Option 2: Use Direct Script (Development)
```bash
cd /path/to/mcp-code-checker
python src/main.py --project-dir /path/to/project
```

### Option 3: Manual Configuration
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

### Option 4: Create Custom Wrapper
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
```

## Validation

After making changes:
1. All common CLI command issues should be covered
2. Installation mode diagnostics should be clear
3. Platform-specific issues should have solutions
4. Fallback strategies should be documented

## Next Step
Proceed to Step 10 to update the installation documentation.
