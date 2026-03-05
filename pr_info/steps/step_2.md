# Step 2: Update `reporting.py` — Remove Category Filter, Add `extra_args`

## Context
See `pr_info/steps/summary.md` for full architectural context.  
Depends on Step 1 (`get_pylint_results` now accepts `extra_args`).

This step removes the two-layer suppression from `get_pylint_prompt`:
- Remove `categories` parameter and `DEFAULT_CATEGORIES` fallback
- Remove `disable_codes` parameter and its hardcoded defaults
- Remove the `filter_pylint_codes_by_category` call
- Add `extra_args` pass-through

---

## WHERE

| File | Action |
|------|--------|
| `tests/test_code_checker_pylint/test_reporting.py` | Update tests — write first |
| `src/mcp_code_checker/code_checker_pylint/reporting.py` | Update implementation |

---

## WHAT

### `get_pylint_prompt()` — updated signature
```python
def get_pylint_prompt(
    project_dir: str,
    extra_args: Optional[list[str]] = None,
    python_executable: Optional[str] = None,
    target_directories: Optional[list[str]] = None,
) -> Optional[str]:
```

All other functions in `reporting.py` (`get_direct_instruction_for_pylint_code`,
`get_prompt_for_known_pylint_code`, `get_prompt_for_unknown_pylint_code`) are **unchanged**.

---

## HOW

### Imports to remove from `reporting.py`
```python
# Remove these imports (no longer needed):
from mcp_code_checker.code_checker_pylint.models import (
    DEFAULT_CATEGORIES,       # ← remove
    PylintMessageType,        # ← remove
    PylintResult,
)
from mcp_code_checker.code_checker_pylint.utils import (
    filter_pylint_codes_by_category,  # ← remove
    normalize_path,
)
```

### Code block to remove in `get_pylint_prompt()`

**Remove** the default categories block:
```python
# DELETE this block:
if categories is None:
    categories = DEFAULT_CATEGORIES
```

**Remove** the default disable_codes block:
```python
# DELETE this block:
if disable_codes is None:
    disable_codes = ["C0114", "C0116", ...]
```

**Remove** the category filter:
```python
# DELETE this line:
codes = filter_pylint_codes_by_category(codes, categories=categories)
```

**Keep** the rest — `get_message_ids()`, prompt generation, error handling — unchanged.

---

## ALGORITHM

```
get_pylint_prompt(project_dir, extra_args, python_executable, target_directories):
  call get_pylint_results(project_dir, extra_args, python_executable, target_directories)
  if pylint_results.error: return error message string
  codes = pylint_results.get_message_ids()   # all codes, no filtering
  if codes is empty: return None
  pick first code
  try get_prompt_for_known_pylint_code(code, ...) → return if not None
  fall back to get_prompt_for_unknown_pylint_code(code, ...)
```

---

## DATA

**Before:** `get_pylint_prompt` would silently return `None` if only W/C/R codes existed  
**After:** `get_pylint_prompt` reports whatever pylint reports (governed by `pyproject.toml`)

Return type is unchanged: `Optional[str]`  
- `None` — pylint found no issues  
- `str` — LLM prompt for the first issue found  
- `str` starting with `"Pylint analysis failed:"` — execution error

---

## TDD: Tests in `tests/test_code_checker_pylint/test_reporting.py`

Check the current test file and update any tests that:
- Pass `categories=` to `get_pylint_prompt` — remove the parameter
- Pass `disable_codes=` to `get_pylint_prompt` — remove the parameter
- Assert filtering behaviour (e.g., W codes being dropped) — update to expect them to pass through

Add a test that verifies warning-level codes ARE included in output (i.e., the filter is gone):
```python
def test_get_pylint_prompt_includes_warning_codes(...):
    # Mock get_pylint_results to return a W-code message
    # Assert get_pylint_prompt returns a non-None prompt
    # (previously it would have returned None due to category filtering)
```

---

## LLM Prompt

```
You are implementing Step 2 of a refactoring task for the mcp-code-checker project.
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for full context.
Step 1 is already complete: `get_pylint_results` now accepts `extra_args` instead of `disable_codes`.

TASK:
Update `src/mcp_code_checker/code_checker_pylint/reporting.py` to remove the
category filter and hardcoded disable_codes from `get_pylint_prompt()`.

CHANGES REQUIRED:

1. In `get_pylint_prompt()`:
   - Remove parameters: `categories: Optional[Set[PylintMessageType]]`, `disable_codes`
   - Add parameter: `extra_args: Optional[list[str]] = None`
   - Remove the `if categories is None: categories = DEFAULT_CATEGORIES` block
   - Remove the `if disable_codes is None: disable_codes = [...]` block
   - Remove the `filter_pylint_codes_by_category(codes, categories=categories)` call
   - Replace with: `codes = pylint_results.get_message_ids()` (no filtering)
   - Pass `extra_args` to `get_pylint_results()` instead of `disable_codes`
   - Update docstring and structlog calls to remove mention of categories/disable_codes
   - Update imports: remove `DEFAULT_CATEGORIES`, `PylintMessageType`,
     `filter_pylint_codes_by_category` (keep `PylintResult`, `normalize_path`)

2. In `tests/test_code_checker_pylint/test_reporting.py`:
   - Read the file first; update any calls to `get_pylint_prompt` to remove
     `categories=` and `disable_codes=` arguments
   - Add a test that confirms warning-level codes (e.g. W0613) are now included
     in the prompt output rather than filtered away

Write tests first, then implement. Do not modify any other files in this step.
Run the tests to confirm they pass before finishing.
```
