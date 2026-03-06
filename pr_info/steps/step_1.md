# Step 1: Update and Remove Tests

## Context
See [summary.md](summary.md) for full context.

This step follows TDD for a deletion task: align tests with the desired end state **before** removing implementation. After this step all tests should still pass against the unmodified codebase (we are only removing tests for features that will be deleted, and refactoring surviving tests).

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.

Make the following test changes. Do NOT modify any production code yet.

1. DELETE the file `tests/test_utils_data_files.py` entirely.

2. In `tests/test_code_checker_mypy/test_integration.py`:
   - Delete the function `test_mypy_in_all_checks` (including its docstring and body).

3. In `tests/test_server_params.py`:
   a. Delete the function `test_run_all_checks_parameters` (including its docstring and body).
   b. Add this module-level helper function near the top of the file (after imports):
      def _get_tool(mock_tool: MagicMock, name: str) -> Any:
          return {f.__name__: f for call in mock_tool.call_args_list for f in [call[0][0]]}[name]
   c. Replace every occurrence of `mock_tool.call_args_list[1][0][0]` with
      `_get_tool(mock_tool, "run_pytest_check")`.

After making changes, run the full test suite and confirm all tests pass.
```

---

## WHERE

| File | Action |
|------|--------|
| `tests/test_utils_data_files.py` | **Delete entirely** |
| `tests/test_code_checker_mypy/test_integration.py` | Delete one function |
| `tests/test_server_params.py` | Delete one function, add helper, refactor lookups |

---

## WHAT

### `tests/test_server_params.py`

**Delete** `test_run_all_checks_parameters` — the entire function (~45 lines).

**Add** module-level helper:
```python
def _get_tool(mock_tool: MagicMock, name: str) -> Any:
    return {f.__name__: f for call in mock_tool.call_args_list for f in [call[0][0]]}[name]
```

**Replace** every `mock_tool.call_args_list[1][0][0]` (appears ~13 times) with:
```python
_get_tool(mock_tool, "run_pytest_check")
```

### `tests/test_code_checker_mypy/test_integration.py`

**Delete** `test_mypy_in_all_checks` — the entire function (~12 lines). The remaining tests in this file are unaffected.

---

## HOW

- `_get_tool` builds a `{function_name: function}` dict from `mock_tool.call_args_list` and returns the named function. This is the same pattern already used in `test_run_pylint_check_signature`.
- No imports change — `Any` and `MagicMock` are already imported in `test_server_params.py`.

---

## ALGORITHM

```
# _get_tool helper
for each recorded call in mock_tool.call_args_list:
    extract the positional arg (the decorated function)
    map function.__name__ -> function
return the entry matching `name`
```

---

## DATA

- `_get_tool(mock_tool, "run_pytest_check")` → the `run_pytest_check` function registered with the MCP server, same object as `mock_tool.call_args_list[1][0][0]` (index stable because pylint=0, pytest=1, mypy=2).
- Return type: `Any` (callable).

---

## Verification

After this step, run:
```
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto", "-m", "not integration"])
```
All tests must pass. The deleted tests are gone; surviving tests still pass against the current (unmodified) server.
