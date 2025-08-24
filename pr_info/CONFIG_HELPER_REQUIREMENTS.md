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
│   ├── cli.py                       # Command-line interface
│   ├── clients/                     # MCP client support
│   │   ├── __init__.py
│   │   ├── base.py                  # Abstract client interface
│   │   └── claude_desktop.py        # Claude Desktop implementation
│   ├── servers/                     # MCP server definitions (NEW)
│   │   ├── __init__.py
│   │   ├── base.py                  # Abstract server interface
│   │   ├── registry.py              # Server registry and discovery
│   │   └── mcp_code_checker.py      # Code checker server definition
│   ├── core/                        # Business logic
│   │   ├── __init__.py
│   │   ├── config_manager.py        # Configuration management
│   │   ├── path_detector.py         # Path auto-detection
│   │   ├── project_detector.py      # Project name detection
│   │   └── backup_manager.py        # Auto-backup functionality
│   └── utils/                       # Shared utilities
│       ├── __init__.py
│       ├── file_utils.py
│       └── json_utils.py

tests/
├── test_config/                     # Configuration tool tests
│   ├── test_cli.py
│   ├── test_clients/
│   │   └── test_claude_desktop.py
│   ├── test_servers/                # Server definition tests (NEW)
│   │   ├── test_base.py
│   │   ├── test_registry.py
│   │   └── test_mcp_code_checker.py
│   ├── test_core/
│   │   ├── test_config_manager.py
│   │   ├── test_path_detector.py
│   │   ├── test_project_detector.py
│   │   └── test_backup_manager.py
│   ├── fixtures/
│   │   ├── sample_configs/
│   │   ├── mock_projects/
│   │   └── server_definitions/      # Server definition fixtures (NEW)
│   └── integration/
│       └── test_end_to_end.py
```

Unit tests will be located in the same repo under `tests/test_config/` to maintain consistency with the existing project structure.

### Server Abstraction Architecture (Extensibility Design)

To support future MCP servers, the configuration tool uses a plugin-based architecture with server-specific definitions:

#### Server Definition Interface
```python
# src/config/servers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path

@dataclass
class ServerParameter:
    """Definition of a server parameter."""
    name: str                    # CLI parameter name (e.g., "log-level")
    arg_name: str               # Server argument name (e.g., "--log-level")
    default: Optional[Any]      # Default value
    required: bool = False      # Whether parameter is required
    description: str = ""       # Parameter description
    param_type: str = "str"     # Parameter type: str, bool, int, path

@dataclass 
class ServerDefinition:
    """Complete definition of an MCP server."""
    name: str                           # Server type name (e.g., "mcp-code-checker")
    display_name: str                   # Human-readable name
    main_module: str                    # Path to main module (e.g., "src/main.py")
    package_root_detect: List[str]      # Files to detect package root
    python_required: bool = True        # Whether Python executable is needed
    venv_support: bool = True          # Whether virtual env is supported
    default_server_name_pattern: str   # Default naming pattern
    parameters: List[ServerParameter]   # Server-specific parameters
    project_indicators: List[str]      # Files that indicate valid projects
    
class ServerConfigBase(ABC):
    """Abstract base class for MCP server configurations."""
    
    @abstractmethod
    def get_definition(self) -> ServerDefinition:
        """Return the server definition."""
        pass
    
    @abstractmethod
    def detect_package_root(self, current_path: Path) -> Optional[Path]:
        """Detect the server package root directory."""
        pass
    
    @abstractmethod
    def validate_project(self, project_path: Path) -> bool:
        """Validate if project is compatible with this server."""
        pass
    
    def generate_server_name(self, project_name: str) -> str:
        """Generate default server name for project."""
        pattern = self.get_definition().default_server_name_pattern
        return pattern.format(project_name=project_name)
```

#### Code Checker Server Implementation
```python
# src/config/servers/mcp_code_checker.py
from pathlib import Path
from typing import Optional, List
from .base import ServerConfigBase, ServerDefinition, ServerParameter

