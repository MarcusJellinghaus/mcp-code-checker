# Milestone 1.1: Configuration Data Model Implementation

## Overview
Implement the core data model for MCP server configurations with focus on the MCP Code Checker. This milestone creates the foundation classes that define server parameters and generate command-line arguments.

## Context
You are working on an MCP configuration helper tool. The full requirements are in `CONFIG_HELPER_REQUIREMENTS.md` in the same directory. This milestone focuses on creating the basic data structures needed to represent server configurations.

## Implementation Requirements

### 1. Core Classes to Implement

#### File: `src/config/servers.py`

Create the following classes:

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path

@dataclass
class ParameterDef:
    """Definition of a server parameter for CLI and config generation."""
    name: str                   # CLI parameter name (e.g., "project-dir") 
    arg_name: str              # Server argument (e.g., "--project-dir")
    param_type: str            # "string", "boolean", "choice", "path"
    required: bool = False     # Whether required
    default: Any = None        # Default value
    choices: List[str] = None  # For choice parameters
    help: str = ""            # Help text for CLI
    is_flag: bool = False      # True for boolean flags (action="store_true")
    
    def __post_init__(self):
        """Validate parameter definition after creation."""
        # Add validation logic here
        pass

@dataclass
class ServerConfig:
    """Complete configuration for an MCP server type."""
    name: str                    # "mcp-code-checker"
    display_name: str           # "MCP Code Checker"
    main_module: str            # "src/main.py"  
    parameters: List[ParameterDef]  # All possible parameters
    
    def generate_args(self, user_params: Dict[str, Any]) -> List[str]:
        """Generate command line args from user parameters."""
        # Implementation needed
        pass
    
    def get_required_params(self) -> List[str]:
        """Get list of required parameter names."""
        # Implementation needed
        pass
    
    def validate_project(self, project_dir: Path) -> bool:
        """Check if project is compatible (server-specific logic)."""
        # Implementation needed
        pass
    
    def get_parameter_by_name(self, name: str) -> Optional[ParameterDef]:
        """Get parameter definition by name."""
        # Implementation needed
        pass

class ServerRegistry:
    """Registry for server configurations."""
    def __init__(self):
        self._servers: Dict[str, ServerConfig] = {}
    
    def register(self, config: ServerConfig) -> None:
        """Register a server configuration."""
        # Implementation needed
        pass
    
    def get(self, name: str) -> Optional[ServerConfig]:
        """Get server configuration by name."""
        # Implementation needed
        pass
    
    def list_servers(self) -> List[str]:
        """Get list of registered server names."""
        # Implementation needed
        pass
    
    def get_all_configs(self) -> Dict[str, ServerConfig]:
        """Get all registered configurations."""
        # Implementation needed
        pass
```

### 2. MCP Code Checker Configuration

Create the complete MCP Code Checker server definition with ALL 8 parameters from the requirements:

```python
# At the bottom of src/config/servers.py

# Global registry instance
registry = ServerRegistry()

# MCP Code Checker built-in config - COMPLETE PARAMETER SET
MCP_CODE_CHECKER = ServerConfig(
    name="mcp-code-checker",
    display_name="MCP Code Checker", 
    main_module="src/main.py",
    parameters=[
        # Required parameters
        ParameterDef(
            name="project-dir", 
            arg_name="--project-dir", 
            param_type="path",
            required=True, 
            help="Base directory for code checking operations (required)"
        ),
        
        # Python execution parameters
        ParameterDef(
            name="python-executable", 
            arg_name="--python-executable", 
            param_type="path",
            help="Path to Python interpreter to use for running tests. If not specified, defaults to the current Python interpreter (sys.executable)"
        ),
        ParameterDef(
            name="venv-path", 
            arg_name="--venv-path", 
            param_type="path",
            help="Path to virtual environment to activate for running tests. When specified, the Python executable from this venv will be used instead of python-executable"
        ),
        
        # Test configuration parameters
        ParameterDef(
            name="test-folder", 
            arg_name="--test-folder", 
            param_type="string",
            default="tests",
            help="Path to the test folder (relative to project_dir). Defaults to 'tests'"
        ),
        ParameterDef(
            name="keep-temp-files", 
            arg_name="--keep-temp-files", 
            param_type="boolean",
            is_flag=True,
            help="Keep temporary files after test execution. Useful for debugging when tests fail"
        ),
        
        # Logging parameters
        ParameterDef(
            name="log-level", 
            arg_name="--log-level", 
            param_type="choice",
            default="INFO",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="Set logging level (default: INFO)"
        ),
        ParameterDef(
            name="log-file", 
            arg_name="--log-file", 
            param_type="path",
            help="Path for structured JSON logs (default: mcp_code_checker_{timestamp}.log in project_dir/logs/)"
        ),
        ParameterDef(
            name="console-only", 
            arg_name="--console-only", 
            param_type="boolean",
            is_flag=True,
            help="Log only to console, ignore --log-file parameter"
        )
    ]
)

