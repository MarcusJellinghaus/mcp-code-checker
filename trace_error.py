"""Script to trace the NoneType error."""

import sys
import os
import traceback

# Add to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import modules
from src.code_checker_pytest.models import Summary

# Test summary comparison
summary = Summary(
    collected=10,
    total=10,
    passed=5,
    failed=2,
    error=None,  # This might be the issue
    skipped=3
)

# Test the comparisons that might be failing
print("Testing comparisons...")
print(f"summary.failed = {summary.failed}")
print(f"summary.error = {summary.error}")

# Try the problematic comparison
try:
    if summary.error > 0:
        print("Error count is greater than 0")
except Exception as e:
    print(f"Error in comparison: {e}")
    traceback.print_exc()

# Try with None check
if summary.error is not None and summary.error > 0:
    print("Error count is greater than 0 (with None check)")
else:
    print("Error count is 0 or None")
