# Milestone 2.1: Complete Parameter Support

## Overview
Implement full support for all 8 MCP Code Checker parameters with dynamic CLI option generation, parameter validation, and smart defaults. This milestone builds upon the basic CLI from Phase 1 to provide complete parameter coverage.

## Prerequisites
- Phase 1 completed (basic CLI, Claude Desktop handler, core data models)
- Existing `ServerConfig` and `ParameterDef` classes
- Basic `setup`, `remove`, `list` commands working

## Goals
1. Support all 8 MCP Code Checker parameters with proper types and validation
2. Dynamic CLI option generation based on server configuration
3. Smart parameter validation and default value handling
4. Complete parameter transformation from CLI args to server command args

## Detailed Requirements

### 1. Complete MCP Code Checker Parameter Set

Implement support for all parameters defined in the requirements:

#### Required Parameters:
- `--project-dir`: Base directory for code checking operations (path, required)

#### Optional Parameters:
- `--python-executable`: Path to Python interpreter (path, auto-detected)
- `--venv-path`: Path to virtual environment (path, auto-detected)
- `--test-folder`: Path to test folder relative to project_dir (string, default: "tests")
- `--keep-temp-files`: Keep temporary files after execution (boolean flag)
- `--log-level`: Logging level (choice: DEBUG|INFO|WARNING|ERROR|CRITICAL, default: INFO)
- `--log-file`: Path for structured JSON logs (path, auto-generated if not specified)
- `--console-only`: Log only to console (boolean flag)

### 2. Enhanced Parameter Definition System

Extend the existing `ParameterDef` class to handle all parameter types:

```python
@dataclass
class ParameterDef:
    name: str                   # CLI parameter name (e.g., "project-dir") 
    arg_name: str              # Server argument (e.g., "--project-dir")
    param_type: str            # "string", "boolean", "choice", "path"
    required: bool = False     # Whether required
    default: any = None        # Default value
    choices: list = None       # For choice parameters
    help: str = ""            # Help text for CLI
    is_flag: bool = False      # True for boolean flags (action="store_true")
    auto_detect: bool = False  # True if value can be auto-detected
    validator: callable = None # Optional validation function
```

### 3. Dynamic CLI Generation

Implement dynamic argument parser generation that creates CLI options based on server parameter definitions:

```python
def build_setup_parser(server_config: ServerConfig) -> argparse.ArgumentParser:
    """Build setup command parser with server-specific parameters."""
    # Implementation should:
    # 1. Create base parser with positional args
    # 2. Add global options (--client, --dry-run, --verbose, --backup)
    # 3. Dynamically add server-specific options based on parameters
    # 4. Handle different parameter types correctly
    # 5. Set proper defaults, choices, and required flags
```

### 4. Parameter Validation System

Implement comprehensive validation for all parameter types:

#### Path Validation:
- Check if paths exist when required
- Validate path permissions
- Handle relative vs absolute paths
- Cross-platform path normalization

#### Choice Validation:
- Validate against allowed choices
- Case-insensitive matching where appropriate

#### Boolean Flag Validation:
- Proper flag handling in argparse
- Correct transformation to command args

#### Auto-Detection Logic:
- Python executable detection (current interpreter, venv, system)
- Virtual environment detection (common patterns: .venv, venv, env)
- Log file path generation (project_dir/logs/mcp_code_checker_{timestamp}.log)

### 5. Command Argument Generation

Implement the `generate_args()` method in `ServerConfig` to transform user parameters into server command arguments:

```python
def generate_args(self, user_params: dict) -> list:
    """Generate command line args from user parameters."""
    # Implementation should:
    # 1. Always start with main module path
    # 2. Add parameters in correct format based on type
    # 3. Handle boolean flags correctly (only add flag name if True)
    # 4. Handle regular parameters (add both flag and value)
    # 5. Apply auto-detection for missing optional parameters
    # 6. Validate all parameters before generating args
```

## Implementation Tasks

### Task 1: Extend Parameter Definitions (4 hours)
1. Update `ParameterDef` class with new fields (validator, auto_detect)
2. Define complete MCP Code Checker parameter set in `servers.py`
3. Add parameter validation functions for each type
4. Write unit tests for parameter definitions

**Expected Files:**
- `src/config/servers.py` (updated)
- `tests/test_config/test_servers.py` (updated)

