# Fix pythonjsonlogger Deprecation Warning

## Issue Reference
**Issue #70**: Fix pythonjsonlogger deprecation warning

## Problem Statement
The `log_utils.py` file uses a deprecated import path `pythonjsonlogger.jsonlogger` that triggers a `DeprecationWarning` in pytest output. This warning appears 4 times in CI test output, adding noise to test results.

## Solution Overview
Update the deprecated import to use the new module path `pythonjsonlogger.json` as introduced in python-json-logger v3.1.0.

## Architectural / Design Changes
**None** - This is a simple import path update with no architectural or design changes. The functionality remains identical; only the import mechanism changes from:
- Importing the module and accessing `JsonFormatter` as an attribute
- To directly importing `JsonFormatter` from its new location

## Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `src/mcp_code_checker/log_utils.py` | Modify | Update import and usage of JsonFormatter |

## Files to Create
None

## Implementation Steps

| Step | Description | File(s) |
|------|-------------|---------|
| 1 | Update import and usage of JsonFormatter | `src/mcp_code_checker/log_utils.py` |

## Acceptance Criteria
- [ ] Deprecation warning no longer appears in pytest output
- [ ] All existing tests pass
- [ ] Pylint, mypy, and pytest checks pass

## Constraints
- Keep version constraint as `>=3.2.1` (no version bump needed)
- Single file change, 2-3 lines affected
