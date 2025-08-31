# Installation Guide for MCP Code Checker

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- git (for development installation)

## Installation Methods

### Method 1: Install from PyPI (When Available)

```bash
# Install the latest release
pip install mcp-code-checker

# Verify installation
mcp-code-checker --version
mcp-code-checker --help
```

### Method 2: Install from GitHub (Recommended)

```bash
# Install directly from the main branch
pip install git+https://github.com/MarcusJellinghaus/mcp-code-checker.git

# Or install a specific version/tag
pip install git+https://github.com/MarcusJellinghaus/mcp-code-checker.git@v1.0.0

# Verify installation
mcp-code-checker --help
```

### Method 3: Development Installation

For contributors or when you need to modify the code:

```bash
# Clone the repository
git clone https://github.com/MarcusJellinghaus/mcp-code-checker.git
cd mcp-code-checker

# Create a virtual environment (recommended)
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix/macOS:
source .venv/bin/activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Verify installation
mcp-code-checker --help

# Run tests to ensure everything works
pytest
```

## Post-Installation Verification

### 1. Verify CLI Command

```bash
# Check if command is available
which mcp-code-checker  # Unix/macOS
where mcp-code-checker  # Windows

# Test the command
mcp-code-checker --version
mcp-code-checker --help
```

### 2. Verify Python Module

```bash
# Test as Python module
python -m mcp_code_checker --help

# Verify import works
python -c "import mcp_code_checker; print('✓ Package imported successfully')"
```

## Installation in Virtual Environments

### Creating a Project-Specific Installation

```bash
# Navigate to your project
cd /path/to/your/project

# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate      # Windows

# Install MCP Code Checker
pip install mcp-code-checker
```

### Using with Poetry

```bash
# Add to your project
poetry add mcp-code-checker

# Or add as development dependency
poetry add --dev mcp-code-checker

# Verify in poetry shell
poetry shell
mcp-code-checker --help
```

### Using with Pipenv

```bash
# Add to Pipfile
pipenv install mcp-code-checker

# Or as dev dependency
pipenv install --dev mcp-code-checker

# Verify in pipenv shell
pipenv shell
mcp-code-checker --help
```

## Platform-Specific Instructions

### Windows

1. **Command Prompt (cmd.exe)**
   ```batch
   pip install mcp-code-checker
   mcp-code-checker --help
   ```

2. **PowerShell**
   ```powershell
   pip install mcp-code-checker
   mcp-code-checker --help
   
   # If you get execution policy errors:
   python -m mcp_code_checker --help
   ```

3. **Adding to PATH**
   If the command isn't found after installation:
   ```batch
   REM Find Python Scripts directory
   python -c "import site; print(site.USER_BASE)"
   
   REM Add Scripts folder to PATH
   REM Replace USERNAME with your actual username
   setx PATH "%PATH%;C:\Users\USERNAME\AppData\Roaming\Python\Python311\Scripts"
   
   REM Restart terminal and try again
   ```

### macOS

1. **With Homebrew Python**
   ```bash
   # Ensure you're using Homebrew Python
   which python3
   # Should show: /opt/homebrew/bin/python3 or /usr/local/bin/python3
   
   python3 -m pip install mcp-code-checker
   ```

2. **With System Python**
   ```bash
   # Use --user flag to avoid permission issues
   pip install --user mcp-code-checker
   
   # Add user bin to PATH if needed
   export PATH="$HOME/.local/bin:$PATH"
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   ```

### Linux

1. **Ubuntu/Debian**
   ```bash
   # Install pip if needed
   sudo apt update
   sudo apt install python3-pip
   
   # Install MCP Code Checker
   pip install --user mcp-code-checker
   
   # Add to PATH if needed
   export PATH="$HOME/.local/bin:$PATH"
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   ```

2. **Fedora/RHEL**
   ```bash
   # Install pip if needed
   sudo dnf install python3-pip
   
   # Install MCP Code Checker
   pip install --user mcp-code-checker
   ```

## Configuration

After installation, you need to configure MCP Code Checker for your preferred client.

### Claude Desktop Configuration

1. Locate your Claude Desktop configuration file:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/claude/claude_desktop_config.json`

2. Add the MCP Code Checker configuration:

   ```json
   {
     "mcpServers": {
       "code_checker": {
         "command": "mcp-code-checker",
         "args": [
           "--project-dir",
           "/path/to/your/project",
           "--log-level",
           "INFO"
         ]
       }
     }
   }
   ```

   **For development mode:**
   ```json
   {
     "mcpServers": {
       "code_checker": {
         "command": "python",
         "args": [
           "-m",
           "src.main",
           "--project-dir",
           "/path/to/your/project"
         ],
         "env": {
           "PYTHONPATH": "/path/to/mcp-code-checker/"
         }
       }
     }
   }
   ```

3. Restart Claude Desktop to apply the changes.

### VSCode Configuration

VSCode 1.102+ supports MCP servers natively. Create or edit the configuration file:

**For workspace configuration (.vscode/mcp.json in your project):**
```json
{
  "servers": {
    "code-checker": {
      "command": "mcp-code-checker",
      "args": ["--project-dir", "."]
    }
  }
}
```

**For user profile configuration:**
- **Windows**: `%APPDATA%\Code\User\mcp.json`
- **macOS**: `~/Library/Application Support/Code/User/mcp.json`
- **Linux**: `~/.config/Code/User/mcp.json`

```json
{
  "servers": {
    "code-checker": {
      "command": "mcp-code-checker",
      "args": ["--project-dir", "/path/to/your/projects"]
    }
  }
}
```

## Troubleshooting Installation

### Command Not Found

If `mcp-code-checker` command is not found after installation:

1. **Check installation location:**
   ```bash
   pip show mcp-code-checker
   ```

2. **Check if scripts were installed:**
   ```bash
   ls $(python -m site --user-base)/bin/  # Unix/macOS
   dir $(python -m site --user-base)\Scripts\  # Windows
   ```

3. **Use Python module as fallback:**
   ```bash
   python -m mcp_code_checker --help
   ```

### Permission Errors

If you get permission errors during installation:

```bash
# Option 1: Use --user flag
pip install --user mcp-code-checker

# Option 2: Use virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install mcp-code-checker

# Option 3: Use pipx for isolated installation
pipx install mcp-code-checker
```

### Import Errors

If you get import errors when running the command:

```bash
# Reinstall with all dependencies
pip install --force-reinstall mcp-code-checker

# Check for conflicting packages
pip list | grep mcp

# In development mode, ensure you're in the right directory
cd /path/to/mcp-code-checker
pip install -e .
```

## Testing the Installation

You can test the MCP server using the MCP Inspector:

### For Installed Package
```bash
npx @modelcontextprotocol/inspector mcp-code-checker --project-dir /path/to/project
```

### For Development Mode
```bash
npx @modelcontextprotocol/inspector \
  python \
  -m \
  src.main \
  --project-dir /path/to/project
```

## Uninstallation

To remove MCP Code Checker:

```bash
# Uninstall the package
pip uninstall mcp-code-checker

# Remove configuration files manually if needed
# Claude Desktop: Edit claude_desktop_config.json
# VSCode: Delete .vscode/mcp.json or edit user mcp.json

# Clean up cache (optional)
pip cache purge
```

## Getting Help

If you encounter issues:

1. Check the project's GitHub Issues: https://github.com/MarcusJellinghaus/mcp-code-checker/issues
2. Run the command with `--help` to see all available options
3. Use `--log-level DEBUG` for more detailed logging
4. Ask for help with detailed error messages and system information
