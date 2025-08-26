"""Tests for enhanced output formatting."""

from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config.output import OutputFormatter


class TestOutputFormatter:
    """Test enhanced output formatting."""

    def test_print_validation_results(self) -> None:
        """Test validation results formatting."""
        validation_result = {
            "success": True,
            "checks": [
                {
                    "status": "success",
                    "name": "Project directory",
                    "message": "Project directory exists: /test/path",
                },
                {
                    "status": "warning",
                    "name": "Test folder",
                    "message": "Test folder not found",
                },
                {
                    "status": "error",
                    "name": "Python executable",
                    "message": "Python executable not found",
                },
            ],
            "warnings": ["Test folder missing"],
            "suggestions": ["Create test folder: mkdir tests"],
            "errors": [],
        }

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            OutputFormatter.print_validation_results(validation_result)
            output = mock_stdout.getvalue()

            # Check for status symbols
            assert OutputFormatter.SUCCESS in output
            assert OutputFormatter.WARNING in output
            assert OutputFormatter.ERROR in output

            # Check for messages
            assert "Project directory exists" in output
            assert "Test folder not found" in output
            assert "Python executable not found" in output

            # Simplified version no longer shows suggestions

    def test_print_configuration_details(self) -> None:
        """Test configuration details formatting."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            OutputFormatter.print_configuration_details(
                "my-checker",
                "mcp-code-checker",
                {
                    "project_dir": "/test/path",
                    "python_executable": "/usr/bin/python3",
                    "log_level": "INFO",
                },
                tree_format=True,
            )
            output = mock_stdout.getvalue()

            # Check content
            assert "my-checker" in output
            assert "mcp-code-checker" in output
            assert "/test/path" in output
            assert "INFO" in output

    def test_print_dry_run_header(self) -> None:
        """Test dry-run header formatting."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            OutputFormatter.print_dry_run_header()
            output = mock_stdout.getvalue()

            assert "DRY RUN" in output
            assert "No changes will be applied" in output

    def test_print_auto_detected_params(self) -> None:
        """Test auto-detected parameters formatting."""
        params = {
            "python_executable": "/home/user/.venv/bin/python",
            "venv_path": "/home/user/.venv",
            "log_file": "/home/user/logs/auto_20240101_120000.log",
            "test_folder": "tests",
            "log_level": "INFO",
        }

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            OutputFormatter.print_auto_detected_params(params)
            output = mock_stdout.getvalue()

            assert "Auto-detected parameters" in output
            assert "Python Executable" in output
            assert "Venv Path" in output

    def test_print_enhanced_server_list(self, tmp_path: Path) -> None:
        """Test enhanced server list formatting."""
        servers = [
            {
                "name": "my-checker",
                "type": "mcp-code-checker",
                "managed": True,
                "command": "/usr/bin/python",
                "args": ["--project-dir", "/test"],
            },
            {
                "name": "external-server",
                "type": "unknown",
                "managed": False,
                "command": "node",
                "args": [],
            },
        ]

        config_path = tmp_path / "config.json"
        config_path.touch()

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            OutputFormatter.print_enhanced_server_list(
                servers, "claude-desktop", config_path, detailed=True
            )
            output = mock_stdout.getvalue()

            # Check sections
            assert "MCP Servers for claude-desktop" in output

            # Check server names
            assert "my-checker" in output
            assert "external-server" in output

            # Check detailed info
            assert "/usr/bin/python" in output
            # Args are not shown in enhanced list (simplified)

    def test_print_dry_run_config_preview(self, tmp_path: Path) -> None:
        """Test dry-run configuration preview."""
        config = {
            "command": "/usr/bin/python",
            "args": ["--project-dir", "/test"],
            "_managed_by": "mcp-config-managed",
            "_server_type": "mcp-code-checker",
            "name": "test-server",
            "type": "mcp-code-checker",
        }

        config_path = tmp_path / "config.json"
        backup_path = tmp_path / "config.backup.json"

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            OutputFormatter.print_dry_run_config_preview(
                config, config_path, backup_path
            )
            output = mock_stdout.getvalue()

            # Check simplified output format
            assert "Would update configuration" in output
            assert "Server: test-server" in output
            assert "Type: mcp-code-checker" in output

            # Check paths
            assert str(config_path) in output
            assert str(backup_path) in output

            # Check success message
            assert "Configuration valid" in output
            assert "Run without --dry-run" in output

    def test_print_dry_run_remove_preview(self, tmp_path: Path) -> None:
        """Test dry-run removal preview."""
        server_info = {
            "name": "my-checker",
            "type": "mcp-code-checker",
            "command": "/usr/bin/python",
        }

        other_servers = [
            {"name": "other-server", "managed": True},
            {"name": "external", "managed": False},
        ]

        config_path = tmp_path / "config.json"
        backup_path = tmp_path / "backup.json"

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            OutputFormatter.print_dry_run_remove_preview(
                "my-checker", server_info, other_servers, config_path, backup_path
            )
            output = mock_stdout.getvalue()

            assert "Would remove server 'my-checker'" in output
            assert "mcp-code-checker" in output
            
            # Check preservation message for other servers
            assert "Preserving 2 other server(s)" in output

            # Check paths
            assert str(config_path) in output
            assert str(backup_path) in output

            # Check success message
            assert "Removal safe" in output


