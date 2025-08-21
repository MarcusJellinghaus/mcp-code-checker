"""
Analysis and solution for the pytest subprocess spawning issue.

THE PROBLEM:
============
When you run `pytest tests`, the following happens:

1. pytest discovers and runs all test files in the tests/ directory
2. Some tests (like test_run_tests()) are INTEGRATION tests that actually call run_tests()
3. run_tests() spawns a NEW pytest subprocess using execute_command()
4. This subprocess runs pytest on a temporary test project
5. If those temporary test files also contained tests that call run_tests(), 
   you'd get infinite recursion (but they don't, so it's safe)

However, you're seeing multiple processes because:
- Each integration test spawns its own pytest subprocess
- If you have N integration tests, you'll see N+1 pytest processes (original + N subprocesses)

THE SOLUTION:
=============
There are several ways to prevent or control this:

1. **Skip integration tests during normal test runs** (RECOMMENDED)
2. **Use markers to separate unit and integration tests**
3. **Add recursion protection using environment variables**
4. **Mock the subprocess calls even in integration tests**
"""

import os
import pytest
from unittest.mock import patch

# Solution 1: Mark integration tests and skip them by default
def mark_integration_tests():
    """
    Add this to your pytest.ini or pyproject.toml:
    
    [tool.pytest.ini_options]
    markers = [
        "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
        "unit: marks tests as unit tests",
    ]
    
    Then mark your tests:
    """
    
    @pytest.mark.integration
    def test_run_tests_integration():
        # This test will actually spawn subprocesses
        pass
    
    @pytest.mark.unit  
    def test_run_tests_unit():
        # This test uses mocks, no subprocesses
        pass

# Solution 2: Add recursion protection
def add_recursion_protection_to_run_tests():
    """
    Modify the run_tests() function to check for recursion:
    """
    
    def run_tests_with_protection(project_dir, test_folder, **kwargs):
        # Check if we're already in a pytest subprocess
        if os.environ.get('PYTEST_SUBPROCESS_DEPTH', '0') != '0':
            raise RuntimeError(
                "Detected recursive pytest execution! "
                "Integration tests should not be run from within pytest subprocesses."
            )
        
        # Set environment variable before spawning subprocess
        env = kwargs.get('env_vars', {}).copy()
        env['PYTEST_SUBPROCESS_DEPTH'] = '1'
        kwargs['env_vars'] = env
        
        # Continue with normal execution
        # ... rest of the function

# Solution 3: Better test organization
def organize_tests_properly():
    """
    Recommended directory structure:
    
    tests/
    ├── unit/                    # Unit tests (with mocks)
    │   ├── test_parsers.py
    │   ├── test_models.py
    │   └── test_reporting.py
    ├── integration/             # Integration tests (spawn subprocesses)  
    │   ├── test_run_tests.py
    │   └── test_full_flow.py
    └── fixtures/                # Test data and helpers
        └── sample_projects/
    
    Then run:
    - `pytest tests/unit` for unit tests only (fast, no subprocesses)
    - `pytest tests/integration` for integration tests (slower, spawns subprocesses)
    - `pytest tests` for everything
    """
    pass

# Solution 4: Use pytest configuration to exclude integration tests by default
PYTEST_INI_CONTENT = """
[tool.pytest.ini_options]
testpaths = ["tests"]
# By default, don't run integration tests
addopts = "-m 'not integration'"
markers = [
    "integration: Integration tests that spawn subprocesses",
    "unit: Unit tests that use mocks",
]

# To run integration tests explicitly:
# pytest -m integration
# To run all tests:
# pytest -m ""
"""

if __name__ == "__main__":
    print(__doc__)
    print("\nRecommended pytest.ini additions:")
    print(PYTEST_INI_CONTENT)
