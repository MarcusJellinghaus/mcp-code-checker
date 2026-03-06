# Step 2: Remove Tools and Dead Code from server.py

## Context
See [summary.md](summary.md) for full context.

Tests were cleaned up in Step 1. This step removes the two MCP tools and all dead code they leave behind in `server.py`.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for context.

In `src/mcp_code_checker/server.py`, make the following deletions:

1. Remove these import lines:
   - `import os`
   - `from mcp_code_checker.utils.data_files import find_data_file`
   - `from mcp_code_checker.utils.subprocess_runner import execute_command`

2. Remove the `_format_pytest_result` method (the simple wrapper that delegates to
   `_format_pytest_result_with_details` — keep `_format_pytest_result_with_details`).

3. Remove the `_find_sleep_script` method.

4. Remove the entire `run_all_checks` tool (the `@self.mcp.tool()` decorated inner
   function inside `_register_tools`, including its decorator and docstring).

5. Remove the entire `second_sleep` tool (the `@self.mcp.tool()` decorated inner
   function inside `_register_tools`, including its decorator and docstring).

Make no other changes. After editing, run all checks (pylint, pytest, mypy).
```

---

## WHERE

| File | Action |
|------|--------|
| `src/mcp_code_checker/server.py` | Remove imports, methods, and tool registrations |

---

## WHAT

### Imports to remove
```python
import os                                                    # ← remove
from mcp_code_checker.utils.data_files import find_data_file  # ← remove
from mcp_code_checker.utils.subprocess_runner import execute_command  # ← remove
```

### Methods to remove from `CodeCheckerServer`

| Method | Lines (approx) | Why |
|--------|---------------|-----|
| `_format_pytest_result` | ~5 | Only called by `run_all_checks` |
| `_find_sleep_script` | ~15 | Only called by `second_sleep` |

### Tool registrations to remove from `_register_tools`

| Tool | Lines (approx) | Why |
|------|---------------|-----|
| `run_all_checks` | ~60 | Convenience wrapper LLMs don't need |
| `second_sleep` | ~50 | Not a code-checking tool |

### What stays
- `_format_pytest_result_with_details` — still used by `run_pytest_check`
- All imports used by the remaining three tools
- `run_pylint_check`, `run_pytest_check`, `run_mypy_check` — unchanged

---

## HOW

Direct code deletion. No new code. No refactoring of remaining methods.

The three surviving tools continue to use:
- `get_pylint_prompt` (pylint)
- `check_code_with_pytest`, `_format_pytest_result_with_details` (pytest)
- `get_mypy_prompt` (mypy)

---

## ALGORITHM

N/A — pure deletion. No new logic.

---

## DATA

After this step:
- `_register_tools` registers exactly 3 tools: `run_pylint_check`, `run_pytest_check`, `run_mypy_check`.
- `CodeCheckerServer` has no `_format_pytest_result` or `_find_sleep_script` methods.
- No reference to `data_files`, `find_data_file`, `execute_command`, or `os` remains.

---

## Verification

```
mcp__code-checker__run_pylint_check()
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto", "-m", "not integration"])
mcp__code-checker__run_mypy_check()
```
All three must pass with no errors.
