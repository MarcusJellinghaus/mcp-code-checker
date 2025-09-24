# show_details Parameter Usage Examples

This document provides comprehensive usage examples for the `show_details` parameter in the `run_pytest_check()` function, designed specifically for LLM interactions with the MCP Code Checker server.

## Common LLM Usage Patterns

### 1. Debug Failing Test
When LLM wants to see why a specific test failed with full diagnostic information:

```python
run_pytest_check(
    extra_args=["tests/test_user_auth.py::test_login_validation"],
    show_details=True
)
```

**What this does:**
- Runs only the specified test 
- Automatically adds `-s` flag to capture print statements
- Shows detailed failure output including stdout, stderr, and longrepr
- Limited to 300 lines total output with truncation indicator

### 2. Quick CI Check  
For routine checks without overwhelming output:

```python
run_pytest_check(show_details=False)  # Default behavior
```

**What this does:**
- Runs all tests with minimal output
- Only shows summary information for large test runs
- Provides hints for small test runs (≤3 tests) to try `show_details=True`
- Collection errors always shown regardless

### 3. Run Specific Tests with Print Statements
When debugging tests that use print statements for diagnostics:

```python
run_pytest_check(
    extra_args=["tests/test_debug.py"],
    show_details=True  # Automatically adds -s for print statements
)
```

**What this does:**
- Runs entire test file
- Captures all print output from tests
- Shows detailed failure information if any tests fail
- Automatic `-s` flag addition means no need to manually specify it

### 4. Pattern-Based Test Selection
Running tests matching a pattern with detailed output:

```python
run_pytest_check(
    extra_args=["-k", "test_calculation"],
    show_details=True
)
```

**What this does:**
- Runs all tests containing "calculation" in their name
- Shows detailed output for any failures
- Includes print statements and full diagnostic information

### 5. Integration Test Run with Summary Only
For integration tests that typically have longer output:

```python
run_pytest_check(
    markers=["integration"], 
    show_details=False
)
```

**What this does:**
- Runs only tests marked with `@pytest.mark.integration`
- Provides summary-only output to avoid overwhelming information
- Still shows collection errors if any occur

### 6. Marker-Based Testing with Details
Running specific test categories with full diagnostic output:

```python
run_pytest_check(
    markers=["unit", "critical"],
    show_details=True
)
```

**What this does:**
- Runs tests marked with both `unit` and `critical` markers
- Shows detailed output for debugging purposes
- Automatically includes `-s` for print statement capture

## Smart Behavior Examples

### Automatic Hints for Small Test Runs
When running a small number of tests without `show_details=True`:

```python
run_pytest_check(
    extra_args=["tests/test_single.py::test_one_function"]
)
```

**Output example:**
```
Pytest completed with failures. Try show_details=True for more information.
```

This hint appears when:
- `show_details=False` (default)
- Total collected tests ≤ 3
- There are test failures

### Automatic `-s` Flag Addition
The system automatically adds the `-s` flag when `show_details=True`:

```python
# These are equivalent:
run_pytest_check(show_details=True)
run_pytest_check(extra_args=["-s"], show_details=True)
```

**Note:** If `-s` is already in `extra_args`, it won't be added again.

## Output Management Examples

### Truncation Behavior
For tests with very long output:

```python
run_pytest_check(
    extra_args=["tests/test_verbose_output.py"],
    show_details=True
)
```

**Output behavior:**
- Up to 300 lines of detailed output shown
- If output exceeds limit: `[Output truncated at 300 lines...]`
- Collection errors always shown regardless of limits
- Up to 10 failing tests reported in detail

### Collection Errors Always Shown
Even with `show_details=False`, critical collection errors are displayed:

```python
run_pytest_check(
    extra_args=["tests/broken_import.py"],
    show_details=False
)
```

**What this does:**
- Shows collection errors (import failures, syntax errors) even in summary mode
- These are critical setup issues that always need attention
- Other test failures only show summary without details

## Flexible Test Selection Integration

### Combining with Various pytest Options

```python
# Stop on first failure with details
run_pytest_check(
    extra_args=["-x"],
    show_details=True
)

# Short tracebacks with details  
run_pytest_check(
    extra_args=["--tb=short"],
    show_details=True
)

# Specific test with custom verbosity
run_pytest_check(
    extra_args=["tests/test_api.py::test_endpoint"],
    verbosity=3,
    show_details=True
)
```

## Performance Considerations

### Large Test Suites
For projects with hundreds of tests:

```python
# Recommended for CI/CD
run_pytest_check(show_details=False)  # Fast summary only

# For debugging specific failures
run_pytest_check(
    extra_args=["-k", "test_specific_failure"],
    show_details=True
)
```

### Memory and Output Management
The `show_details=True` parameter includes built-in safeguards:

- **Maximum 10 failing tests** reported in detail
- **300-line output limit** with truncation
- **Automatic filtering** of less critical information in large test runs

## Best Practices for LLMs

1. **Default to summary mode** (`show_details=False`) for initial test runs
2. **Use details mode** (`show_details=True`) when investigating specific failures
3. **Combine with specific test selection** to focus debugging efforts
4. **Let the system handle `-s` flag automatically** when using `show_details=True`
5. **Trust the smart hints** for when to switch to detailed mode

## Error Handling Examples

### Invalid Test Selection
```python
run_pytest_check(
    extra_args=["tests/nonexistent_test.py"],
    show_details=True
)
```
Collection errors will be shown regardless of `show_details` setting.

### Environment Issues
```python
run_pytest_check(
    env_vars={"PYTHONPATH": "/custom/path"},
    show_details=True
)
```
Environment-related failures will be captured in detailed output.

This comprehensive set of examples demonstrates how the `show_details` parameter enhances the pytest interface while maintaining smart defaults for different use cases.