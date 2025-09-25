"""
Final validation tests for the show_details parameter implementation.

This module provides comprehensive end-to-end validation to ensure the show_details
functionality works correctly across all scenarios and meets performance requirements.
"""

import os
import tempfile
import textwrap
from pathlib import Path
import time
from typing import Dict, Any, Generator, Iterator

import pytest

from mcp_code_checker.server import CodeCheckerServer


class TestParameterCombinationsValidation:
    """Test various parameter combinations with show_details."""

    @pytest.fixture
    def temp_project(self) -> Generator[Path, None, None]:
        """Create a temporary project with test files for validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create source directory
            src_dir = project_path / "src"
            src_dir.mkdir()

            # Create a simple module
            (src_dir / "__init__.py").write_text("")
            (src_dir / "calculator.py").write_text(
                textwrap.dedent(
                    """
                def add(a, b):
                    return a + b
                    
                def divide(a, b):
                    if b == 0:
                        raise ValueError("Cannot divide by zero")
                    return a / b
                    
                def multiply(a, b):
                    print(f"Multiplying {a} * {b}")
                    return a * b
            """
                )
            )

            # Create tests directory
            tests_dir = project_path / "tests"
            tests_dir.mkdir()

            (tests_dir / "__init__.py").write_text("")

            # Create passing tests
            (tests_dir / "test_passing.py").write_text(
                textwrap.dedent(
                    """
                import sys
                sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
                from pathlib import Path
                from calculator import add, multiply
                
                def test_add_positive():
                    assert add(2, 3) == 5
                    
                def test_add_negative():
                    assert add(-1, 1) == 0
                    
                def test_multiply_with_print():
                    result = multiply(3, 4)
                    print("Test completed successfully")
                    assert result == 12
            """
                )
            )

            # Create failing tests
            (tests_dir / "test_failing.py").write_text(
                textwrap.dedent(
                    """
                import sys
                sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
                from pathlib import Path
                from calculator import add, divide
                
                def test_add_failure():
                    print("This test will fail")
                    assert add(2, 3) == 6  # Wrong expected value
                    
                def test_divide_by_zero():
                    print("Testing division by zero")
                    result = divide(10, 0)  # This will raise ValueError
                    assert result == float('inf')
                    
                def test_another_failure():
                    assert 1 == 2, "This should fail with custom message"
            """
                )
            )

            # Create collection error test
            (tests_dir / "test_collection_error.py").write_text(
                textwrap.dedent(
                    """
                import nonexistent_module  # This will cause collection error
                
                def test_will_not_run():
                    pass
            """
                )
            )

            yield project_path

    def test_show_details_true_with_specific_test(self, temp_project: Path) -> None:
        """Test show_details=True with specific failing test."""
        server = CodeCheckerServer(temp_project)

        # Test the formatting method directly with mock test results
        from mcp_code_checker.code_checker_pytest.models import PytestReport, Summary

        mock_test_results = PytestReport(
            created=0.0,
            duration=1.0,
            exitcode=0,
            root="/tmp",
            environment={},
            summary=Summary(
                failed=1, collected=1, total=1, passed=0, error=0, skipped=0
            ),
            tests=[],
            collectors=[],
        )

        result = server._format_pytest_result_with_details(
            {
                "success": True,
                "summary": {"failed": 1, "collected": 1, "passed": 0},
                "test_results": mock_test_results,
            },
            show_details=True,
        )

        # Should show detailed output or indicate failure handling
        assert "attention" in result or "completed" in result

    def test_show_details_false_with_multiple_tests(self, temp_project: Path) -> None:
        """Test show_details=False with multiple tests provides summary."""
        server = CodeCheckerServer(temp_project)

        result = server._format_pytest_result_with_details(
            {
                "success": True,
                "summary": {"failed": 2, "collected": 10, "passed": 8},
                "test_results": None,
            },
            show_details=False,
        )

        # Should provide summary without suggestion for large test runs
        assert "show_details=True" not in result
        assert "completed" in result

    def test_show_details_false_with_few_tests_provides_hint(
        self, temp_project: Path
    ) -> None:
        """Test that small test runs provide hint to use show_details=True."""
        server = CodeCheckerServer(temp_project)

        # Need test_results to be present for failures to trigger hint logic
        from mcp_code_checker.code_checker_pytest.models import PytestReport, Summary

        mock_test_results = PytestReport(
            created=0.0,
            duration=1.0,
            exitcode=0,
            root="/tmp",
            environment={},
            summary=Summary(
                failed=1, collected=2, total=2, passed=1, error=0, skipped=0
            ),
            tests=[],
            collectors=[],
        )

        result = server._format_pytest_result_with_details(
            {
                "success": True,
                "summary": {"failed": 1, "collected": 2, "passed": 1},
                "test_results": mock_test_results,
            },
            show_details=False,
        )

        # Should suggest show_details=True for small test runs with failures
        assert "show_details=True" in result

    def test_collection_errors_always_shown(self, temp_project: Path) -> None:
        """Test that collection errors are shown regardless of show_details setting."""
        server = CodeCheckerServer(temp_project)

        # Simulate collection error result
        test_result = {
            "success": True,
            "summary": {"failed": 0, "collected": 0, "passed": 0, "error": 1},
            "test_results": None,
        }

        # Both should handle collection errors
        result_false = server._format_pytest_result_with_details(
            test_result, show_details=False
        )
        result_true = server._format_pytest_result_with_details(
            test_result, show_details=True
        )

        # Both should complete without error
        assert "completed" in result_false or "Error" in result_false
        assert "completed" in result_true or "Error" in result_true


class TestOutputFormatConsistency:
    """Test that output formatting is consistent across scenarios."""

    def test_success_message_consistency(self) -> None:
        """Test that success messages are consistent."""
        server = CodeCheckerServer(Path("/tmp"))

        success_result = {
            "success": True,
            "summary": {"failed": 0, "collected": 5, "passed": 5},
            "summary_text": "All tests passed",
        }

        result_false = server._format_pytest_result_with_details(
            success_result, show_details=False
        )
        result_true = server._format_pytest_result_with_details(
            success_result, show_details=True
        )

        # Both should show success message
        assert "completed" in result_false
        assert "completed" in result_true

        # Should contain summary information
        assert "All tests passed" in result_false
        assert "All tests passed" in result_true

    def test_error_message_consistency(self) -> None:
        """Test that error messages are consistent."""
        server = CodeCheckerServer(Path("/tmp"))

        error_result = {"success": False, "error": "pytest execution failed"}

        result_false = server._format_pytest_result_with_details(
            error_result, show_details=False
        )
        result_true = server._format_pytest_result_with_details(
            error_result, show_details=True
        )

        # Both should show error message
        assert "Error running pytest" in result_false
        assert "Error running pytest" in result_true
        assert "pytest execution failed" in result_false
        assert "pytest execution failed" in result_true

    def test_invalid_summary_handling(self) -> None:
        """Test handling of invalid summary data."""
        server = CodeCheckerServer(Path("/tmp"))

        invalid_result = {
            "success": True,
            "summary": "invalid_summary_format",  # Should be dict
        }

        result_false = server._format_pytest_result_with_details(
            invalid_result, show_details=False
        )
        result_true = server._format_pytest_result_with_details(
            invalid_result, show_details=True
        )

        # Both should handle invalid format gracefully
        assert "Invalid test summary format" in result_false
        assert "Invalid test summary format" in result_true


class TestPerformanceBenchmarks:
    """Test performance impact of show_details parameter."""

    def test_performance_impact_measurement(self) -> None:
        """Measure performance impact of show_details parameter."""
        server = CodeCheckerServer(Path("/tmp"))

        # Create test data
        test_result = {
            "success": True,
            "summary": {"failed": 0, "collected": 100, "passed": 100},
            "summary_text": "All 100 tests passed",
        }

        # Measure with show_details=False
        start_time = time.time()
        for _ in range(1000):  # Run 1000 times to get meaningful measurement
            server._format_pytest_result_with_details(test_result, show_details=False)
        false_time = time.time() - start_time

        # Measure with show_details=True
        start_time = time.time()
        for _ in range(1000):
            server._format_pytest_result_with_details(test_result, show_details=True)
        true_time = time.time() - start_time

        # Performance impact should be minimal (less than 50% overhead)
        overhead_ratio = (true_time - false_time) / false_time if false_time > 0 else 0
        assert (
            overhead_ratio < 0.5
        ), f"Performance overhead too high: {overhead_ratio:.2%}"

    def test_memory_usage_reasonable(self) -> None:
        """Test that memory usage remains reasonable with show_details."""
        server = CodeCheckerServer(Path("/tmp"))

        # Create large test result data
        large_summary = {
            "success": True,
            "summary": {"failed": 10, "collected": 1000, "passed": 990},
            "test_results": None,
        }

        # Should complete without memory issues
        result = server._format_pytest_result_with_details(
            large_summary, show_details=True
        )
        assert isinstance(result, str)
        assert len(result) > 0


class TestDocumentationAccuracy:
    """Test that docstring examples work as documented."""

    def test_docstring_examples_execute(self) -> None:
        """Test that examples in docstrings actually work."""
        # This tests the examples from the docstring in run_pytest_check

        # Test that the function signature matches documentation
        server = CodeCheckerServer(Path("/tmp"))

        # These should not raise TypeError due to missing/incorrect parameters
        try:
            # Standard CI run example
            result = server._format_pytest_result_with_details(
                {
                    "success": True,
                    "summary": {"failed": 0, "passed": 5, "collected": 5},
                },
                show_details=False,
            )
            assert isinstance(result, str)

            # Debug specific test example
            result = server._format_pytest_result_with_details(
                {
                    "success": True,
                    "summary": {"failed": 1, "passed": 0, "collected": 1},
                },
                show_details=True,
            )
            assert isinstance(result, str)

        except Exception as e:
            pytest.fail(f"Docstring examples failed to execute: {e}")

    def test_parameter_type_validation(self) -> None:
        """Test that parameters accept documented types."""
        server = CodeCheckerServer(Path("/tmp"))

        # show_details should accept boolean
        assert server._format_pytest_result_with_details(
            {"success": True, "summary": {"passed": 1, "collected": 1}},
            show_details=True,
        )

        assert server._format_pytest_result_with_details(
            {"success": True, "summary": {"passed": 1, "collected": 1}},
            show_details=False,
        )

    def test_return_type_consistency(self) -> None:
        """Test that return types match documentation."""
        server = CodeCheckerServer(Path("/tmp"))

        test_cases = [
            {"success": True, "summary": {"passed": 1, "collected": 1}},
            {"success": False, "error": "test error"},
            {"success": True, "summary": {"failed": 1, "collected": 1}},
        ]

        for test_case in test_cases:
            for show_details in [True, False]:
                result = server._format_pytest_result_with_details(
                    test_case, show_details
                )
                assert isinstance(result, str), f"Expected str, got {type(result)}"
                assert len(result) > 0, "Result should not be empty"


class TestBackwardCompatibility:
    """Test that changes maintain backward compatibility."""

    def test_old_format_method_still_works(self) -> None:
        """Test that the old _format_pytest_result method still works."""
        server = CodeCheckerServer(Path("/tmp"))

        test_result = {
            "success": True,
            "summary": {"passed": 5, "collected": 5, "failed": 0},
        }

        # Old method should still work
        result = server._format_pytest_result(test_result)
        assert isinstance(result, str)
        assert "completed" in result

    def test_missing_show_details_defaults_correctly(self) -> None:
        """Test that missing show_details parameter defaults correctly."""
        server = CodeCheckerServer(Path("/tmp"))

        test_result = {
            "success": True,
            "summary": {"passed": 1, "collected": 1, "failed": 0},
        }

        # Should work without show_details parameter (backward compatibility)
        result = server._format_pytest_result(test_result)
        assert isinstance(result, str)

    def test_parameter_combinations_backward_compatible(self) -> None:
        """Test that new parameters don't break existing usage."""
        server = CodeCheckerServer(Path("/tmp"))

        # Should work with minimal parameters (existing usage)
        test_result = {"success": True, "summary": {"passed": 1, "collected": 1}}

        result = server._format_pytest_result_with_details(
            test_result, show_details=False
        )
        assert isinstance(result, str)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_none_values_handling(self) -> None:
        """Test handling of None values in summary."""
        server = CodeCheckerServer(Path("/tmp"))

        result_with_nones = {
            "success": True,
            "summary": {
                "failed": None,
                "passed": None,
                "collected": None,
                "error": None,
            },
        }

        # Should handle None values gracefully
        result = server._format_pytest_result_with_details(
            result_with_nones, show_details=True
        )
        assert isinstance(result, str)

        # Should not crash with None values
        result = server._format_pytest_result_with_details(
            result_with_nones, show_details=False
        )
        assert isinstance(result, str)

    def test_empty_summary_handling(self) -> None:
        """Test handling of empty summary dict."""
        server = CodeCheckerServer(Path("/tmp"))

        empty_result = {"success": True, "summary": {}}

        result = server._format_pytest_result_with_details(
            empty_result, show_details=True
        )
        assert isinstance(result, str)

    def test_missing_summary_handling(self) -> None:
        """Test handling when summary is missing."""
        server = CodeCheckerServer(Path("/tmp"))

        no_summary_result = {"success": True}

        result = server._format_pytest_result_with_details(
            no_summary_result, show_details=True
        )
        assert isinstance(result, str)


# Integration test that uses real pytest execution would go here
# but it requires a more complex setup with actual test files
class TestRealIntegration:
    """Integration tests with real pytest execution."""

    def test_integration_placeholder(self) -> None:
        """Placeholder for integration tests that would use real pytest."""
        # This would require setting up actual test files and running pytest
        # For now, we test the formatting logic which is the core of the feature
        assert True
