"""Tests for VSCode-specific integration functionality."""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.config.clients import VSCodeHandler
from src.config.integration import (
    generate_vscode_command,
    is_package_installed,
    make_paths_absolute,
    make_paths_relative,
)
from src.config.utils import detect_mcp_installation, recommend_command_format


class TestPackageDetection:
    """Test package installation detection."""

    def test_is_package_installed_true(self):
        """Test detecting an installed package."""
        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_spec = MagicMock()
            mock_find_spec.return_value = mock_spec

            assert is_package_installed("mcp_code_checker") is True
            mock_find_spec.assert_called_once_with("mcp_code_checker")

    def test_is_package_installed_false(self):
        """Test detecting a non-installed package."""
        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = None

            assert is_package_installed("nonexistent_package") is False

    def test_is_package_installed_import_error(self):
        """Test handling ImportError."""
        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.side_effect = ImportError("Module not found")

            assert is_package_installed("bad_package") is False


class TestVSCodeCommandGeneration:
    """Test VSCode command generation."""

    def test_generate_vscode_command_with_package(self):
        """Test command generation when package is installed."""
        with patch("src.config.integration.is_package_installed", return_value=True):
            config = {
                "command": sys.executable,
                "args": ["src/main.py", "--project-dir", "/path/to/project"],
                "_server_type": "mcp-code-checker",
            }

            result = generate_vscode_command(
                "mcp-code-checker", config, workspace=False
            )

            assert result["command"] == sys.executable
            assert result["args"][:2] == ["-m", "mcp_code_checker"]
            assert "--project-dir" in result["args"]
            assert result["_server_type"] == "mcp-code-checker"

    def test_generate_vscode_command_without_package(self):
        """Test command generation when package is not installed."""
        with patch("src.config.integration.is_package_installed", return_value=False):
            config = {
                "command": sys.executable,
                "args": ["src/main.py", "--project-dir", "/path/to/project"],
            }

            result = generate_vscode_command("mcp-code-checker", config, workspace=True)

            assert result["command"] == sys.executable
            assert result["args"][0] == "src/main.py"

    def test_generate_vscode_command_other_server_type(self):
        """Test command generation for non-MCP Code Checker servers."""
        config = {
            "command": "node",
            "args": ["server.js", "--port", "3000"],
        }

        result = generate_vscode_command("other-server", config)

        assert result["command"] == "node"
        assert result["args"] == ["server.js", "--port", "3000"]

    def test_generate_vscode_command_preserves_env(self):
        """Test that environment variables are preserved."""
        config = {
            "command": sys.executable,
            "args": ["main.py"],
            "env": {"PYTHONPATH": "/custom/path", "DEBUG": "1"},
        }

        result = generate_vscode_command("mcp-code-checker", config)

        assert "env" in result
        assert result["env"]["PYTHONPATH"] == "/custom/path"
        assert result["env"]["DEBUG"] == "1"


class TestPathNormalization:
    """Test path normalization functions."""

    def test_make_paths_relative_project_dir(self, tmp_path):
        """Test making project directory relative."""
        config = {"args": ["--project-dir", str(tmp_path / "subdir")]}

        result = make_paths_relative(config, tmp_path)

        assert result["args"] == ["--project-dir", "subdir"]

    def test_make_paths_relative_already_relative(self, tmp_path):
        """Test that already relative paths are preserved."""
        config = {"args": ["--project-dir", "subdir/project"]}

        result = make_paths_relative(config, tmp_path)

        assert result["args"] == ["--project-dir", "subdir/project"]

    def test_make_paths_relative_different_drive_windows(self):
        """Test handling paths on different drives on Windows."""
        if sys.platform != "win32":
            pytest.skip("Windows-specific test")

        config = {"args": ["--project-dir", "D:\\projects\\test"]}

        # Use C: as base (assuming tests run on C: drive)
        result = make_paths_relative(config, Path("C:\\workspace"))

        # Should keep absolute path since it's on a different drive
        assert result["args"] == ["--project-dir", "D:\\projects\\test"]

    def test_make_paths_relative_parent_directory(self, tmp_path):
        """Test that paths going up directories stay absolute."""
        parent = tmp_path.parent
        config = {"args": ["--project-dir", str(parent)]}

        result = make_paths_relative(config, tmp_path)

        # Should keep absolute since relative would use ..
        assert result["args"] == ["--project-dir", str(parent)]

    def test_make_paths_absolute_relative_path(self, tmp_path):
        """Test making relative paths absolute."""
        original_cwd = Path.cwd()
        try:
            # Change to tmp_path for testing
            import os

            os.chdir(tmp_path)

            config = {"args": ["--project-dir", "subdir"]}

            result = make_paths_absolute(config)

            expected = str((tmp_path / "subdir").resolve())
            assert result["args"] == ["--project-dir", expected]
        finally:
            # Restore original directory
            os.chdir(original_cwd)

    def test_make_paths_absolute_already_absolute(self):
        """Test that absolute paths are preserved."""
        import os

        # Use platform-appropriate absolute path
        if os.name == "nt":
            abs_path = "C:\\absolute\\path"
        else:
            abs_path = "/absolute/path"

        config = {"args": ["--project-dir", abs_path]}

        result = make_paths_absolute(config)

        assert result["args"] == ["--project-dir", abs_path]

    def test_path_normalization_multiple_path_args(self, tmp_path):
        """Test normalizing multiple path arguments."""
        config = {
            "args": [
                "--project-dir",
                str(tmp_path / "project"),
                "--venv-path",
                str(tmp_path / "venv"),
                "--log-file",
                str(tmp_path / "log.txt"),
                "--other-arg",
                "value",
            ]
        }

        result = make_paths_relative(config, tmp_path)

        assert result["args"] == [
            "--project-dir",
            "project",
            "--venv-path",
            "venv",
            "--log-file",
            "log.txt",
            "--other-arg",
            "value",
        ]


