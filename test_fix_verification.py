"""
Quick test to verify the subprocess runner fixes.
"""

import subprocess
import sys
from pathlib import Path

# Run only the specific tests that were failing
test_path = Path("tests/test_subprocess_runner.py")

# Run the specific test methods
test_names = [
    "TestExecuteSubprocess::test_execute_command_permission_error",
    "TestExecuteSubprocess::test_execute_command_unexpected_error",
]

for test_name in test_names:
    print(f"\nRunning {test_name}...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", f"{test_path}::{test_name}", "-v"],
        capture_output=True,
        text=True,
    )
    
    print(f"Exit code: {result.returncode}")
    if result.returncode == 0:
        print("✓ Test passed!")
    else:
        print("✗ Test failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

print("\n" + "="*50)
print("Running all tests in test_subprocess_runner.py...")
result = subprocess.run(
    [sys.executable, "-m", "pytest", str(test_path), "-v"],
    capture_output=True,
    text=True,
)

print(f"Exit code: {result.returncode}")
if "failed" in result.stdout:
    print("Some tests failed:")
    # Extract failure summary
    lines = result.stdout.split('\n')
    for i, line in enumerate(lines):
        if "FAILED" in line or "short test summary" in line:
            print(line)
else:
    print("All tests passed!")
