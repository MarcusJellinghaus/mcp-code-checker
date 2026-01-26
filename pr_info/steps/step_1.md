# Step 1: Update JsonFormatter Import and Usage

## Overview
Update the deprecated `pythonjsonlogger.jsonlogger` import to use the new module path `pythonjsonlogger.json`.

## WHERE: File Paths
- `src/mcp_code_checker/log_utils.py`

## WHAT: Changes Required

### 1. Update Import Statement (line 12)

**Current:**
```python
from pythonjsonlogger import jsonlogger
```

**New:**
```python
from pythonjsonlogger.json import JsonFormatter
```

### 2. Update Usage (line 46)

**Current:**
```python
json_formatter = jsonlogger.JsonFormatter(  # type: ignore[attr-defined]
    fmt="%(timestamp)s %(level)s %(name)s %(message)s %(module)s %(funcName)s %(lineno)d",
    timestamp=True,
)
```

**New:**
```python
json_formatter = JsonFormatter(
    fmt="%(timestamp)s %(level)s %(name)s %(message)s %(module)s %(funcName)s %(lineno)d",
    timestamp=True,
)
```

## HOW: Integration Points
- No changes to integration points
- No changes to function signatures
- No changes to module exports

## ALGORITHM
```
1. Import JsonFormatter directly from pythonjsonlogger.json
2. Use JsonFormatter directly instead of jsonlogger.JsonFormatter
3. Remove type: ignore comment (no longer needed with direct import)
```

## DATA: Return Values and Data Structures
No changes to return values or data structures.

## Verification
Run the following MCP tools to verify the fix:
```
mcp__code-checker__run_pytest_check(extra_args=["-v"])
mcp__code-checker__run_pylint_check()
mcp__code-checker__run_mypy_check()
```
Confirm: no deprecation warnings, all tests pass, no linting or type errors.

## Test-Driven Development Note
This change does not require new tests as:
- Existing tests in `tests/test_log_utils.py` already cover the logging functionality
- The change is purely an import path update with identical behavior
- Running the existing test suite will verify the fix works and produces no deprecation warnings

---

## LLM Prompt for Implementation

```
You are implementing Step 1 of Issue #70: Fix pythonjsonlogger deprecation warning.

Reference: pr_info/steps/summary.md

Task: Update the deprecated import in src/mcp_code_checker/log_utils.py

Changes required:
1. Line 12: Change `from pythonjsonlogger import jsonlogger` to `from pythonjsonlogger.json import JsonFormatter`
2. Line 46: Change `jsonlogger.JsonFormatter(  # type: ignore[attr-defined]` to `JsonFormatter(`

After making changes, run MCP tools (run_pytest_check, run_pylint_check, run_mypy_check) to verify:
- No deprecation warnings appear
- All tests pass
- No linting or type errors

This is a 2-line change with no functional differences.
```
