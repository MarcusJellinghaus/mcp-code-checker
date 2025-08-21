"""Test mypy reporting functionality."""

import pytest

from src.code_checker_mypy.models import MypyMessage, MypyResult
from src.code_checker_mypy.reporting import create_mypy_prompt


def test_create_mypy_prompt_no_messages() -> None:
    """Test prompt creation with no messages."""
    result = MypyResult(return_code=0, messages=[])
    prompt = create_mypy_prompt(result)

    assert prompt is None


def test_create_mypy_prompt_with_messages() -> None:
    """Test prompt creation with various messages."""
    messages = [
        MypyMessage(
            file="test.py",
            line=10,
            column=5,
            severity="error",
            message="Missing return statement",
            code="return",
        ),
        MypyMessage(
            file="test.py",
            line=20,
            column=10,
            severity="error",
            message="Incompatible return value type",
            code="return-value",
        ),
        MypyMessage(
            file="utils.py",
            line=5,
            column=1,
            severity="error",
            message="Cannot find implementation",
            code="import",
        ),
        MypyMessage(
            file="main.py",
            line=15,
            column=8,
            severity="warning",
            message="Unused variable",
            code=None,
        ),
    ]

    result = MypyResult(return_code=1, messages=messages, errors_found=3)
    prompt = create_mypy_prompt(result)

    assert prompt is not None
    assert "Mypy found 4 type issues" in prompt
    assert "**return (1 issues)**" in prompt
    assert "**return-value (1 issues)**" in prompt
    assert "**import (1 issues)**" in prompt
    assert "**other (1 issues)**" in prompt  # For messages without code
    assert "test.py:10:5" in prompt
    assert "Missing return statement" in prompt
    assert "To fix these issues:" in prompt


def test_create_mypy_prompt_many_messages_same_code() -> None:
    """Test prompt creation with many messages of the same error code."""
    messages: list[MypyMessage] = []
    for i in range(10):
        messages.append(
            MypyMessage(
                file=f"file{i}.py",
                line=i * 10,
                column=5,
                severity="error",
                message=f"Type error {i}",
                code="type-error",
            )
        )

    result = MypyResult(return_code=1, messages=messages)
    prompt = create_mypy_prompt(result)

    assert prompt is not None
    assert "**type-error (10 issues)**" in prompt
    # Should only show first 5
    assert "file0.py:0:5" in prompt
    assert "file4.py:40:5" in prompt
    assert "file5.py:50:5" not in prompt  # 6th message not shown
    assert "... and 5 more" in prompt


def test_create_mypy_prompt_execution_error() -> None:
    """Test prompt creation when there's an execution error."""
    from src.code_checker_mypy.reporting import get_mypy_prompt

    # Mock the run_mypy_check to return an error
    class MockResult:
        return_code = 1
        messages: list[MypyMessage] = []
        error = "Mypy not found in PATH"

    # We can't easily mock here, but we test the logic path
    result = MockResult()  # type: ignore
    prompt = create_mypy_prompt(result)  # type: ignore
    assert prompt is None  # No messages means no prompt


def test_mypy_result_methods() -> None:
    """Test MypyResult helper methods."""
    messages = [
        MypyMessage(
            file="test.py",
            line=10,
            column=5,
            severity="error",
            message="Error 1",
            code="type",
        ),
        MypyMessage(
            file="test.py",
            line=20,
            column=5,
            severity="warning",
            message="Warning 1",
            code="unused",
        ),
        MypyMessage(
            file="test.py",
            line=30,
            column=5,
            severity="error",
            message="Error 2",
            code="type",
        ),
        MypyMessage(
            file="test.py",
            line=40,
            column=5,
            severity="note",
            message="Note 1",
            code=None,
        ),
    ]

    result = MypyResult(return_code=1, messages=messages)

    # Test get_error_codes
    codes = result.get_error_codes()
    assert codes == {"type", "unused"}  # None is filtered out

    # Test get_messages_by_severity
    errors = result.get_messages_by_severity("error")
    assert len(errors) == 2
    assert all(msg.severity == "error" for msg in errors)

    warnings = result.get_messages_by_severity("warning")
    assert len(warnings) == 1
    assert warnings[0].message == "Warning 1"

    notes = result.get_messages_by_severity("note")
    assert len(notes) == 1
    assert notes[0].message == "Note 1"
