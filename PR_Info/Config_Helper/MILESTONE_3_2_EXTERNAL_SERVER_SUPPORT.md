# Milestone 3.2: External Server Support Implementation

## Context
You are implementing Phase 3, Milestone 3.2 of the MCP Configuration Helper tool. Previous milestones have completed:
- Phase 1: Core foundation with basic ServerConfig, ClaudeDesktopHandler, and CLI
- Phase 2: Complete parameter support, advanced CLI features, and cross-platform polish
- Phase 3.1: Server Registry with built-in MCP Code Checker configuration

This milestone adds external server discovery via Python entry points, enabling other MCP packages to register their own server configurations.

## Objective
Implement external server discovery that:
1. Discovers server configurations from other packages via entry points
2. Validates external server configurations
3. Integrates external servers with the existing registry
4. Handles errors gracefully when external servers fail to load
5. Provides clear feedback about discovered servers

## Requirements

### 1. External Server Discovery System
Create `src/config/discovery.py`:

```python
import sys
from importlib.metadata import entry_points, PackageNotFoundError
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

from .servers import ServerConfig, registry

logger = logging.getLogger(__name__)

class ServerDiscoveryError(Exception):
    """Raised when server discovery fails."""
    pass

class ExternalServerValidator:
    """Validates external server configurations."""
    
    @staticmethod
    def validate_server_config(config: any, source_name: str) -> Tuple[bool, List[str]]:
        """
        Validate external server configuration.
        
        Args:
            config: The configuration object from external package
            source_name: Name of the source (for error reporting)
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if it's a ServerConfig instance
        if not isinstance(config, ServerConfig):
            errors.append(f"Configuration from {source_name} is not a ServerConfig instance (got {type(config).__name__})")
            return False, errors
        
        # Validate required fields
        if not config.name:
            errors.append(f"Server config from {source_name} missing required 'name' field")
        
        if not config.display_name:
            errors.append(f"Server config from {source_name} missing required 'display_name' field")
        
        if not config.main_module:
            errors.append(f"Server config from {source_name} missing required 'main_module' field")
        
        if not isinstance(config.parameters, list):
            errors.append(f"Server config from {source_name} 'parameters' must be a list")
        
        # Validate name format (should be valid for CLI)
        if config.name and not config.name.replace('-', '').replace('_', '').isalnum():
            errors.append(f"Server config from {source_name} has invalid name '{config.name}' (should contain only letters, numbers, hyphens, and underscores)")
        
        # Check for name conflicts with built-in servers
        if config.name and config.name in ["mcp-code-checker"]:
            errors.append(f"Server config from {source_name} conflicts with built-in server name '{config.name}'")
        
        return len(errors) == 0, errors

def discover_external_servers() -> Dict[str, Tuple[ServerConfig, str]]:
    """
    Discover external MCP server configurations via entry points.
    
    Returns:
        Dict mapping server names to (ServerConfig, source_package) tuples
    """
    discovered = {}
    errors = []
    
    try:
        # Use importlib.metadata for Python 3.8+ compatibility
        eps = entry_points()
        
        # Handle both old and new entry_points() API
        if hasattr(eps, 'select'):
            # New API (Python 3.10+)
            mcp_entries = eps.select(group='mcp.server_configs')
        else:
            # Old API (Python 3.8-3.9)
            mcp_entries = eps.get('mcp.server_configs', [])
        
        for entry_point in mcp_entries:
            try:
                logger.debug(f"Loading server config from entry point: {entry_point.name}")
                
                # Load the configuration
                config = entry_point.load()
                
                # Get source package name
                source_package = getattr(entry_point, 'dist', None)
                source_name = source_package.name if source_package else entry_point.name
                
                # Validate configuration
                validator = ExternalServerValidator()
                is_valid, validation_errors = validator.validate_server_config(config, source_name)
                
                if is_valid:
                    # Check for duplicate names
                    if config.name in discovered:
                        existing_source = discovered[config.name][1]
                        logger.warning(f"Duplicate server name '{config.name}' from {source_name} (already registered by {existing_source}). Skipping.")
                        continue
                    
                    discovered[config.name] = (config, source_name)
                    logger.info(f"Discovered external server: {config.display_name} ({config.name}) from {source_name}")
                else:
                    for error in validation_errors:
                        logger.warning(f"Invalid server config: {error}")
                        errors.extend(validation_errors)
                
            except Exception as e:
                error_msg = f"Failed to load server config from {entry_point.name}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
    
    except Exception as e:
        error_msg = f"Failed to discover external servers: {e}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    return discovered

def register_external_servers(discovered_servers: Dict[str, Tuple[ServerConfig, str]]) -> Tuple[int, List[str]]:
    """
    Register discovered external servers with the global registry.
    
    Args:
        discovered_servers: Dict from discover_external_servers()
        
    Returns:
        Tuple of (successfully_registered_count, list_of_errors)
    """
    registered_count = 0
    errors = []
    
    for server_name, (config, source_package) in discovered_servers.items():
        try:
            # Check if already registered (shouldn't happen, but be safe)
            if registry.is_registered(server_name):
                logger.warning(f"Server '{server_name}' is already registered. Skipping external registration from {source_package}.")
                continue
            
            # Register with the global registry
            registry.register(config)
            registered_count += 1
            logger.debug(f"Registered external server: {config.display_name} from {source_package}")
            
        except Exception as e:
            error_msg = f"Failed to register server '{server_name}' from {source_package}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    return registered_count, errors

def initialize_external_servers(verbose: bool = False) -> Tuple[int, List[str]]:
    """
    Complete external server initialization process.
    
    Args:
        verbose: Whether to print detailed discovery information
        
    Returns:
        Tuple of (registered_count, list_of_errors)
    """
    if verbose:
        print("Discovering external MCP server configurations...")
    
    # Discover external servers
    discovered = discover_external_servers()
    
    if verbose and discovered:
        print(f"Found {len(discovered)} external server configuration(s):")
        for name, (config, source) in discovered.items():
            print(f"  • {config.display_name} ({name}) from {source}")
    elif verbose:
        print("No external server configurations found.")
    
    # Register discovered servers
    registered_count, errors = register_external_servers(discovered)
    
    if verbose and registered_count > 0:
        print(f"Successfully registered {registered_count} external server(s).")
    
    if verbose and errors:
        print("Errors during discovery:")
        for error in errors:
            print(f"  ⚠ {error}")
    
    return registered_count, errors
```

