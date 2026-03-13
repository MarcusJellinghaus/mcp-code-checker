# Step 5: Pass `_resolved_python` to Runners and Remove Duplicate Fallback

## Context
See `pr_info/steps/summary.md` for full context. This is step 5 of 7 (post-review fix).

Identified during code review (Decision 10): The server resolves the Python executable in `_resolve_python_executable()` but tool handlers still pass raw `self.python_executable` to runners. Each runner independently falls back to `sys.executable`, duplicating resolution logic.

## Goal
Pass `self._resolved_python` from tool handlers to runners. Remove the `python_executable or sys.executable` fallback pattern from each runner.

## LLM Prompt
> Implement Step 5 of Issue #89 (see `pr_info/steps/summary.md` for context, Decision 10 in `pr_info/steps/Decisions.md`). The server's `_resolved_python` must be passed to all runner functions instead of the raw `self.python_executable`. Remove the duplicate `python_executable or sys.executable` fallback from each runner. Write/update tests first (TDD), then implement. Run all quality checks after.

## WHERE

- `src/mcp_code_checker/server.py` — change tool handlers to pass `self._resolved_python`
- `src/mcp_code_checker/code_checker_pytest/runners.py` — remove `py_executable = python_executable or sys.executable` fallback
- `src/mcp_code_checker/code_checker_pylint/runners.py` — remove `python_exe = python_executable if python_executable is not None else sys.executable` fallback
- `src/mcp_code_checker/code_checker_mypy/runners.py` — remove `python_exe = python_executable or sys.executable` fallback

## WHAT

### Modified: `server.py` tool handlers

In `run_pylint_check`, `run_pytest_check`, and `run_mypy_check`, replace `python_executable=self.python_executable` with `python_executable=self._resolved_python`.

### Modified: All three runners

Remove the fallback pattern. The `python_executable` parameter is now guaranteed to be a resolved path (never `None`).

**Pylint** (`get_pylint_results`):
```python
# BEFORE:
python_exe = python_executable if python_executable is not None else sys.executable
# AFTER:
python_exe = python_executable  # Already resolved by server
```
Note: The `python_executable` parameter type changes from `Optional[str]` to `str` since the server always passes a resolved value.

**Mypy** (`run_mypy_check`):
```python
# BEFORE:
python_exe = python_executable or sys.executable
# AFTER:
python_exe = python_executable  # Already resolved by server
```

**Pytest** (`run_tests` and `check_code_with_pytest`):
```python
# BEFORE:
py_executable = python_executable or sys.executable
# AFTER:
py_executable = python_executable  # Already resolved by server
```

### Signature changes

For all three runners, change `python_executable: Optional[str] = None` to `python_executable: str` (required, no default). This makes the contract explicit: callers must provide a resolved path.

**Important**: `check_code_with_pytest` delegates to `run_tests`. Both signatures need updating.

## HOW

- Update server.py tool handlers: replace `self.python_executable` → `self._resolved_python`
- Update runner function signatures: `python_executable` becomes required `str`
- Remove `import sys` from runners if `sys.executable` is no longer referenced (check other usages first)
- Update existing tests that call runners directly — they may need to pass an explicit `python_executable`

## ALGORITHM

```
# server.py tool handlers (same pattern for all three):
# BEFORE:
get_pylint_prompt(..., python_executable=self.python_executable, ...)
# AFTER:
get_pylint_prompt(..., python_executable=self._resolved_python, ...)

# Each runner:
# BEFORE:
python_exe = python_executable or sys.executable
# AFTER:
python_exe = python_executable
```

## DATA

- No new data structures
- Parameter type change: `python_executable: Optional[str]` → `python_executable: str` in runner signatures
- No behavioral change — the resolved value was already being used at runtime via the fallback

## Tests

### Update existing tests
- `tests/test_error_transparency.py` — tests that call runners directly (e.g., `run_tests(project_dir=".", test_folder="tests")`) now need to pass `python_executable=sys.executable` explicitly
- `tests/test_tool_availability.py` — verify that `self._resolved_python` (not `self.python_executable`) is passed to runners in the `test_available_tool_runs_normally` test

### New test
- Add a test in `test_tool_availability.py` that verifies the resolved python is what gets passed to the runner (mock the runner, assert the `python_executable` kwarg matches `server._resolved_python`)

## Verification
- All existing tests pass (with updated call signatures)
- `test_available_tool_runs_normally` confirms resolved python is forwarded
- No runner contains `sys.executable` fallback for the python executable resolution
- Run pylint, pytest, mypy — all pass
