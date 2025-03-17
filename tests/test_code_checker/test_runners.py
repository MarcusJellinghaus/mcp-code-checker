"""
Tests for the code_checker_pytest runner functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest



from src.code_checker_pytest import (
    PytestReport,
    check_code_with_pytest,
    run_tests,
)

from tests.test_code_checker.test_code_checker_pytest_common import _create_test_project, _cleanup_test_project


def test_run_tests() -> None:
    """Integration test for run_tests function with a sample project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        _create_test_project(test_dir)

        try:
            # Run the tests and parse the report
            result = run_tests(str(test_dir), "tests")
            assert isinstance(result, PytestReport)

            # Check the summary
            assert result.summary.total == 2
            assert result.summary.passed == 1
            assert result.summary.failed == 1
            assert result.summary.collected == 2

            # Make sure tests are not None before accessing
            assert result.tests is not None

            # Find the passing and failing tests
            passing_test = next(
                (t for t in result.tests if t.nodeid.endswith("::test_passing")), None
            )
            failing_test = next(
                (t for t in result.tests if t.nodeid.endswith("::test_failing")), None
            )

            # Assert the passing test
            assert passing_test is not None
            assert passing_test.outcome == "passed"
            assert passing_test.call is not None
            assert passing_test.call.outcome == "passed"

            # Assert the failing test
            assert failing_test is not None
            assert failing_test.outcome == "failed"
            assert failing_test.call is not None
            assert failing_test.call.outcome == "failed"
            assert failing_test.call.crash is not None
            assert "assert 1 == 2" in failing_test.call.crash.message
        finally:
            _cleanup_test_project(test_dir)


def test_run_tests_no_tests_found() -> None:
    """Test the run_tests function when no tests are found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        (test_dir / "src").mkdir(parents=True, exist_ok=True)
        (test_dir / "tests").mkdir(parents=True, exist_ok=True)

        with open(test_dir / "src" / "__init__.py", "w") as f:
            f.write("")
        with open(test_dir / "tests" / "__init__.py", "w") as f:
            f.write("")

        try:
            with pytest.raises(
                Exception, match="No Tests Found: Pytest did not find any tests to run."
            ):
                run_tests(str(test_dir), "tests")
        finally:
            _cleanup_test_project(test_dir)


@patch("src.code_checker_pytest.runners.run_tests")
def test_check_code_with_pytest(mock_run_tests: MagicMock) -> None:
    """Test the full check_code_with_pytest function."""
    # Create a mock Summary instance for our mock report
    mock_summary = MagicMock()
    mock_summary.collected = 2
    mock_summary.total = 2
    mock_summary.passed = 2
    mock_summary.failed = 0
    mock_summary.error = 0
    mock_summary.skipped = 0
    mock_summary.xfailed = 0
    mock_summary.xpassed = 0
    mock_summary.deselected = 0

    # Mock the run_tests function to return a test report
    mock_report = PytestReport(
        created=1678972345.123,
        duration=0.5,
        exitcode=0,
        root="/path/to/project",
        environment={"Python": "3.9.0"},
        summary=mock_summary,
    )
    mock_run_tests.return_value = mock_report

    # Call the function
    result = check_code_with_pytest("/test/project")

    # Verify the results
    assert result["success"] is True
    assert "summary" in result
    assert "Collected 2 tests" in result["summary"]
    assert "✅ Passed: 2" in result["summary"]
    assert result["failed_tests_prompt"] is None
    assert result["test_results"] == mock_report


@patch("src.code_checker_pytest.runners.run_tests")
def test_check_code_with_pytest_with_failed_tests(mock_run_tests: MagicMock) -> None:
    """Test check_code_with_pytest with failed tests."""
    # Create a mock Summary instance for our mock report
    mock_summary = MagicMock()
    mock_summary.collected = 4
    mock_summary.total = 4
    mock_summary.passed = 2
    mock_summary.failed = 2
    mock_summary.error = 0
    mock_summary.skipped = 0
    mock_summary.xfailed = 0
    mock_summary.xpassed = 0
    mock_summary.deselected = 0

    # Create a mock test stage with failed outcome
    mock_call = MagicMock()
    mock_call.outcome = "failed"
    mock_call.crash = MagicMock()
    mock_call.crash.message = "AssertionError: assert 1 == 2"
    mock_call.traceback = [MagicMock()]
    mock_call.stdout = "Test output"
    mock_call.stderr = "Test error"
    mock_call.longrepr = "Failure representation"

    # Create mock tests
    mock_test = MagicMock()
    mock_test.nodeid = "test_file.py::test_failing"
    mock_test.outcome = "failed"
    mock_test.call = mock_call

    # Set up the mock report
    mock_report = PytestReport(
        created=1678972345.123,
        duration=0.5,
        exitcode=1,
        root="/path/to/project",
        environment={"Python": "3.9.0"},
        summary=mock_summary,
        tests=[mock_test],
    )
    mock_run_tests.return_value = mock_report

    # Call the function
    result = check_code_with_pytest("/test/project")

    # Verify the results
    assert result["success"] is True
    assert "summary" in result
    assert "Collected 4 tests" in result["summary"]
    assert "✅ Passed: 2" in result["summary"]
    assert "❌ Failed: 2" in result["summary"]
    assert result["failed_tests_prompt"] is not None
    assert "test_file.py::test_failing" in result["failed_tests_prompt"]
    assert result["test_results"] == mock_report


@patch("src.code_checker_pytest.runners.run_tests")
def test_check_code_with_pytest_with_error(mock_run_tests: MagicMock) -> None:
    """Test check_code_with_pytest with an error during test execution."""
    # Make run_tests raise an exception
    mock_run_tests.side_effect = Exception("Test execution error")

    # Call the function
    result = check_code_with_pytest("/test/project")

    # Verify the results
    assert result["success"] is False
    assert "error" in result
    assert result["error"] == "Test execution error"
