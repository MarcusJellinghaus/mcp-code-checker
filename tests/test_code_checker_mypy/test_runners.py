"""Test mypy runner functionality."""

import pytest

from src.code_checker_mypy import run_mypy_check


def test_run_mypy_check_on_project() -> None:
    """Test running mypy on the actual project."""
    result = run_mypy_check(project_dir=".", strict=True, target_directories=["src"])

    assert result.return_code in [0, 1]  # 0=no errors, 1=errors found
    assert isinstance(result.messages, list)


def test_run_mypy_check_non_existent_directory() -> None:
    """Test running mypy on a non-existent directory."""
    with pytest.raises(FileNotFoundError, match="Project directory not found"):
        run_mypy_check(project_dir="/non/existent/directory")


def test_run_mypy_check_with_disabled_codes() -> None:
    """Test running mypy with disabled error codes."""
    result = run_mypy_check(
        project_dir=".",
        strict=True,
        disable_error_codes=["import", "arg-type"],
        target_directories=["src"],
    )

    assert result.return_code in [0, 1]
    # Verify that disabled codes are not in the results
    for msg in result.messages:
        if msg.code:
            assert msg.code not in ["import", "arg-type"]
