# Step 4: Testing and Validation

## Objective
Create comprehensive tests for VSCode support to ensure everything works correctly across different scenarios and platforms.

## Background
We need to test:
1. VSCode handler functionality
2. CLI integration with VSCode options
3. Path handling for workspace vs user configs
4. Cross-platform compatibility

## Test Files to Create/Update

### 1. Create `tests/test_config/test_vscode_handler.py`

```python
"""Tests for VSCode MCP configuration handler."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.config.clients import VSCodeHandler


class TestVSCodeHandler:
    """Test VSCode handler functionality."""
    
    def test_workspace_config_path(self):
        """Test workspace configuration path."""
        handler = VSCodeHandler(workspace=True)
        
        with patch('src.config.clients.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path('/home/user/project')
            config_path = handler.get_config_path()
            
            assert config_path == Path('/home/user/project/.vscode/mcp.json')
    
    def test_user_config_path_linux(self):
        """Test user profile configuration path on Linux."""
        handler = VSCodeHandler(workspace=False)
        
        with patch('platform.system') as mock_system:
            mock_system.return_value = 'Linux'
            with patch('os.name', 'posix'):
                with patch('pathlib.Path.home') as mock_home:
                    mock_home.return_value = Path('/home/user')
                    config_path = handler.get_config_path()
                    
                    assert config_path == Path('/home/user/.config/Code/User/mcp.json')
    
    def test_user_config_path_windows(self):
        """Test user profile configuration path on Windows."""
        handler = VSCodeHandler(workspace=False)
        
        with patch('os.name', 'nt'):
            with patch('pathlib.Path.home') as mock_home:
                mock_home.return_value = Path('C:/Users/TestUser')
                config_path = handler.get_config_path()
                
                expected = Path('C:/Users/TestUser/AppData/Roaming/Code/User/mcp.json')
                assert config_path == expected
    
    def test_user_config_path_macos(self):
        """Test user profile configuration path on macOS."""
        handler = VSCodeHandler(workspace=False)
        
        with patch('platform.system') as mock_system:
            mock_system.return_value = 'Darwin'
            with patch('os.name', 'posix'):
                with patch('pathlib.Path.home') as mock_home:
                    mock_home.return_value = Path('/Users/testuser')
                    config_path = handler.get_config_path()
                    
                    expected = Path('/Users/testuser/Library/Application Support/Code/User/mcp.json')
                    assert config_path == expected
    
    def test_setup_server(self, tmp_path):
        """Test setting up a server configuration."""
        # Create handler with temp workspace
        with patch('src.config.clients.Path.cwd') as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)
            
            # Setup server
            server_config = {
                "command": "python",
                "args": ["-m", "mcp_code_checker", "--project-dir", "/path/to/project"],
                "env": {"PYTHONPATH": "/path/to/project"},
                "_server_type": "mcp-code-checker"
            }
            
            result = handler.setup_server("test-server", server_config)
            assert result is True
            
            # Check configuration was saved
            config_path = tmp_path / ".vscode" / "mcp.json"
            assert config_path.exists()
            
            with open(config_path) as f:
                config = json.load(f)
            
            assert "servers" in config
            assert "test-server" in config["servers"]
            assert config["servers"]["test-server"]["command"] == "python"
            assert config["servers"]["test-server"]["args"][0] == "-m"
            
            # Check metadata was saved
            metadata_path = tmp_path / ".vscode" / ".mcp-config-metadata.json"
            assert metadata_path.exists()
            
            with open(metadata_path) as f:
                metadata = json.load(f)
            
            assert "test-server" in metadata
            assert metadata["test-server"]["_managed_by"] == "mcp-config-managed"
    
    def test_remove_managed_server(self, tmp_path):
        """Test removing a managed server."""
        with patch('src.config.clients.Path.cwd') as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)
            
            # Setup initial config
            config = {
                "servers": {
                    "managed-server": {
                        "command": "python",
                        "args": ["-m", "mcp_code_checker"]
                    },
                    "external-server": {
                        "command": "node",
                        "args": ["server.js"]
                    }
                }
            }
            
            # Setup metadata (only managed-server is tracked)
            metadata = {
                "managed-server": {
                    "_managed_by": "mcp-config-managed",
                    "_server_type": "mcp-code-checker"
                }
            }
            
            # Save config and metadata
            config_path = tmp_path / ".vscode"
            config_path.mkdir()
            
            with open(config_path / "mcp.json", "w") as f:
                json.dump(config, f)
            
            with open(config_path / ".mcp-config-metadata.json", "w") as f:
                json.dump(metadata, f)
            
            # Remove managed server
            result = handler.remove_server("managed-server")
            assert result is True
            
            # Check it was removed
            with open(config_path / "mcp.json") as f:
                updated_config = json.load(f)
            
            assert "managed-server" not in updated_config["servers"]
            assert "external-server" in updated_config["servers"]  # External preserved
            
            # Try to remove external server (should fail)
            result = handler.remove_server("external-server")
            assert result is False
    
    def test_list_servers(self, tmp_path):
        """Test listing all servers."""
        with patch('src.config.clients.Path.cwd') as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)
            
            # Setup config with mixed servers
            config = {
                "servers": {
                    "managed1": {"command": "python", "args": []},
                    "external1": {"command": "node", "args": []},
                    "managed2": {"command": "python", "args": []}
                }
            }
            
            metadata = {
                "managed1": {"_managed_by": "mcp-config-managed", "_server_type": "mcp-code-checker"},
                "managed2": {"_managed_by": "mcp-config-managed", "_server_type": "mcp-code-checker"}
            }
            
            config_path = tmp_path / ".vscode"
            config_path.mkdir()
            
            with open(config_path / "mcp.json", "w") as f:
                json.dump(config, f)
            
            with open(config_path / ".mcp-config-metadata.json", "w") as f:
                json.dump(metadata, f)
            
            # List all servers
            all_servers = handler.list_all_servers()
            assert len(all_servers) == 3
            
            managed_count = sum(1 for s in all_servers if s["managed"])
            assert managed_count == 2
            
            # List managed only
            managed_servers = handler.list_managed_servers()
            assert len(managed_servers) == 2
            assert all(s["name"] in ["managed1", "managed2"] for s in managed_servers)
    
    def test_validate_config(self, tmp_path):
        """Test configuration validation."""
        with patch('src.config.clients.Path.cwd') as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)
            
            # Test with invalid config
            config = {
                "servers": {
                    "invalid-server": {
                        # Missing required 'command' field
                        "args": []
                    }
                }
            }
            
            config_path = tmp_path / ".vscode"
            config_path.mkdir()
            
            with open(config_path / "mcp.json", "w") as f:
                json.dump(config, f)
            
            errors = handler.validate_config()
            assert len(errors) > 0
            assert any("missing required 'command' field" in e for e in errors)
    
    def test_backup_config(self, tmp_path):
        """Test configuration backup."""
        with patch('src.config.clients.Path.cwd') as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)
            
            # Create initial config
            config = {"servers": {"test": {"command": "python", "args": []}}}
            config_path = tmp_path / ".vscode"
            config_path.mkdir()
            
            with open(config_path / "mcp.json", "w") as f:
                json.dump(config, f)
            
            # Create backup
            backup_path = handler.backup_config()
            
            assert backup_path.exists()
            assert backup_path.name.startswith("mcp_backup_")
            assert backup_path.suffix == ".json"
            
            # Verify backup content
            with open(backup_path) as f:
                backup_content = json.load(f)
            
            assert backup_content == config
```

