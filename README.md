# MCP Code Checker

A Model Context Protocol (MCP) server providing code quality checking operations. This server offers a API for performing code quality checks within a specified project directory, following the MCP protocol design.

## Overview

This MCP server enables AI assistants like Claude (via Claude Desktop), VSCode with GitHub Copilot, or other MCP-compatible systems to perform quality checks on your code. With these capabilities, AI assistants can:

- Run pylint checks to identify code quality issues
- Execute pytest to identify failing tests
- Run mypy for type checking
- Generate smart prompts for LLMs to explain issues and suggest fixes
- Combine multiple checks for comprehensive code quality analysis

All operations are securely contained within your specified project directory, giving you control while enabling powerful AI collaboration for code quality improvement.

By connecting your AI assistant to your code checking tools, you can transform your debugging workflow - describe what you need in natural language and let the AI identify and fix issues directly in your project files.

## Documentation

- [**User Guide**](docs/config/USER_GUIDE.md) - Complete command reference and setup instructions
- [**Troubleshooting**](docs/config/TROUBLESHOOTING.md) - Common issues and solutions

## Features

- `run_pylint_check`: Run pylint on the project code and generate smart prompts for LLMs
- `run_pytest_check`: Run pytest on the project code and generate smart prompts for LLMs
- `run_mypy_check`: Run mypy type checking on the project code
- `run_all_checks`: Run all code checks (pylint, pytest, and mypy) and generate combined results

### Pylint Parameters

The pylint tools expose the following parameters for customization:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `categories` | list | ['error', 'fatal'] | List of pylint message categories to include |
| `disable_codes` | list | None | List of pylint error codes to disable during analysis |
| `target_directories` | list | ["src", "tests"] | List of directories to analyze relative to project_dir |

**Target Directories Examples:**
- `["src"]` - Analyze only source code directory
- `["src", "tests"]` - Analyze both source and test directories (default)
- `["mypackage", "tests"]` - For projects with different package structures
- `["lib", "scripts", "tests"]` - For complex multi-directory projects
- `["."]` - Analyze entire project directory (may be slow for large projects)

### Pytest Parameters

Both `run_pytest_check` and `run_all_checks` expose the following parameters for customization:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `markers` | list | None | Optional list of pytest markers to filter tests |
| `verbosity` | integer | 2 | Pytest verbosity level (0-3) |
| `extra_args` | list | None | Optional list of additional pytest arguments |
| `env_vars` | dictionary | None | Optional environment variables for the subprocess |

### Mypy Parameters

The mypy tools expose the following parameters for customization:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strict` | boolean | True | Use strict mode settings |
| `disable_error_codes` | list | None | List of mypy error codes to ignore |
| `target_directories` | list | ["src", "tests"] | List of directories to check relative to project_dir |
| `follow_imports` | string | 'normal' | How to handle imports during type checking |

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

**Quick install:**

```bash
# Install from GitHub (recommended)
pip install git+https://github.com/MarcusJellinghaus/mcp-code-checker.git

# Verify installation
mcp-code-checker --help
```

**Development install:**

```bash
# Clone and install for development
git clone https://github.com/MarcusJellinghaus/mcp-code-checker.git
cd mcp-code-checker
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
mcp-code-checker --help
```

## Using as a Dependency

### In requirements.txt

Add this line to your `requirements.txt`:

```txt
mcp-code-checker @ git+https://github.com/MarcusJellinghaus/mcp-code-checker.git
```

### In pyproject.toml

Add to your project dependencies:

```toml
[project]
dependencies = [
    "mcp-code-checker @ git+https://github.com/MarcusJellinghaus/mcp-code-checker.git",
    # ... other dependencies
]

# Or as an optional dependency
[project.optional-dependencies]
dev = [
    "mcp-code-checker @ git+https://github.com/MarcusJellinghaus/mcp-code-checker.git",
]
```

### Installation Commands

After adding to requirements.txt or pyproject.toml:

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Install from pyproject.toml
pip install .
# Or with optional dependencies
pip install ".[dev]"
```

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

## Project Structure Support

The server automatically detects and analyzes Python code in standard project structures:

**Default Analysis:**
- `src/` directory (if present) - Main source code
- `tests/` directory (if present) - Test files

