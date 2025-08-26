"""Tests for integration between ServerConfig and ClientHandler."""

import sys
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from src.config.clients import ClaudeDesktopHandler
from src.config.integration import (
    generate_client_config,
    remove_mcp_server,
    setup_mcp_server,
)
from src.config.servers import MCP_CODE_CHECKER, ParameterDef, ServerConfig


class TestGenerateClientConfig:
    """Test client configuration generation."""

    @pytest.fixture
    def server_config(self) -> ServerConfig:
        """Create a test server configuration."""
        return ServerConfig(
            name="test-server",
            display_name="Test Server",
            main_module="src/main.py",
            parameters=[
                ParameterDef(
                    name="project-dir",
                    arg_name="--project-dir",
                    param_type="path",
                    required=True,
                ),
                ParameterDef(
                    name="log-level",
                    arg_name="--log-level",
                    param_type="choice",
                    choices=["DEBUG", "INFO", "WARNING"],
                    default="INFO",
                ),
                ParameterDef(
                    name="verbose",
                    arg_name="--verbose",
                    param_type="boolean",
                    is_flag=True,
                ),
            ],
        )

    def test_generate_basic_config(
        self, server_config: ServerConfig, tmp_path: Path
    ) -> None:
        """Test generating basic client configuration."""
        # Use underscore format as expected by generate_args
        user_params = {
            "project_dir": str(tmp_path),
            "log_level": "DEBUG",
            "verbose": True,
        }

        config = generate_client_config(
            server_config,
            "test-instance",
            user_params,
            python_executable="/usr/bin/python3",
        )

        assert config["command"] == "/usr/bin/python3"
        # The first argument should contain main.py
        assert "main.py" in config["args"][0]
        assert "--project-dir" in config["args"]
        assert str(tmp_path) in config["args"]
        assert "--log-level" in config["args"]
        assert "DEBUG" in config["args"]
        assert "--verbose" in config["args"]
        assert config["_server_type"] == "test-server"

    def test_generate_config_with_auto_python(
        self, server_config: ServerConfig, tmp_path: Path
    ) -> None:
        """Test configuration with auto-detected Python."""
        user_params = {"project_dir": str(tmp_path)}

        config = generate_client_config(
            server_config,
            "test-instance",
            user_params,
            python_executable=None,  # Auto-detect
        )

        assert config["command"] == sys.executable

    def test_generate_config_missing_required(
        self, server_config: ServerConfig
    ) -> None:
        """Test that missing required parameters raise error."""
        user_params = {"log_level": "INFO"}  # Missing required project_dir

        with pytest.raises(ValueError) as exc_info:
            generate_client_config(server_config, "test", user_params)
        assert "project-dir is required" in str(exc_info.value)

    def test_generate_config_invalid_choice(
        self, server_config: ServerConfig, tmp_path: Path
    ) -> None:
        """Test that invalid choice values raise error."""
        user_params = {
            "project_dir": str(tmp_path),
            "log_level": "INVALID",
        }

        with pytest.raises(ValueError) as exc_info:
            generate_client_config(server_config, "test", user_params)
        assert "not in valid choices" in str(exc_info.value)

    def test_generate_config_with_venv(
        self, server_config: ServerConfig, tmp_path: Path
    ) -> None:
        """Test configuration with virtual environment."""
        venv_path = tmp_path / "venv"
        venv_path.mkdir()

        # Create fake venv structure
        if sys.platform == "win32":
            scripts_dir = venv_path / "Scripts"
            scripts_dir.mkdir()
            python_exe = scripts_dir / "python.exe"
        else:
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            python_exe = bin_dir / "python"

        python_exe.touch()

        # Add venv parameter to server config
        server_config.parameters.append(
            ParameterDef(
                name="venv-path",
                arg_name="--venv-path",
                param_type="path",
            )
        )

        user_params = {
            "project_dir": str(tmp_path),
            "venv_path": str(venv_path),
        }

        config = generate_client_config(server_config, "test", user_params)

        # Should use Python from venv
        assert str(python_exe) in config["command"]

    def test_generate_config_path_normalization(
        self, server_config: ServerConfig, tmp_path: Path
    ) -> None:
        """Test that paths are normalized to absolute."""
        user_params = {
            "project_dir": ".",  # Relative path
        }

        with patch("src.config.integration.Path.cwd", return_value=tmp_path):
            config = generate_client_config(server_config, "test", user_params)

        # Should be normalized to absolute
        project_arg_index = config["args"].index("--project-dir")
        project_path = config["args"][project_arg_index + 1]
        assert Path(project_path).is_absolute()

    def test_generate_config_with_pythonpath(
        self, server_config: ServerConfig, tmp_path: Path
    ) -> None:
        """Test that PYTHONPATH is set in environment."""
        user_params = {"project_dir": str(tmp_path)}

        config = generate_client_config(server_config, "test", user_params)

        assert "env" in config
        assert "PYTHONPATH" in config["env"]
        # On Windows, PYTHONPATH should have a trailing backslash
        expected_pythonpath = str(tmp_path)
        if sys.platform == "win32" and not expected_pythonpath.endswith("\\"):
            expected_pythonpath += "\\"
        assert config["env"]["PYTHONPATH"] == expected_pythonpath


