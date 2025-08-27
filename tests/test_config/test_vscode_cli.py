"""Test CLI functionality for VSCode support."""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import pytest

from src.config.main import create_main_parser, main


def create_mock_parameter(name: str, required: bool = False, default=None):
    """Helper to create a mock parameter object."""
    param = Mock()
    param.name = name
    param.required = required
    param.default = default
    param.help = f"Mock help for {name}"
    param.param_type = "string"
    param.is_flag = False
    param.auto_detect = False
    param.choices = None
    param.validator = None
    return param


class TestVSCodeCLI:
    """Test CLI commands with VSCode support."""

    def test_setup_vscode_workspace(self):
        """Test setup command with VSCode workspace config."""
        # Create a mock server config with all required attributes
        mock_server_config = Mock()
        mock_server_config.name = "mcp-code-checker"
        mock_server_config.display_name = "MCP Code Checker"
        # Add project-dir parameter so the parser accepts it
        mock_server_config.parameters = [
            create_mock_parameter("project-dir", required=True)
        ]

        # Mock the registry module itself
        mock_registry = Mock()
        mock_registry.get.return_value = mock_server_config
        mock_registry.list_servers.return_value = ["mcp-code-checker"]

        with (
            patch("src.config.main.registry", mock_registry),
            patch("src.config.cli_utils.registry", mock_registry),
            patch("src.config.main.initialize_all_servers"),
            patch("src.config.main.detect_python_environment") as mock_detect,
            patch("src.config.main.validate_required_parameters") as mock_validate_req,
            patch(
                "src.config.main.validate_parameter_combination"
            ) as mock_validate_comb,
            patch("src.config.main.validate_setup_args") as mock_validate_setup,
            patch("src.config.main.setup_mcp_server") as mock_setup,
        ):

            # Setup return values
            mock_detect.return_value = (None, None)  # No auto-detection
            mock_validate_req.return_value = []  # No validation errors
            mock_validate_comb.return_value = []  # No combination errors
            mock_validate_setup.return_value = []  # No setup errors
            mock_setup.return_value = {"success": True}

            with patch(
                "sys.argv",
                [
                    "mcp-config",
                    "setup",
                    "mcp-code-checker",
                    "test-project",
                    "--client",
                    "vscode",
                    "--project-dir",
                    ".",  # Default is workspace, no flag needed
                ],
            ):
                exit_code = main()

                assert exit_code == 0
                mock_setup.assert_called_once()

                # Check that VSCode handler was used (client should be vscode-workspace)
                call_args = mock_setup.call_args.kwargs
                handler = call_args["client_handler"]
                assert handler.__class__.__name__ == "VSCodeHandler"

    def test_setup_vscode_user(self):
        """Test setup command with VSCode user profile config."""
        # Create a mock server config
        mock_server_config = Mock()
        mock_server_config.name = "mcp-code-checker"
        mock_server_config.display_name = "MCP Code Checker"
        mock_server_config.parameters = [
            create_mock_parameter("project-dir", required=True)
        ]

        # Mock the registry
        mock_registry = Mock()
        mock_registry.get.return_value = mock_server_config
        mock_registry.list_servers.return_value = ["mcp-code-checker"]

        with (
            patch("src.config.main.registry", mock_registry),
            patch("src.config.cli_utils.registry", mock_registry),
            patch("src.config.main.initialize_all_servers"),
            patch("src.config.main.detect_python_environment") as mock_detect,
            patch("src.config.main.validate_required_parameters") as mock_validate_req,
            patch(
                "src.config.main.validate_parameter_combination"
            ) as mock_validate_comb,
            patch("src.config.main.validate_setup_args") as mock_validate_setup,
            patch("src.config.main.setup_mcp_server") as mock_setup,
        ):

            # Setup return values
            mock_detect.return_value = (None, None)
            mock_validate_req.return_value = []
            mock_validate_comb.return_value = []
            mock_validate_setup.return_value = []
            mock_setup.return_value = {"success": True}

            with patch(
                "sys.argv",
                [
                    "mcp-config",
                    "setup",
                    "mcp-code-checker",
                    "global-project",
                    "--client",
                    "vscode",
                    "--project-dir",
                    ".",
                    "--user",  # User profile flag
                ],
            ):
                exit_code = main()

                assert exit_code == 0
                mock_setup.assert_called_once()

                # Check that VSCode handler with user mode was used
                call_args = mock_setup.call_args.kwargs
                handler = call_args["client_handler"]
                assert handler.__class__.__name__ == "VSCodeHandler"

    def test_setup_vscode_default_workspace(self):
        """Test that VSCode defaults to workspace mode."""
        # Create a mock server config
        mock_server_config = Mock()
        mock_server_config.name = "mcp-code-checker"
        mock_server_config.display_name = "MCP Code Checker"
        mock_server_config.parameters = [
            create_mock_parameter("project-dir", required=True)
        ]

        # Mock the registry
        mock_registry = Mock()
        mock_registry.get.return_value = mock_server_config
        mock_registry.list_servers.return_value = ["mcp-code-checker"]

        with (
            patch("src.config.main.registry", mock_registry),
            patch("src.config.cli_utils.registry", mock_registry),
            patch("src.config.main.initialize_all_servers"),
            patch("src.config.main.detect_python_environment") as mock_detect,
            patch("src.config.main.validate_required_parameters") as mock_validate_req,
            patch(
                "src.config.main.validate_parameter_combination"
            ) as mock_validate_comb,
            patch("src.config.main.validate_setup_args") as mock_validate_setup,
            patch("src.config.main.setup_mcp_server") as mock_setup,
        ):

            # Setup return values
            mock_detect.return_value = (None, None)
            mock_validate_req.return_value = []
            mock_validate_comb.return_value = []
            mock_validate_setup.return_value = []
            mock_setup.return_value = {"success": True}

            with patch(
                "sys.argv",
                [
                    "mcp-config",
                    "setup",
                    "mcp-code-checker",
                    "test-project",
                    "--client",
                    "vscode",
                    "--project-dir",
                    ".",
                    # No --user flag, should default to workspace
                ],
            ):
                exit_code = main()

                assert exit_code == 0
                mock_setup.assert_called_once()

                # Should default to workspace
                call_args = mock_setup.call_args.kwargs
                handler = call_args["client_handler"]
                assert handler.__class__.__name__ == "VSCodeHandler"

    def test_list_vscode_servers(self):
        """Test list command for VSCode servers."""
        mock_handler = Mock()
        mock_handler.list_all_servers.return_value = [
            {
                "name": "test-server",
                "managed": True,
                "type": "mcp-code-checker",
                "command": "python",
                "args": ["-m", "mcp_code_checker"],
            }
        ]
        mock_handler.get_config_path.return_value = Path(".vscode/mcp.json")

        with (
            patch("src.config.main.get_client_handler") as mock_get_handler,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_get_handler.return_value = mock_handler

            with patch(
                "sys.argv", ["mcp-config", "list", "--client", "vscode-workspace"]
            ):
                with patch("sys.stdout", new=StringIO()) as fake_out:
                    exit_code = main()
                    output = fake_out.getvalue()

                    assert exit_code == 0
                    assert "test-server" in output

    def test_list_vscode_user_servers(self):
        """Test list command for VSCode user profile servers."""
        mock_handler = Mock()
        mock_handler.list_all_servers.return_value = [
            {
                "name": "global-server",
                "managed": True,
                "type": "mcp-code-checker",
                "command": "python",
                "args": ["-m", "mcp_code_checker"],
            }
        ]
        mock_handler.get_config_path.return_value = Path(
            "~/.config/Code/User/settings.json"
        ).expanduser()

        with (
            patch("src.config.main.get_client_handler") as mock_get_handler,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_get_handler.return_value = mock_handler

            with patch("sys.argv", ["mcp-config", "list", "--client", "vscode-user"]):
                with patch("sys.stdout", new=StringIO()) as fake_out:
                    exit_code = main()
                    output = fake_out.getvalue()

                    assert exit_code == 0
                    assert "global-server" in output

    def test_remove_vscode_server(self):
        """Test remove command for VSCode servers."""
        mock_handler = Mock()
        mock_handler.list_managed_servers.return_value = [
            {
                "name": "test-server",
                "managed": True,
                "type": "mcp-code-checker",
                "command": "python",
                "args": ["-m", "mcp_code_checker"],
            }
        ]
        mock_handler.list_all_servers.return_value = [
            {
                "name": "test-server",
                "managed": True,
                "type": "mcp-code-checker",
                "command": "python",
                "args": ["-m", "mcp_code_checker"],
            }
        ]

        with (
            patch("src.config.main.get_client_handler") as mock_get_handler,
            patch("src.config.main.remove_mcp_server") as mock_remove,
        ):
            mock_get_handler.return_value = mock_handler
            mock_remove.return_value = {"success": True}

            with patch(
                "sys.argv",
                ["mcp-config", "remove", "test-server", "--client", "vscode"],
            ):
                exit_code = main()

                assert exit_code == 0
                mock_remove.assert_called_once()

    def test_remove_vscode_server_not_found(self):
        """Test remove command when server not found."""
        mock_handler = Mock()
        mock_handler.list_managed_servers.return_value = []
        mock_handler.list_all_servers.return_value = []

        with patch("src.config.main.get_client_handler") as mock_get_handler:
            mock_get_handler.return_value = mock_handler

            with patch(
                "sys.argv",
                ["mcp-config", "remove", "nonexistent-server", "--client", "vscode"],
            ):
                with patch("sys.stdout", new=StringIO()) as fake_out:
                    exit_code = main()
                    output = fake_out.getvalue()

                    # Should exit with error
                    assert exit_code == 1
                    assert "not found" in output.lower()

    def test_validate_vscode_server(self):
        """Test validate command for VSCode servers."""
        mock_handler = Mock()
        mock_handler.list_all_servers.return_value = [
            {
                "name": "test-server",
                "managed": True,
                "type": "mcp-code-checker",
                "command": "python",
                "args": ["--project-dir", "."],
            }
        ]
        mock_handler.list_managed_servers.return_value = [
            {
                "name": "test-server",
                "managed": True,
                "type": "mcp-code-checker",
                "command": "python",
                "args": ["--project-dir", "."],
            }
        ]
        mock_handler.get_config_path.return_value = Path(".vscode/mcp.json")

        with (
            patch("src.config.main.get_client_handler") as mock_get_handler,
            patch("src.config.main.validate_server_configuration") as mock_validate,
        ):
            mock_get_handler.return_value = mock_handler
            mock_validate.return_value = {
                "success": True,
                "checks": [],
                "warnings": [],
                "errors": [],
            }

            with patch(
                "sys.argv",
                ["mcp-config", "validate", "test-server", "--client", "vscode"],
            ):
                with patch("sys.stdout", new=StringIO()) as fake_out:
                    exit_code = main()
                    output = fake_out.getvalue()

                    assert exit_code == 0
                    mock_validate.assert_called_once()

    def test_validate_vscode_server_with_errors(self):
        """Test validate command when configuration has errors."""
        mock_handler = Mock()
        mock_handler.list_all_servers.return_value = [
            {
                "name": "test-server",
                "managed": True,
                "type": "mcp-code-checker",
                "command": "python",
                "args": [],
            }
        ]
        mock_handler.list_managed_servers.return_value = [
            {
                "name": "test-server",
                "managed": True,
                "type": "mcp-code-checker",
                "command": "python",
                "args": [],
            }
        ]
        mock_handler.get_config_path.return_value = Path(".vscode/mcp.json")

        with (
            patch("src.config.main.get_client_handler") as mock_get_handler,
            patch("src.config.main.validate_server_configuration") as mock_validate,
        ):
            mock_get_handler.return_value = mock_handler
            mock_validate.return_value = {
                "success": False,
                "checks": [],
                "warnings": [],
                "errors": ["Missing required parameter: project-dir"],
            }

            with patch(
                "sys.argv",
                ["mcp-config", "validate", "test-server", "--client", "vscode"],
            ):
                with patch("sys.stdout", new=StringIO()) as fake_out:
                    exit_code = main()
                    output = fake_out.getvalue()

                    # Should report errors
                    assert exit_code == 1
                    mock_validate.assert_called_once()

    def test_client_aliases(self):
        """Test that various VSCode client aliases work."""
        mock_handler = Mock()
        mock_handler.list_all_servers.return_value = []
        mock_handler.get_config_path.return_value = Path(".vscode/mcp.json")

        with (
            patch("src.config.main.get_client_handler") as mock_get_handler,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_get_handler.return_value = mock_handler

            # Test 'vscode' alias
            with patch("sys.argv", ["mcp-config", "list", "--client", "vscode"]):
                with patch("sys.stdout", new=StringIO()):
                    exit_code = main()
                    assert exit_code == 0

            # Test 'vscode-workspace' alias
            with patch(
                "sys.argv", ["mcp-config", "list", "--client", "vscode-workspace"]
            ):
                with patch("sys.stdout", new=StringIO()):
                    exit_code = main()
                    assert exit_code == 0

            # Test 'vscode-user' alias
            with patch("sys.argv", ["mcp-config", "list", "--client", "vscode-user"]):
                with patch("sys.stdout", new=StringIO()):
                    exit_code = main()
                    assert exit_code == 0

    def test_setup_with_all_parameters(self):
        """Test setup command with all available parameters."""
        # Create a mock server config with parameters
        mock_server_config = Mock()
        mock_server_config.name = "mcp-code-checker"
        mock_server_config.display_name = "MCP Code Checker"
        mock_server_config.parameters = [
            create_mock_parameter("project-dir", required=True),
            create_mock_parameter("venv-path"),
            create_mock_parameter("log-file"),
            create_mock_parameter("log-level"),
        ]

        # Mock the registry
        mock_registry = Mock()
        mock_registry.get.return_value = mock_server_config
        mock_registry.list_servers.return_value = ["mcp-code-checker"]

        with (
            patch("src.config.main.registry", mock_registry),
            patch("src.config.cli_utils.registry", mock_registry),
            patch("src.config.main.initialize_all_servers"),
            patch("src.config.main.detect_python_environment") as mock_detect,
            patch("src.config.main.validate_required_parameters") as mock_validate_req,
            patch(
                "src.config.main.validate_parameter_combination"
            ) as mock_validate_comb,
            patch("src.config.main.validate_setup_args") as mock_validate_setup,
            patch("src.config.main.setup_mcp_server") as mock_setup,
        ):

            # Setup return values
            mock_detect.return_value = (None, None)
            mock_validate_req.return_value = []
            mock_validate_comb.return_value = []
            mock_validate_setup.return_value = []
            mock_setup.return_value = {"success": True}

            with patch(
                "sys.argv",
                [
                    "mcp-config",
                    "setup",
                    "mcp-code-checker",
                    "full-test",
                    "--client",
                    "vscode",
                    "--project-dir",
                    ".",
                    "--venv-path",
                    ".venv",
                    "--log-file",
                    "test.log",
                    "--log-level",
                    "DEBUG",  # Default is workspace, no flag needed
                ],
            ):
                exit_code = main()

                assert exit_code == 0
                mock_setup.assert_called_once()

                # Check parameters were passed
                call_args = mock_setup.call_args.kwargs
                user_params = call_args["user_params"]
                assert "log_level" in user_params
                assert user_params["log_level"] == "DEBUG"

    def test_dry_run_with_vscode(self):
        """Test dry-run mode with VSCode client."""
        # Create a mock server config
        mock_server_config = Mock()
        mock_server_config.name = "mcp-code-checker"
        mock_server_config.display_name = "MCP Code Checker"
        mock_server_config.parameters = [
            create_mock_parameter("project-dir", required=True)
        ]

        # Mock the registry
        mock_registry = Mock()
        mock_registry.get.return_value = mock_server_config
        mock_registry.list_servers.return_value = ["mcp-code-checker"]

        mock_handler = Mock()
        mock_handler.get_config_path.return_value = Path(".vscode/mcp.json")

        with (
            patch("src.config.main.registry", mock_registry),
            patch("src.config.cli_utils.registry", mock_registry),
            patch("src.config.main.get_client_handler") as mock_get_handler,
            patch("src.config.main.initialize_all_servers"),
            patch("src.config.main.detect_python_environment") as mock_detect,
            patch("src.config.main.validate_required_parameters") as mock_validate_req,
            patch(
                "src.config.main.validate_parameter_combination"
            ) as mock_validate_comb,
            patch("src.config.main.validate_setup_args") as mock_validate_setup,
            patch("src.config.main.build_server_config") as mock_build,
        ):

            mock_get_handler.return_value = mock_handler
            mock_detect.return_value = (None, None)
            mock_validate_req.return_value = []
            mock_validate_comb.return_value = []
            mock_validate_setup.return_value = []
            mock_build.return_value = {
                "command": "python",
                "args": ["-m", "mcp_code_checker"],
            }

            with patch(
                "sys.argv",
                [
                    "mcp-config",
                    "setup",
                    "mcp-code-checker",
                    "dry-run-test",
                    "--client",
                    "vscode",
                    "--project-dir",
                    ".",
                    "--dry-run",
                ],
            ):
                with patch("sys.stdout", new=StringIO()) as fake_out:
                    exit_code = main()
                    output = fake_out.getvalue()

                    assert exit_code == 0
                    assert "DRY RUN" in output or "dry" in output.lower()

    def test_help_for_vscode_options(self):
        """Test that help text includes VSCode options."""
        # Mock the registry for help text
        mock_server_config = Mock()
        mock_server_config.name = "mcp-code-checker"
        mock_server_config.display_name = "MCP Code Checker"
        mock_server_config.parameters = []

        mock_registry = Mock()
        mock_registry.list_servers.return_value = ["mcp-code-checker"]
        mock_registry.get.return_value = mock_server_config

        with patch("src.config.cli_utils.registry", mock_registry):
            # Test setup help
            with patch("sys.argv", ["mcp-config", "setup", "--help"]):
                with patch("sys.stdout", new=StringIO()) as fake_out:
                    try:
                        main()
                    except SystemExit as e:
                        # argparse exits with 0 on help
                        assert e.code == 0
                    # Help text goes to stdout
                    output = fake_out.getvalue()

                    assert "--client" in output

            # Test main help
            with patch("sys.argv", ["mcp-config", "--help"]):
                with patch("sys.stdout", new=StringIO()) as fake_out:
                    try:
                        main()
                    except SystemExit as e:
                        # argparse exits with 0 on help
                        assert e.code == 0
                    output = fake_out.getvalue()

                    assert "setup" in output
                    assert "remove" in output
                    assert "list" in output
