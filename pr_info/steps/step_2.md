# Step 2: Add Stderr Surfacing and "No Module Named" Detection to All Runners

## Context
See `pr_info/steps/summary.md` for full context. This is step 2 of 4.

## Goal
When a tool subprocess fails with no usable output, surface stderr (truncated to 500 chars) in the error message. When stderr contains `"No module named <tool>"`, raise a specific actionable error instead.

## LLM Prompt
> Implement Step 2 of Issue #89 (see `pr_info/steps/summary.md` for context). Add a `MAX_STDERR_IN_ERROR = 500` constant to `subprocess_runner.py`. Then improve error messages in all three runners (pytest, pylint, mypy) to detect "No module named" and to surface truncated stderr on failure. Write tests first (TDD), then implement.

## WHERE

- `src/mcp_code_checker/utils/subprocess_runner.py` — add constant
- `src/mcp_code_checker/code_checker_pytest/runners.py` — improve error in `run_tests()`
- `src/mcp_code_checker/code_checker_pylint/runners.py` — improve error in `get_pylint_results()`
- `src/mcp_code_checker/code_checker_mypy/runners.py` — improve error in `run_mypy_check()`
- `tests/test_error_transparency.py` — new test file

## WHAT

### In `subprocess_runner.py`:
- **Add**: `MAX_STDERR_IN_ERROR: int = 500` module-level constant
- **Add**: Shared helper function `check_tool_missing_error(stderr: str, tool_name: str, python_path: str) -> str | None` — checks stderr for `"No module named <tool>"`, returns a specific actionable error string or `None`. Also provides `truncate_stderr(stderr: str) -> str` for truncating stderr to `MAX_STDERR_IN_ERROR` chars.

### In pytest `runners.py` — `run_tests()`:

**Function**: No new functions. Modify the existing error path at the bottom of `run_tests()` where `RuntimeError("Test execution completed but no report file was generated...")` is raised.

**Signature change**: None.

**Current code** (~line 188):
```python
raise RuntimeError(
    "Test execution completed but no report file was generated. "
    "Check for configuration errors in pytest.ini or pytest plugins."
)
```

**New logic**: Before this raise, check `combined_output` for `"No module named pytest"`. If matched, raise a specific error. Otherwise, append truncated stderr.

### In pylint `runners.py` — `get_pylint_results()`:

**Current code** (~line 96): When `subprocess_result.execution_error` is set, it returns:
```python
return PylintResult(return_code=..., messages=[], error=subprocess_result.execution_error, raw_output=None)
```

**New logic**: Before returning, check `subprocess_result.stderr` for `"No module named pylint"`. If matched, return specific error. For the existing `execution_error` case, append truncated stderr if available.

### In mypy `runners.py` — `run_mypy_check()`:

**New logic**: Add "No module named mypy" check **early**, right after `execute_command()` returns, **before** any parsing or existing `return_code==2` handling. This gives tool-missing detection priority. The existing return_code==2 stderr handling for config errors remains unchanged and handles other cases.

**Current code** (~line 107): When `result.execution_error` is set:
```python
return MypyResult(return_code=..., messages=[], error=result.execution_error)
```

**Additional**: For the `execution_error` case, append truncated stderr if available.

## HOW

Import `check_tool_missing_error`, `truncate_stderr`, and `MAX_STDERR_IN_ERROR` from `mcp_code_checker.utils.subprocess_runner` in each runner. Use the shared helper instead of duplicating detection logic.

## ALGORITHM (pseudocode for each runner)

```
# Shared helper in subprocess_runner.py:
def check_tool_missing_error(stderr, tool_name, python_path) -> str | None:
    if f"No module named {tool_name}" in stderr:
        return f"{tool_name} is not installed in the configured Python environment ({python_path}). ..."
    return None

def truncate_stderr(stderr, max_len=MAX_STDERR_IN_ERROR) -> str:
    return stderr[:max_len] + ("..." if len(stderr) > max_len else "")

# Each runner calls the shared helper:
stderr = subprocess_result.stderr or ""
tool_error = check_tool_missing_error(stderr, "<toolname>", python_path)
if tool_error:
    raise/return tool_error
elif no_usable_output:
    append truncate_stderr(stderr) to existing error message
```

**For mypy specifically**: The tool-missing check goes right after `execute_command()`, before the existing `return_code==2` block.

## DATA

- **New constant**: `MAX_STDERR_IN_ERROR = 500` in `subprocess_runner.py`
- **Return values**: No structural changes. Error strings become more descriptive.
- **Error message format for missing tool**:
  `"<tool> is not installed in the configured Python environment (<python_path>). Ensure --python-executable and --venv-path point to the environment where <tool> is installed."`

## Tests (TDD — write first)

### File: `tests/test_error_transparency.py`

```python
# Test structure outline:

class TestPytestNoModuleDetection:
    """Test that 'No module named pytest' in stderr produces actionable error."""
    
    def test_no_module_pytest_detected(self):
        # Mock execute_command to return stderr="No module named pytest"
        # Call run_tests() and assert RuntimeError with specific message
    
    def test_stderr_surfaced_on_generic_failure(self):
        # Mock execute_command to return stderr="some other error"
        # Call run_tests() and assert error contains truncated stderr

class TestPylintNoModuleDetection:
    """Test that 'No module named pylint' in stderr produces actionable error."""
    
    def test_no_module_pylint_detected(self):
        # Mock execute_command to return execution_error + stderr with "No module named pylint"
        # Call get_pylint_results() and assert error contains specific message
    
    def test_stderr_appended_to_execution_error(self):
        # Mock with generic stderr, assert it's included in error

class TestMypyNoModuleDetection:
    """Test that 'No module named mypy' in stderr produces actionable error."""
    
    def test_no_module_mypy_detected(self):
        # Mock execute_command to return execution_error + stderr with "No module named mypy"
        # Call run_mypy_check() and assert error contains specific message
    
    def test_stderr_appended_to_execution_error(self):
        # Mock with generic stderr, assert it's included in error

class TestMaxStderrTruncation:
    """Test that stderr is truncated to MAX_STDERR_IN_ERROR chars."""
    
    def test_long_stderr_truncated(self):
        # Provide stderr > 500 chars, assert output is truncated
```

## Verification
- Run `tests/test_error_transparency.py` — all new tests pass
- Run full test suite — no regressions