class TestSetupMCPServer:
    """Test setup_mcp_server function."""

    @pytest.fixture
    def mock_handler(self) -> MagicMock:
        """Create a mock client handler."""
        handler = MagicMock(spec=ClaudeDesktopHandler)
        handler.get_config_path.return_value = Path("/mock/config.json")
        handler.setup_server.return_value = True
        return handler

    def test_setup_server_success(
        self, mock_handler: MagicMock, tmp_path: Path
    ) -> None:
        """Test successful server setup."""
        user_params = {
            "project_dir": str(tmp_path),
            "log_level": "INFO",
        }

        result = setup_mcp_server(
            mock_handler,
            MCP_CODE_CHECKER,
            "my-checker",
            user_params,
        )

        assert result["success"] is True
        assert result["server_name"] == "my-checker"
        assert result["operation"] == "setup"
        assert "config" in result
        assert "message" in result
        mock_handler.setup_server.assert_called_once()

    def test_setup_server_dry_run(
        self, mock_handler: MagicMock, tmp_path: Path
    ) -> None:
        """Test dry run mode."""
        user_params = {"project_dir": str(tmp_path)}

        result = setup_mcp_server(
            mock_handler,
            MCP_CODE_CHECKER,
            "my-checker",
            user_params,
            dry_run=True,
        )

        assert result["success"] is True
        assert result["dry_run"] is True
        assert "Would set up" in result["message"]
        mock_handler.setup_server.assert_not_called()

    def test_setup_server_validation_error(self, mock_handler: MagicMock) -> None:
        """Test setup with validation errors."""
        user_params: Dict[str, Any] = {}  # Missing required project-dir

        result = setup_mcp_server(
            mock_handler,
            MCP_CODE_CHECKER,
            "my-checker",
            user_params,
        )

        assert result["success"] is False
        assert "error" in result
        assert "project-dir is required" in result["error"]
        mock_handler.setup_server.assert_not_called()

    def test_setup_server_handler_failure(
        self, mock_handler: MagicMock, tmp_path: Path
    ) -> None:
        """Test when handler fails to set up server."""
        mock_handler.setup_server.return_value = False
        user_params = {"project_dir": str(tmp_path)}

        result = setup_mcp_server(
            mock_handler,
            MCP_CODE_CHECKER,
            "my-checker",
            user_params,
        )

        assert result["success"] is False
        assert "Failed to set up" in result["message"]