### Task 2: Dynamic CLI Generation (6 hours)
1. Implement `build_setup_parser()` function
2. Handle all parameter types in argument parser creation
3. Add proper help text, defaults, and validation
4. Update main CLI to use dynamic parser
5. Write tests for CLI generation with different server configs

**Expected Files:**
- `src/config/main.py` (updated)
- `src/config/cli_utils.py` (new)
- `tests/test_config/test_cli_utils.py` (new)

### Task 3: Auto-Detection System (6 hours)
1. Implement Python executable detection
2. Implement virtual environment detection
3. Implement log file path generation
4. Add project structure validation
5. Write comprehensive tests for auto-detection

**Expected Files:**
- `src/config/utils.py` (updated)
- `tests/test_config/test_utils.py` (updated)

### Task 4: Parameter Validation (4 hours)
1. Implement validation functions for each parameter type
2. Add comprehensive error messages
3. Handle edge cases (missing paths, invalid choices, etc.)
4. Write validation tests with various scenarios

**Expected Files:**
- `src/config/validation.py` (new)
- `tests/test_config/test_validation.py` (new)

## Test Requirements

### Unit Tests
1. **Parameter Definition Tests:**
   - All 8 parameters correctly defined
   - Default values applied correctly
   - Validation functions work for each parameter type

2. **CLI Generation Tests:**
   - Dynamic parser creation for MCP Code Checker
   - All parameter types handled correctly in argparse
   - Help text and defaults properly set

3. **Auto-Detection Tests:**
   - Python executable detection in various scenarios
   - Virtual environment detection with different patterns
   - Log file path generation with timestamps

4. **Validation Tests:**
   - Path validation (exists, permissions, relative/absolute)
   - Choice validation (valid/invalid choices)
   - Boolean flag handling
   - Error message quality

### Integration Tests
1. **End-to-End Parameter Flow:**
   - CLI args → parameter parsing → validation → command generation
   - Test with all parameter combinations
   - Test with missing optional parameters (auto-detection)

2. **Real Configuration Generation:**
   - Generate actual Claude Desktop configuration
   - Verify all parameters correctly transformed
   - Test with various project structures

## Acceptance Criteria

### Must Have:
1. All 8 MCP Code Checker parameters fully supported
2. `mcp-config setup mcp-code-checker "test" --project-dir .` works with auto-detection
3. `mcp-config setup mcp-code-checker "test" --project-dir . --python-executable /usr/bin/python3 --venv-path .venv --test-folder tests --keep-temp-files --log-level DEBUG --log-file ./logs/test.log --console-only` works with all parameters
4. Parameter validation prevents invalid configurations
5. Auto-detection fills in reasonable defaults for optional parameters
6. Generated command arguments are correct for MCP Code Checker server

### Should Have:
1. Clear error messages for invalid parameters
2. Help text shows all available options with descriptions
3. Cross-platform path handling works correctly
4. Auto-detection handles edge cases gracefully

### Test Coverage:
- Minimum 90% code coverage for new modules
- All parameter combinations tested
- All auto-detection scenarios tested
- All validation scenarios tested

## Example Usage After Implementation

```bash
# Basic usage with auto-detection
mcp-config setup mcp-code-checker "my-checker" --project-dir .
# Should auto-detect Python executable and venv, use default test folder

# Full parameter specification
mcp-config setup mcp-code-checker "debug-checker" \
  --project-dir /home/user/myproject \
  --python-executable /usr/bin/python3.11 \
  --venv-path /home/user/myproject/.venv \
  --test-folder custom-tests \
  --keep-temp-files \
  --log-level DEBUG \
  --log-file /home/user/myproject/logs/debug.log

# Console-only logging
mcp-config setup mcp-code-checker "console-checker" \
  --project-dir . \
  --console-only

# Should generate proper Claude Desktop configuration with all parameters
```

## Deliverables

1. **Enhanced Parameter System:** Complete support for all 8 MCP Code Checker parameters
2. **Dynamic CLI:** Argument parser generated from server configuration
3. **Auto-Detection:** Smart defaults for Python executable, venv, and log file paths
4. **Validation:** Comprehensive parameter validation with clear error messages
5. **Tests:** Complete test coverage for all new functionality
6. **Documentation:** Updated help text and parameter descriptions

This milestone provides the foundation for a production-ready configuration tool that handles all MCP Code Checker parameters correctly and provides excellent user experience through auto-detection and validation.
