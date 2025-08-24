# MCP Code Checker Configuration Helper - Requirements & Implementation Plan

## Overview

This document outlines the requirements and implementation plan for adding a configuration helper tool to the MCP Code Checker project. The configuration helper will solve the current complex manual setup process by automating Claude Desktop configuration and providing a better user experience.

## Background & Motivation

### Current User Pain Points
- **Complex manual configuration**: Users must manually edit `claude_desktop_config.json` with absolute paths
- **Cross-platform path issues**: Different path formats between Windows/Mac/Linux cause errors  
- **Error-prone JSON editing**: Manual JSON editing leads to syntax errors and configuration mistakes
- **Multiple installation methods**: Confusing documentation with various setup approaches
- **Path resolution problems**: Users struggle with virtual environments, Python executables, and PYTHONPATH

### Why Not Just Installation Helper?
After discussion, we determined that an **installation helper would be overkill** because:
- Current `pip install` process is already simple
- Python packaging handles dependencies automatically
- The real complexity is in **configuration**, not installation
- Users' main struggle is Claude Desktop setup, not package installation

## Project Goals

1. **Eliminate manual Claude Desktop configuration** - Automate the complex JSON setup process
2. **Provide cross-platform compatibility** - Handle path differences automatically
3. **Support multiple MCP clients** - Extensible architecture for future clients beyond Claude Desktop
4. **Ensure configuration safety** - create backup file before editing the config file
5. **Improve user experience** - Transform complex multi-step process into simple commands

## Requirements

### Functional Requirements