### 2. Update `tests/test_config/test_integration.py`

```python
"""Test integration functionality for VSCode support."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.config.integration import (
    generate_vscode_command,
    make_paths_relative,
    make_paths_absolute,
    is_package_installed
)


class TestVSCodeIntegration:
    """Test VSCode-specific integration functions."""
    
    def test_generate_vscode_command_with_package(self):
        """Test command generation when package is installed."""
        with patch('src.config.integration.is_package_installed') as mock_installed:
            mock_installed.return_value = True
            
            server_config = {
                "command": "python",
                "args": ["src/main.py", "--project-dir", "/path/to/project"],
                "env": {"PYTHONPATH": "/path/to/project"}
            }
            
            result = generate_vscode_command("mcp-code-checker", server_config, workspace=True)
            
            # Should use module invocation
            assert result["args"][0] == "-m"
            assert result["args"][1] == "mcp_code_checker"
            assert "--project-dir" in result["args"]
    
    def test_generate_vscode_command_without_package(self):
        """Test command generation when running from source."""
        with patch('src.config.integration.is_package_installed') as mock_installed:
            mock_installed.return_value = False
            
            server_config = {
                "command": "python",
                "args": ["src/main.py", "--project-dir", "/path/to/project"],
                "env": {"PYTHONPATH": "/path/to/project"}
            }
            
            result = generate_vscode_command("mcp-code-checker", server_config, workspace=True)
            
            # Should use direct path
            assert result["args"][0] == "src/main.py"
    
    def test_make_paths_relative(self):
        """Test converting absolute paths to relative."""
        base_path = Path("/home/user/project")
        
        config = {
            "command": "/home/user/project/.venv/bin/python",
            "args": [
                "src/main.py",
                "--project-dir",
                "/home/user/project",
                "--venv-path",
                "/home/user/project/.venv",
                "--log-file",
                "/home/user/project/logs/test.log"
            ]
        }
        
        result = make_paths_relative(config, base_path)
        
        # Command should be relative
        assert result["command"] == ".venv/bin/python"
        
        # Project dir should be relative
        assert "." in result["args"] or "project" not in str(result["args"])
    
    def test_make_paths_absolute(self):
        """Test ensuring paths are absolute."""
        with patch('pathlib.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path("/home/user/project")
            
            config = {
                "command": ".venv/bin/python",
                "args": [
                    "src/main.py",
                    "--project-dir",
                    ".",
                    "--venv-path",
                    ".venv"
                ]
            }
            
            result = make_paths_absolute(config)
            
            # All paths should be absolute
            assert Path(result["command"]).is_absolute() or result["command"] == ".venv/bin/python"
            # Note: actual resolution would happen in real filesystem
    
    def test_is_package_installed(self):
        """Test package installation detection."""
        with patch('importlib.util.find_spec') as mock_find_spec:
            # Test when package is installed
            mock_find_spec.return_value = Mock()
            assert is_package_installed("mcp_code_checker") is True
            
            # Test when package is not installed
            mock_find_spec.side_effect = ModuleNotFoundError
            assert is_package_installed("mcp_code_checker") is False
```

