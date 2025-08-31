"""
Tests for the server functionality with updated parameter exposure.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_project_dir() -> Path:
    """Return a mock project directory path."""
    return Path("/fake/project/dir")


@pytest.mark.asyncio
async def test_run_pytest_check_parameters(mock_project_dir: Path) -> None:
    """Test that run_pytest_check properly uses server parameters and passes parameters correctly."""
    with (
        patch("mcp.server.fastmcp.FastMCP") as mock_fastmcp,
        patch("mcp_code_checker.server.check_code_with_pytest") as mock_check_pytest,
    ):
        # Setup mocks
        mock_tool = MagicMock()
        mock_fastmcp.return_value.tool.return_value = mock_tool

        # Setup mock result that check_code_with_pytest will return
        mock_check_pytest.return_value = {
            "success": True,
            "summary": {"passed": 5, "failed": 0, "error": 0},
            "test_results": MagicMock(),
        }

        # Import after patching to ensure mocks are in place
        from mcp_code_checker.server import CodeCheckerServer

        # Create server with the static parameters
        server = CodeCheckerServer(
            mock_project_dir, test_folder="custom_tests", keep_temp_files=True
        )

        # Get the run_pytest_check function (it's the second tool registered)
        # Order: run_pylint_check (0), run_pytest_check (1)
        assert (
            len(mock_tool.call_args_list) >= 2
        ), "Expected at least 2 tools to be registered"
        run_pytest_check = mock_tool.call_args_list[1][0][0]

        # Call with only the dynamic parameters (without test_folder and keep_temp_files)
        result = run_pytest_check(
            markers=["slow", "integration"],
            verbosity=3,
            extra_args=["--no-header"],
            env_vars={"TEST_ENV": "value"},
        )

        # Verify check_code_with_pytest was called with correct parameters
        # test_folder and keep_temp_files should come from the server instance
        mock_check_pytest.assert_called_once_with(
            project_dir=str(mock_project_dir),
            test_folder="custom_tests",  # From server constructor
            python_executable=None,
            markers=["slow", "integration"],
            verbosity=3,
            extra_args=["--no-header"],
            env_vars={"TEST_ENV": "value"},
            venv_path=None,
            keep_temp_files=True,  # From server constructor
        )

        # Verify the result is properly formatted
        assert "All 5 tests passed successfully" in result


@pytest.mark.asyncio
async def test_run_all_checks_parameters(mock_project_dir: Path) -> None:
    """Test that run_all_checks properly uses server parameters and passes parameters correctly."""
    with (
        patch("mcp.server.fastmcp.FastMCP") as mock_fastmcp,
        patch("mcp_code_checker.server.get_pylint_prompt") as mock_pylint,
        patch("mcp_code_checker.server.check_code_with_pytest") as mock_check_pytest,
        patch("mcp_code_checker.server.get_mypy_prompt") as mock_mypy,
    ):
        # Setup mocks
        mock_tool = MagicMock()
        mock_fastmcp.return_value.tool.return_value = mock_tool

        # Setup mock results
        mock_pylint.return_value = None
        mock_check_pytest.return_value = {
            "success": True,
            "summary": {"passed": 5, "failed": 0, "error": 0},
            "test_results": MagicMock(),
        }
        mock_mypy.return_value = None

        # Import after patching to ensure mocks are in place
        from mcp_code_checker.server import CodeCheckerServer

        # Create server with the static parameters
        server = CodeCheckerServer(
            mock_project_dir, test_folder="custom_tests", keep_temp_files=True
        )

        # Get the run_all_checks function (it's decorated by mock_tool)
        # Order: run_pylint_check (0), run_pytest_check (1), run_mypy_check (2), run_all_checks (3)
        assert (
            len(mock_tool.call_args_list) >= 4
        ), "Expected at least 4 tools to be registered"
        run_all_checks = mock_tool.call_args_list[3][0][0]

        # Call with only the dynamic parameters (without test_folder and keep_temp_files)
        # The function needs to be invoked to trigger the actual checks
        result = run_all_checks(
            markers=["slow", "integration"],
            verbosity=3,
            extra_args=["--no-header"],
            env_vars={"TEST_ENV": "value"},
            categories=["error"],  # Pass as list of strings
        )

        # Verify check_code_with_pytest was called with correct parameters
        # test_folder and keep_temp_files should come from the server instance
        mock_check_pytest.assert_called_once_with(
            project_dir=str(mock_project_dir),
            test_folder="custom_tests",  # From server constructor
            python_executable=None,
            markers=["slow", "integration"],
            verbosity=3,
            extra_args=["--no-header"],
            env_vars={"TEST_ENV": "value"},
            venv_path=None,
            keep_temp_files=True,  # From server constructor
        )

        # Verify the result contains information from all checks
        assert "All code checks completed" in result
        assert "Pylint:" in result
        assert "Pytest:" in result
        assert "Mypy:" in result
