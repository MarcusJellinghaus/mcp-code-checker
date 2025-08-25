"""Tests for the main CLI module."""

import sys
from argparse import Namespace
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.config.main import (
    add_list_parser,
    add_remove_parser,
    add_server_specific_options,
    add_setup_parser,
    create_main_parser,
    extract_user_parameters,
    handle_list_command,
    handle_remove_command,
    handle_setup_command,
    main,
    print_server_info,
    print_setup_summary,
)
from src.config.servers import ParameterDef, ServerConfig


class TestMainParserCreation:
    """Test parser creation and configuration."""

    def test_main_parser_creation(self) -> None:
        """Test that main parser is created correctly."""
        parser = create_main_parser()
        assert parser.prog == "mcp-config"
        description = parser.description or ""
        assert "MCP Configuration Helper" in description

    def test_subcommands_added(self) -> None:
        """Test that all subcommands are added."""
        parser = create_main_parser()
        # Parse with --help to check subcommands exist
        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])

    def test_setup_command_parsing(self) -> None:
        """Test setup command argument parsing."""
        parser = create_main_parser()
        args = parser.parse_args(
            ["setup", "mcp-code-checker", "test-server", "--project-dir", "."]
        )
        assert args.command == "setup"
        assert args.server_type == "mcp-code-checker"
        assert args.server_name == "test-server"
        assert args.project_dir == Path(".")

    def test_remove_command_parsing(self) -> None:
        """Test remove command argument parsing."""
        parser = create_main_parser()
        args = parser.parse_args(["remove", "test-server"])
        assert args.command == "remove"
        assert args.server_name == "test-server"

    def test_list_command_parsing(self) -> None:
        """Test list command argument parsing."""
        parser = create_main_parser()
        args = parser.parse_args(["list"])
        assert args.command == "list"

    def test_list_command_with_options(self) -> None:
        """Test list command with optional arguments."""
        parser = create_main_parser()
        args = parser.parse_args(["list", "--detailed", "--managed-only"])
        assert args.command == "list"
        assert args.detailed is True
        assert args.managed_only is True

    def test_setup_command_with_dry_run(self) -> None:
        """Test setup command with dry-run option."""
        parser = create_main_parser()
        args = parser.parse_args(
            ["setup", "mcp-code-checker", "test", "--project-dir", ".", "--dry-run"]
        )
        assert args.dry_run is True

    def test_invalid_command(self) -> None:
        """Test that invalid commands raise error."""
        parser = create_main_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["invalid-command"])


class TestServerSpecificOptions:
    """Test server-specific option handling."""

    def test_add_server_specific_options(self) -> None:
        """Test adding server-specific options to parser."""
        # Create a mock server config
        mock_config = ServerConfig(
            name="test-server",
            display_name="Test Server",
            main_module="test",
            parameters=[
                ParameterDef(
                    name="project-dir",
                    arg_name="--project-dir",
                    param_type="path",
                    required=True,
                    help="Project directory",
                ),
                ParameterDef(
                    name="debug",
                    arg_name="--debug",
                    param_type="boolean",
                    is_flag=True,
                    help="Enable debug mode",
                ),
                ParameterDef(
                    name="log-level",
                    arg_name="--log-level",
                    param_type="choice",
                    choices=["DEBUG", "INFO", "WARNING"],
                    default="INFO",
                    help="Log level",
                ),
            ],
        )

        # Mock registry
        with patch("src.config.main.registry") as mock_registry:
            mock_registry.get.return_value = mock_config

            import argparse

            parser = argparse.ArgumentParser()
            add_server_specific_options(parser, "test-server")

            # Test that options were added
            args = parser.parse_args(
                ["--project-dir", "/test", "--debug", "--log-level", "DEBUG"]
            )
            assert args.project_dir == Path("/test")
            assert args.debug is True
            assert args.log_level == "DEBUG"

    def test_add_server_specific_options_no_config(self) -> None:
        """Test handling when server config doesn't exist."""
        with patch("src.config.main.registry") as mock_registry:
            mock_registry.get.return_value = None

            import argparse

            parser = argparse.ArgumentParser()
            # Should not raise error
            add_server_specific_options(parser, "nonexistent")


