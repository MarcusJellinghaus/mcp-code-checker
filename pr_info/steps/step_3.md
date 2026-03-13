# Step 3: Add Startup Tool Validation in Server

## Context
See `pr_info/steps/summary.md` for full context. This is step 3 of 4.

## Goal
On server startup, validate that pytest, pylint, and mypy are available in the configured Python environment. Cache results in `self._tool_availability`. Short-circuit tool handlers with a clear error when a tool is unavailable.

## LLM Prompt
> Implement Step 3 of Issue #89 (see `pr_info/steps/summary.md` for context). Add startup validation to `CodeCheckerServer` that checks tool availability using the resolved Python executable. Cache results and short-circuit tool handlers when tools are missing. Write tests first (TDD), then implement.

## WHERE

- `src/mcp_code_checker/server.py` — add `_resolve_python_executable()`, `_check_tool_availability()`, availability checks in tool handlers
- `src/mcp_code_checker/code_checker_pytest/runners.py` — remove internal venv resolution logic from `run_tests()` (server now passes resolved executable)
- `tests/test_tool_availability.py` — new test file

## WHAT

### New private methods in `CodeCheckerServer`:

#### `_resolve_python_executable(self) -> str`
Centralizes the venv→python_executable→sys.executable resolution logic.

**Signature**: `def _resolve_python_executable(self) -> str`

**Returns**: Absolute path to the resolved Python executable.

#### `_check_tool_availability(self) -> dict[str, bool]`
Runs `<python> -m <tool> --version` for each tool and returns availability dict.

**Signature**: `def _check_tool_availability(self) -> dict[str, bool]`

**Returns**: `{"pytest": True/False, "pylint": True/False, "mypy": True/False}`

### Modified: `__init__`
After `self._register_tools()`, add:
```python
self._resolved_python = self._resolve_python_executable()
self._tool_availability = self._check_tool_availability()
```

Log resolved path and availability at **DEBUG** level:
```python
structured_logger.debug(
    "Tool environment resolved",
    python_executable=self._resolved_python,
    tool_availability=self._tool_availability,
)
```

### Modified: tool handlers
At the top of each tool handler (`run_pylint_check`, `run_pytest_check`, `run_mypy_check`), add an availability check that returns an immediate error string.

### Modified: `run_tests()` in pytest `runners.py`
Remove the internal venv→python resolution block (the `if venv_path: ... venv_python = ...` logic). The server layer now resolves the python executable and passes it as `python_executable`. This aligns pytest with how pylint and mypy runners already work — they receive a resolved `python_executable` and don't do their own venv resolution.

## HOW

- Import `subprocess` (or use `execute_command` from subprocess_runner) for version checks
- Use `os`, `sys` for path resolution
- Log warnings via existing `logger` and `structured_logger`

## ALGORITHM

### `_resolve_python_executable`:
```
if self.venv_path:
    if windows: python = venv_path/Scripts/python.exe
    else: python = venv_path/bin/python
    if not exists(python): raise FileNotFoundError
    return python
elif self.python_executable:
    return self.python_executable
else:
    return sys.executable
```

Note: This centralizes logic previously duplicated in `run_tests()`. After this change, the server resolves the executable once and passes it to all runners. The `venv_path` parameter is still accepted by `run_tests()` for PATH adjustment, but python executable resolution happens at the server layer.

### `_check_tool_availability`:
```
availability = {}
for tool in ["pytest", "pylint", "mypy"]:
    result = execute_command([self._resolved_python, "-m", tool, "--version"], timeout=10)
    available = result.return_code == 0 and not result.execution_error
    availability[tool] = available
    if not available:
        logger.warning(f"{tool} not found in {self._resolved_python}. "
                       "Ensure --python-executable and --venv-path point to "
                       "the environment where {tool} is installed.")
return availability
```

### Tool handler short-circuit (same pattern for all three):
```
if not self._tool_availability.get("pytest", False):
    return (f"pytest is not available in the configured Python environment "
            f"({self._resolved_python}). Ensure --python-executable and "
            f"--venv-path point to the environment where pytest is installed. "
            f"Restart the server after installing.")
```

## DATA

- **New instance attributes**:
  - `self._resolved_python: str` — resolved Python executable path
  - `self._tool_availability: dict[str, bool]` — cached availability per tool
- **Return value on unavailable tool**: Plain error string (not exception), consistent with existing tool handler return type `str`

## Tests (TDD — write first)

### File: `tests/test_tool_availability.py`

```python
# Test structure outline:

class TestResolvePythonExecutable:
    """Test _resolve_python_executable logic."""
    
    def test_venv_path_windows(self):
        # Mock os.name == "nt", verify Scripts/python.exe path
    
    def test_venv_path_unix(self):
        # Mock os.name != "nt", verify bin/python path
    
    def test_python_executable_fallback(self):
        # No venv_path, python_executable set, verify it's returned
    
    def test_sys_executable_fallback(self):
        # Neither set, verify sys.executable is returned

class TestCheckToolAvailability:
    """Test _check_tool_availability caching."""
    
    def test_all_tools_available(self):
        # Mock execute_command returning success for all, verify dict
    
    def test_one_tool_missing(self):
        # Mock pytest missing, others available
        # Verify dict has pytest=False, others=True
        # Verify warning logged
    
    def test_all_tools_missing(self):
        # Mock all failing, verify all False

class TestToolHandlerShortCircuit:
    """Test that tool handlers return immediate error when tool unavailable."""
    
    def test_pytest_unavailable_returns_error(self):
        # Set _tool_availability["pytest"] = False
        # Call run_pytest_check tool, assert error string returned
    
    def test_pylint_unavailable_returns_error(self):
        # Same for pylint
    
    def test_mypy_unavailable_returns_error(self):
        # Same for mypy
    
    def test_available_tool_runs_normally(self):
        # Set _tool_availability["pytest"] = True
        # Verify normal execution proceeds (mock the runner)
```

## Verification
- Run `tests/test_tool_availability.py` — all new tests pass
- Run full test suite — no regressions
- Verify that `run_tests()` no longer does venv→python resolution internally
- Manual test: configure venv without pytest, start server, call tool — expect clear error
- Verify DEBUG log shows resolved python path and tool availability on startup