class TestInstallationDetection:
    """Test MCP installation detection."""

    def test_detect_mcp_installation_package(self, tmp_path):
        """Test detecting package installation."""
        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_spec = MagicMock()
            mock_find_spec.return_value = mock_spec

            # Mock the import of mcp_code_checker
            mock_module = MagicMock()
            mock_module.__version__ = "1.0.0"

            with patch.dict("sys.modules", {"mcp_code_checker": mock_module}):
                info: dict[str, Any] = detect_mcp_installation(tmp_path)

            assert info["installed_as_package"] is True
            assert info["module_name"] == "mcp_code_checker"
            assert info["version"] == "1.0.0"

    def test_detect_mcp_installation_source(self, tmp_path):
        """Test detecting source installation."""
        # Create a fake source structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        main_py = src_dir / "main.py"
        main_py.write_text("# MCP Code Checker\nimport mcp\ncode_analysis()")

        with patch("importlib.util.find_spec", return_value=None):
            info = detect_mcp_installation(tmp_path)

        assert info["installed_as_package"] is False
        assert info["source_path"] == str(main_py)
        assert info.get("likely_mcp_code_checker") is True

    def test_detect_mcp_installation_neither(self, tmp_path):
        """Test when neither package nor source is found."""
        with patch("importlib.util.find_spec", return_value=None):
            info = detect_mcp_installation(tmp_path)

        assert info["installed_as_package"] is False
        assert info["source_path"] is None
        assert info["module_name"] is None


class TestCommandRecommendation:
    """Test command format recommendations."""

    def test_recommend_vscode_with_package(self):
        """Test VSCode recommendation with package installed."""
        info = {"installed_as_package": True}

        result = recommend_command_format("vscode", "mcp-code-checker", info)

        assert "python -m mcp_code_checker" in result

    def test_recommend_vscode_without_package(self):
        """Test VSCode recommendation without package."""
        info = {"installed_as_package": False}

        result = recommend_command_format("vscode-workspace", "mcp-code-checker", info)

        assert "python src/main.py" in result

    def test_recommend_claude_desktop(self):
        """Test Claude Desktop recommendation."""
        info = {"installed_as_package": True}

        result = recommend_command_format("claude-desktop", "mcp-code-checker", info)

        assert "Direct script execution" in result

    def test_recommend_unknown_client(self):
        """Test recommendation for unknown client."""
        info = {}

        result = recommend_command_format("unknown", "server", info)

        assert "Default command format" in result


class TestIntegrationWithVSCodeHandler:
    """Test integration with VSCodeHandler."""

    def test_generate_client_config_for_vscode(self, tmp_path):
        """Test generating config specifically for VSCode."""
        from src.config.integration import generate_client_config
        from src.config.servers import ParameterDef, ServerConfig

        # Create a mock server config
        server_config = ServerConfig(
            name="mcp-code-checker",
            display_name="MCP Code Checker",
            main_module="src/main.py",
            parameters=[
                ParameterDef(
                    name="project-dir",
                    arg_name="--project-dir",
                    param_type="path",
                    required=True,
                    help="Project directory",
                )
            ],
        )

        # Create VSCode handler
        handler = VSCodeHandler(workspace=True)

        # Mock package installation check
        with patch("src.config.integration.is_package_installed", return_value=True):
            config = generate_client_config(
                server_config,
                "test-server",
                {"project_dir": str(tmp_path)},
                client_handler=handler,
            )

        # Should use module invocation for VSCode
        assert config["args"][:2] == ["-m", "mcp_code_checker"]
        assert config["command"] == sys.executable

    def test_setup_mcp_server_with_vscode(self, tmp_path):
        """Test full setup flow with VSCode handler."""
        from src.config.integration import setup_mcp_server
        from src.config.servers import ParameterDef, ServerConfig

        # Create a mock server config
        server_config = ServerConfig(
            name="mcp-code-checker",
            display_name="MCP Code Checker",
            main_module="src/main.py",
            parameters=[
                ParameterDef(
                    name="project-dir",
                    arg_name="--project-dir",
                    param_type="path",
                    required=True,
                    help="Project directory",
                )
            ],
        )

        # Create VSCode handler with mocked methods
        handler = Mock(spec=VSCodeHandler)
        handler.workspace = True
        handler.get_config_path.return_value = tmp_path / ".vscode" / "mcp.json"
        handler.setup_server.return_value = True

        # Mock package detection
        with patch("src.config.integration.is_package_installed", return_value=True):
            result = setup_mcp_server(
                handler,
                server_config,
                "test-server",
                {"project_dir": str(tmp_path)},
                dry_run=False,
            )

        assert result["success"] is True
        assert result["server_name"] == "test-server"
        handler.setup_server.assert_called_once()

        # Check that the config passed to setup_server was formatted for VSCode
        call_args = handler.setup_server.call_args
        server_config_arg = call_args[0][1]  # Second positional argument
        assert "-m" in server_config_arg.get("args", [])
