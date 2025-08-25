# Help Command Documentation

## Overview

The `help` command provides detailed documentation for MCP server parameters, making it easier for users to understand what each parameter does, which ones are required, and how to use them effectively.

## Features

### 1. **Comprehensive Parameter Documentation**
- Detailed descriptions for each parameter
- Clear indication of required vs optional parameters
- Auto-detection information for applicable parameters
- Default values and valid choices

### 2. **Multiple Help Modes**
- **Standard Help**: Shows all parameters with descriptions
- **Verbose Help**: Includes examples, auto-detection details, and extended explanations
- **Quick Reference**: Compact cheat sheet with common usage patterns
- **Parameter-Specific Help**: Deep dive into a single parameter

### 3. **Smart Parameter Grouping**
Parameters are organized into logical categories:
- **Required Parameters**: Must be provided
- **Auto-Detected Parameters**: Will be automatically discovered if not specified
- **Optional Parameters**: Can be omitted, have sensible defaults

## Usage

### Basic Help
Show all parameters for a server type:
```bash
mcp-config help mcp-code-checker
```

### Verbose Help
Get extended documentation with examples:
```bash
mcp-config help mcp-code-checker --verbose
# or
mcp-config help mcp-code-checker -v
```

### Quick Reference
Display a compact cheat sheet:
```bash
mcp-config help mcp-code-checker --quick
# or
mcp-config help mcp-code-checker -q
```

### Parameter-Specific Help
Get detailed information about a single parameter:
```bash
mcp-config help mcp-code-checker --parameter project-dir
# or
mcp-config help mcp-code-checker -p project-dir
```

### All Servers
Show help for all available server types:
```bash
mcp-config help
```

## Output Examples

### Standard Help Output
```
MCP Code Checker (mcp-code-checker)
====================================

A comprehensive code checking server that runs pylint, pytest,
and mypy on your Python projects. Provides intelligent prompts
for LLMs to help fix issues found during code analysis.

Main module: src/main.py

REQUIRED PARAMETERS:
--------------------
  --project-dir <PATH> [REQUIRED]
      Base directory for code checking operations (required).

AUTO-DETECTED PARAMETERS (optional):
-------------------------------------
These parameters will be automatically detected from your project
if not explicitly specified.

  --python-executable <PATH> [AUTO-DETECTED]
      Path to Python interpreter to use for running tests.
      If not specified, auto-detects from project or uses current interpreter.

  --venv-path <PATH> [AUTO-DETECTED]
      Path to virtual environment to activate for running tests.
      Auto-detects common venv patterns (.venv, venv, env) if not specified.

OPTIONAL PARAMETERS:
--------------------
  --test-folder <STRING> [DEFAULT: tests]
      Path to the test folder (relative to project_dir).
      Defaults to 'tests'.

  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL} [DEFAULT: INFO]
      Set logging level (default: INFO).

[... more parameters ...]
```

### Quick Reference Output
```
QUICK REFERENCE: MCP Code Checker
==================================

Required: --project-dir

Common Usage Patterns:
----------------------

1. Minimal (auto-detects Python environment):
   mcp-config setup mcp-code-checker my-server --project-dir .

2. With virtual environment:
   mcp-config setup mcp-code-checker my-server \
     --project-dir . --venv-path .venv

3. Debug mode:
   mcp-config setup mcp-code-checker my-server \
     --project-dir . --log-level DEBUG --keep-temp-files

Parameter Cheat Sheet:
---------------------
 * --project-dir <path> - Base directory for code checking operations
 ° --python-executable <path> - Path to Python interpreter to use for running
 ° --venv-path <path> - Path to virtual environment to activate for
   --test-folder <path> - Path to the test folder (relative to project_dir)
   --keep-temp-files (flag) - Keep temporary files after test execution
   --log-level [DEBUG/INFO/WARNING/ERROR/CRITICAL] - Set logging level
 ° --log-file <path> - Path for structured JSON logs
   --console-only (flag) - Log only to console, ignore --log-file parameter

Legend: * = required, ° = auto-detected
```

### Verbose Parameter Help
When using `--verbose` or viewing specific parameter help:
```
  --project-dir <PATH> [REQUIRED]
      Base directory for code checking operations (required).

      Type: path
      
      Examples:
        --project-dir .
        --project-dir /home/user/my-project
        --project-dir ../another-project
```

## Benefits

1. **Reduced Learning Curve**: New users can quickly understand what parameters are available and how to use them.

2. **Self-Documenting**: The help system keeps documentation in sync with the actual code, reducing maintenance burden.

3. **Context-Aware**: Shows only relevant information based on what the user is asking for.

4. **Examples Included**: Verbose mode provides real-world examples for each parameter type.

5. **Auto-Detection Clarity**: Clearly indicates which parameters will be auto-detected and how.

## Integration with Other Commands

The help command complements other mcp-config commands:

- Use `help` before `setup` to understand parameters
- Use `list-server-types` to see available servers, then `help` for details
- Use `validate` to check configuration, `help` to fix issues

## Future Enhancements

Potential improvements for the help system:

1. **Interactive Mode**: Step-by-step parameter selection
2. **Configuration Templates**: Export example configurations
3. **Validation Hints**: Show common parameter combinations
4. **Localization**: Multi-language support
5. **Web Documentation**: Auto-generate HTML documentation