**Custom Project Structures:**
Use the `target_directories` parameter to specify different directories:

```python
# For a package-based structure
target_directories = ["mypackage", "tests"]

# For a simple project with code in root
target_directories = ["."]

# For complex multi-module projects
target_directories = ["module1", "module2", "shared", "tests"]
```

## Structured Logging

The server provides comprehensive logging capabilities:

- **Standard human-readable logs** to console for development/debugging
- **Structured JSON logs** to file for analysis and monitoring
- **Function call tracking** with parameters, timing, and results
- **Automatic error context capture** with full stack traces
- **Configurable log levels** (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Default timestamped log files** in `project_dir/logs/mcp_code_checker_{timestamp}.log`

Example structured log entries:
```json
{
  "timestamp": "2025-08-05 14:30:15",
  "level": "info",
  "event": "Starting pylint check",
  "project_dir": "/path/to/project",
  "disable_codes": ["C0114", "C0116"],
  "target_directories": ["src", "tests"]
}
```

Use `--console-only` to disable file logging for simple development scenarios.

## Using with Claude Desktop App

To enable Claude to use this code checking server:

1. **Install MCP Code Checker:**
   ```bash
   pip install git+https://github.com/MarcusJellinghaus/mcp-code-checker.git
   # Or from source: pip install -e .
   ```

2. **Configure Claude Desktop manually:**
   
   Edit the configuration file for your platform:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/claude/claude_desktop_config.json`

   **Example configuration (when installed as package):**
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

   **Example configuration (development mode):**
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

3. **Restart Claude Desktop** to apply changes

## Using with VSCode

VSCode 1.102+ supports MCP servers natively. Configure manually:

### Workspace Configuration (Recommended for Teams)

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

**For development mode:**
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

### User Profile Configuration (Personal Setup)

Create or edit the user configuration file:
- **Windows**: `%APPDATA%\Code\User\mcp.json`
- **macOS**: `~/Library/Application Support/Code/User/mcp.json`  
- **Linux**: `~/.config/Code/User/mcp.json`

```json
{
  "servers": {
    "code-checker-global": {
      "command": "mcp-code-checker",
      "args": ["--project-dir", "/path/to/your/projects"]
    }
  }
}
```

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

## Available Tools

The server exposes the following MCP tools:

### Run Pylint Check
- Runs pylint on the project code and generates smart prompts for LLMs
- Returns: A string containing either pylint results or a prompt for an LLM to interpret
- Helps identify code quality issues, style problems, and potential bugs
- Customizable with parameters for disabling specific pylint codes and targeting specific directories
- Supports flexible project structures through `target_directories` parameter

### Run Pytest Check
- Runs pytest on the project code and generates smart prompts for LLMs
- Returns: A string containing either pytest results or a prompt for an LLM to interpret
- Identifies failing tests and provides detailed information about test failures
- Customizable with parameters for test selection, environment, and verbosity

### Run Mypy Check
- Runs mypy type checking on the project code
- Returns: A string containing mypy results or a prompt for an LLM to interpret
- Identifies type errors and provides suggestions for better type safety
- Customizable with parameters for strict mode, error code filtering, and target directories

### Run All Checks
- Runs all code checks (pylint, pytest, and mypy) and generates combined results
- Returns: A string containing results from all checks and/or LLM prompts
- Provides a comprehensive analysis of code quality in a single operation
- Supports customization parameters for all three tools, including target directories

## Security Features

- All checks are performed within the specified project directory
- Code execution is limited to the Python test files within the project
- Results are formatted for easy interpretation by both humans and LLMs
- Directory traversal protection through validation of target directories

## Development

### Setting up the development environment

```bash
# Clone the repository
git clone https://github.com/MarcusJellinghaus/mcp-code-checker.git
cd mcp-code-checker

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Unix/MacOS:
source .venv/bin/activate

# Install dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Running with MCP Dev Tools

```bash
# Set the PYTHONPATH and run the server module using mcp dev
set PYTHONPATH=. && mcp dev src/server.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

The MIT License is a permissive license that allows reuse with minimal restrictions. It permits use, copying, modification, and distribution with proper attribution.

## Links

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Filesystem Tools](https://github.com/MarcusJellinghaus/mcp_server_filesystem)