class MCPCodeCheckerConfig(ServerConfigBase):
    """Configuration definition for MCP Code Checker server."""
    
    def get_definition(self) -> ServerDefinition:
        return ServerDefinition(
            name="mcp-code-checker",
            display_name="MCP Code Checker",
            main_module="src/main.py",
            package_root_detect=["src/main.py", "pyproject.toml"],
            python_required=True,
            venv_support=True,
            default_server_name_pattern="mcp_code_checker on p {project_name}",
            parameters=[
                ServerParameter(
                    name="project-dir", 
                    arg_name="--project-dir",
                    required=True,
                    description="Target project directory for code checking"
                ),
                ServerParameter(
                    name="python-executable",
                    arg_name="--python-executable", 
                    description="Python interpreter path"
                ),
                ServerParameter(
                    name="venv-path",
                    arg_name="--venv-path",
                    description="Virtual environment path"
                ),
                ServerParameter(
                    name="test-folder",
                    arg_name="--test-folder",
                    default="tests",
                    description="Test directory path"
                ),
                ServerParameter(
                    name="log-level",
                    arg_name="--log-level",
                    default="INFO", 
                    description="Logging level"
                ),
                ServerParameter(
                    name="log-file",
                    arg_name="--log-file",
                    param_type="path",
                    description="Custom log file path"
                ),
                ServerParameter(
                    name="console-only",
                    arg_name="--console-only",
                    param_type="bool",
                    description="Disable file logging"
                ),
                ServerParameter(
                    name="keep-temp-files",
                    arg_name="--keep-temp-files", 
                    param_type="bool",
                    description="Preserve temporary files for debugging"
                )
            ],
            project_indicators=[
                "pyproject.toml", "setup.py", "requirements.txt",
                "src/", "tests/", "*.py"
            ]
        )
    
    def detect_package_root(self, current_path: Path) -> Optional[Path]:
        """Detect mcp-code-checker package root."""
        for indicator in ["src/main.py", "pyproject.toml"]:
            if (current_path / indicator).exists():
                return current_path
        return None
    
    def validate_project(self, project_path: Path) -> bool:
        """Check if project is a valid Python project."""
        indicators = self.get_definition().project_indicators
        return any((project_path / indicator).exists() for indicator in indicators)
```

#### Server Registry
```python
# src/config/servers/registry.py
from typing import Dict, List, Optional
from .base import ServerConfigBase
from .mcp_code_checker import MCPCodeCheckerConfig

class ServerRegistry:
    """Registry for all supported MCP servers."""
    
    def __init__(self):
        self._servers: Dict[str, ServerConfigBase] = {
            "mcp-code-checker": MCPCodeCheckerConfig()
        }
    
    def get_server(self, name: str) -> Optional[ServerConfigBase]:
        """Get server configuration by name."""
        return self._servers.get(name)
    
    def list_servers(self) -> List[str]:
        """List all available server names."""
        return list(self._servers.keys())
    
    def register_server(self, name: str, config: ServerConfigBase) -> None:
        """Register a new server configuration."""
        self._servers[name] = config

# Global registry instance
server_registry = ServerRegistry()
```

### Command-Line Interface Design

#### Parameter Analysis
Based on real configuration files and server implementation, the tool must handle:
- **Project directory** (required): Target project for code checking
- **Python executable** (auto-detect): Python interpreter path
- **Virtual environment** (auto-detect): Virtual environment path  
- **Server name** (auto-generate): Unique identifier with project context
- **Log level** (optional): Defaults to INFO
- **Log file** (optional): Custom path for structured JSON logs
- **Console only** (optional): Flag to disable file logging
- **Test folder** (optional): Path to test directory, defaults to "tests"
- **Keep temp files** (optional): Debug flag to preserve temporary files
- **PYTHONPATH** (auto-set): Points to mcp-code-checker package root

#### Core Commands (MVP)
```bash
# Setup with auto-detected server type (for current project)
mcp-code-checker-config setup --project-dir /path/to/project
# Creates: "mcp_code_checker on p {project_name}"

# Setup with explicit server type (for future extensibility)
mcp-code-checker-config setup --server-type mcp-code-checker --project-dir /path/to/project

