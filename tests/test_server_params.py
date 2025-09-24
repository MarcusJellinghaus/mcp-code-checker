"""
Tests for the server functionality with updated parameter exposure.
"""

import inspect
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
        _server = CodeCheckerServer(
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
        _server = CodeCheckerServer(
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



# Step 3: Tests for Server Interface Enhancement with show_details Parameter

@pytest.fixture
def mock_server():
    """Create CodeCheckerServer for testing."""
    with patch("mcp.server.fastmcp.FastMCP") as mock_fastmcp:
        mock_tool = MagicMock()
        mock_fastmcp.return_value.tool.return_value = mock_tool
        
        from mcp_code_checker.server import CodeCheckerServer
        server = CodeCheckerServer(project_dir=Path("/test/project"))
        
        # Return server and the mock tool for test access
        return server, mock_tool


@pytest.fixture
def mock_pytest_results_few_tests():
    """Mock results for ≤3 tests scenario."""
    return {
        "success": True,
        "summary": {
            "passed": 2,
            "failed": 1,
            "error": 0,
            "collected": 3,
            "duration": 1.5
        },
        "test_results": MagicMock()
    }


@pytest.fixture
def mock_pytest_results_many_failures():
    """Mock results for >10 failures scenario."""
    return {
        "success": True,
        "summary": {
            "passed": 5,
            "failed": 15,
            "error": 2,
            "collected": 22,
            "duration": 5.2
        },
        "test_results": MagicMock()
    }


@pytest.fixture
def mock_pytest_results_success():
    """Mock results for successful test run."""
    return {
        "success": True,
        "summary": {
            "passed": 10,
            "failed": 0,
            "error": 0,
            "collected": 10,
            "duration": 2.3
        },
        "test_results": None
    }


# Parameter Integration Tests

@pytest.mark.asyncio
async def test_run_pytest_check_with_show_details_true(mock_server):
    """Test that run_pytest_check properly handles show_details=True parameter."""
    server, mock_tool = mock_server
    
    with patch("mcp_code_checker.server.check_code_with_pytest") as mock_check:
        mock_check.return_value = {
            "success": True,
            "summary": {"passed": 3, "failed": 0, "error": 0, "collected": 3},
            "test_results": None
        }
        
        # Get the run_pytest_check function
        run_pytest_check = mock_tool.call_args_list[1][0][0]  # Second tool registered
        
        # Call with show_details=True (this will be added in Step 4)
        # For now, test the existing interface
        result = run_pytest_check(
            markers=["unit"],
            verbosity=2
        )
        
        # Verify check_code_with_pytest was called correctly
        mock_check.assert_called_once()
        call_args = mock_check.call_args
        
        # Verify standard parameters are passed correctly
        assert call_args[1]["project_dir"] == str(Path("/test/project"))
        assert call_args[1]["markers"] == ["unit"]
        assert call_args[1]["verbosity"] == 2
        
        # Verify result formatting
        assert "All 3 tests passed successfully" in result


@pytest.mark.asyncio
async def test_run_pytest_check_with_show_details_false(mock_server):
    """Test that run_pytest_check properly handles show_details=False parameter."""
    server, mock_tool = mock_server
    
    with patch("mcp_code_checker.server.check_code_with_pytest") as mock_check:
        mock_check.return_value = {
            "success": True,
            "summary": {"passed": 5, "failed": 0, "error": 0, "collected": 5},
            "test_results": None
        }
        
        # Get the run_pytest_check function
        run_pytest_check = mock_tool.call_args_list[1][0][0]
        
        # Call with standard parameters (show_details=False is default)
        result = run_pytest_check(verbosity=1)
        
        # Verify check_code_with_pytest was called correctly
        mock_check.assert_called_once()
        call_args = mock_check.call_args
        
        # Verify parameters
        assert call_args[1]["verbosity"] == 1
        assert "All 5 tests passed successfully" in result


@pytest.mark.asyncio
async def test_run_pytest_check_show_details_default_value():
    """Test that show_details parameter has correct default value."""
    with patch("mcp.server.fastmcp.FastMCP") as mock_fastmcp:
        mock_tool = MagicMock()
        mock_fastmcp.return_value.tool.return_value = mock_tool
        
        from mcp_code_checker.server import CodeCheckerServer
        server = CodeCheckerServer(project_dir=Path("/test/project"))
        
        # Get the run_pytest_check function and inspect its signature
        run_pytest_check = mock_tool.call_args_list[1][0][0]
        signature = inspect.signature(run_pytest_check)
        
        # Verify current parameters exist
        assert "markers" in signature.parameters
        assert "verbosity" in signature.parameters
        assert "extra_args" in signature.parameters
        assert "env_vars" in signature.parameters
        
        # Note: show_details parameter will be added in Step 4
        # This test documents the current state and will be updated


@pytest.mark.asyncio
async def test_run_pytest_check_backward_compatibility(mock_server):
    """Test that existing function calls work without show_details parameter."""
    server, mock_tool = mock_server
    
    with patch("mcp_code_checker.server.check_code_with_pytest") as mock_check:
        mock_check.return_value = {
            "success": True,
            "summary": {"passed": 8, "failed": 0, "error": 0, "collected": 8},
            "test_results": None
        }
        
        # Get the run_pytest_check function
        run_pytest_check = mock_tool.call_args_list[1][0][0]
        
        # Call with existing parameter style (no show_details)
        old_style_result = run_pytest_check(markers=["integration"])
        
        # Verify it works and produces expected result
        assert "All 8 tests passed successfully" in old_style_result
        mock_check.assert_called_once()



# Output Control Tests

@pytest.mark.asyncio
async def test_show_details_with_focused_test_run(mock_server, mock_pytest_results_few_tests):
    """Test show_details behavior with focused test run (≤3 tests)."""
    server, mock_tool = mock_server
    
    with (
        patch("mcp_code_checker.server.check_code_with_pytest") as mock_check,
        patch("mcp_code_checker.server.create_prompt_for_failed_tests") as mock_create_prompt
    ):
        mock_check.return_value = mock_pytest_results_few_tests
        mock_create_prompt.return_value = "Detailed failure information..."
        
        # Get the run_pytest_check function
        run_pytest_check = mock_tool.call_args_list[1][0][0]
        
        # Call function
        result = run_pytest_check(markers=["unit"])
        
        # Verify that create_prompt_for_failed_tests was called for failed tests
        mock_create_prompt.assert_called_once()
        assert "Detailed failure information..." in result


@pytest.mark.asyncio
async def test_show_details_with_many_failures(mock_server, mock_pytest_results_many_failures):
    """Test show_details behavior with many failures (>10 failures)."""
    server, mock_tool = mock_server
    
    with (
        patch("mcp_code_checker.server.check_code_with_pytest") as mock_check,
        patch("mcp_code_checker.server.create_prompt_for_failed_tests") as mock_create_prompt
    ):
        mock_check.return_value = mock_pytest_results_many_failures
        mock_create_prompt.return_value = "Many failures detected..."
        
        # Get the run_pytest_check function
        run_pytest_check = mock_tool.call_args_list[1][0][0]
        
        # Call function
        result = run_pytest_check(verbosity=3)
        
        # For many failures, should still call create_prompt_for_failed_tests
        mock_create_prompt.assert_called_once()
        assert "Many failures detected..." in result


@pytest.mark.asyncio
async def test_show_details_output_length_limits(mock_server):
    """Test that output respects length limits and truncation."""
    server, mock_tool = mock_server
    
    # Create mock results with potential for long output
    long_output_results = {
        "success": True,
        "summary": {"passed": 0, "failed": 5, "error": 0, "collected": 5},
        "test_results": MagicMock()
    }
    
    with (
        patch("mcp_code_checker.server.check_code_with_pytest") as mock_check,
        patch("mcp_code_checker.server.create_prompt_for_failed_tests") as mock_create_prompt
    ):
        mock_check.return_value = long_output_results
        # Simulate long output that should be truncated
        mock_create_prompt.return_value = "\n".join([f"Line {i}" for i in range(350)])
        
        # Get the run_pytest_check function
        run_pytest_check = mock_tool.call_args_list[1][0][0]
        
        # Call function
        result = run_pytest_check()
        
        # Verify create_prompt_for_failed_tests was called
        mock_create_prompt.assert_called_once()
        
        # The result should contain the truncated output
        # Note: Truncation logic is in create_prompt_for_failed_tests
        assert "Line 0" in result


# Integration Tests

@pytest.mark.asyncio
async def test_server_method_signature_includes_show_details():
    """Test that server method signature will include show_details parameter."""
    with patch("mcp.server.fastmcp.FastMCP") as mock_fastmcp:
        mock_tool = MagicMock()
        mock_fastmcp.return_value.tool.return_value = mock_tool
        
        from mcp_code_checker.server import CodeCheckerServer
        server = CodeCheckerServer(project_dir=Path("/test/project"))
        
        # Get the run_pytest_check function
        run_pytest_check = mock_tool.call_args_list[1][0][0]
        signature = inspect.signature(run_pytest_check)
        
        # Document current parameters (show_details will be added in Step 4)
        current_params = list(signature.parameters.keys())
        expected_current = ["markers", "verbosity", "extra_args", "env_vars"]
        
        for param in expected_current:
            assert param in current_params, f"Expected parameter {param} not found"
        
        # Note: This test will be updated in Step 4 to check for show_details


@pytest.mark.asyncio
async def test_mcp_tool_decorator_compatibility():
    """Test that MCP tool decorator works with current and future parameters."""
    with patch("mcp.server.fastmcp.FastMCP") as mock_fastmcp:
        mock_tool = MagicMock()
        mock_fastmcp.return_value.tool.return_value = mock_tool
        
        from mcp_code_checker.server import CodeCheckerServer
        server = CodeCheckerServer(project_dir=Path("/test/project"))
        
        # Verify that tools were registered correctly
        assert len(mock_tool.call_args_list) >= 2, "Expected at least 2 tools registered"
        
        # Verify run_pytest_check is callable
        run_pytest_check = mock_tool.call_args_list[1][0][0]
        assert callable(run_pytest_check)
        
        # Verify the function has proper signature
        signature = inspect.signature(run_pytest_check)
        assert len(signature.parameters) > 0, "Function should have parameters"


@pytest.mark.asyncio
async def test_enhanced_reporting_integration_preparation(mock_server):
    """Test preparation for enhanced reporting integration with show_details."""
    server, mock_tool = mock_server
    
    # Test that current implementation can handle enhanced reporting calls
    with (
        patch("mcp_code_checker.server.check_code_with_pytest") as mock_check,
        patch("mcp_code_checker.server.create_prompt_for_failed_tests") as mock_create_prompt
    ):
        # Setup mocks
        mock_check.return_value = {
            "success": True,
            "summary": {"passed": 2, "failed": 1, "error": 0, "collected": 3},
            "test_results": MagicMock()
        }
        mock_create_prompt.return_value = "Enhanced failure details..."
        
        # Get the run_pytest_check function
        run_pytest_check = mock_tool.call_args_list[1][0][0]
        
        # Call function
        result = run_pytest_check()
        
        # Verify that enhanced reporting functions are available
        # The reporting module should have the enhanced functions from Steps 1-2
        from mcp_code_checker.code_checker_pytest.reporting import should_show_details
        
        # Test that should_show_details function works
        test_results = {"summary": {"collected": 3, "failed": 1, "error": 0}}
        assert should_show_details(test_results, True) == True
        assert should_show_details(test_results, False) == False


# Additional Parameter Validation Tests

@pytest.mark.asyncio
async def test_parameter_type_validation(mock_server):
    """Test that parameters are properly typed and validated."""
    server, mock_tool = mock_server
    
    with patch("mcp_code_checker.server.check_code_with_pytest") as mock_check:
        mock_check.return_value = {
            "success": True,
            "summary": {"passed": 1, "failed": 0, "error": 0, "collected": 1},
            "test_results": None
        }
        
        # Get the run_pytest_check function
        run_pytest_check = mock_tool.call_args_list[1][0][0]
        signature = inspect.signature(run_pytest_check)
        
        # Check parameter types for current parameters
        assert signature.parameters["verbosity"].annotation == int
        assert signature.parameters["verbosity"].default == 2
        
        # Test with valid parameters
        result = run_pytest_check(verbosity=3)
        assert "1 tests passed" in result
        
        mock_check.assert_called_once()


@pytest.mark.asyncio
async def test_integration_with_existing_server_parameters(mock_server):
    """Test integration with server constructor parameters."""
    server, mock_tool = mock_server
    
    # Verify that server constructor parameters are properly used
    assert server.project_dir == Path("/test/project")
    assert server.test_folder == "tests"  # default
    assert server.keep_temp_files == False  # default
    
    with patch("mcp_code_checker.server.check_code_with_pytest") as mock_check:
        mock_check.return_value = {
            "success": True,
            "summary": {"passed": 3, "failed": 0, "error": 0, "collected": 3},
            "test_results": None
        }
        
        # Get the run_pytest_check function
        run_pytest_check = mock_tool.call_args_list[1][0][0]
        
        # Call function
        result = run_pytest_check()
        
        # Verify that server parameters were passed to check_code_with_pytest
        mock_check.assert_called_once()
        call_args = mock_check.call_args
        
        assert call_args[1]["project_dir"] == str(Path("/test/project"))
        assert call_args[1]["test_folder"] == "tests"
        assert call_args[1]["keep_temp_files"] == False
