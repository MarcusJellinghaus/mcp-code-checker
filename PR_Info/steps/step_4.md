# Step 4: Update Server Interface with show_details Parameter

## LLM Prompt
```
I'm implementing the "Add show_details Parameter to Pytest Interface" project (see PR_Info/steps/summary.md). 

Please implement Step 4: Update the server interface to add the show_details parameter to run_pytest_check(). Integrate with the enhanced reporting functions from Steps 1-2 and ensure the tests from Step 3 pass.

Reference the summary for context and implement only the server interface changes described in this step.
```

## WHERE: File Locations
- **Primary**: `src/mcp_code_checker/server.py` (modify existing function)
- **Secondary**: No new files needed

## WHAT: Main Functions to Modify

### Enhanced Tool Function:
```python
@self.mcp.tool()
@log_function_call  
def run_pytest_check(
    markers: Optional[List[str]] = None,
    verbosity: int = 2,
    extra_args: Optional[List[str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    show_details: bool = False,  # NEW parameter
) -> str:
```

### New Helper Method:
```python
def _should_show_details(self, test_results: dict, show_details: bool) -> bool:
    """Determine if detailed output should be shown (delegate to reporting module)."""
```

### Enhanced Formatting Method:
```python  
def _format_pytest_result_with_details(
    self,
    test_results: dict[str, Any], 
    show_details: bool
) -> str:
    """Enhanced formatting that respects show_details parameter."""
```

## HOW: Integration Points
- **Import Enhancement**: `from mcp_code_checker.code_checker_pytest.reporting import should_show_details`
- **MCP Tool Decorator**: Existing `@self.mcp.tool()` automatically handles new parameter
- **Backward Compatibility**: Default `show_details=False` maintains existing behavior
- **Error Handling**: Maintain existing try/except patterns

## ALGORITHM: Core Implementation Logic
```
1. Accept show_details parameter in run_pytest_check signature
2. Pass existing parameters to check_code_with_pytest (unchanged)
3. Use enhanced _format_pytest_result_with_details for output formatting
4. Call should_show_details helper to determine detail level
5. Pass parameters to enhanced create_prompt_for_failed_tests
```

## DATA: Function Parameters and Integration

### Updated Function Signature:
```python
def run_pytest_check(
    markers: Optional[List[str]] = None,
    verbosity: int = 2,  # pytest's native -v verbosity  
    extra_args: Optional[List[str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    show_details: bool = False,  # NEW: LLM output control
) -> str:
```

### Enhanced Formatting Logic:
```python
def _format_pytest_result_with_details(self, test_results: dict, show_details: bool) -> str:
    # Error case - unchanged
    if not test_results["success"]:
        return f"Error running pytest: {test_results.get('error', 'Unknown error')}"
    
    # Import and use reporting helper
    from mcp_code_checker.code_checker_pytest.reporting import should_show_details
    
    should_show = should_show_details(test_results, show_details)
    
    # Success/failure formatting with controlled detail
    if failures_exist and should_show:
        # Use enhanced create_prompt_for_failed_tests with new parameters
        return create_prompt_for_failed_tests(
            test_results["test_results"],
            max_number_of_tests_reported=10,  # Increased limit
            include_print_output=True,
            max_failures=10
        )
    elif failures_exist and not should_show:
        # Minimal output with helpful hint
        return f"Pytest completed with failures. Use show_details=True to see details."
    else:
        # Success case - unchanged
        return existing_success_message
```

### Integration Flow:
1. **Parameter Acceptance**: Server receives `show_details` from LLM
2. **Test Execution**: Calls existing `check_code_with_pytest` (no changes needed)
3. **Result Processing**: Uses `_format_pytest_result_with_details` instead of `_format_pytest_result`
4. **Decision Logic**: Calls `should_show_details()` from reporting module
5. **Enhanced Output**: Passes control parameters to `create_prompt_for_failed_tests`

### Backward Compatibility Guarantee:
- Default `show_details=False` produces identical output to current behavior
- All existing parameters work unchanged
- Existing calling code continues to work without modification
- Tool registration maintains same interface for non-show_details calls