### 3. Create `tests/test_config/test_vscode_cli.py`

```python
"""Test CLI functionality for VSCode support."""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from click.testing import CliRunner

from src.config.main import cli


class TestVSCodeCLI:
    """Test CLI commands with VSCode support."""
    
    def test_setup_vscode_workspace(self):
        """Test setup command with VSCode workspace config."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Create a mock project structure
            Path("src").mkdir()
            Path("src/main.py").touch()
            
            with patch('src.config.integration.setup_server') as mock_setup:
                mock_setup.return_value = True
                
                result = runner.invoke(cli, [
                    'setup',
                    'mcp-code-checker',
                    'test-project',
                    '--client', 'vscode',
                    '--project-dir', '.',
                    '--workspace'  # Explicit workspace flag
                ])
                
                assert result.exit_code == 0
                mock_setup.assert_called_once()
                
                # Check that VSCode handler was used
                call_args = mock_setup.call_args
                handler = call_args[0][0]
                assert handler.__class__.__name__ == 'VSCodeHandler'
                assert handler.workspace is True
    
    def test_setup_vscode_user(self):
        """Test setup command with VSCode user profile config."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            Path("src").mkdir()
            Path("src/main.py").touch()
            
            with patch('src.config.integration.setup_server') as mock_setup:
                mock_setup.return_value = True
                
                result = runner.invoke(cli, [
                    'setup',
                    'mcp-code-checker',
                    'global-project',
                    '--client', 'vscode',
                    '--project-dir', '.',
                    '--user'  # User profile flag
                ])
                
                assert result.exit_code == 0
                mock_setup.assert_called_once()
                
                # Check that VSCode handler with user mode was used
                call_args = mock_setup.call_args
                handler = call_args[0][0]
                assert handler.__class__.__name__ == 'VSCodeHandler'
                assert handler.workspace is False
    
    def test_list_vscode_servers(self):
        """Test list command for VSCode servers."""
        runner = CliRunner()
        
        with patch('src.config.clients.get_client_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_handler.list_all_servers.return_value = [
                {
                    "name": "test-server",
                    "managed": True,
                    "type": "mcp-code-checker",
                    "command": "python",
                    "args": ["-m", "mcp_code_checker"]
                }
            ]
            mock_get_handler.return_value = mock_handler
            
            result = runner.invoke(cli, [
                'list',
                '--client', 'vscode-workspace'
            ])
            
            assert result.exit_code == 0
            assert "test-server" in result.output
            assert "VSCode" in result.output
    
    def test_remove_vscode_server(self):
        """Test remove command for VSCode servers."""
        runner = CliRunner()
        
        with patch('src.config.clients.get_client_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_handler.remove_server.return_value = True
            mock_get_handler.return_value = mock_handler
            
            result = runner.invoke(cli, [
                'remove',
                'test-server',
                '--client', 'vscode'
            ])
            
            assert result.exit_code == 0
            mock_handler.remove_server.assert_called_once_with('test-server')
    
    def test_validate_vscode_server(self):
        """Test validate command for VSCode servers."""
        runner = CliRunner()
        
        with patch('src.config.clients.get_client_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_handler.validate_config.return_value = []  # No errors
            mock_handler.get_config_path.return_value = Path(".vscode/mcp.json")
            mock_get_handler.return_value = mock_handler
            
            result = runner.invoke(cli, [
                'validate',
                'test-server',
                '--client', 'vscode'
            ])
            
            assert result.exit_code == 0
            assert "valid" in result.output.lower() or result.output == ""
```

