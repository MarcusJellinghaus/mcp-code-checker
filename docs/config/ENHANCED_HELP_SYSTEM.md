# Enhanced Help System - Complete Documentation

## Overview

The MCP Configuration Helper now features a comprehensive help system that documents **both** the mcp-config tool itself AND the server-specific parameters. This dual-purpose help system provides users with complete documentation at their fingertips.

## Two Types of Help

### 1. **Tool Command Help**
Documentation for mcp-config commands like `setup`, `remove`, `list`, etc.

### 2. **Server Parameter Help**  
Documentation for server-specific parameters like `--project-dir`, `--log-level`, etc.

## Complete Feature Set

### Tool-Level Help

```bash
# Show tool overview
mcp-config help

# Show help for specific commands
mcp-config help setup
mcp-config help remove
mcp-config help list
mcp-config help validate
mcp-config help init
mcp-config help list-server-types

# Verbose command help with detailed explanations
mcp-config help setup --verbose

# Comprehensive documentation for ALL commands
mcp-config help --all
```

### Server-Level Help

```bash
# Show all parameters for a server
mcp-config help mcp-code-checker

# Verbose server help with examples
mcp-config help mcp-code-checker --verbose

# Quick reference card
mcp-config help mcp-code-checker --quick

# Help for specific parameter
mcp-config help mcp-code-checker --parameter project-dir
```

## Command Documentation Includes

Each command's help shows:

- **Usage syntax** - How to use the command
- **Arguments** - Required positional arguments
- **Options** - Command-specific flags and options
- **Examples** - Real-world usage examples
- **Detailed descriptions** (in verbose mode)

### Example: Setup Command Help

```
SETUP COMMAND
=============

Setup an MCP server configuration in Claude Desktop.

USAGE:
  mcp-config setup <server-type> <server-name> [options]

ARGUMENTS:
  server-type        Type of server to configure (e.g., mcp-code-checker)
  server-name        Name for this server instance (your choice)

COMMAND OPTIONS:
  --client CHOICE    MCP client to configure [default: claude-desktop]
                     Choices: claude-desktop
  --dry-run          Preview changes without applying them
  --verbose          Show detailed output during setup
  --backup           Create backup before changes [default: true]
  --no-backup        Skip backup creation

SERVER-SPECIFIC OPTIONS:
  Each server type has its own parameters. Use one of these to see them:
    mcp-config help mcp-code-checker  # For code checker parameters
    mcp-config setup <server> -h      # Quick parameter list

EXAMPLES:
  # Basic setup with auto-detection
  mcp-config setup mcp-code-checker my-checker --project-dir .

  # Preview changes without applying
  mcp-config setup mcp-code-checker test --project-dir . --dry-run

  # Verbose setup with custom Python
  mcp-config setup mcp-code-checker prod --project-dir . \
    --python-executable /usr/bin/python3.11 --verbose
```

## Server Parameter Documentation

Server help is organized into categories:

1. **Required Parameters** - Must be provided
2. **Auto-Detected Parameters** - Automatically discovered if not specified
3. **Optional Parameters** - Have sensible defaults

Each parameter shows:
- Type (path, string, choice, boolean)
- Default value (if applicable)
- Auto-detection capability
- Detailed help text
- Examples (in verbose mode)

## Help Command Options

### General Options
- `--verbose` / `-v` - Show extended help with detailed explanations
- `--all` / `-a` - Show comprehensive documentation for everything

### Server-Specific Options
- `--parameter PARAM` / `-p PARAM` - Show help for specific parameter
- `--quick` / `-q` - Show quick reference card

### Disambiguation Options
- `--command` / `-c` - Treat topic as a command name
- `--server` / `-s` - Treat topic as a server type

## Smart Topic Detection

The help system intelligently determines whether you're asking for:
- Command help (setup, remove, list, etc.)
- Server help (mcp-code-checker, etc.)

If ambiguous, it provides suggestions and can be disambiguated with flags.

## Benefits of the Enhanced Help System

1. **Complete Documentation** - Everything is documented in one place
2. **Context-Aware** - Shows relevant help based on what you're trying to do
3. **Multiple Detail Levels** - From quick reference to comprehensive docs
4. **Self-Documenting** - Help stays in sync with actual functionality
5. **User-Friendly** - Clear organization and examples
6. **Discoverable** - Users can explore all features through help

## Usage Patterns

### New User Exploration
```bash
# Start with overview
mcp-config help

# Learn about setup
mcp-config help setup --verbose

# Understand server parameters
mcp-config help mcp-code-checker

# Get quick reference
mcp-config help mcp-code-checker --quick
```

### Quick Reference
```bash
# Just need parameter names
mcp-config help mcp-code-checker --quick

# Specific parameter details
mcp-config help mcp-code-checker -p log-level
```

### Troubleshooting
```bash
# Understand validation
mcp-config help validate

# Check remove behavior
mcp-config help remove --verbose
```

### Complete Documentation
```bash
# Everything at once
mcp-config help --all > mcp-config-docs.txt
```

## Implementation Details

The help system is implemented with:

1. **CommandHelpFormatter** - Formats help for mcp-config commands
2. **HelpFormatter** - Formats help for server parameters
3. **Smart routing** - Determines help type from context
4. **Modular design** - Easy to extend with new commands/servers

## Future Enhancements

Potential improvements:
- Interactive help browser
- HTML/Markdown export
- Context-sensitive help (shows help based on current directory)
- Multi-language support
- Video tutorials integration
- AI-powered help suggestions
