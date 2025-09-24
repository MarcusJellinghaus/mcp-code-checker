# Test data directory for pytest reporting integration tests

This directory contains sample test files used by the integration tests to verify the complete end-to-end flow of the pytest reporting functionality, specifically the show_details parameter.

## Directory Structure

- `focused_project/` - Small project for focused debugging scenarios (≤3 tests)
- `large_project/` - Large project with multiple test files and many failures
- `edge_cases/` - Projects that test edge cases like collection errors

## Usage

These test files are used by `tests/test_integration_show_details.py` to create realistic test scenarios that verify:

1. Print statement visibility in various scenarios
2. Output length management and truncation
3. Error handling with malformed projects  
4. Performance with different project sizes
5. Clean temporary file handling

## Test File Characteristics

### focused_project/
- **test_simple.py**: 2 tests (1 pass, 1 fail with prints)
- **conftest.py**: Basic pytest configuration

### large_project/
- **test_module_a.py**: 5 tests (3 pass, 2 fail)
- **test_module_b.py**: 10 tests (5 pass, 5 fail)
- **test_module_c.py**: 8 tests (all pass)

### edge_cases/
- **test_no_assertions.py**: Collection errors 
- **test_all_pass.py**: No failures
