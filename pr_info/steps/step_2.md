# Step 2: Implement LogRecord Extra Fields Support

## LLM Prompt
```
Implement Step 2 of Issue #74 (see pr_info/steps/summary.md).
Add the `extra` field to LogRecord model and implement filtering logic in parsers.py.
This should make the test from Step 1 pass.
```

## WHERE
- **File 1**: `src/mcp_code_checker/code_checker_pytest/models.py`
- **File 2**: `src/mcp_code_checker/code_checker_pytest/parsers.py`

## WHAT

### models.py
Add fields to `LogRecord` dataclass:
```python
message: str = ""  # Formatted message (msg % args), included for completeness
extra: Dict[str, Any] = field(default_factory=dict)
```

### parsers.py
Derive field set from dataclass and modify `parse_test_stage()`:
```python
# Derive known fields from LogRecord dataclass to auto-sync if fields are added.
# The "extra" field is excluded as it's our container for unknown fields.
LOG_RECORD_FIELDS = set(LogRecord.__dataclass_fields__.keys()) - {"extra"}

# In parse_test_stage(), modify log parsing logic
```

## HOW

### models.py
- Add import: `from dataclasses import dataclass, field`
- Add `message: str = ""` field (for completeness, some configs include it)
- Add `extra` field as last field in `LogRecord` with default empty dict

### parsers.py
- Add `LOG_RECORD_FIELDS` constant at module level after imports
- Modify the log record parsing block (currently lines 42-46) to filter fields

## ALGORITHM
```
1. Define LOG_RECORD_FIELDS = set of all known LogRecord field names
2. For each log_record_data dict from JSON:
   a. known_fields = {k: v for k, v in log_record_data.items() if k in LOG_RECORD_FIELDS}
   b. extra_fields = {k: v for k, v in log_record_data.items() if k not in LOG_RECORD_FIELDS}
   c. Create LogRecord(**known_fields, extra=extra_fields)
3. Append to log_records list
```

## DATA

### LOG_RECORD_FIELDS (derived from dataclass)
```python
# Derive known fields from LogRecord dataclass to auto-sync if fields are added.
# The "extra" field is excluded as it's our container for unknown fields.
LOG_RECORD_FIELDS = set(LogRecord.__dataclass_fields__.keys()) - {"extra"}
```

### Modified LogRecord dataclass
```python
@dataclass
class LogRecord:
    """Represents a log record matching Python's logging.LogRecord interface.

    Note: Some attribute names use camelCase to maintain compatibility with
    Python's standard logging.LogRecord class.
    
    The `extra` field captures any additional fields added via Python's
    logging extra parameter (e.g., logger.info("msg", extra={"key": "value"})).
    """
    # ... existing fields ...
    taskName: str = ""
    asctime: str = ""
    message: str = ""  # Formatted message (msg % args), included for completeness
    extra: Dict[str, Any] = field(default_factory=dict)
```

## VERIFICATION
```bash
# Test from Step 1 should now PASS
uv run pytest tests/test_code_checker/test_parsers.py::test_parse_report_with_extra_log_fields -v

# Run all parser tests to ensure no regressions
uv run pytest tests/test_code_checker/test_parsers.py -v

# Run full test suite
uv run pytest
```
