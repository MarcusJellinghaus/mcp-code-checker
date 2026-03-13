# Step 6: Extract Shared Test Helper to `conftest.py`

## Context
See `pr_info/steps/summary.md` for full context. This is step 6 of 7 (post-review fix).

Identified during code review (Decision 12): Both `test_tool_availability.py` and `test_error_transparency.py` define identical `_make_command_result()` helper functions.

## Goal
Extract `_make_command_result()` to `tests/conftest.py` as a shared pytest fixture. Remove duplicates from both test files.

## LLM Prompt
> Implement Step 6 of Issue #89 (see `pr_info/steps/summary.md` for context, Decision 12 in `pr_info/steps/Decisions.md`). Extract the duplicate `_make_command_result()` helper from `test_tool_availability.py` and `test_error_transparency.py` into a new `tests/conftest.py`. Use a regular function (not a fixture) since it's a factory, not a fixture. Run all quality checks after.

## WHERE

- `tests/conftest.py` — new file, shared test utilities
- `tests/test_tool_availability.py` — remove local `_make_command_result`, import from conftest
- `tests/test_error_transparency.py` — remove local `_make_command_result`, import from conftest

## WHAT

### New: `tests/conftest.py`

```python
"""Shared test utilities and fixtures."""

from mcp_code_checker.utils.subprocess_runner import CommandResult


def make_command_result(
    return_code: int = 0,
    stdout: str = "",
    stderr: str = "",
    execution_error: str | None = None,
    timed_out: bool = False,
) -> CommandResult:
    """Helper to build a CommandResult for mocking."""
    return CommandResult(
        return_code=return_code,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
        execution_error=execution_error,
    )
```

Note: Use `make_command_result` (no underscore prefix) since it's now a public shared helper. Since it's a factory function (takes parameters, returns a new object), it should be a plain function, not a pytest fixture.

### Modified: `tests/test_tool_availability.py`
- Remove the local `_make_command_result` function definition
- Add `from conftest import make_command_result` (or just use it directly — pytest auto-discovers conftest.py)
- Replace all `_make_command_result(...)` calls with `make_command_result(...)`

### Modified: `tests/test_error_transparency.py`
- Same changes as above

## HOW

- pytest automatically loads `conftest.py` from the tests directory
- Plain functions in conftest.py can be imported directly by test files
- No fixture decorator needed — this is a factory helper, not a fixture

## ALGORITHM

```
# 1. Create tests/conftest.py with make_command_result()
# 2. In test_tool_availability.py:
#    - Remove _make_command_result definition
#    - Add: from conftest import make_command_result
#    - Replace all calls
# 3. In test_error_transparency.py:
#    - Same as above
```

## DATA

- No new data structures — same `CommandResult` return type
- Function renamed from `_make_command_result` to `make_command_result` (public API)

## Tests

- All existing tests in both files must pass unchanged (only the helper source changes)
- No new tests needed — this is a pure refactoring step

## Verification
- `tests/test_tool_availability.py` — all tests pass
- `tests/test_error_transparency.py` — all tests pass
- No duplicate `_make_command_result` definitions remain in test files
- Run pylint, pytest, mypy — all pass