### 2. Integration with Main Application
Update `src/config/__init__.py` to auto-initialize external servers:

```python
"""MCP Configuration Helper - Main package initialization."""

from .servers import registry
from .discovery import initialize_external_servers
import logging

# Set up logging
logger = logging.getLogger(__name__)

def initialize_all_servers(verbose: bool = False):
    """Initialize built-in and external servers."""
    # Built-in servers are already registered in servers.py
    builtin_count = len(registry.get_all_configs())
    
    if verbose:
        print(f"Loaded {builtin_count} built-in server configuration(s).")
    
    # Initialize external servers
    external_count, errors = initialize_external_servers(verbose)
    
    total_count = builtin_count + external_count
    
    if verbose:
        print(f"Total: {total_count} server configuration(s) available.")
    
    return total_count, errors

# Auto-initialize on import (with error handling)
try:
    initialize_all_servers(verbose=False)
except Exception as e:
    logger.warning(f"Failed to initialize external servers: {e}")
    # Continue with built-in servers only
```

### 3. Enhanced CLI Commands
Update `src/config/main.py` to show external server information:

```python
def list_server_types_command(args):
    """List all available server types with source information."""
    configs = registry.get_all_configs()
    
    if not configs:
        print("No server types available.")
        return
    
    print("Available server types:")
    
    # Group by built-in vs external
    builtin_servers = []
    external_servers = []
    
    for name, config in configs.items():
        if name == "mcp-code-checker":  # Known built-in
            builtin_servers.append((name, config))
        else:
            external_servers.append((name, config))
    
    # Display built-in servers
    if builtin_servers:
        print("\n  Built-in servers:")
        for name, config in builtin_servers:
            print(f"    • {name}: {config.display_name}")
            if args.verbose:
                print(f"      Module: {config.main_module}")
                print(f"      Parameters: {len(config.parameters)}")
                required = config.get_required_params()
                if required:
                    print(f"      Required: {', '.join(required)}")
    
    # Display external servers
    if external_servers:
        print("\n  External servers:")
        for name, config in external_servers:
            print(f"    • {name}: {config.display_name}")
            if args.verbose:
                print(f"      Module: {config.main_module}")
                print(f"      Parameters: {len(config.parameters)}")
                required = config.get_required_params()
                if required:
                    print(f"      Required: {', '.join(required)}")
    
    if args.verbose:
        print(f"\nTotal: {len(configs)} server type(s) available.")

def setup_command(args):
    """Enhanced setup command with external server support."""
    # Re-initialize to catch any newly installed servers
    if args.verbose:
        print("Checking for server configurations...")
        initialize_all_servers(verbose=True)
    
    server_config = registry.get(args.server_type)
    if not server_config:
        available = registry.list_servers()
        print(f"Error: Unknown server type '{args.server_type}'")
        print(f"Available server types: {', '.join(available)}")
        print(f"Use 'mcp-config list-server-types' to see detailed information.")
        return False
    
    # Rest of setup logic remains the same
    # ...

def init_command(args):
    """New command to re-scan for external servers."""
    print("Scanning for MCP server configurations...")
    total_count, errors = initialize_all_servers(verbose=True)
    
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  ⚠ {error}")
        print("\nSome external servers may not be available.")
    
    print(f"\nInitialization complete. {total_count} server type(s) ready.")
```

### 4. Example External Server Configuration
Create documentation showing how external packages should expose their configurations.

Create `pr_info/EXTERNAL_SERVER_EXAMPLE.md`:

```markdown
# External Server Configuration Example

External MCP packages can register their server configurations using Python entry points.

## Setup in pyproject.toml

```toml
[project.entry-points."mcp.server_configs"]
filesystem = "mcp_filesystem.config:FILESYSTEM_CONFIG"
database = "mcp_database.config:DATABASE_CONFIG"
```

## Configuration Definition

```python
# In mcp_filesystem/config.py
from mcp_config.servers import ServerConfig, ParameterDef

FILESYSTEM_CONFIG = ServerConfig(
    name="mcp-filesystem",
    display_name="MCP Filesystem",
    main_module="src/main.py", 
    parameters=[
        ParameterDef(
            name="root-dir", 
            arg_name="--root-dir", 
            param_type="path",
            required=True,
            help="Root directory for filesystem access"
        ),
        ParameterDef(
            name="read-only", 
            arg_name="--read-only", 
            param_type="boolean",
            is_flag=True,
            help="Enable read-only mode"
        ),
        ParameterDef(
            name="max-file-size", 
            arg_name="--max-file-size", 
            param_type="string",
            default="10MB",
            help="Maximum file size to read"
        )
    ]
)
```

## Usage

After installation, the external server becomes available:

```bash
mcp-config list-server-types
mcp-config setup mcp-filesystem "docs-fs" --root-dir ./docs --read-only
```
```

## Testing Requirements

Create comprehensive tests in `tests/test_config/test_discovery.py`:

### Test Categories:

1. **Server Discovery Tests**
   - Discovery with no external servers
   - Discovery with valid external servers
   - Discovery with invalid external servers
   - Entry point loading error handling

2. **Validation Tests**
   - Valid ServerConfig validation
   - Invalid ServerConfig validation (missing fields, wrong types)
   - Name conflict detection
   - Parameter validation

3. **Integration Tests**
   - External server registration with registry
   - CLI command integration
   - Error handling and reporting

4. **Mock External Servers**
   - Create mock external server configurations for testing
   - Test various error scenarios

### Example Test Structure:

```python
import pytest
from unittest.mock import Mock, patch
from src.config.discovery import (
    discover_external_servers,
    ExternalServerValidator,
    initialize_external_servers
)
from src.config.servers import ServerConfig, ParameterDef

def test_discover_no_external_servers():
    """Test discovery when no external servers are available."""
    with patch('src.config.discovery.entry_points') as mock_eps:
        mock_eps.return_value.select.return_value = []
        discovered = discover_external_servers()
        assert discovered == {}

def test_discover_valid_external_server():
    """Test discovery of valid external server."""
    # Mock a valid external server
    mock_config = ServerConfig(
        name="test-server",
        display_name="Test Server",
        main_module="test/main.py",
        parameters=[]
    )
    # Test discovery and registration
    pass

def test_external_server_validation():
    """Test external server configuration validation."""
    validator = ExternalServerValidator()
    
    # Test valid config
    valid_config = ServerConfig(...)
    is_valid, errors = validator.validate_server_config(valid_config, "test")
    assert is_valid
    assert len(errors) == 0
    
    # Test invalid config
    invalid_config = "not a server config"
    is_valid, errors = validator.validate_server_config(invalid_config, "test")
    assert not is_valid
    assert len(errors) > 0

def test_name_conflict_detection():
    """Test detection of name conflicts with built-in servers."""
    # Test server with same name as built-in
    pass
```

## Validation Criteria

### Functional Requirements:
- [ ] Entry point discovery works with both old and new importlib.metadata APIs
- [ ] External server configurations are properly validated
- [ ] Invalid external servers are rejected with clear error messages
- [ ] Name conflicts with built-in servers are detected and prevented
- [ ] CLI commands show both built-in and external servers
- [ ] Error handling doesn't break the application when external servers fail

### Quality Requirements:
- [ ] Comprehensive test coverage including error scenarios
- [ ] Clear logging and error reporting
- [ ] Graceful degradation when external servers fail to load
- [ ] No impact on performance when no external servers are present
- [ ] Thread-safe discovery and registration

### Integration Requirements:
- [ ] Seamless integration with existing ServerRegistry
- [ ] CLI commands work with external servers
- [ ] Auto-discovery on application startup
- [ ] Manual re-discovery command available

## Expected Deliverables

1. **External Discovery System**
   - `src/config/discovery.py` with complete discovery implementation
   - Validation system for external server configurations
   - Integration with existing registry

2. **Enhanced CLI**
   - Updated `list-server-types` command showing built-in vs external
   - `init` command for manual re-discovery
   - Enhanced setup command with external server support

3. **Test Suite**
   - `tests/test_config/test_discovery.py` with comprehensive coverage
   - Mock external servers for testing
   - Error scenario testing

4. **Documentation**
   - Example external server configuration
   - Instructions for external package authors

## Success Metrics

- All tests pass with >90% code coverage
- External servers can be discovered and used seamlessly
- Robust error handling for various failure modes
- Clear feedback about discovered servers and any issues
- No performance impact when no external servers are present
- Foundation ready for production use with external MCP packages

This milestone enables the MCP Configuration Helper to work with any MCP server package that follows the configuration convention, making it truly extensible.
