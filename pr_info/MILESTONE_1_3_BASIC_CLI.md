# Milestone 1.3: Basic CLI Implementation

## Overview
Implement the command-line interface (CLI) for the MCP configuration helper. This milestone creates the user-facing commands (`setup`, `remove`, `list`) with path auto-detection and basic functionality. This completes Phase 1 with a working configuration tool.

## Context
You are working on an MCP configuration helper tool. The full requirements are in `CONFIG_HELPER_REQUIREMENTS.md` in the same directory. This milestone builds on:
- Milestone 1.1: Configuration data model (`src/config/servers.py`, `src/config/utils.py`)
- Milestone 1.2: Claude Desktop handler (`src/config/clients.py`, `src/config/integration.py`, `src/config/detection.py`)

## Implementation Requirements

### 1. CLI Entry Point

#### File: `src/config/main.py`

Create the main CLI application:

```python
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from .servers import registry
from .clients import get_client_handler
from .integration import setup_mcp_server, remove_mcp_server
from .detection import detect_python_environment
from .utils import validate_required_parameters

def create_main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="mcp-config",
        description="MCP Configuration Helper - Automate MCP server setup for Claude Desktop and other clients",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp-config setup mcp-code-checker my-checker --project-dir .
  mcp-config setup mcp-code-checker debug --project-dir . --log-level DEBUG --keep-temp-files
  mcp-config remove my-checker
  mcp-config list --detailed
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.required = True
    
    # Add subcommand parsers
    add_setup_parser(subparsers)
    add_remove_parser(subparsers)
    add_list_parser(subparsers)
    
    return parser

def add_setup_parser(subparsers):
    """Add the setup command parser."""
    # Implementation needed
    pass

def add_remove_parser(subparsers):
    """Add the remove command parser."""
    # Implementation needed
    pass

def add_list_parser(subparsers):
    """Add the list command parser."""
    # Implementation needed
    pass

def handle_setup_command(args) -> int:
    """Handle the setup command."""
    # Implementation needed
    pass

def handle_remove_command(args) -> int:
    """Handle the remove command."""
    # Implementation needed
    pass

def handle_list_command(args) -> int:
    """Handle the list command."""
    # Implementation needed
    pass

def main() -> int:
    """Main CLI entry point."""
    try:
        parser = create_main_parser()
        args = parser.parse_args()
        
        # Dispatch to appropriate handler
        if args.command == 'setup':
            return handle_setup_command(args)
        elif args.command == 'remove':
            return handle_remove_command(args)
        elif args.command == 'list':
            return handle_list_command(args)
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### 2. Setup Command Implementation

The setup command should:
1. **Dynamic Parameter Generation:** Generate CLI options based on ServerConfig
2. **Auto-Detection:** Detect Python executable and virtual environment
3. **Validation:** Validate required parameters and project structure
4. **Dry-Run Support:** Preview changes without applying them

```python
def add_setup_parser(subparsers):
    """Add the setup command parser with dynamic options."""
    setup_parser = subparsers.add_parser(
        'setup', 
        help='Setup an MCP server configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Setup an MCP server in Claude Desktop configuration"
    )
    
    # Positional arguments
    setup_parser.add_argument(
        'server_type', 
        help='Server type (currently only "mcp-code-checker" supported)'
    )
    setup_parser.add_argument(
        'server_name', 
        help='Name for this server instance'
    )
    
    # Global options
    setup_parser.add_argument(
        '--client', 
        default='claude-desktop', 
        choices=['claude-desktop'],
        help='MCP client to configure (default: claude-desktop)'
    )
    setup_parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Preview changes without applying them'
    )
    setup_parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Show detailed output'
    )
    setup_parser.add_argument(
        '--backup', 
        action='store_true', 
        default=True,
        help='Create backup before making changes (default: true)'
    )
    
    # Add server-specific options dynamically
    # This will be implemented to read from ServerConfig
    add_server_specific_options(setup_parser, "mcp-code-checker")

