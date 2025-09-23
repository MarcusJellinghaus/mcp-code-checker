# Step 3: Implement Tests for Server Interface Enhancement

## LLM Prompt
```
I'm implementing the "Add show_details Parameter to Pytest Interface" project (see PR_Info/steps/summary.md). 

Please implement Step 3: Create comprehensive tests for the enhanced server interface that will include the new show_details parameter. Focus on testing the integration between the server parameter and the underlying reporting functions.

Reference the summary for context and build upon the reporting enhancements from Steps 1-2. Implement only the testing components described in this step.
```

## WHERE: File Locations
- **Primary**: `tests/test_server_params.py` (extend existing)
- **Secondary**: May need `tests/test_server_integration.py` (new file if needed)

## WHAT: Main Test Functions to Implement

### Parameter Integration Tests:
```python
def test_run_pytest_check_with_show_details_true()
def test_run_pytest_check_with_show_details_false()  
def test_run_pytest_check_show_details_default_value()
def test_run_pytest_check_backward_compatibility()
```

### Output Control Tests:
```python
def test_show_details_with_focused_test_run()  
def test_show_details_with_many_failures()
def test_show_details_output_length_limits()
```

### Integration Tests:
```python
def test_server_method_signature_includes_show_details()
def test_mcp_tool_decorator_compatibility() 
```

## HOW: Integration Points
- **Import**: `from mcp_code_checker.server import CodeCheckerServer`
- **Mocking**: Mock `check_code_with_pytest` to return controlled test results
- **Test Structure**: Use pytest fixtures for server instances and mock responses
- **MCP Testing**: Verify tool registration and parameter passing

## ALGORITHM: Core Testing Strategy
```
1. Create CodeCheckerServer instance with test project directory
2. Mock check_code_with_pytest to return various test result scenarios  
3. Call run_pytest_check with different show_details values
4. Assert correct parameter passing to underlying functions
5. Verify output formatting matches expected behavior
```

## DATA: Test Fixtures and Expected Behavior

### Mock Server Setup:
```python
@pytest.fixture
def mock_server():
    """Create CodeCheckerServer for testing"""
    return CodeCheckerServer(project_dir=Path("/test/project"))

@pytest.fixture  
def mock_pytest_results_few_tests():
    """Mock results for ≤3 tests scenario"""
    
@pytest.fixture
def mock_pytest_results_many_failures():
    """Mock results for >10 failures scenario"""
```

### Expected Parameter Behavior:
- **Default**: `show_details=False` maintains current output behavior
- **Explicit True**: `show_details=True` passes through to enhanced reporting
- **Integration**: Parameter correctly flows from server → runners → reporting
- **Tool Registration**: MCP tool decorator properly handles new parameter

### Test Verification Points:
```python
# 1. Parameter Default Value
assert signature.parameters['show_details'].default == False

# 2. Parameter Type Annotation  
assert signature.parameters['show_details'].annotation == bool

# 3. Output Control Integration
with patch('mcp_code_checker.code_checker_pytest.runners.check_code_with_pytest') as mock_check:
    server.run_pytest_check(show_details=True)
    # Verify enhanced reporting called correctly

# 4. Backward Compatibility
old_style_result = server.run_pytest_check(markers=['unit'])  
new_style_result = server.run_pytest_check(markers=['unit'], show_details=False)
assert old_style_result == new_style_result
```

### Coverage Requirements:
- ✅ Parameter exists with correct default value
- ✅ Parameter type checking and validation
- ✅ Integration with underlying reporting functions
- ✅ Backward compatibility maintained
- ✅ MCP tool decorator works with new parameter
- ✅ Output length control based on test scenarios
