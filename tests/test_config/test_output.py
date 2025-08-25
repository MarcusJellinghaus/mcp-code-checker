"""Tests for the output formatting module."""

from pathlib import Path

import pytest

from src.config.output import OutputFormatter


class TestOutputFormatter:
    """Test the OutputFormatter class."""

    def test_print_success(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test success message formatting."""
        OutputFormatter.print_success("Operation completed")
        captured = capsys.readouterr()
        assert "✓ Operation completed" in captured.out

    def test_print_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test error message formatting."""
        OutputFormatter.print_error("Operation failed")
        captured = capsys.readouterr()
        assert "✗ Operation failed" in captured.out

    def test_print_info(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test info message formatting."""
        OutputFormatter.print_info("Important information")
        captured = capsys.readouterr()
        assert "ℹ Important information" in captured.out

    def test_print_warning(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test warning message formatting."""
        OutputFormatter.print_warning("This is a warning")
        captured = capsys.readouterr()
        assert "⚠ This is a warning" in captured.out

    def test_print_setup_summary(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test setup summary formatting."""
        params = {
            "project_dir": Path("/test/project"),
            "debug": True,
            "log_level": "DEBUG",
            "workers": 4,
            "empty_value": None,  # Should be skipped
        }

        OutputFormatter.print_setup_summary("my-server", "test-type", params)
        captured = capsys.readouterr()

        assert "Setup Summary:" in captured.out
        assert "Server Name: my-server" in captured.out
        assert "Server Type: test-type" in captured.out
        # Check for path in cross-platform way (Windows uses backslash)
        assert "project-dir:" in captured.out
        assert "test" in captured.out and "project" in captured.out
        assert "debug: True" in captured.out
        assert "log-level: DEBUG" in captured.out
        assert "workers: 4" in captured.out
        assert "empty-value" not in captured.out

    def test_print_server_list_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test server list formatting with no servers."""
        OutputFormatter.print_server_list([])
        captured = capsys.readouterr()
        assert "No servers found" in captured.out

    def test_print_server_list_basic(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test basic server list formatting."""
        servers = [
            {"name": "server1", "type": "type1", "managed": True},
            {"name": "server2", "type": "type2", "managed": False},
        ]

        OutputFormatter.print_server_list(servers, detailed=False)
        captured = capsys.readouterr()

        assert "● server1 (type1)" in captured.out
        assert "○ server2 (type2)" in captured.out

    def test_print_server_list_detailed(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test detailed server list formatting."""
        servers = [
            {
                "name": "server1",
                "type": "type1",
                "managed": True,
                "command": "python -m server1",
                "args": ["--arg1", "--arg2"],
            },
            {
                "name": "server2",
                "type": "type2",
                "managed": False,
                "command": "node server2.js",
            },
        ]

        OutputFormatter.print_server_list(servers, detailed=True)
        captured = capsys.readouterr()

        assert "● server1 (type1)" in captured.out
        assert "Command: python -m server1" in captured.out
        assert "Args: --arg1 --arg2" in captured.out

        assert "○ server2 (type2)" in captured.out
        assert "Command: node server2.js" in captured.out
        assert "External server" in captured.out

    def test_print_server_list_long_args_truncation(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that long arguments are truncated."""
        long_args = ["--" + "x" * 50 for _ in range(5)]
        servers = [
            {
                "name": "server1",
                "type": "type1",
                "managed": True,
                "command": "test",
                "args": long_args,
            }
        ]

        OutputFormatter.print_server_list(servers, detailed=True)
        captured = capsys.readouterr()
        assert "..." in captured.out

    def test_print_validation_errors(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test validation error formatting."""
        errors = [
            "Missing required parameter: project-dir",
            "Invalid value for log-level",
            "Path does not exist: /invalid/path",
        ]

        OutputFormatter.print_validation_errors(errors)
        captured = capsys.readouterr()

        assert "❌ Validation Errors:" in captured.out
        assert "• Missing required parameter: project-dir" in captured.out
        assert "• Invalid value for log-level" in captured.out
        assert "• Path does not exist: /invalid/path" in captured.out

    def test_print_validation_errors_empty(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test validation errors with empty list."""
        OutputFormatter.print_validation_errors([])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_format_table(self) -> None:
        """Test table formatting."""
        headers = ["Name", "Type", "Status"]
        rows = [
            ["server1", "mcp-code-checker", "Active"],
            ["server2", "test-server", "Inactive"],
            ["very-long-server-name", "type", "Running"],
        ]

        table = OutputFormatter.format_table(headers, rows)

        assert "Name" in table
        assert "Type" in table
        assert "Status" in table
        assert "server1" in table
        assert "mcp-code-checker" in table
        assert "Active" in table
        assert "-" in table  # Separator line

    def test_format_table_empty(self) -> None:
        """Test table formatting with empty data."""
        result = OutputFormatter.format_table([], [])
        assert result == ""

        result = OutputFormatter.format_table(["Header"], [])
        assert "Header" in result

    def test_format_table_cell_truncation(self) -> None:
        """Test that long cells are truncated."""
        headers = ["Name"]
        rows = [["x" * 100]]

        table = OutputFormatter.format_table(headers, rows, max_width=80)
        assert "..." in table


class TestOutputFormatterIntegration:
    """Integration tests for OutputFormatter."""

    def test_complete_setup_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test complete setup output sequence."""
        # Simulate a complete setup output
        OutputFormatter.print_info("Starting server setup...")

        params = {
            "project_dir": Path("/my/project"),
            "log_level": "INFO",
            "debug": False,
        }
        OutputFormatter.print_setup_summary("my-checker", "mcp-code-checker", params)

        OutputFormatter.print_success("Server configured successfully")

        captured = capsys.readouterr()
        assert "ℹ Starting server setup..." in captured.out
        assert "Setup Summary:" in captured.out
        assert "✓ Server configured successfully" in captured.out

    def test_complete_error_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test complete error output sequence."""
        # Simulate an error scenario
        OutputFormatter.print_info("Validating configuration...")

        errors = [
            "Project directory does not exist",
            "Invalid Python executable",
        ]
        OutputFormatter.print_validation_errors(errors)

        OutputFormatter.print_error("Setup failed due to validation errors")

        captured = capsys.readouterr()
        assert "ℹ Validating configuration..." in captured.out
        assert "❌ Validation Errors:" in captured.out
        assert "✗ Setup failed" in captured.out

    def test_server_list_output_sequence(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test server list output sequence."""
        OutputFormatter.print_info("Fetching server configurations...")

        servers = [
            {
                "name": "checker1",
                "type": "mcp-code-checker",
                "managed": True,
                "command": "python -m mcp_code_checker",
            },
            {
                "name": "external",
                "type": "custom",
                "managed": False,
                "command": "custom-server",
            },
        ]

        OutputFormatter.print_server_list(servers, detailed=True)
        OutputFormatter.print_success(f"Found {len(servers)} servers")

        captured = capsys.readouterr()
        assert "ℹ Fetching server configurations..." in captured.out
        assert "● checker1" in captured.out
        assert "○ external" in captured.out
        assert "✓ Found 2 servers" in captured.out