#### Core Features (Phase 1 - MVP)
- **F1**: Auto-detect Claude Desktop configuration file location across platforms (Windows/Mac/Linux)
- **F2**: Generate syntactically correct MCP server configuration with absolute paths
- **F3**: Merge safely with existing Claude Desktop configurations (don't overwrite other MCP servers)
- **F4**: Validate project directory exists and appears to be a Python project
- **F5**: Auto-detect Python executable and virtual environments
- **F6**: Cross-platform path handling (forward/backward slashes, spaces in paths)
- **F7**: Dry run mode - preview changes without applying them

#### Additional Features (MVP)
- **F8**: Remove server configuration cleanly
- **F9**: Basic configuration validation (project directory exists, appears to be Python project)

### Non-Functional Requirements

#### Performance
- **NF1**: Configuration operations should complete within 5 seconds
- **NF2**: File operations should be atomic (complete or rollback)

#### Reliability  
- **NF3**: Always create backup before modifying existing configurations
- **NF4**: Handle file permission errors gracefully
- **NF5**: Validate all user inputs before processing

#### Usability
- **NF6**: Clear error messages with actionable guidance
- **NF7**: Consistent command-line interface following Unix conventions
- **NF8**: Comprehensive help documentation

#### Maintainability
- **NF9**: Modular architecture supporting multiple MCP clients
- **NF10**: Comprehensive unit test coverage (>90% for core modules)
- **NF11**: Clear separation between CLI interface and business logic

## Technical Architecture

### Entry Points Configuration
```toml
[project.scripts]
mcp-code-checker = "src.main:main"                    # Main server (existing)
mcp-code-checker-config = "src.config:main"           # Configuration helper (new)

[project.entry-points."mcp.servers"]  
code-checker = "src.server:create_server"             # MCP server discovery (new)
```

### Package Structure
```
src/
├── config/                          # Configuration tool package
│   ├── __init__.py                  
│   ├── main.py                      # CLI entry point
│   ├── cli.py                       # Command-line interface (setup/remove only)
│   ├── clients/                     # MCP client support
│   │   ├── __init__.py
│   │   ├── base.py                  # Abstract client interface
│   │   └── claude_desktop.py        # Claude Desktop implementation
│   ├── core/                        # Business logic
│   │   ├── __init__.py
│   │   ├── config_manager.py        # Configuration management
│   │   ├── path_detector.py         # Path auto-detection
│   │   └── backup_manager.py        # Auto-backup only (not manual)
│   └── utils/                       # Shared utilities
│       ├── __init__.py
│       ├── file_utils.py
│       └── json_utils.py

tests/
├── test_config/                     # Configuration tool tests
│   ├── test_cli.py
│   ├── test_clients/
│   │   └── test_claude_desktop.py
│   ├── test_core/
│   │   ├── test_config_manager.py
│   │   ├── test_path_detector.py
│   │   └── test_backup_manager.py
│   ├── fixtures/
│   │   ├── sample_configs/
│   │   └── mock_projects/
│   └── integration/
│       └── test_end_to_end.py
```

Unit tests will be located in the same repo under `tests/test_config/` to maintain consistency with the existing project structure.

### Command-Line Interface Design

#### Core Commands (MVP)
```bash
# Setup/update server configuration
mcp-code-checker-config setup --project-dir /path/to/project

# Preview changes without applying (dry run)
mcp-code-checker-config setup --project-dir /path/to/project --dry-run

# Specify custom Python executable
mcp-code-checker-config setup --project-dir /path/to/project --python-exe /path/to/python

# Use virtual environment
mcp-code-checker-config setup --project-dir /path/to/project --venv-path /path/to/venv

# Remove server configuration (simple - no parameters needed)
mcp-code-checker-config remove

# Remove with dry run preview
mcp-code-checker-config remove --dry-run
```


## Implementation Plan

### Phase 1: Core Functionality (MVP) - 2 weeks
**Goal**: Solve the main user pain point with minimal complexity

**Tasks**:
1. **T1.1**: Implement `PathDetector` class for auto-detecting Python executables and project validation
2. **T1.2**: Create `ClaudeDesktopConfig` class for configuration file location and JSON generation
3. **T1.3**: Build basic CLI interface with `setup` and `remove` commands
4. **T1.4**: Implement safe configuration merging (preserve existing MCP servers, single server entry)
5. **T1.5**: Add cross-platform path handling and validation
6. **T1.6**: Create comprehensive unit tests under `tests/test_config/`

**Success Criteria**:
- Users can run `mcp-code-checker-config setup --project-dir .` and get working Claude Desktop configuration
- Users can cleanly remove with `mcp-code-checker-config remove`
- Cross-platform compatibility (Windows/Mac/Linux)
- Safe merging with existing configurations
- Automatic backup before changes (safety only)
- Comprehensive error handling and user feedback

### Deferred Features (Future Phases)
**Goal**: Add advanced features based on user feedback

**Potential Future Features**:
- Multiple project support
- Manual backup/restore commands
- Advanced configuration validation
- List/management commands
- Configuration profiles
- Support for additional MCP clients

## Path Auto-Detection Strategy

### Detection Priority Order
1. **Explicit parameters**: User-provided `--python-exe` or `--venv-path`
2. **Virtual environment**: Auto-detect if running in venv or find venv in project directory
3. **Current Python**: Use `sys.executable` as fallback

### Project Validation
- Check for Python project indicators: `pyproject.toml`, `setup.py`, `requirements.txt`, `src/`, `tests/`
- Validate directory exists and is readable
- Provide helpful error messages for non-Python directories

### Cross-Platform Considerations
- **Windows**: Handle `Scripts/python.exe`, backslash paths, spaces in paths
- **Mac/Linux**: Handle `bin/python`, forward slash paths
- **All platforms**: Convert to absolute paths, handle symbolic links

## Backup Strategy

### Automatic Backups (Simplified)
- **When**: Before any configuration modification (setup or remove)
- **Where**: `~/.mcp-code-checker/backups/`
- **Naming**: `claude_desktop_backup_{timestamp}.json`
- **Purpose**: Safety only - no manual restore commands in MVP

### Configuration Management Approach

#### Single Server Model
- One `mcp-code-checker` entry in Claude Desktop config
- Setup command updates/creates this single entry
- Remove command cleanly removes only our entry
- No need for server naming or multiple project tracking


## Testing Strategy

### Unit Tests (>90% coverage target)
- **Path detection**: Mock different OS environments, venv structures
- **Configuration generation**: Test JSON output with various parameters  
- **Backup management**: Test creation, conflict resolution, cleanup
- **CLI interface**: Test argument parsing, command execution
- **Error handling**: Test permission errors, invalid inputs, file not found

### Integration Tests
- **End-to-end workflows**: Complete configuration setup process
- **Cross-platform**: Test on Windows/Mac/Linux (CI/CD)
- **Real file system**: Test with actual Claude Desktop config files

### Test Structure
Tests are located in the same repo under `tests/test_config/` to maintain consistency with the existing project structure.

```
tests/
├── test_config/                     # Configuration tool tests
│   ├── test_cli.py                  # CLI interface tests
│   ├── test_clients/
│   │   └── test_claude_desktop.py   # Claude Desktop client tests
│   ├── test_core/
│   │   ├── test_config_manager.py   # Configuration management tests
│   │   ├── test_path_detector.py    # Path detection tests
│   │   └── test_backup_manager.py   # Backup functionality tests
│   ├── fixtures/
│   │   ├── sample_configs/          # Sample configuration files
│   │   └── mock_projects/           # Mock project structures
│   └── integration/
│       └── test_end_to_end.py       # Full workflow tests
```

## Success Metrics

### User Experience Improvements
- **Before**: 5-step manual process with JSON editing
- **After**: 2-command workflow (setup/remove)
- **Error reduction**: Eliminate JSON syntax and path errors
- **Cross-platform**: Consistent experience across all platforms
- **Safety**: Automatic backup before any changes

### Technical Quality
- **Test coverage**: >90% for core modules, >85% overall
- **Performance**: <5 seconds for all configuration operations
- **Reliability**: Zero data loss with automatic backup system
- **Maintainability**: Clean, modular architecture focused on core functionality

### Adoption Metrics
- **Documentation updates**: Simplified installation instructions in README
- **User feedback**: Reduced configuration-related support requests
- **Development velocity**: Faster delivery with focused scope

## Future Considerations

### Potential Future Enhancements
- **Multiple project support**: Manage multiple MCP Code Checker instances
- **Additional MCP clients**: Cursor IDE, VS Code extensions, other AI assistants
- **Advanced configuration management**: Manual backup/restore, validation, profiles
- **Team features**: Configuration sharing, synchronization across machines
- **GUI tool**: Desktop app for non-technical users

## Conclusion

This configuration helper will transform the MCP Code Checker from a technically complex tool requiring manual setup into a professional, user-friendly package that "just works" across platforms. The simplified MVP approach ensures we deliver immediate value with minimal complexity.

The key insight from our discussion was focusing on **configuration automation** rather than installation complexity, as the real user pain point is Claude Desktop setup, not package installation. By adopting a KISS (Keep It Simple, Stupid) approach with single project support and core commands only, we can deliver 80% of the value with 20% of the complexity, enabling faster development and lower risk while maintaining the ability to add advanced features based on actual user feedback.