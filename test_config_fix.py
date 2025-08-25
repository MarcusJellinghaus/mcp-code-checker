#!/usr/bin/env python
"""Test script to verify mcp-config setup works."""

import sys
from pathlib import Path

# Add src to path so we can import directly
sys.path.insert(0, str(Path(__file__).parent))

from src.config.main import main

# Set up test arguments
test_args = [
    "setup",
    "mcp-code-checker",
    "my-checker",
    "--project-dir", ".",
    "--dry-run"  # Use dry-run for testing
]

# Override sys.argv
original_argv = sys.argv
sys.argv = ["mcp-config"] + test_args

try:
    result = main()
    if result == 0:
        print("\n✅ SUCCESS: mcp-config setup command works correctly!")
    else:
        print(f"\n❌ FAILED: mcp-config returned exit code {result}")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    sys.argv = original_argv