class TestExtractUserParameters:
    """Test parameter extraction from CLI arguments."""

    def test_extract_user_parameters(self) -> None:
        """Test extracting user parameters from args."""
        mock_config = ServerConfig(
            name="test-server",
            display_name="Test Server",
            main_module="test",
            parameters=[
                ParameterDef(
                    name="project-dir",
                    arg_name="--project-dir",
                    param_type="path",
                    required=True,
                    help="Project directory",
                ),
                ParameterDef(
                    name="debug",
                    arg_name="--debug",
                    param_type="boolean",
                    is_flag=True,
                    help="Debug mode",
                ),
                ParameterDef(
                    name="workers",
                    arg_name="--workers",
                    param_type="string",
                    default="4",
                    help="Number of workers",
                ),
            ],
        )

        args = Namespace(
            project_dir=Path("/test"), debug=True, workers=8, other_attr="ignored"
        )

        params = extract_user_parameters(args, mock_config)

        assert params["project_dir"] == Path("/test")
        assert params["debug"] is True
        assert params["workers"] == 8
        assert "other_attr" not in params

    def test_extract_user_parameters_with_defaults(self) -> None:
        """Test that None values are not included."""
        mock_config = ServerConfig(
            name="test-server",
            display_name="Test Server",
            main_module="test",
            parameters=[
                ParameterDef(
                    name="optional-param",
                    arg_name="--optional-param",
                    param_type="string",
                    help="Optional parameter",
                ),
            ],
        )

        args = Namespace(optional_param=None)
        params = extract_user_parameters(args, mock_config)
        assert "optional_param" not in params


