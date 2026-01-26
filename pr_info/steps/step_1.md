# Step 1: Add Test for LogRecord with Extra Fields (TDD)

## LLM Prompt
```
Implement Step 1 of Issue #74 (see pr_info/steps/summary.md).
Add a test that verifies LogRecord parsing handles extra fields from Python's logging extra parameter.
The test should initially fail (TDD approach) until Step 2 implements the fix.
```

## WHERE
- **File**: `tests/test_code_checker/test_parsers.py`

## WHAT
Add new test function:
```python
def test_parse_report_with_extra_log_fields() -> None:
    """Test parsing log records with extra fields from logging extra parameter."""
```

## HOW
- Add test at end of existing test file
- Test uses inline JSON with log record containing extra fields (`package_name`, `relative_path`)
- Verify parsing succeeds and extra fields are captured in `extra` dict

## ALGORITHM
```
1. Define JSON string with log record containing standard fields + extra fields (package_name, relative_path)
2. Call parse_pytest_report(json_string)
3. Assert report.tests[0].call.log.logs[0] has correct standard field values
4. Assert report.tests[0].call.log.logs[0].extra contains {"package_name": "my_package", "relative_path": "file.txt"}
5. Assert extra dict does NOT contain standard fields (they should be in their proper attributes)
```

## DATA
**Test Input JSON** (log record section):
```json
{
  "name": "my_logger",
  "msg": "Looking for data file",
  "args": null,
  "levelname": "DEBUG",
  "levelno": 10,
  "pathname": "/path/to/file.py",
  "filename": "file.py",
  "module": "file",
  "exc_info": null,
  "exc_text": null,
  "stack_info": null,
  "lineno": 42,
  "funcName": "find_file",
  "created": 1519772464.291738,
  "msecs": 291.73803329467773,
  "relativeCreated": 332.90839195251465,
  "thread": 140671803118912,
  "threadName": "MainThread",
  "processName": "MainProcess",
  "process": 31481,
  "package_name": "my_package",
  "relative_path": "file.txt"
}
```

**Expected Result**:
- Parsing succeeds (no exception)
- `log_record.msg == "Looking for data file"`
- `log_record.extra == {"package_name": "my_package", "relative_path": "file.txt"}`

## VERIFICATION
```bash
# Test should FAIL until Step 2 is implemented
uv run pytest tests/test_code_checker/test_parsers.py::test_parse_report_with_extra_log_fields -v
```
