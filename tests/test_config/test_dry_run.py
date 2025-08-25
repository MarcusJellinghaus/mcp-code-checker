"""Tests for dry-run functionality."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config.clients import ClaudeDesktopHandler
from src.config.integration import setup_mcp_server, remove_mcp_server, generate_client_config
from src.config.servers import ServerConfig, ParameterDef


class TestDryRunFunctionality:
    """Test dry-run mode for all commands."""
    
    def test_setup_dry_run(self, tmp_path: Path) -> None:
        """Test setup command in dry-run mode."""
        # Create mock server config
        server_config = ServerConfig(
            name="test-server",
            display_name="Test Server",
            main_module="test.module",
            parameters=[
                ParameterDef(
                    name="project-dir",
                    arg_name="--project-dir",
                    param_type="path",
                    required=True,
                    help="Project directory"
                )
            ]
        )
        
        # Create mock client handler
        mock_client = MagicMock(spec=ClaudeDesktopHandler)
        mock_client.get_config_path.return_value = tmp_path / "config.json"
        mock_client.setup_server.return_value = True
        
        # Test parameters
        user_params = {
            "project_dir": str(tmp_path)
        }
        
        # Run setup in dry-run mode
        result = setup_mcp_server(
            client_handler=mock_client,
            server_config=server_config,
            server_name="my-test",
            user_params=user_params,
            python_executable=sys.executable,
            dry_run=True
        )
        
        # Verify results
        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["operation"] == "setup"
        assert "Would set up server" in result["message"]
        
        # Verify no actual changes were made
        mock_client.setup_server.assert_not_called()
        
    def test_remove_dry_run(self, tmp_path: Path) -> None:
        """Test remove command in dry-run mode."""
        # Create mock client handler
        mock_client = MagicMock(spec=ClaudeDesktopHandler)
        mock_client.get_config_path.return_value = tmp_path / "config.json"
        mock_client.list_all_servers.return_value = [
            {
                "name": "my-server",
                "managed": True,
                "type": "mcp-code-checker"
            }
        ]
        mock_client.remove_server.return_value = True
        
        # Run remove in dry-run mode
        result = remove_mcp_server(
            client_handler=mock_client,
            server_name="my-server",
            dry_run=True
        )
        
        # Verify results
        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["operation"] == "remove"
        assert "Would remove server" in result["message"]
        
        # Verify no actual changes were made
        mock_client.remove_server.assert_not_called()
        
    def test_dry_run_validation_succeeds_when_params_valid(self, tmp_path: Path) -> None:
        """Test dry-run proceeds when all parameters are valid."""
        # Create mock server config with required parameter
        server_config = ServerConfig(
            name="test-server",
            display_name="Test Server",
            main_module="test.module",
            parameters=[
                ParameterDef(
                    name="required-param",
                    arg_name="--required-param",
                    param_type="string",
                    required=True,
                    help="Required parameter"
                )
            ]
        )
        
        # Create mock client handler
        mock_client = MagicMock(spec=ClaudeDesktopHandler)
        mock_client.get_config_path.return_value = tmp_path / "config.json"
        
        # Provide required parameter (using underscore format)
        user_params = {
            "required_param": "test_value"
        }
        
        # Should succeed in dry-run with valid params
        result = setup_mcp_server(
            client_handler=mock_client,
            server_config=server_config,
            server_name="test",
            user_params=user_params,
            dry_run=True
        )
        
        # Should be successful
        assert result["success"] is True
        assert result["dry_run"] is True
        
        # Verify no setup was attempted
        mock_client.setup_server.assert_not_called()
        
    def test_generate_client_config_validation(self) -> None:
        """Test that generate_client_config validates required parameters."""
        # Create server config with required parameter
        server_config = ServerConfig(
            name="test-server",
            display_name="Test Server",
            main_module="test.module",
            parameters=[
                ParameterDef(
                    name="required-param",
                    arg_name="--required-param",
                    param_type="string",
                    required=True,
                    help="Required parameter"
                )
            ]
        )
        
        # Missing required parameter
        user_params: dict[str, str] = {}
        
        # Should raise ValueError for missing required parameter
        with pytest.raises(ValueError, match="Parameter validation failed"):
            generate_client_config(
                server_config=server_config,
                server_name="test",
                user_params=user_params
            )


class TestDryRunOutput:
    """Test dry-run output formatting."""
    
    @patch("src.config.output.OutputFormatter.print_dry_run_header")
    @patch("src.config.output.OutputFormatter.print_dry_run_config_preview")
    def test_setup_dry_run_output(self, mock_preview: MagicMock, mock_header: MagicMock) -> None:
        """Test that dry-run setup produces correct output."""
        from src.config.main import handle_setup_command
        
        # Create mock args
        mock_args = MagicMock()
        mock_args.server_type = "mcp-code-checker"
        mock_args.server_name = "test-checker"
        mock_args.client = "claude-desktop"
        mock_args.dry_run = True
        mock_args.verbose = False
        mock_args.backup = True
        mock_args.project_dir = "."
        
        # Mock registry
        with patch("src.config.main.registry") as mock_registry:
            mock_server_config = MagicMock()
            mock_server_config.name = "mcp-code-checker"
            mock_server_config.parameters = []
            mock_registry.get.return_value = mock_server_config
            
            # Mock other dependencies
            with patch("src.config.main.get_client_handler") as mock_get_client:
                mock_client = MagicMock()
                mock_client.get_config_path.return_value = Path("/tmp/config.json")
                mock_get_client.return_value = mock_client
                
                with patch("src.config.main.extract_user_parameters") as mock_extract:
                    mock_extract.return_value = {"project_dir": "."}
                    
                    with patch("src.config.main.detect_python_environment") as mock_detect:
                        mock_detect.return_value = ("/usr/bin/python", None)
                        
                        with patch("src.config.main.validate_required_parameters") as mock_validate:
                            mock_validate.return_value = []
                            
                            # Run the command
                            result = handle_setup_command(mock_args)
                            
                            # Verify dry-run output was called
                            mock_header.assert_called_once()
                            mock_preview.assert_called_once()
                            
                            # Should return success
                            assert result == 0
                            
    @patch("src.config.output.OutputFormatter.print_dry_run_header")
    @patch("src.config.output.OutputFormatter.print_dry_run_remove_preview")
    def test_remove_dry_run_output(self, mock_preview: MagicMock, mock_header: MagicMock) -> None:
        """Test that dry-run remove produces correct output."""
        from src.config.main import handle_remove_command
        
        # Create mock args
        mock_args = MagicMock()
        mock_args.server_name = "test-checker"
        mock_args.client = "claude-desktop"
        mock_args.dry_run = True
        mock_args.verbose = False
        mock_args.backup = True
        
        # Mock client handler
        with patch("src.config.main.get_client_handler") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_config_path.return_value = Path("/tmp/config.json")
            mock_client.list_managed_servers.return_value = [
                {"name": "test-checker", "type": "mcp-code-checker", "command": "python"}
            ]
            mock_client.list_all_servers.return_value = [
                {"name": "test-checker", "type": "mcp-code-checker", "managed": True},
                {"name": "other", "type": "external", "managed": False}
            ]
            mock_get_client.return_value = mock_client
            
            # Run the command
            result = handle_remove_command(mock_args)
            
            # Verify dry-run output was called
            mock_header.assert_called_once()
            mock_preview.assert_called_once()
            
            # Verify preview was called with correct arguments
            call_args = mock_preview.call_args[0]
            assert call_args[0] == "test-checker"  # server_name
            assert call_args[1]["name"] == "test-checker"  # server_info
            
            # Should return success
            assert result == 0
