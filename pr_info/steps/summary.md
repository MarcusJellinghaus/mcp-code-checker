# Summary: Remove run_all_checks() and second_sleep() MCP Tools

## Issue
[#86](https://github.com/MarcusJellinghaus/mcp-code-checker/issues/86) — Remove `run_all_checks()` and `second_sleep()` MCP tools.

## Architectural / Design Changes

### Before
The MCP server registered **5 tools**:
1. `run_pylint_check`
2. `run_pytest_check`
3. `run_mypy_check`
4. `run_all_checks` ← removed
5. `second_sleep` ← removed

### After
The MCP server registers **3 tools**:
1. `run_pylint_check`
2. `run_pytest_check`
3. `run_mypy_check`

### Design Rationale
- **`run_all_checks`**: A convenience wrapper that sequentially runs pylint, pytest, and mypy. LLMs can call the three individual tools directly with full parameter control (e.g. `show_details` for pytest, `extra_args` for pylint). A combined wrapper discourages selective and efficient use.
- **`second_sleep`**: A subprocess-based sleep utility used for testing MCP subprocess execution. It is not a code-checking tool and doesn't belong in this service.

### Dead Code Removed
Removing `second_sleep` makes the following infrastructure dead code:
- `_find_sleep_script()` method in `server.py` — only used by `second_sleep`
- `_format_pytest_result()` method in `server.py` — only called by `run_all_checks`
- `utils/data_files.py` — 600+ line module used only by `_find_sleep_script()`
- `resources/sleep_script.py` — Python script invoked as subprocess by `second_sleep`
- `resources/` folder — empty after `sleep_script.py` removal

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_code_checker/server.py` | Remove tools, dead methods, dead imports |
| `src/mcp_code_checker/utils/__init__.py` | Remove `data_files` re-exports and docstring reference |
| `pyproject.toml` | Remove `mcp_code_checker.resources` package-data entry |
| `vulture_whitelist.py` | Remove `_.run_all_checks` and `_.second_sleep` entries |
| `tests/test_server_params.py` | Delete test for removed tool; add name-based helper; refactor lookups |
| `tests/test_code_checker_mypy/test_integration.py` | Delete `test_mypy_in_all_checks` |

## Files Deleted

| File | Reason |
|------|--------|
| `src/mcp_code_checker/resources/sleep_script.py` | Only used by `second_sleep` |
| `src/mcp_code_checker/resources/` | Empty after `sleep_script.py` removal |
| `src/mcp_code_checker/utils/data_files.py` | Only used by `_find_sleep_script()` |
| `tests/test_utils_data_files.py` | Tests dead code |

## Files NOT Changed
- `.claude/CLAUDE.md` — already does not list `run_all_checks` or `second_sleep`
- All other test files — no dependency on removed tools or data_files module

## Implementation Steps

| Step | Description | Files Touched |
|------|-------------|---------------|
| [Step 1](step_1.md) | Update and remove tests | `test_server_params.py`, `test_integration.py`, delete `test_utils_data_files.py` |
| [Step 2](step_2.md) | Remove tools and dead code from server.py | `server.py` |
| [Step 3](step_3.md) | Delete dead files | `resources/sleep_script.py`, `resources/`, `utils/data_files.py` |
| [Step 4](step_4.md) | Update configuration and supporting files | `utils/__init__.py`, `pyproject.toml`, `vulture_whitelist.py` |