class TestRemoveMCPServer:
    """Test remove_mcp_server function."""

    @pytest.fixture
    def mock_handler(self) -> MagicMock:
        """Create a mock client handler."""
        handler = MagicMock(spec=ClaudeDesktopHandler)
        handler.get_config_path.return_value = Path("/mock/config.json")
        handler.remove_server.return_value = True
        handler.list_all_servers.return_value = [
            {"name": "managed-server", "managed": True},
            {"name": "external-server", "managed": False},
        ]
        return handler

    def test_remove_server_success(self, mock_handler: MagicMock) -> None:
        """Test successful server removal."""
        result = remove_mcp_server(mock_handler, "managed-server")

        assert result["success"] is True
        assert result["server_name"] == "managed-server"
        assert result["operation"] == "remove"
        assert "Successfully removed" in result["message"]
        mock_handler.remove_server.assert_called_once_with("managed-server")

    def test_remove_server_dry_run(self, mock_handler: MagicMock) -> None:
        """Test dry run mode for removal."""
        result = remove_mcp_server(mock_handler, "managed-server", dry_run=True)

        assert result["success"] is True
        assert result["dry_run"] is True
        assert "Would remove" in result["message"]
        mock_handler.remove_server.assert_not_called()

    def test_remove_nonexistent_server(self, mock_handler: MagicMock) -> None:
        """Test removing a server that doesn't exist."""
        result = remove_mcp_server(mock_handler, "nonexistent")

        assert result["success"] is False
        assert "not found" in result["message"]
        mock_handler.remove_server.assert_not_called()

    def test_remove_external_server(self, mock_handler: MagicMock) -> None:
        """Test that external servers cannot be removed."""
        result = remove_mcp_server(mock_handler, "external-server")

        assert result["success"] is False
        assert "not managed by this tool" in result["message"]
        mock_handler.remove_server.assert_not_called()

    def test_remove_server_handler_failure(self, mock_handler: MagicMock) -> None:
        """Test when handler fails to remove server."""
        mock_handler.remove_server.return_value = False

        result = remove_mcp_server(mock_handler, "managed-server")

        assert result["success"] is False
        assert "Failed to remove" in result["message"]


class TestMCPCodeCheckerIntegration:
    """Test integration with the actual MCP Code Checker config."""

    def test_mcp_code_checker_config_generation(self, tmp_path: Path) -> None:
        """Test generating config for MCP Code Checker."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        user_params = {
            "project_dir": str(project_dir),
            "log_level": "DEBUG",
            "test_folder": "tests",
            "keep_temp_files": True,
        }

        config = generate_client_config(
            MCP_CODE_CHECKER,
            "checker-instance",
            user_params,
            python_executable="/usr/bin/python3",
        )

        assert config["command"] == "/usr/bin/python3"
        assert config["_server_type"] == "mcp-code-checker"

        # Check arguments
        args = config["args"]
        # The first argument should be the absolute path to main.py
        assert args[0].endswith("src/main.py") or args[0].endswith("src\\main.py")
        assert "--project-dir" in args
        assert str(project_dir) in args
        assert "--log-level" in args
        assert "DEBUG" in args
        assert "--test-folder" in args
        assert "tests" in args
        assert "--keep-temp-files" in args

        # Check environment
        assert "PYTHONPATH" in config["env"]
        # On Windows, PYTHONPATH should have a trailing backslash
        expected_pythonpath = str(project_dir)
        if sys.platform == "win32" and not expected_pythonpath.endswith("\\"):
            expected_pythonpath += "\\"
        assert config["env"]["PYTHONPATH"] == expected_pythonpath

    def test_mcp_code_checker_minimal_config(self, tmp_path: Path) -> None:
        """Test minimal configuration for MCP Code Checker."""
        user_params = {"project_dir": str(tmp_path)}

        config = generate_client_config(
            MCP_CODE_CHECKER,
            "minimal",
            user_params,
        )

        # Should work with just required parameters
        assert config["command"] == sys.executable
        args = config["args"]
        assert "--project-dir" in args
        assert str(tmp_path) in args

        # Default log level should be included
        assert "--log-level" in args
        assert "INFO" in args
