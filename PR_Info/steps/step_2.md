# Step 2: Enhance Reporting Functions with Output Control

## LLM Prompt
```
I'm implementing the "Add show_details Parameter to Pytest Interface" project (see PR_Info/steps/summary.md). 

Please implement Step 2: Enhance the reporting functions to support controlled output display. Add the include_print_output parameter to create_prompt_for_failed_tests() and implement the should_show_details() helper function.

Reference the summary for context and ensure the tests from Step 1 pass. Implement only the functionality described in this step.
```

## WHERE: File Locations
- **Primary**: `src/mcp_code_checker/code_checker_pytest/reporting.py` (modify existing)
- **Secondary**: No new files needed

## WHAT: Main Functions to Implement

### Enhanced Function Signature:
```python
def create_prompt_for_failed_tests(
    test_session_result: PytestReport, 
    max_number_of_tests_reported: int = 1,
    include_print_output: bool = True,  # NEW parameter
    max_failures: int = 10,  # NEW parameter (hardcoded limit)
    max_output_lines: int = 300  # NEW parameter for overall output limit
) -> Optional[str]:
```

### New Helper Function:
```python
def should_show_details(test_results: dict, show_details: bool) -> bool:
    """Determine if detailed output should be shown based on test results and user preference."""
```

### Enhanced Summary Function (optional):
```python  
def get_detailed_test_summary(test_session_result: PytestReport, show_details: bool) -> str:
    """Enhanced summary that can include additional detail hints."""
```

## HOW: Integration Points
- **Backward Compatibility**: Default parameters maintain existing behavior
- **Import Dependencies**: No new imports needed
- **Function Decorators**: Keep existing `@log_function_call` decorators
- **Error Handling**: Maintain existing exception handling patterns

## ALGORITHM: Core Logic Implementation
```
1. should_show_details: Check test_count ≤ 3 OR failures ≤ 10
2. create_prompt: if include_print_output, add stdout/stderr sections  
3. create_prompt: limit failures to max_failures parameter
4. Enhanced formatting: conditionally include longrepr content
5. Maintain compatibility: existing calls work unchanged
```

## DATA: Function Parameters and Returns

### Input Parameters:
- `test_session_result: PytestReport` - Existing pytest report object
- `max_number_of_tests_reported: int = 1` - Existing limit (keep default for compatibility)
- `include_print_output: bool = True` - NEW: Whether to include stdout/stderr/longrepr 
- `max_failures: int = 10` - NEW: Maximum number of failures to report (hardcoded)
- `max_output_lines: int = 300` - NEW: Overall output line limit with truncation indicator

### Return Values:
- `create_prompt_for_failed_tests()` returns `Optional[str]`
  - `None` if no failures
  - Formatted string with controlled detail level if failures exist
- `should_show_details()` returns `bool`
  - `True` if conditions meet criteria for showing details
  - `False` otherwise

### Decision Logic for should_show_details():
```python
def should_show_details(test_results: dict, show_details: bool) -> bool:
    if not show_details:
        return False
    
    summary = test_results.get("summary", {})
    total_collected = summary.get("collected", 0) or 0
    failed_count = summary.get("failed", 0) or 0
    error_count = summary.get("error", 0) or 0
    
    # Show details if few tests OR manageable failures
    return total_collected <= 3 or (failed_count + error_count) <= 10
```

### Output Format Changes:
- **With include_print_output=True**: Include all stdout, stderr, longrepr sections
- **With include_print_output=False**: Include only basic error messages and tracebacks  
- **Max failures limit**: Stop processing after max_failures tests (hardcoded at 10)
- **Output length limit**: Truncate at 300 lines total with "..." indicator
- **Collection errors**: Always shown regardless of settings (critical setup issues)
- **Compatibility**: Default behavior unchanged (include_print_output=True, max_failures=1)
