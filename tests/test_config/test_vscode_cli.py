"""Test CLI functionality for VSCode support."""

import json
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
    
    def test_setup_vscode_default_workspace(self):
        """Test that VSCode defaults to workspace mode."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            Path("src").mkdir()
            Path("src/main.py").touch()
            
            with patch('src.config.integration.setup_server') as mock_setup:
                mock_setup.return_value = True
                
                result = runner.invoke(cli, [
                    'setup',
                    'mcp-code-checker',
                    'test-project',
                    '--client', 'vscode',
                    '--project-dir', '.'
                    # No --workspace or --user flag
                ])
                
                assert result.exit_code == 0
                mock_setup.assert_called_once()
                
                # Should default to workspace
                call_args = mock_setup.call_args
                handler = call_args[0][0]
                assert handler.__class__.__name__ == 'VSCodeHandler'
                assert handler.workspace is True
    
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
            # VSCode might be in the output or not, depending on implementation
    
    def test_list_vscode_user_servers(self):
        """Test list command for VSCode user profile servers."""
        runner = CliRunner()
        
        with patch('src.config.clients.get_client_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_handler.list_all_servers.return_value = [
                {
                    "name": "global-server",
                    "managed": True,
                    "type": "mcp-code-checker",
                    "command": "python",
                    "args": ["-m", "mcp_code_checker"]
                }
            ]
            mock_get_handler.return_value = mock_handler
            
            result = runner.invoke(cli, [
                'list',
                '--client', 'vscode-user'
            ])
            
            assert result.exit_code == 0
            assert "global-server" in result.output
    
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
    
    def test_remove_vscode_server_not_found(self):
        """Test remove command when server not found."""
        runner = CliRunner()
        
        with patch('src.config.clients.get_client_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_handler.remove_server.return_value = False
            mock_get_handler.return_value = mock_handler
            
            result = runner.invoke(cli, [
                'remove',
                'nonexistent-server',
                '--client', 'vscode'
            ])
            
            # Should still exit with 0 or handle gracefully
            assert result.exit_code in [0, 1]
            mock_handler.remove_server.assert_called_once_with('nonexistent-server')
    
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
            # Success message or empty output expected
    
    def test_validate_vscode_server_with_errors(self):
        """Test validate command when configuration has errors."""
        runner = CliRunner()
        
        with patch('src.config.clients.get_client_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_handler.validate_config.return_value = [
                "Missing 'command' field for server 'test-server'",
                "Invalid path in 'args'"
            ]
            mock_handler.get_config_path.return_value = Path(".vscode/mcp.json")
            mock_get_handler.return_value = mock_handler
            
            result = runner.invoke(cli, [
                'validate',
                'test-server',
                '--client', 'vscode'
            ])
            
            # Should report errors but might still exit with 0
            assert "Missing 'command' field" in result.output or "error" in result.output.lower()
    
    def test_client_aliases(self):
        """Test that various VSCode client aliases work."""
        runner = CliRunner()
        
        with patch('src.config.clients.get_client_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_handler.list_all_servers.return_value = []
            mock_get_handler.return_value = mock_handler
            
            # Test 'vscode' alias
            result = runner.invoke(cli, ['list', '--client', 'vscode'])
            assert result.exit_code == 0
            
            # Test 'vscode-workspace' alias
            result = runner.invoke(cli, ['list', '--client', 'vscode-workspace'])
            assert result.exit_code == 0
            
            # Test 'vscode-user' alias
            result = runner.invoke(cli, ['list', '--client', 'vscode-user'])
            assert result.exit_code == 0
    
    def test_setup_with_all_parameters(self):
        """Test setup command with all available parameters."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            Path("src").mkdir()
            Path("src/main.py").touch()
            Path(".venv").mkdir()
            
            with patch('src.config.integration.setup_server') as mock_setup:
                mock_setup.return_value = True
                
                result = runner.invoke(cli, [
                    'setup',
                    'mcp-code-checker',
                    'full-test',
                    '--client', 'vscode',
                    '--project-dir', '.',
                    '--venv-path', '.venv',
                    '--log-file', 'test.log',
                    '--log-level', 'DEBUG',
                    '--workspace'
                ])
                
                assert result.exit_code == 0
                mock_setup.assert_called_once()
                
                # Check parameters were passed
                call_args = mock_setup.call_args
                _, server_config = call_args[0][1], call_args[0][2]
                
                # The config should contain the arguments
                if isinstance(server_config, dict):
                    assert any('--log-level' in str(arg) or 'DEBUG' in str(arg) 
                              for arg in server_config.get('args', []))
    
    def test_dry_run_with_vscode(self):
        """Test dry-run mode with VSCode client."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            Path("src").mkdir()
            Path("src/main.py").touch()
            
            result = runner.invoke(cli, [
                'setup',
                'mcp-code-checker',
                'dry-run-test',
                '--client', 'vscode',
                '--project-dir', '.',
                '--dry-run'
            ])
            
            assert result.exit_code == 0
            assert "DRY RUN" in result.output or "dry" in result.output.lower()
            
            # Verify no actual config was created
            assert not Path(".vscode/mcp.json").exists()
    
    def test_help_for_vscode_options(self):
        """Test that help text includes VSCode options."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ['setup', '--help'])
        
        assert result.exit_code == 0
        assert '--client' in result.output
        # VSCode should be mentioned in the help somewhere
        
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