class TestCommandHandlers:
    """Test command handler functions."""

    @patch("src.config.main.setup_mcp_server")  # type: ignore[misc]
    @patch("src.config.main.validate_required_parameters")  # type: ignore[misc]
    @patch("src.config.main.detect_python_environment")  # type: ignore[misc]
    @patch("src.config.main.get_client_handler")  # type: ignore[misc]
    @patch("src.config.main.registry")  # type: ignore[misc]
    def test_handle_setup_command_success(
        self,
        mock_registry: Any,
        mock_get_client: Any,
        mock_detect: Any,
        mock_validate: Any,
        mock_setup: Any,
    ) -> None:
        """Test successful setup command handling."""
        # Setup mocks
        mock_config = MagicMock()
        mock_config.name = "test-server"
        mock_config.parameters = []
        mock_registry.get.return_value = mock_config

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_detect.return_value = (Path("/usr/bin/python"), Path("/venv"))
        mock_validate.return_value = []  # No validation errors
        mock_setup.return_value = {"success": True, "backup_path": "/backup"}

        args = Namespace(
            server_type="test-server",
            server_name="my-server",
            client="claude-desktop",
            dry_run=False,
            verbose=False,
            backup=True,
        )

        result = handle_setup_command(args)
        assert result == 0
        mock_setup.assert_called_once()

    @patch("src.config.main.registry")  # type: ignore[misc]
    def test_handle_setup_command_unknown_server(self, mock_registry: Any) -> None:
        """Test setup command with unknown server type."""
        mock_registry.get.return_value = None
        mock_registry.list_servers.return_value = ["server1", "server2"]

        args = Namespace(
            server_type="unknown",
            server_name="test",
            client="claude-desktop",
            dry_run=False,
            verbose=False,
        )

        result = handle_setup_command(args)
        assert result == 1

    @patch("src.config.main.setup_mcp_server")  # type: ignore[misc]
    @patch("src.config.main.validate_required_parameters")  # type: ignore[misc]
    @patch("src.config.main.detect_python_environment")  # type: ignore[misc]
    @patch("src.config.main.get_client_handler")  # type: ignore[misc]
    @patch("src.config.main.registry")  # type: ignore[misc]
    def test_handle_setup_command_dry_run(
        self,
        mock_registry: Any,
        mock_get_client: Any,
        mock_detect: Any,
        mock_validate: Any,
        mock_setup: Any,
    ) -> None:
        """Test setup command in dry-run mode."""
        mock_config = MagicMock()
        mock_config.name = "test-server"
        mock_config.parameters = []
        mock_registry.get.return_value = mock_config

        mock_detect.return_value = (Path("/usr/bin/python"), None)
        mock_validate.return_value = []

        args = Namespace(
            server_type="test-server",
            server_name="my-server",
            client="claude-desktop",
            dry_run=True,
            verbose=False,
            backup=True,
        )

        result = handle_setup_command(args)
        assert result == 0
        mock_setup.assert_not_called()  # Should not call setup in dry-run

    @patch("src.config.main.remove_mcp_server")  # type: ignore[misc]
    @patch("src.config.main.get_client_handler")  # type: ignore[misc]
    def test_handle_remove_command_success(
        self, mock_get_client: Any, mock_remove: Any
    ) -> None:
        """Test successful remove command handling."""
        mock_client = MagicMock()
        mock_client.list_managed_servers.return_value = [
            {"name": "test-server", "type": "test", "command": "test", "managed": True}
        ]
        mock_get_client.return_value = mock_client

        mock_remove.return_value = {"success": True, "backup_path": "/backup"}

        args = Namespace(
            server_name="test-server",
            client="claude-desktop",
            dry_run=False,
            verbose=False,
            backup=True,
        )

        result = handle_remove_command(args)
        assert result == 0
        mock_remove.assert_called_once()

    @patch("src.config.main.get_client_handler")  # type: ignore[misc]
    def test_handle_remove_command_not_managed(self, mock_get_client: Any) -> None:
        """Test remove command for non-managed server."""
        mock_client = MagicMock()
        mock_client.list_managed_servers.return_value = []
        mock_client.list_all_servers.return_value = [
            {
                "name": "external-server",
                "type": "test",
                "command": "test",
                "managed": False,
            }
        ]
        mock_get_client.return_value = mock_client

        args = Namespace(
            server_name="external-server",
            client="claude-desktop",
            dry_run=False,
            verbose=False,
        )

        result = handle_remove_command(args)
        assert result == 1

    @patch("src.config.main.get_client_handler")  # type: ignore[misc]
    def test_handle_list_command_success(self, mock_get_client: Any) -> None:
        """Test successful list command handling."""
        mock_client = MagicMock()
        mock_client.get_config_path.return_value = Path("/config.json")
        mock_client.list_all_servers.return_value = [
            {"name": "server1", "type": "type1", "command": "cmd1", "managed": True},
            {"name": "server2", "type": "type2", "command": "cmd2", "managed": False},
        ]
        mock_get_client.return_value = mock_client

        args = Namespace(client="claude-desktop", detailed=False, managed_only=False)

        result = handle_list_command(args)
        assert result == 0

    @patch("src.config.main.get_client_handler")  # type: ignore[misc]
    def test_handle_list_command_managed_only(self, mock_get_client: Any) -> None:
        """Test list command with managed-only filter."""
        mock_client = MagicMock()
        mock_client.get_config_path.return_value = Path("/config.json")
        mock_client.list_managed_servers.return_value = [
            {"name": "server1", "type": "type1", "command": "cmd1", "managed": True}
        ]
        mock_get_client.return_value = mock_client

        args = Namespace(client="claude-desktop", detailed=False, managed_only=True)

        result = handle_list_command(args)
        assert result == 0


