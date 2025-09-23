# Step 1: Implement Tests for Reporting Enhancement Logic

## LLM Prompt
```
I'm implementing the "Add show_details Parameter to Pytest Interface" project (see PR_Info/steps/summary.md). 

Please implement Step 1: Create comprehensive tests for the enhanced reporting logic that will control detailed output display. Focus on testing the decision logic for when to show details and the enhanced formatting functions.

Reference the summary for context and implement only the testing components described in this step.
```

## WHERE: File Locations
- **Primary**: `tests/test_code_checker/test_reporting.py` (extend existing)
- **Test Data**: Add test fixtures inline (no separate files needed)

## WHAT: Main Functions to Test

### Test Functions to Implement:
```python
# Test the new decision logic
def test_should_show_details_with_few_tests()
def test_should_show_details_with_many_tests()  
def test_should_show_details_with_failures()
def test_should_show_details_false_by_default()

# Test the enhanced formatting
def test_create_prompt_with_print_output_enabled()
def test_create_prompt_with_print_output_disabled() 
def test_create_prompt_respects_max_failures_limit()
```

### Helper Functions to Test:
```python
def test_should_show_details(test_results: dict, show_details: bool) -> bool
```

## HOW: Integration Points
- **Import**: Extend existing `from mcp_code_checker.code_checker_pytest.reporting import ...`
- **Test Structure**: Use pytest fixtures for mock `PytestReport` objects
- **Assertions**: Verify output content and length restrictions

## ALGORITHM: Core Testing Logic
```
1. Create mock PytestReport with varying test counts/failures
2. Test decision logic: should_show_details(results, flag) -> bool
3. Test enhanced formatting: create_prompt(..., include_print_output=True/False)  
4. Verify output limits: max 10 failures, appropriate truncation
5. Assert backward compatibility: existing tests still pass
```

## DATA: Test Fixtures and Expected Returns

### Input Test Data:
```python
@pytest.fixture
def minimal_test_results():
    """Mock results for ≤3 tests"""
    return {"summary": {"collected": 2, "passed": 1, "failed": 1}}

@pytest.fixture  
def large_test_results():
    """Mock results for >10 failures"""
    return {"summary": {"collected": 50, "passed": 35, "failed": 15}}

@pytest.fixture
def mock_pytest_report_with_prints():
    """PytestReport with stdout/print content in longrepr"""
```

### Expected Return Values:
- `should_show_details()` returns `bool`
- Enhanced `create_prompt_for_failed_tests()` returns `Optional[str]` with controlled content
- Output length verification via `len(result.split('\n'))` assertions
- Print statement inclusion/exclusion verification via string content checks

### Test Coverage Requirements:
- ✅ Few tests (≤3) → always show details when requested
- ✅ Many failures (>10) → limit to 10 failures maximum  
- ✅ Print output inclusion/exclusion based on parameter
- ✅ Backward compatibility (existing behavior unchanged)
- ✅ Edge cases (0 tests, None values, empty strings)
