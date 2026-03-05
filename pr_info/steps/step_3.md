# Step 3: Update `server.py` — Update MCP Tools, Delete `_parse_pylint_categories`

## Context
See `pr_info/steps/summary.md` for full architectural context.  
Depends on Step 2 (`get_pylint_prompt` now accepts `extra_args`, no `categories`/`disable_codes`).

This step updates the MCP server layer: removes the `_parse_pylint_categories` helper,
updates the `run_pylint_check` MCP tool signature, and removes `categories` from `run_all_checks`.

---

## WHERE

| File | Action |
|------|--------|
| `tests/test_server_params.py` | Update tests — write first |
| `src/mcp_code_checker/server.py` | Update implementation |

---

## WHAT

### `_parse_pylint_categories()` — DELETE entirely
```python
# DELETE this entire method:
def _parse_pylint_categories(self, categories: Optional[List[str]]) -> ...:
    ...
```

### `run_pylint_check` MCP tool — updated signature
```python
def run_pylint_check(
    extra_args: Optional[List[str]] = None,
    target_directories: Optional[List[str]] = None,
) -> str:
```

### `run_all_checks` MCP tool — updated signature
```python
def run_all_checks(
    markers: Optional[List[str]] = None,
    verbosity: int = 2,
    extra_args: Optional[List[str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    target_directories: Optional[List[str]] = None,
    mypy_strict: bool = True,
    mypy_disable_codes: list[str] | None = None,
) -> str:
    # Note: `categories` parameter removed; `extra_args` is for pytest (unchanged)
```

---

## HOW

### `run_pylint_check` MCP tool body change

**Before:**
```python
pylint_categories = self._parse_pylint_categories(categories)
pylint_prompt = get_pylint_prompt(
    str(self.project_dir),
    categories=pylint_categories,
    disable_codes=disable_codes,
    python_executable=self.python_executable,
    target_directories=target_directories,
)
```

**After:**
```python
pylint_prompt = get_pylint_prompt(
    str(self.project_dir),
    extra_args=extra_args,
    python_executable=self.python_executable,
    target_directories=target_directories,
)
```

### `run_all_checks` MCP tool body change

Same pattern: remove `pylint_categories = self._parse_pylint_categories(categories)` line,
update `get_pylint_prompt()` call to pass no `categories`/`disable_codes`.

### Import cleanup in `server.py`

```python
# Remove from import:
from mcp_code_checker.code_checker_pylint import PylintMessageType, get_pylint_prompt
#                                                ^^^^^^^^^^^^^^^^^ remove this
```

---

## ALGORITHM

```
run_pylint_check MCP tool (extra_args, target_directories):
  call get_pylint_prompt(project_dir, extra_args, python_executable, target_directories)
  format result via _format_pylint_result()
  return string

run_all_checks MCP tool (markers, verbosity, extra_args, env_vars, target_dirs, ...):
  call get_pylint_prompt(project_dir, extra_args=None, ...)   # no pylint extra_args
  call check_code_with_pytest(..., extra_args=extra_args, ...) # extra_args is for pytest
  call get_mypy_prompt(...)
  combine and return results
```

Note: In `run_all_checks`, `extra_args` remains a pytest parameter (unchanged). There is
no `pylint_extra_args` — the issue explicitly states users needing pylint fine-grained
control should call `run_pylint_check` directly.

---

## DATA

**`run_pylint_check` MCP tool:**
- Input: `extra_args: Optional[List[str]]`, `target_directories: Optional[List[str]]`
- Output: `str` — formatted pylint result or "No issues found" message

**`run_all_checks` MCP tool:**
- Input: same as before minus `categories`
- Output: `str` — combined results from all three checks

---

## TDD: Tests to Update in `tests/test_server_params.py`

### `test_run_all_checks_parameters`
- Remove `categories=["error"]` from the `run_all_checks(...)` call
- Remove any assertion that `mock_pylint` was called with `categories=...`
- Verify `mock_pylint` is called with `extra_args=None` (or just verify it's called)

### Signature test (if present)
- Verify `run_pylint_check` signature has `extra_args` but NOT `categories` or `disable_codes`
- Verify `run_all_checks` signature does NOT have `categories`

---

## LLM Prompt

```
You are implementing Step 3 of a refactoring task for the mcp-code-checker project.
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for full context.
Steps 1 and 2 are already complete:
- `get_pylint_results` accepts `extra_args` instead of `disable_codes`
- `get_pylint_prompt` accepts `extra_args`, has no `categories` or `disable_codes`

TASK:
Update `src/mcp_code_checker/server.py` to align the MCP tool layer with the simplified API.

CHANGES REQUIRED:

1. Delete `_parse_pylint_categories()` method entirely from `CodeCheckerServer`.

2. Update the `run_pylint_check` MCP tool (inside `_register_tools`):
   - Remove parameters: `categories`, `disable_codes`
   - Add parameter: `extra_args: Optional[List[str]] = None`
   - Remove the `pylint_categories = self._parse_pylint_categories(categories)` line
   - Update `get_pylint_prompt(...)` call: remove `categories=`, `disable_codes=`;
     add `extra_args=extra_args`
   - Update the structlog calls and docstring

3. Update the `run_all_checks` MCP tool (inside `_register_tools`):
   - Remove parameter: `categories`
   - Remove the `pylint_categories = self._parse_pylint_categories(categories)` line
   - Update `get_pylint_prompt(...)` call: remove `categories=`, remove `disable_codes=`
   - Update docstring

4. Update import in `server.py`:
   - Remove `PylintMessageType` from the pylint import
     (only `get_pylint_prompt` is needed from that module)

5. In `tests/test_server_params.py`:
   - In `test_run_all_checks_parameters`: remove `categories=["error"]` from the call;
     remove any assertion checking pylint was called with categories
   - Add a test verifying `run_pylint_check` signature has `extra_args` and
     does NOT have `categories` or `disable_codes`

Write tests first, then implement. Do not modify any other files in this step.
Run the tests to confirm they pass before finishing.
```
