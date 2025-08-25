# Milestone 3.1: Server Registry Implementation

## Context
You are implementing Phase 3, Milestone 3.1 of the MCP Configuration Helper tool. Previous milestones have completed:
- Phase 1: Core foundation with basic ServerConfig, ClaudeDesktopHandler, and CLI
- Phase 2: Complete parameter support, advanced CLI features, and cross-platform polish

This milestone focuses on creating a clean server registry system to prepare for external server extensibility.

## Objective
Create a simple, robust server registration system that:
1. Provides a clean interface for server definitions
2. Supports built-in server configurations
3. Enables server discovery and lookup
4. Validates server configurations
5. Sets the foundation for external server support (next milestone)

## Requirements

### 1. Server Registry Core
Create `src/config/servers.py` with:

```python
@dataclass
class ParameterDef:
    """Definition of a server parameter for CLI and configuration generation."""
    name: str                   # CLI parameter name (e.g., "project-dir") 
    arg_name: str              # Server argument (e.g., "--project-dir")
    param_type: str            # "string", "boolean", "choice", "path"
    required: bool = False     # Whether required
    default: any = None        # Default value
    choices: list = None       # For choice parameters
    help: str = ""            # Help text for CLI
    is_flag: bool = False      # True for boolean flags (action="store_true")

@dataclass
class ServerConfig:
    """Complete configuration definition for an MCP server type."""
    name: str                    # "mcp-code-checker"
    display_name: str           # "MCP Code Checker"
    main_module: str            # "src/main.py"  
    parameters: list[ParameterDef]  # All possible parameters
    
    def generate_args(self, user_params: dict) -> list:
        """Generate command line args from user parameters."""
        # Implementation required
        pass
    
    def get_required_params(self) -> list[str]:
        """Get list of required parameter names."""
        # Implementation required
        pass
    
    def validate_project(self, project_dir: Path) -> bool:
        """Check if project is compatible (server-specific logic)."""
        # Implementation required - server-specific validation
        pass
    
    def get_parameter_by_name(self, name: str) -> Optional[ParameterDef]:
        """Get parameter definition by name."""
        # Implementation required
        pass

class ServerRegistry:
    """Central registry for all server configurations."""
    def __init__(self):
        self._servers = {}
    
    def register(self, config: ServerConfig):
        """Register a server configuration."""
        # Implementation required
        pass
    
    def get(self, name: str) -> ServerConfig:
        """Get server configuration by name."""
        # Implementation required
        pass
    
    def list_servers(self) -> list:
        """List all registered server names."""
        # Implementation required
        pass
    
    def get_all_configs(self) -> dict[str, ServerConfig]:
        """Get all server configurations."""
        # Implementation required
        pass
    
    def is_registered(self, name: str) -> bool:
        """Check if server is registered."""
        # Implementation required
        pass

# Global registry instance
registry = ServerRegistry()
```

### 2. Built-in MCP Code Checker Definition
In the same file, define the complete MCP Code Checker server configuration:

```python
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

# Register built-in server
registry.register(MCP_CODE_CHECKER)
```

### 3. Integration with Existing CLI
Update existing CLI code in `src/config/main.py` to use the registry:

```python
from .servers import registry

def setup_command(args):
    """Setup command using server registry."""
    server_config = registry.get(args.server_type)
    if not server_config:
        available = registry.list_servers()
        print(f"Error: Unknown server type '{args.server_type}'")
        print(f"Available server types: {', '.join(available)}")
        return False
    
    # Use server_config for validation and generation
    # ... rest of setup logic
```

Add new CLI command:

```python
def list_server_types_command(args):
    """List all available server types."""
    configs = registry.get_all_configs()
    print("Available server types:")
    for name, config in configs.items():
        print(f"  {name}: {config.display_name}")
        if args.verbose:
            print(f"    Main module: {config.main_module}")
            print(f"    Parameters: {len(config.parameters)}")
            required_params = config.get_required_params()
            if required_params:
                print(f"    Required parameters: {', '.join(required_params)}")
```

