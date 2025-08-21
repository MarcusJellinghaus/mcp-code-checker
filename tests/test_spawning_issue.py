"""
Test file to demonstrate the multiple process spawning issue.
"""

import subprocess
import sys
import time
import os

def test_identify_spawning_issue() -> None:
    """This test will help us see what's happening with subprocess spawning."""
    
    # Print current process info
    print(f"\n{'='*60}")
    print(f"CURRENT TEST PROCESS:")
    print(f"  PID: {os.getpid()}")
    print(f"  Python: {sys.executable}")
    print(f"  Working dir: {os.getcwd()}")
    
    # Check if we're already in a nested pytest call
    pytest_depth = os.environ.get('PYTEST_DEPTH', '0')
    print(f"  PYTEST_DEPTH: {pytest_depth}")
    
    if int(pytest_depth) > 0:
        print("  ⚠️  WARNING: This appears to be a NESTED pytest call!")
    
    print(f"{'='*60}\n")
    
    # This test passes to avoid noise
    assert True

def test_check_environment_variables() -> None:
    """Check what environment variables are set during test execution."""
    
    print("\n" + "="*60)
    print("PYTEST-RELATED ENVIRONMENT VARIABLES:")
    for key, value in os.environ.items():
        if 'PYTEST' in key.upper() or 'TEST' in key.upper():
            print(f"  {key}: {value[:100]}...")  # Truncate long values
    print("="*60 + "\n")
    
    assert True