# Register the built-in server
registry.register(MCP_CODE_CHECKER)
```

### 3. Validation Utilities

#### File: `src/config/utils.py`

Create basic validation functions:

```python
from pathlib import Path
from typing import List, Dict, Any

def validate_parameter_value(param_def: ParameterDef, value: Any) -> List[str]:
    """
    Validate a parameter value against its definition.
    
    Returns:
        List of validation errors (empty if valid)
    """
    # Implementation needed
    pass

def validate_required_parameters(server_config: ServerConfig, user_params: Dict[str, Any]) -> List[str]:
    """
    Validate that all required parameters are provided.
    
    Returns:
        List of validation errors (empty if valid)
    """
    # Implementation needed
    pass

def normalize_path_parameter(value: str, base_path: Path) -> str:
    """
    Normalize a path parameter to absolute path.
    
    Args:
        value: Path value (can be relative or absolute)
        base_path: Base directory for relative paths
        
    Returns:
        Absolute path as string
    """
    # Implementation needed
    pass
```

### 4. Package Structure

Create the following files:
- `src/config/__init__.py` (empty for now)
- `src/config/servers.py` (main implementation)
- `src/config/utils.py` (validation utilities)

## Implementation Details

### ParameterDef Validation
- Validate `param_type` is one of: "string", "boolean", "choice", "path"
- For `choice` type, ensure `choices` list is provided and non-empty
- For `boolean` type with `is_flag=True`, ensure `default` is boolean
- Validate `name` and `arg_name` are non-empty strings

### ServerConfig.generate_args() Logic
1. Start with `[self.main_module]`
2. Iterate through parameters
3. For each parameter:
   - Get user value or default
   - Skip if value is None
   - For flags (`is_flag=True`): add `arg_name` only if value is True
   - For regular params: add `[arg_name, str(value)]`
4. Return complete args list

### ServerConfig.validate_project() Logic
For MCP Code Checker specifically:
- Check if `project_dir/src/main.py` exists
- Check if `project_dir/src` exists
- Return True if valid, False otherwise

### ServerRegistry Functionality
- `register()`: Store config by name, validate no duplicates
- `get()`: Return config by name or None
- `list_servers()`: Return sorted list of server names
- `get_all_configs()`: Return copy of internal dict

## Test Requirements

### File: `tests/test_config/test_servers.py`

Create comprehensive tests for:

1. **ParameterDef Tests:**
   - Valid parameter creation
   - Invalid parameter types
   - Validation logic
   - Edge cases (empty strings, None values)

2. **ServerConfig Tests:**
   - MCP Code Checker configuration completeness
   - `generate_args()` with various parameter combinations
   - Required parameter detection
   - Project validation logic
   - Parameter lookup by name

3. **ServerRegistry Tests:**
   - Server registration and retrieval
   - Duplicate server handling
   - List operations
   - Empty registry behavior

4. **Integration Tests:**
   - Complete MCP Code Checker parameter set
   - Argument generation for all parameter types
   - Path parameter handling

### File: `tests/test_config/test_utils.py`

Create tests for:
- Parameter value validation
- Required parameter validation  
- Path normalization
- Error message formatting

## Acceptance Criteria

1. **MCP Code Checker Configuration Complete:**
   ```python
   config = registry.get("mcp-code-checker")
   assert len(config.parameters) == 8
   assert "project-dir" in [p.name for p in config.parameters]
   ```

2. **Argument Generation Works:**
   ```python
   args = config.generate_args({"project-dir": "/path/to/project", "log-level": "DEBUG"})
   assert args[0] == "src/main.py"
   assert "--project-dir" in args
   assert "/path/to/project" in args
   ```

3. **Validation Functions:**
   ```python
   errors = validate_required_parameters(config, {})
   assert "project-dir is required" in errors
   ```

4. **All Tests Pass:**
   - Run `pytest tests/test_config/test_servers.py -v`
   - Run `pytest tests/test_config/test_utils.py -v`
   - All tests should pass with good coverage

## Next Steps
After completing this milestone, you'll have the foundation data model that Milestone 1.2 (Claude Desktop Handler) will use to generate actual configuration files.
