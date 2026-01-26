# Issue #74: Fix LogRecord Parsing with Extra Fields

## Problem Statement

When running `run_pytest_check` on projects that use Python's logging `extra` parameter, the JSON report parsing fails:
```
Error running pytest: LogRecord.__init__() got an unexpected keyword argument 'package_name'
```

**Root Cause:** The `LogRecord` dataclass has fixed fields, but `pytest-json-report` captures the entire `LogRecord.__dict__`, including custom fields added via `extra={"package_name": "value"}`.

## Solution Overview

Add an `extra` field to `LogRecord` and filter known/unknown fields during parsing.

## Architectural Changes

### Data Model Change
- **`LogRecord` dataclass**: Add `message: str` field (for completeness) and `extra: Dict[str, Any]` field to store unknown fields from logging's `extra` parameter

### Parser Change  
- **`parsers.py`**: Derive known fields from `LogRecord` dataclass and filter unknown fields into `extra`

## Files Modified

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_code_checker/code_checker_pytest/models.py` | Modified | Add `extra` field to `LogRecord` |
| `src/mcp_code_checker/code_checker_pytest/parsers.py` | Modified | Add `LOG_RECORD_FIELDS` constant and filtering logic |
| `tests/test_code_checker/test_parsers.py` | Modified | Add test for extra fields |

## Implementation Steps

1. **Step 1**: Add test for LogRecord with extra fields (TDD)
2. **Step 2**: Add `extra` field to `LogRecord` model and implement filtering in parser

## Design Decisions

1. **Preserve extra fields**: Store in `extra` dict rather than discarding - preserves debugging info
2. **Targeted fix**: Only modify `LogRecord` parsing, not other dataclasses (KISS/YAGNI)
3. **Inline filtering**: Simple set-based filtering instead of generic helper function
4. **Include `message` field**: Added for completeness, some logging configs include it
5. **Derive field set from dataclass**: Auto-syncs if fields are added, with explanatory comment