## Implementation Details

### ServerConfig Methods Implementation

```python
def generate_args(self, user_params: dict) -> list:
    """Generate command line args from user parameters."""
    args = [self.main_module]  # Always start with main module
    
    for param in self.parameters:
        value = user_params.get(param.name, param.default)
        if value is not None:
            if param.is_flag and value:
                # For boolean flags, just add the flag if True
                args.append(param.arg_name)
            elif not param.is_flag:
                # For regular parameters, add name and value
                args.extend([param.arg_name, str(value)])
    
    return args

def validate_project(self, project_dir: Path) -> bool:
    """Check if project is compatible (server-specific logic)."""
    if self.name == "mcp-code-checker":
        # Check for src/main.py
        main_py = project_dir / "src" / "main.py"
        return main_py.exists()
    
    # Default: any directory is valid
    return True
```

## Testing Requirements

Create comprehensive tests in `tests/test_config/test_servers.py`:

### Test Categories:

1. **ParameterDef Tests**
   - Parameter creation and validation
   - Type checking
   - Default value handling

2. **ServerConfig Tests**
   - Configuration creation
   - Argument generation from parameters
   - Project validation logic
   - Required parameter identification

3. **ServerRegistry Tests**
   - Server registration and retrieval
   - Duplicate registration handling
   - Server lookup by name
   - Registry listing functionality

4. **Built-in Server Tests**
   - MCP Code Checker configuration completeness
   - All 8 parameters properly defined
   - Argument generation for various parameter combinations
   - Project validation logic

### Example Test Structure:

```python
def test_parameter_def_creation():
    """Test ParameterDef creation and properties."""
    param = ParameterDef(
        name="test-param",
        arg_name="--test-param",
        param_type="string",
        required=True,
        help="Test parameter"
    )
    assert param.name == "test-param"
    assert param.required is True

def test_server_config_arg_generation():
    """Test argument generation from parameters."""
    # Test with various parameter combinations
    pass

def test_registry_operations():
    """Test server registration and retrieval."""
    registry = ServerRegistry()
    # Test registration, lookup, listing
    pass

def test_mcp_code_checker_config():
    """Test built-in MCP Code Checker configuration."""
    config = registry.get("mcp-code-checker")
    assert config is not None
    assert len(config.parameters) == 8
    # Test each parameter is properly defined
    pass
```

## Validation Criteria

### Functional Requirements:
- [ ] ServerRegistry can register and retrieve server configurations
- [ ] Built-in MCP Code Checker configuration includes all 8 parameters
- [ ] ServerConfig.generate_args() produces correct command line arguments
- [ ] Project validation works for MCP Code Checker projects
- [ ] CLI integration works with registry lookup

### Quality Requirements:
- [ ] All classes have proper type hints
- [ ] Comprehensive test coverage (>90%)
- [ ] Clear error messages for invalid operations
- [ ] Thread-safe registry operations
- [ ] Proper handling of edge cases

### Integration Requirements:
- [ ] Existing CLI commands work with registry
- [ ] No breaking changes to current functionality
- [ ] New `list-server-types` command works correctly
- [ ] Registry integrates cleanly with existing codebase

## Expected Deliverables

1. **Core Implementation**
   - `src/config/servers.py` with complete ServerRegistry and ServerConfig
   - Built-in MCP Code Checker configuration
   - Integration with existing CLI code

2. **Test Suite**
   - `tests/test_config/test_servers.py` with comprehensive test coverage
   - Tests for all server registry functionality
   - Validation of built-in server configuration

3. **CLI Enhancement**
   - `list-server-types` command implementation
   - Registry integration in setup/remove commands
   - Proper error handling for unknown server types

## Success Metrics

- All tests pass with >90% code coverage
- Existing functionality remains unchanged
- New server types can be easily added to registry
- Clear separation between server definitions and runtime logic
- Foundation ready for external server discovery (next milestone)

This milestone creates a solid, testable foundation for server extensibility while maintaining the simplicity and reliability of the existing system.
