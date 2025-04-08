# MCP Code Checker - Cline Integration Guide

This guide explains how to integrate the MCP Code Checker with Cline in VS Code to enable code quality checking capabilities.

## Overview

The MCP Code Checker provides tools for analyzing Python code quality using pylint and pytest. When integrated with Cline in VS Code, it allows you to:

- Run code quality checks directly from Cline
- Get detailed feedback on code issues
- Receive suggestions for fixing problems
- Analyze test failures and get guidance on resolving them

## Installation

### Prerequisites

- Python 3.11 or higher
- VS Code with the Cline extension installed
- MCP Code Checker repository

### Step 1: Clone the Repository

```bash
git clone https://github.com/MarcusJellinghaus/mcp-code-checker.git
cd mcp-code-checker
```

### Step 2: Install Dependencies

```bash
# Create and activate a virtual environment (recommended)
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install the package and dependencies
pip install -e .
```

### Step 3: Configure for Cline

The MCP Code Checker includes a setup script that automatically configures it for use with Cline:

```bash
# Run the setup script from the project root directory
python cline/setup_for_cline.py --project-dir "C:\path\to\your\project" --preset standard
```

Options:

- `--project-dir`: Path to the project directory you want to analyze (defaults to current directory)
- `--preset`: Configuration preset to use (choices: strict, standard, minimal, debug)
- `--server-name`: Name to use for the MCP server in the configuration (default: code_checker)

### Step 4: Restart VS Code

After running the setup script, restart VS Code to apply the changes.

## Using with Cline

Once configured, you can use the MCP Code Checker with Cline by asking it to perform code quality checks. Here are some example prompts:

### Example Prompts

#### Run a Pylint Check

```
Can you check my code for quality issues using pylint?
```

#### Run a Pytest Check

```
Can you run my tests and tell me if there are any failures?
```

#### Run All Checks

```
Can you perform a complete code quality analysis on my project?
```

### Understanding the Results

The MCP Code Checker provides detailed information about code quality issues and test failures. The results include:

- **Issue Type**: The type of issue detected (e.g., error, warning, convention)
- **Location**: The file and line number where the issue was found
- **Description**: A description of the issue
- **Suggestion**: A suggestion for how to fix the issue

For test failures, the results include:

- **Test Name**: The name of the failing test
- **Error Message**: The error message from the test failure
- **Traceback**: The traceback showing where the failure occurred
- **Suggestion**: A suggestion for how to fix the test

## Configuration Presets

The MCP Code Checker supports several configuration presets:

- **strict**: Checks for all issues (convention, refactor, warning, error, fatal)
- **standard**: Checks for warnings and errors (warning, error, fatal)
- **minimal**: Checks for errors only (error, fatal)
- **debug**: Checks for errors with verbose output and keeps temporary files (error, fatal, verbosity=3)

## Advanced Configuration

### Customizing the MCP Server Configuration

The setup script creates a configuration file at:

- Windows: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`
- macOS: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- Linux: `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

You can manually edit this file to customize the configuration further.

### Available Tools

The MCP Code Checker provides the following tools:

#### run_pylint_check

Runs pylint on the project code and generates smart prompts for LLMs.

Parameters:

- `disable_codes`: Optional list of pylint error codes to disable during analysis

#### run_pytest_check

Runs pytest on the project code and generates smart prompts for LLMs.

Parameters:

- `markers`: Optional list of pytest markers to filter tests
- `verbosity`: Integer for pytest verbosity level (0-3)
- `extra_args`: Optional list of additional pytest arguments
- `env_vars`: Optional dictionary of environment variables for the subprocess

#### run_all_checks

Runs all code checks (pylint and pytest) and generates combined results.

Parameters:

- All parameters from run_pylint_check and run_pytest_check
- `categories`: Optional set of pylint message categories to include

## Troubleshooting

### Common Issues

#### MCP Server Not Connected

If Cline reports that the MCP server is not connected:

1. Check that VS Code has been restarted after running the setup script
2. Verify that the configuration file exists and contains the correct paths
3. Check the VS Code logs for any error messages

#### Python Environment Issues

If the MCP server fails to start due to Python environment issues:

1. Ensure that the Python executable path in the configuration is correct
2. Verify that all dependencies are installed
3. Check that the PYTHONPATH environment variable is set correctly in the configuration file. It should be set to "." to ensure the server can find the necessary modules

> **Note**: The PYTHONPATH setting is critical for the MCP Code Checker to work properly. The setup script now automatically sets this to "." which allows the server to find the necessary modules regardless of where the project is located.

### Logs

Check the VS Code logs for more information about any issues:

- Windows: `%APPDATA%\Code\logs`
- macOS: `~/Library/Application Support/Code/logs`
- Linux: `~/.config/Code/logs`

## Example Workflow

1. Open your Python project in VS Code
2. Configure the MCP Code Checker for your project using the setup script
3. Restart VS Code
4. Open Cline and ask it to check your code quality
5. Review the results and make the suggested improvements
6. Run the checks again to verify that the issues have been resolved

## Additional Resources

- [MCP Code Checker Repository](https://github.com/MarcusJellinghaus/mcp-code-checker)
- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Cline Documentation](https://cline.ai/docs)