# Setup with custom server name
mcp-code-checker-config setup --project-dir /path/to/project --server-name "my-checker"

# Specify custom Python executable and venv
mcp-code-checker-config setup --project-dir /path/to/project \
  --python-exe /path/to/python --venv-path /path/to/venv

# Specify additional server parameters (server-specific)
mcp-code-checker-config setup --project-dir /path/to/project \
  --test-folder "tests" --log-level "DEBUG" --log-file "/custom/log/path.log"

# Use console-only logging (no log file)
mcp-code-checker-config setup --project-dir /path/to/project --console-only

# Enable debug mode with temp file preservation
mcp-code-checker-config setup --project-dir /path/to/project --keep-temp-files

# Preview changes (dry run)
mcp-code-checker-config setup --project-dir /path/to/project --dry-run

# List available server types (future extensibility)
mcp-code-checker-config list-servers

# Remove specific server by name
mcp-code-checker-config remove --server-name "mcp_code_checker on p myproject"

# Remove with dry run preview  
mcp-code-checker-config remove --server-name "mcp_code_checker on p myproject" --dry-run

# List all configured servers (of all types)
mcp-code-checker-config list

# List only mcp-code-checker servers
mcp-code-checker-config list --server-type mcp-code-checker
```

## Configuration File Analysis Results

### Key Insights from Real-World Usage
Analysis of actual Claude Desktop configurations reveals:

**Server Naming Patterns:**
- `"mcp_code_checker on p code_checker"` - Server type + project context
- `"llm_notes__filesystem"` - Project + server type with separator
- `"calculator"` - Simple descriptive names

**Multi-Server Usage:**
- Users frequently run multiple MCP servers on the same project
- Common combinations: filesystem server + code checker on same project
- Each server provides different capabilities (file ops vs code analysis)

**Path Patterns:**
- All Windows paths use escaped backslashes: `"C:\\Users\\..."`
- Virtual environments consistently in project root: `{project}\.venv`
- PYTHONPATH points to server package root, not project directory

**Configuration Structure:**
```json
{
    "command": "path/to/python.exe",
    "args": [
        "path/to/main.py", 
        "--project-dir", "path/to/project",
        "--python-executable", "path/to/python.exe",
        "--venv-path", "path/to/venv",
        "--test-folder", "tests",
        "--log-level", "INFO",
        "--log-file", "path/to/logfile.log",
        "--keep-temp-files"
    ],
    "env": {"PYTHONPATH": "path/to/server/package"}
}
```

**User Pain Points Confirmed:**
- Manual path configuration is error-prone
- Server name collision potential with multiple projects
- JSON escaping issues on Windows
- Need for project-aware server identification

#### Additional Parameters Discovered
After analyzing main.py, server.py, and README.md, the following additional parameters were identified:

**Essential for MVP:**
- `--test-folder`: Path to test directory (default: "tests")
- `--log-level`: Logging level (default: "INFO")
- `--log-file`: Custom log file path (optional)
- `--console-only`: Disable file logging flag
- `--keep-temp-files`: Debug flag to preserve temporary files
- `--python-executable`: Explicit Python interpreter path
- `--venv-path`: Virtual environment path

**Parameter Priority for Configuration Helper:**
1. **Always include**: `--project-dir`, `--python-executable`, `--venv-path`, `--log-level`
2. **Include by default**: `--test-folder` ("tests")
3. **Include if specified**: `--log-file`, `--console-only`, `--keep-temp-files`
4. **Auto-detect and include**: PYTHONPATH environment variable

**Generated Args Array Structure:**
```json
"args": [
    "/path/to/main.py",
    "--project-dir", "/path/to/project",
    "--python-executable", "/path/to/python",
    "--venv-path", "/path/to/venv",
    "--test-folder", "tests",
    "--log-level", "INFO"
    // Optional: "--log-file", "path"
    // Optional: "--console-only"
    // Optional: "--keep-temp-files"
]
```

## Implementation Plan

### Phase 1: Core Functionality (MVP) - 2 weeks
**Goal**: Solve the main user pain point with extensible architecture for future servers

**Tasks**:
1. **T1.1**: Implement server abstraction layer (`ServerConfigBase`, `ServerDefinition`, `ServerParameter`)
2. **T1.2**: Create `MCPCodeCheckerConfig` server definition with all identified parameters
3. **T1.3**: Build `ServerRegistry` for plugin-based server discovery
4. **T1.4**: Implement `PathDetector` class for auto-detecting Python executables and project validation
5. **T1.5**: Create `ProjectDetector` class for auto-detecting project names from various sources
6. **T1.6**: Create `ClaudeDesktopConfig` class for configuration file location and JSON generation
7. **T1.7**: Build CLI interface with `setup`, `remove`, `list`, and `list-servers` commands
8. **T1.8**: Implement safe configuration merging (preserve all other MCP servers)
9. **T1.9**: Add server name generation and conflict detection
10. **T1.10**: Add cross-platform path handling and JSON escaping
11. **T1.11**: Create comprehensive unit tests under `tests/test_config/`

**Success Criteria**:
- Users can run `mcp-code-checker-config setup --project-dir .` and get working configuration with meaningful server name
- Users can cleanly remove by server name: `mcp-code-checker-config remove --server-name "mcp_code_checker on p myproject"`
- Users can list available server types: `mcp-code-checker-config list-servers`
- Users can list existing servers: `mcp-code-checker-config list`
- Cross-platform compatibility (Windows/Mac/Linux) with proper path escaping
- Safe merging preserves all other MCP servers (filesystem, calculator, etc.)
- Extensible architecture allows easy addition of new MCP servers
- Server definitions are completely isolated and modular
- Automatic backup before changes (safety only)
- Server name conflicts detected and resolved
- Comprehensive error handling and user feedback

### Deferred Features (Future Phases)
**Goal**: Add advanced features based on user feedback and extend to other MCP servers

**Potential Future Features**:
- Support for additional MCP clients (VS Code, Cursor, etc.)
- Extract the config tool into separate project for better reusability with other MCP servers
- GUI tool for non-technical users
- Configuration profiles and templates

### Extensibility Benefits

**For Future MCP Server Support:**
```python
# Adding a new MCP server is as simple as:
# 1. Create server definition
class MCPFilesystemConfig(ServerConfigBase):
    def get_definition(self) -> ServerDefinition:
        return ServerDefinition(
            name="mcp-filesystem",
            display_name="MCP Filesystem", 
            main_module="src/main.py",
            default_server_name_pattern="filesystem on p {project_name}",
            parameters=[...],  # Filesystem-specific parameters
            ...
        )