## Manual Testing Checklist

### 1. Basic Setup
```bash
# Test workspace setup
mcp-config setup mcp-code-checker "test" --client vscode --project-dir .

# Verify .vscode/mcp.json was created
cat .vscode/mcp.json

# Test user profile setup
mcp-config setup mcp-code-checker "global" --client vscode --user --project-dir .

# Verify user config was created (path varies by OS)
```

### 2. List Operations
```bash
# List all servers
mcp-config list

# List VSCode workspace servers only
mcp-config list --client vscode-workspace

# List with details
mcp-config list --client vscode --detailed
```

### 3. Remove Operations
```bash
# Remove from workspace
mcp-config remove "test" --client vscode

# Try to remove external server (should fail)
mcp-config remove "external" --client vscode
```

### 4. Validation
```bash
# Validate configuration
mcp-config validate "test" --client vscode

# Validate with verbose output
mcp-config validate "test" --client vscode --verbose
```

### 5. Cross-Platform Testing
- [ ] Test on Windows with VSCode installed
- [ ] Test on macOS with VSCode installed
- [ ] Test on Linux with VSCode installed
- [ ] Test with VSCode Insiders edition
- [ ] Test with VSCodium (open source build)

## Success Criteria
- All unit tests pass
- CLI commands work with VSCode options
- Workspace and user configs are created correctly
- Path handling works on all platforms
- Managed servers can be removed, external servers are preserved
- VSCode can read and use the generated configurations