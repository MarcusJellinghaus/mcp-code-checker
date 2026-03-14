# Step 3: Wire `max_issues` into `server.py`, slim docstring + integration test

> **Context**: See `pr_info/steps/summary.md` for the full issue and architectural overview.  
> **Depends on**: Steps 1 and 2 (reporting.py changes complete).

## Goal

Add `max_issues` parameter to the MCP tool `run_pylint_check` in `server.py`, pass it through to `get_pylint_prompt()`, slim down the docstring, and adjust `_format_pylint_result` for the new zero-issues behavior.

## WHERE

- **Implementation**: `src/mcp_code_checker/server.py`
- **Test**: `tests/test_code_checker_pylint/test_reporting.py` (add integration-style test with mock)

## WHAT — Updated Signatures

### `run_pylint_check` in server.py (lines ~117-155)

```python
@self.mcp.tool()
@log_function_call
def run_pylint_check(
    extra_args: Optional[List[str]] = None,
    target_directories: Optional[List[str]] = None,
    max_issues: int = 1,  # NEW
) -> str:
    """
    Run pylint on the project code and generate smart prompts for LLMs.

    Args:
        extra_args: Additional pylint arguments.
        target_directories: Directories to analyze relative to project_dir. Defaults to ["src"] and "tests" if it exists.
        max_issues: Number of issue types to show in detail (default: 1). Remaining issues shown as summary counts.
    """
```

### `_format_pylint_result` (lines ~83-87)

```python
def _format_pylint_result(self, pylint_prompt: Optional[str]) -> str:
    """Format pylint check result."""
    if pylint_prompt is None:
        return "Pylint check completed. No issues found that require attention."
    return pylint_prompt  # Changed: prompt is now self-contained (includes "Pylint passed" or detailed output)
```

Note: The prefix `"Pylint found issues that need attention:\n\n"` is removed because the detailed output already starts with `"pylint found some issues related to code..."`. The `None` path is preserved — `get_pylint_prompt` still returns `None` for zero issues (Decision 3).

## HOW — Integration Points

- `get_pylint_prompt` is imported from `mcp_code_checker.code_checker_pylint` (already imported, line ~8)
- Pass `max_issues` through: `get_pylint_prompt(..., max_issues=max_issues)`
- The `run_all_checks` tool in server.py also calls pylint — check if it needs updating (it currently calls `run_pylint_check` which will automatically get the new default)

## ALGORITHM

No complex logic — just parameter passthrough:

```
1. Add max_issues parameter to run_pylint_check signature
2. Pass max_issues to get_pylint_prompt() call
3. Simplify _format_pylint_result to return prompt directly
4. Slim down docstring
```

## DATA

No new data structures. Return value is still `str`.

## Changes Detail

### In `run_pylint_check` (server.py):

1. Add `max_issues: int = 1` to function signature
2. Add to structured_logger call: `max_issues=max_issues`
3. Pass to `get_pylint_prompt()`:
   ```python
   pylint_prompt = get_pylint_prompt(
       str(self.project_dir),
       extra_args=extra_args,
       python_executable=self.python_executable,
       target_directories=target_directories,
       max_issues=max_issues,  # NEW
   )
   ```
4. Replace docstring with slim version

### In `_format_pylint_result` (server.py):

Change the return for non-None case from:
```python
return f"Pylint found issues that need attention:\n\n{pylint_prompt}"
```
to:
```python
return pylint_prompt
```

## Tests

Add to `tests/test_server_params.py` (existing server test file — Decision 5):

### `TestServerPylintMaxIssues` (mock-based):

1. **`test_run_pylint_check_passes_max_issues`** — mock `get_pylint_prompt`, call with `max_issues=3`, verify `get_pylint_prompt` was called with `max_issues=3`
2. **`test_run_pylint_check_default_max_issues`** — call without `max_issues`, verify `get_pylint_prompt` was called with `max_issues=1`
3. **`test_format_pylint_result_returns_prompt_directly`** — verify `_format_pylint_result` returns the prompt string without extra prefix

## LLM Prompt

```
Implement Step 3 of Issue #32 (see pr_info/steps/summary.md and pr_info/steps/step_3.md).

Steps 1 and 2 are already complete (reporting.py has _group_and_sort_issues 
and refactored get_pylint_prompt with max_issues).

Changes needed in server.py:
1. Add max_issues: int = 1 parameter to run_pylint_check
2. Pass it through to get_pylint_prompt()
3. Slim down the run_pylint_check docstring (see step_3.md for exact text)
4. Simplify _format_pylint_result to return prompt directly (no prefix)
Then add integration tests to test_server_params.py:
1. test_run_pylint_check_passes_max_issues
2. test_run_pylint_check_default_max_issues  
3. test_format_pylint_result_returns_prompt_directly

Run all tests + pylint/mypy checks when done.
```