def add_server_specific_options(parser: argparse.ArgumentParser, server_type: str):
    """Add server-specific CLI options based on ServerConfig."""
    server_config = registry.get(server_type)
    if not server_config:
        return
    
    for param in server_config.parameters:
        option_name = f'--{param.name}'
        
        kwargs = {
            'help': param.help,
            'dest': param.name.replace('-', '_')  # Convert to valid Python identifier
        }
        
        if param.required:
            kwargs['required'] = True
        
        if param.default is not None:
            kwargs['default'] = param.default
        
        if param.param_type == "boolean" and param.is_flag:
            kwargs['action'] = 'store_true'
        elif param.param_type == "choice":
            kwargs['choices'] = param.choices
        elif param.param_type == "path":
            kwargs['type'] = Path
        
        parser.add_argument(option_name, **kwargs)
```

### 3. Command Handlers

#### Setup Command Handler

```python
def handle_setup_command(args) -> int:
    """Handle the setup command with full validation and auto-detection."""
    try:
        # Validate server type
        server_config = registry.get(args.server_type)
        if not server_config:
            print(f"Error: Unknown server type '{args.server_type}'")
            print(f"Available types: {', '.join(registry.list_servers())}")
            return 1
        
        # Get client handler
        client_handler = get_client_handler(args.client)
        
        # Extract user parameters from args
        user_params = extract_user_parameters(args, server_config)
        
        # Auto-detect Python environment if not provided
        if 'python_executable' not in user_params or not user_params['python_executable']:
            project_dir = Path(user_params.get('project_dir', '.'))
            python_exe, venv_path = detect_python_environment(project_dir)
            user_params['python_executable'] = python_exe
            if venv_path and 'venv_path' not in user_params:
                user_params['venv_path'] = venv_path
        
        # Validate parameters
        validation_errors = validate_required_parameters(server_config, user_params)
        if validation_errors:
            print("Validation errors:")
            for error in validation_errors:
                print(f"  - {error}")
            return 1
        
        # Show what will be done
        if args.verbose or args.dry_run:
            print_setup_summary(args.server_name, server_config, user_params, args.client)
        
        if args.dry_run:
            print("\nDry run completed. No changes made.")
            return 0
        
        # Perform setup
        result = setup_mcp_server(
            client_handler=client_handler,
            server_config=server_config,
            server_name=args.server_name,
            user_params=user_params,
            python_executable=user_params['python_executable'],
            dry_run=False
        )
        
        if result['success']:
            print(f"✓ Successfully configured server '{args.server_name}'")
            if 'backup_path' in result:
                print(f"  Backup created: {result['backup_path']}")
            print(f"  Configuration saved to: {client_handler.get_config_path()}")
            return 0
        else:
            print(f"✗ Failed to configure server: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"Setup failed: {e}")
        return 1

def extract_user_parameters(args, server_config) -> Dict[str, Any]:
    """Extract user-provided parameters from CLI args."""
    # Implementation needed
    pass

def print_setup_summary(server_name: str, server_config, user_params: Dict[str, Any], client: str):
    """Print a summary of what will be configured."""
    # Implementation needed
    pass
```

#### Remove Command Handler

```python
def handle_remove_command(args) -> int:
    """Handle the remove command with safety checks."""
    try:
        # Get client handler
        client_handler = get_client_handler(args.client)
        
        # Check if server exists and is managed by us
        managed_servers = client_handler.list_managed_servers()
        managed_names = [s['name'] for s in managed_servers]
        
        if args.server_name not in managed_names:
            all_servers = client_handler.list_all_servers()
            all_names = [s['name'] for s in all_servers]
            
            if args.server_name in all_names:
                print(f"Error: Server '{args.server_name}' exists but is not managed by mcp-config")
                print("Only servers created by mcp-config can be removed")
                return 1
            else:
                print(f"Error: Server '{args.server_name}' not found")
                if managed_names:
                    print(f"Managed servers: {', '.join(managed_names)}")
                return 1
        
        # Show what will be removed
        if args.verbose or args.dry_run:
            server_info = next(s for s in managed_servers if s['name'] == args.server_name)
            print(f"Will remove server '{args.server_name}':")
            print(f"  Type: {server_info['type']}")
            print(f"  Command: {server_info['command']}")
        
        if args.dry_run:
            print("\nDry run completed. No changes made.")
            return 0
        
        # Perform removal
        result = remove_mcp_server(
            client_handler=client_handler,
            server_name=args.server_name,
            dry_run=False
        )
        
        if result['success']:
            print(f"✓ Successfully removed server '{args.server_name}'")
            if 'backup_path' in result:
                print(f"  Backup created: {result['backup_path']}")
            return 0
        else:
            print(f"✗ Failed to remove server: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"Remove failed: {e}")
        return 1
```

#### List Command Handler

```python
def handle_list_command(args) -> int:
    """Handle the list command with detailed output."""
    try:
        # Get client handler(s)
        if args.client:
            clients = [args.client]
        else:
            clients = ['claude-desktop']  # Default for now
        
        for client_name in clients:
            client_handler = get_client_handler(client_name)
            
            print(f"\n{client_name.title()} Configuration:")
            print(f"Config file: {client_handler.get_config_path()}")
            
            if args.managed_only:
                servers = client_handler.list_managed_servers()
                title = "Managed Servers"
            else:
                servers = client_handler.list_all_servers()
                title = "All Servers"
            
            if not servers:
                print(f"  No servers found")
                continue
            
            print(f"\n{title}:")
            for server in servers:
                print_server_info(server, args.detailed)
        
        return 0
        
    except Exception as e:
        print(f"List failed: {e}")
        return 1

def print_server_info(server: Dict[str, Any], detailed: bool = False):
    """Print formatted server information."""
    managed_mark = "●" if server['managed'] else "○"
    print(f"  {managed_mark} {server['name']} ({server['type']})")
    
    if detailed:
        print(f"    Command: {server['command']}")
        if server['args']:
            print(f"    Args: {' '.join(server['args'])}")
        if not server['managed']:
            print(f"    Note: External server (not managed by mcp-config)")
        print()
```

### 4. Package Entry Point

#### File: `pyproject.toml` (add to existing)

Add the CLI entry point:

```toml
[project.scripts]
mcp-config = "src.config.main:main"
```

### 5. Output Formatting

Create user-friendly output with proper formatting:

#### File: `src/config/output.py`

```python
from typing import Dict, Any, List
from pathlib import Path

class OutputFormatter:
    """Handle formatted output for CLI commands."""
    
    @staticmethod
    def print_success(message: str):
        """Print success message with checkmark."""
        print(f"✓ {message}")
    
    @staticmethod
    def print_error(message: str):
        """Print error message with X mark."""
        print(f"✗ {message}")
    
    @staticmethod
    def print_info(message: str):
        """Print informational message."""
        print(f"ℹ {message}")
    
    @staticmethod
    def print_setup_summary(server_name: str, server_type: str, params: Dict[str, Any]):
        """Print formatted setup summary."""
        print(f"\nSetup Summary:")
        print(f"  Server Name: {server_name}")
        print(f"  Server Type: {server_type}")
        print(f"  Parameters:")
        
        for key, value in params.items():
            if value is not None:
                print(f"    {key.replace('_', '-')}: {value}")
    
    @staticmethod
    def print_server_list(servers: List[Dict[str, Any]], detailed: bool = False):
        """Print formatted server list."""
        if not servers:
            print("  No servers found")
            return
        
        for server in servers:
            managed_icon = "●" if server['managed'] else "○"
            print(f"  {managed_icon} {server['name']} ({server['type']})")
            
            if detailed:
                print(f"    Command: {server.get('command', 'N/A')}")
                if server.get('args'):
                    args_str = ' '.join(server['args'])
                    if len(args_str) > 80:
                        args_str = args_str[:77] + "..."
                    print(f"    Args: {args_str}")
                
                if not server['managed']:
                    print(f"    Note: External server (not managed by mcp-config)")
                print()
```

## Implementation Details

### CLI Argument Processing
- Use `argparse` with proper help text and formatting
- Convert CLI args (kebab-case) to parameter names (snake_case)
- Handle boolean flags correctly (presence = True)
- Validate required parameters before processing

### Auto-Detection Logic
- Check for virtual environments in standard locations (.venv, venv, etc.)
- Fall back to system Python if no venv found
- Validate detected Python executable
- Show detected values in verbose mode

### Error Handling
- Catch and display user-friendly error messages
- Provide suggestions when possible
- Use appropriate exit codes (0 = success, 1 = error)
- Show stack traces only in verbose mode

### Path Handling
- Convert relative paths to absolute paths
- Validate path existence for critical paths
- Handle cross-platform path differences
- Normalize path separators

## Test Requirements

### File: `tests/test_config/test_main.py`

Create comprehensive CLI tests:

1. **Argument Parsing Tests:**
   ```python
   def test_main_parser_creation():
       parser = create_main_parser()
       assert parser.prog == "mcp-config"
   
   def test_setup_command_parsing():
       # Test all argument combinations
       pass
   
   def test_invalid_arguments():
       # Test error handling
       pass
   ```

2. **Command Handler Tests:**
   ```python
   def test_setup_command_success():
       # Mock successful setup
       pass
   
   def test_setup_command_validation_errors():
       # Test parameter validation
       pass
   
   def test_remove_command_success():
       # Mock successful removal
       pass
   
   def test_remove_external_server_error():
       # Should refuse to remove external servers
       pass
   
   def test_list_command_output():
       # Test output formatting
       pass
   ```

3. **Auto-Detection Tests:**
   ```python
   def test_python_detection():
       # Test Python executable detection
       pass
   
   def test_venv_detection():
       # Test virtual environment detection
       pass
   ```

4. **Integration Tests:**
   ```python
   def test_end_to_end_setup():
       # Full setup workflow
       pass
   
   def test_dry_run_functionality():
       # Dry run should not make changes
       pass
   ```

### File: `tests/test_config/test_output.py`

Create output formatting tests:
- Success/error message formatting
- Server list formatting
- Setup summary formatting
- Long argument truncation

## Manual Testing

Create a test script to verify CLI functionality:

#### File: `tests/manual_cli_test.py`

```python
#!/usr/bin/env python3
"""Manual testing script for CLI functionality."""

import subprocess
import sys
from pathlib import Path

def run_command(cmd: list) -> tuple:
    """Run a command and return (return_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"

def test_cli_commands():
    """Test basic CLI commands."""
    tests = [
        # Help commands
        (["mcp-config", "--help"], 0),
        (["mcp-config", "setup", "--help"], 0),
        (["mcp-config", "remove", "--help"], 0),
        (["mcp-config", "list", "--help"], 0),
        
        # List command (should work even with no config)
        (["mcp-config", "list"], 0),
        
        # Dry run setup
        (["mcp-config", "setup", "mcp-code-checker", "test", "--project-dir", ".", "--dry-run"], 0),
        
        # Invalid commands
        (["mcp-config", "invalid"], 1),
        (["mcp-config", "setup", "invalid-server"], 1),
    ]
    
    for cmd, expected_code in tests:
        print(f"Testing: {' '.join(cmd)}")
        code, stdout, stderr = run_command(cmd)
        
        if code == expected_code:
            print(f"  ✓ PASS (exit code: {code})")
        else:
            print(f"  ✗ FAIL (expected: {expected_code}, got: {code})")
            if stderr:
                print(f"    stderr: {stderr}")
        print()

if __name__ == "__main__":
    test_cli_commands()
```

## Acceptance Criteria

1. **CLI Entry Point Works:**
   ```bash
   mcp-config --help
   # Should show main help with subcommands
   ```

2. **Setup Command Works:**
   ```bash
   mcp-config setup mcp-code-checker test --project-dir . --dry-run
   # Should show what would be configured without errors
   ```

3. **Remove Command Works:**
   ```bash
   mcp-config remove nonexistent
   # Should show appropriate error message
   ```

4. **List Command Works:**
   ```bash
   mcp-config list
   # Should show current configuration (even if empty)
   ```

5. **Auto-Detection Works:**
   ```python
   from src.config.detection import detect_python_environment
   python_exe, venv_path = detect_python_environment(Path("."))
   assert python_exe is not None
   ```

6. **All Tests Pass:**
   ```bash
   pytest tests/test_config/test_main.py -v
   pytest tests/test_config/test_output.py -v
   python tests/manual_cli_test.py
   ```

7. **Package Installation Works:**
   ```bash
   pip install -e .
   mcp-config --help
   # Should work from anywhere
   ```

## Next Steps
After completing this milestone, you'll have a working CLI tool that can configure MCP Code Checker servers in Claude Desktop. This completes Phase 1, and you can move on to Phase 2 (Enhanced Functionality) or Phase 3 (Extensibility).
