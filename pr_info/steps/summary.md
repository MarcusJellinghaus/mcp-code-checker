# Issue #89: Improve Error Transparency When Tools Are Not Installed

## Summary

When pytest, pylint, or mypy is not installed in the configured Python environment, the MCP server surfaces misleading generic errors instead of the real cause. Users must dig through log files to find messages like `No module named pytest`. This implementation improves error transparency across all three tools consistently.

## Architectural / Design Changes

### 1. New startup validation layer in `CodeCheckerServer`

**Before:** The server starts without checking whether the configured Python environment actually has the tools installed. Failures only surface at call time with misleading messages.

**After:** `CodeCheckerServer.__init__` validates tool availability at startup using the resolved Python executable. Results are cached in `self._tool_availability: dict[str, bool]`. Each tool handler short-circuits with a clear error if its tool was flagged unavailable. A new private method `_resolve_python_executable()` centralizes venv→executable→sys.executable resolution logic for the server layer. The pytest runner's internal venv resolution is removed so all runners follow the same pattern: receive a resolved `python_executable` from the server. Resolved path and availability are logged at DEBUG level.

### 2. Improved error messages in all three runners

**Before:** When a subprocess fails with no usable output, runners return generic errors like "no report file was generated" (pytest) or just the `execution_error` field (pylint/mypy). The stderr containing the real cause is discarded.

**After:** All three runners use a shared helper (`check_tool_missing_error()` and `truncate_stderr()` in `subprocess_runner.py`) to:
- Check stderr for `"No module named <tool>"` and raise a specific, actionable error.
- Append truncated stderr (up to `MAX_STDERR_IN_ERROR = 500` chars) to error messages when no usable output is produced.

For mypy, the tool-missing check is placed early (before existing return_code==2 handling) to give it priority.

### 3. Removal of dead code (`collect_environment_info`)

**Before:** `collect_environment_info()` makes 4+ subprocess calls on every pytest run (pytest version, pip list, trace-config, CPU/memory) using `sys.executable` (wrong executable). The collected data is stored in `PytestReport.environment_context` but **never surfaced to the MCP client**.

**After:** `collect_environment_info()`, `EnvironmentContext` model, and all related references are removed. This eliminates latency from unnecessary subprocess calls on every test run.

### 4. Documentation updates

CLI `--help` strings and README are updated to clarify that `--python-executable` / `--venv-path` should point to the tool's own venv (where pytest/pylint/mypy are installed), not the project's runtime venv.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_code_checker/server.py` | Add `_resolve_python_executable()`, `_check_tool_availability()`, `_tool_availability` dict, short-circuit checks in tool handlers |
| `src/mcp_code_checker/utils/subprocess_runner.py` | Add `MAX_STDERR_IN_ERROR = 500` constant, `check_tool_missing_error()` and `truncate_stderr()` shared helpers |
| `src/mcp_code_checker/code_checker_pytest/runners.py` | Add "No module named" detection, stderr surfacing, remove `collect_environment_info` call and `environment_info` from result dict, remove internal venv resolution (server now passes resolved executable) |
| `src/mcp_code_checker/code_checker_pytest/utils.py` | Remove `collect_environment_info()` function |
| `src/mcp_code_checker/code_checker_pytest/models.py` | Remove `EnvironmentContext` dataclass and `environment_context` field from `PytestReport` |
| `src/mcp_code_checker/code_checker_pylint/runners.py` | Add "No module named" detection, stderr surfacing on error |
| `src/mcp_code_checker/code_checker_mypy/runners.py` | Add "No module named" detection, stderr surfacing on error |
| `src/mcp_code_checker/main.py` | Update `--help` strings for `--python-executable` and `--venv-path` |
| `README.md` | Add Configuration/Troubleshooting section |

## Files Created (Tests)

| File | Purpose |
|------|---------|
| `tests/test_tool_availability.py` | Tests for startup validation and short-circuit behavior |
| `tests/test_error_transparency.py` | Tests for "No module named" detection and stderr surfacing in all three runners |

## Files Modified (Tests)

| File | Change |
|------|--------|
| `tests/test_code_checker/test_runners.py` | Remove `assert result.environment_context is not None` (line 103) |

## Implementation Steps

| Step | Description | Files |
|------|-------------|-------|
| 1 | Remove `collect_environment_info()` dead code | `utils.py`, `runners.py`, `models.py` |
| 2 | Add stderr surfacing and "No module named" detection to all runners | `subprocess_runner.py`, pytest/pylint/mypy `runners.py`, `test_error_transparency.py` |
| 3 | Add startup tool validation in server | `server.py`, `test_tool_availability.py` |
| 4 | Update documentation (CLI help + README) | `main.py`, `README.md` |