# 2. Register in registry
server_registry.register_server("mcp-filesystem", MCPFilesystemConfig())

# 3. Users can now use:
# mcp-code-checker-config setup --server-type mcp-filesystem --project-dir /path
```

**Architectural Advantages:**
- **Separation of Concerns**: Server logic isolated from configuration logic
- **Extensibility**: New servers added without modifying core code
- **Maintainability**: Each server definition is self-contained
- **Testability**: Server definitions can be unit tested independently
- **Consistency**: All servers follow the same configuration pattern
- **Future-Proofing**: Architecture scales to dozens of different MCP servers

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
- **Additional MCP clients**: Cursor IDE, VS Code extensions, other AI assistants
- **Advanced configuration management**: Manual backup/restore, validation, profiles
- **Team features**: Configuration sharing, synchronization across machines
- **GUI tool**: Desktop app for non-technical users

## Conclusion

This configuration helper will transform the MCP Code Checker from a technically complex tool requiring manual setup into a professional, user-friendly package that "just works" across platforms. The simplified MVP approach ensures we deliver immediate value with minimal complexity.

The key insight from our discussion was focusing on **configuration automation** rather than installation complexity, as the real user pain point is Claude Desktop setup, not package installation. By adopting a KISS (Keep It Simple, Stupid) approach with single project support and core commands only, we can deliver 80% of the value with 20% of the complexity, enabling faster development and lower risk while maintaining the ability to add advanced features based on actual user feedback.