class TestOutputFunctions:
    """Test output formatting functions."""

    def test_print_server_info_basic(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test basic server info printing."""
        server = {
            "name": "test-server",
            "type": "test-type",
            "command": "test-cmd",
            "managed": True,
        }

        print_server_info(server, detailed=False)
        captured = capsys.readouterr()
        assert "● test-server (test-type)" in captured.out

    def test_print_server_info_detailed(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test detailed server info printing."""
        server = {
            "name": "test-server",
            "type": "test-type",
            "command": "test-cmd",
            "args": ["--arg1", "--arg2"],
            "managed": False,
        }

        print_server_info(server, detailed=True)
        captured = capsys.readouterr()
        assert "○ test-server (test-type)" in captured.out
        assert "Command: test-cmd" in captured.out
        assert "Args: --arg1 --arg2" in captured.out
        assert "External server" in captured.out

    def test_print_server_info_long_args_truncated(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that long arguments are truncated."""
        long_arg = "x" * 100
        server = {
            "name": "test",
            "type": "test",
            "command": "cmd",
            "args": [long_arg],
            "managed": True,
        }

        print_server_info(server, detailed=True)
        captured = capsys.readouterr()
        assert "..." in captured.out

    def test_print_setup_summary(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test setup summary printing."""
        mock_config = MagicMock()
        mock_config.name = "test-server"

        user_params = {
            "project_dir": Path("/test"),
            "debug": True,
            "log_level": "DEBUG",
            "python_executable": "/usr/bin/python",
        }

        print_setup_summary("my-server", mock_config, user_params, "claude-desktop")
        captured = capsys.readouterr()

        assert "Setup Summary:" in captured.out
        assert "Client: claude-desktop" in captured.out
        assert "Server Name: my-server" in captured.out
        # Check for path in cross-platform way (Windows uses backslash)
        assert "project-dir:" in captured.out
        assert "test" in captured.out
        assert "Python Executable: /usr/bin/python" in captured.out


class TestMainFunction:
    """Test the main entry point."""

    @patch("src.config.main.handle_setup_command")  # type: ignore[misc]
    def test_main_setup_command(self, mock_handle: Any, monkeypatch: Any) -> None:
        """Test main function with setup command."""
        mock_handle.return_value = 0
        monkeypatch.setattr(
            sys,
            "argv",
            ["mcp-config", "setup", "mcp-code-checker", "test", "--project-dir", "."],
        )

        result = main()
        assert result == 0
        mock_handle.assert_called_once()

    @patch("src.config.main.handle_remove_command")  # type: ignore[misc]
    def test_main_remove_command(self, mock_handle: Any, monkeypatch: Any) -> None:
        """Test main function with remove command."""
        mock_handle.return_value = 0
        monkeypatch.setattr(sys, "argv", ["mcp-config", "remove", "test-server"])

        result = main()
        assert result == 0
        mock_handle.assert_called_once()

    @patch("src.config.main.handle_list_command")  # type: ignore[misc]
    def test_main_list_command(self, mock_handle: Any, monkeypatch: Any) -> None:
        """Test main function with list command."""
        mock_handle.return_value = 0
        monkeypatch.setattr(sys, "argv", ["mcp-config", "list"])

        result = main()
        assert result == 0
        mock_handle.assert_called_once()

    def test_main_keyboard_interrupt(self, monkeypatch: Any) -> None:
        """Test handling of keyboard interrupt."""
        monkeypatch.setattr(sys, "argv", ["mcp-config", "list"])

        with patch("src.config.main.create_main_parser") as mock_parser:
            mock_parser.side_effect = KeyboardInterrupt

            result = main()
            assert result == 1

    def test_main_general_exception(self, monkeypatch: Any) -> None:
        """Test handling of general exceptions."""
        monkeypatch.setattr(sys, "argv", ["mcp-config", "list"])

        with patch("src.config.main.create_main_parser") as mock_parser:
            mock_parser.side_effect = Exception("Test error")

            result = main()
            assert result == 1
