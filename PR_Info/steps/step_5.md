# Step 5: Implement End-to-End Integration Tests

## LLM Prompt
```
I'm implementing the "Add show_details Parameter to Pytest Interface" project (see PR_Info/steps/summary.md). 

Please implement Step 5: Create comprehensive end-to-end integration tests that verify the complete flow from MCP tool call through to formatted output. Test realistic scenarios that LLMs would use.

Reference the summary for context and build upon all previous steps (1-4). Implement only the integration testing components described in this step.
```

## WHERE: File Locations
- **Primary**: `tests/test_integration_show_details.py` (new file)
- **Test Data**: `tests/testdata/show_details/` (new directory with sample test files)

## WHAT: Main Test Functions to Implement

### End-to-End Scenario Tests:
```python
def test_focused_debugging_session()  # ≤3 tests with show_details=True
def test_large_test_suite_with_failures()  # >10 failures with show_details=True  
def test_standard_ci_run()  # Normal run with show_details=False
def test_backward_compatibility_full_flow()  # Existing behavior unchanged
```

### Real-World Usage Pattern Tests:
```python
def test_specific_test_with_prints()  # extra_args + show_details
def test_marker_filtering_with_details()  # markers + show_details  
def test_verbose_pytest_with_show_details()  # verbosity + show_details interaction
```

### Edge Case Integration Tests:
```python
def test_no_tests_found_with_show_details()
def test_all_tests_pass_with_show_details()  
def test_collection_errors_with_show_details()
```

## HOW: Integration Points
- **Real Test Files**: Create actual test files that pass/fail predictably
- **Server Setup**: Use real CodeCheckerServer instances, not mocks
- **File System**: Create temporary directories with real test structures
- **Process Execution**: Allow actual pytest subprocess execution

## ALGORITHM: Integration Testing Strategy
```
1. Create temporary project with real Python test files
2. Initialize CodeCheckerServer pointing to temp project
3. Execute run_pytest_check with various show_details combinations
4. Parse and verify actual output content and structure
5. Clean up temporary files and validate no side effects
```

## DATA: Test Scenarios and Expected Outcomes

### Test Data Structure:
```
tests/testdata/show_details/
├── focused_project/
│   ├── test_simple.py  # 2 tests: 1 pass, 1 fail with prints
│   └── conftest.py     # Basic pytest configuration
├── large_project/  
│   ├── test_module_a.py  # 5 tests: 3 pass, 2 fail  
│   ├── test_module_b.py  # 10 tests: 5 pass, 5 fail
│   └── test_module_c.py  # 8 tests: all pass
└── edge_cases/
    ├── test_no_assertions.py  # Collection errors
    └── test_all_pass.py      # No failures
```

### Expected Integration Behaviors:
```python
# Focused Session (≤3 tests)
def test_focused_debugging_session():
    # Setup: Project with 2 tests (1 pass, 1 fail with print statements)
    result = server.run_pytest_check(
        extra_args=["test_simple.py"], 
        show_details=True
    )
    
    # Verify: Detailed output includes print statements
    assert "Debug: processing value" in result  # From failing test
    assert "Longrepr:" in result  # Detailed traceback
    assert len(result.split('\n')) > 20  # Substantial detail
    
# Large Test Suite (>10 failures)  
def test_large_test_suite_with_failures():
    result = server.run_pytest_check(show_details=True)
    
    # Verify: Limited to 10 failures, includes details
    failure_sections = result.count("Test ID:")
    assert failure_sections <= 10  # Respects limit
    assert "showing details for" in result.lower()  # Indicates truncation
    
# Standard CI Run
def test_standard_ci_run():
    result = server.run_pytest_check(show_details=False)  # Default behavior
    
    # Verify: Minimal output, hint about show_details
    assert result.count('\n') < 10  # Compact output
    assert "Use show_details=True" in result  # Helpful hint
```

### Integration Coverage Requirements:
- ✅ Real pytest subprocess execution with actual test files
- ✅ Complete parameter flow from tool call to formatted output
- ✅ Output length management with real content
- ✅ Print statement visibility in various scenarios
- ✅ Error handling with malformed projects
- ✅ Performance verification (reasonable execution times)
- ✅ Clean temporary file handling

### Success Criteria:
- All integration tests pass consistently
- Output format matches expected LLM-friendly structure  
- Backward compatibility verified with real usage patterns
- No regression in existing functionality
- Proper resource cleanup (no temp files left behind)
