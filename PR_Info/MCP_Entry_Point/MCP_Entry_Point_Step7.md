# Step 7: Update README.md Documentation

## Objective
Update the main README to document the new CLI command usage.

## File to Modify
- `README.md` - Update all usage examples and installation instructions

## Changes to Make

### 1. Update "Running the Server" Section

Replace the current "Running the Server" section with:

```markdown
## Running the Server

### Using the CLI Command (Recommended)
After installation, you can run the server using the `mcp-code-checker` command:

```bash
mcp-code-checker --project-dir /path/to/project [options]
```

### Using Python Module (Alternative)
You can also run the server as a Python module:

```bash
python -m mcp_code_checker --project-dir /path/to/project [options]

# Or for development (from source directory)
python -m src.main --project-dir /path/to/project [options]
```

### Available Options

- `--project-dir`: **Required**. Path to the project directory to analyze
- `--python-executable`: Optional. Path to Python interpreter for running tests
- `--venv-path`: Optional. Path to virtual environment to activate
- `--test-folder`: Optional. Test folder path relative to project (default: "tests")
- `--log-level`: Optional. Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-file`: Optional. Path for structured JSON logs
- `--console-only`: Optional. Log only to console
- `--keep-temp-files`: Optional. Keep temporary files after execution

Example with options:
```bash
mcp-code-checker \
  --project-dir /path/to/project \
  --venv-path /path/to/project/.venv \
  --log-level DEBUG
```
```

### 2. Update "Using with Claude Desktop App" Section

Update the configuration example to show both methods:

```markdown
## Using with Claude Desktop App

To enable Claude to use this code checking server:

1. Install MCP Code Checker:
   ```bash
   pip install mcp-code-checker
   # Or from source: pip install -e .
   ```

2. Configure using the helper tool (recommended):
   ```bash
   mcp-config setup mcp-code-checker "my-project" --project-dir /path/to/project
   ```

3. Or manually edit the configuration file:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/claude/claude_desktop_config.json`

   Example configuration (when installed as package):
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

   Example configuration (development mode):
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

4. Restart Claude Desktop to apply changes
```

### 3. Update "Using with VSCode" Section

```markdown
## Using with VSCode

VSCode 1.102+ supports MCP servers natively. Configure using the helper tool or manually:

### Quick Setup (Recommended)

```bash
# Install MCP Code Checker
pip install mcp-code-checker

# Configure for current workspace
mcp-config setup mcp-code-checker "my-project" --client vscode --project-dir .

# Or configure globally
mcp-config setup mcp-code-checker "global" --client vscode-user --project-dir ~/projects
```

### Manual Configuration

Create or edit `.vscode/mcp.json` in your workspace:

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

For development mode:
```json
{
  "servers": {
    "code-checker": {
      "command": "python",
      "args": ["-m", "src.main", "--project-dir", "."],
      "env": {
        "PYTHONPATH": "/path/to/mcp-code-checker"
      }
    }
  }
}
```
```

### 4. Update "Installation" Section

Add a note about the CLI command:

```markdown
## Installation

### Option 1: Install from PyPI (When Available)

```bash
pip install mcp-code-checker

# Verify installation
mcp-code-checker --help
```

### Option 2: Install from GitHub (Recommended)

```bash
# Install directly from GitHub
pip install git+https://github.com/MarcusJellinghaus/mcp-code-checker.git

# Verify installation
mcp-code-checker --help
```

### Option 3: Development Installation

```bash
# Clone and install for development
git clone https://github.com/MarcusJellinghaus/mcp-code-checker.git
cd mcp-code-checker

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode (includes CLI command)
pip install -e .
# Or with development dependencies
pip install -e ".[dev]"

# Verify installation
mcp-code-checker --help
```
```

### 5. Update "Using MCP Inspector" Section

```markdown
## Using MCP Inspector

MCP Inspector allows you to debug and test your MCP server:

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
```

## Testing the Documentation

After making these changes, verify that:
1. All code examples are correct
2. Both CLI and module methods are documented
3. Installation instructions include CLI command verification
4. Configuration examples work for both methods

## Next Step
Proceed to Step 8 to update the User Guide documentation.
