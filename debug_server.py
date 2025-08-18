"""Test script to debug the NoneType comparison error."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pathlib import Path
from src.server import CodeCheckerServer

# Create a server instance
server = CodeCheckerServer(
    project_dir=Path(os.path.dirname(__file__)),
    test_folder="tests",
    keep_temp_files=False
)

# Try to run pytest check
try:
    # Get the registered function
    run_pytest_check = None
    for tool_name, tool_func in server.mcp._tools.items():
        if 'pytest' in tool_name:
            run_pytest_check = tool_func
            break
    
    if run_pytest_check:
        print("Found pytest check function, running...")
        result = run_pytest_check(
            extra_args=['-k', 'test_command_result_creation', '-v']
        )
        print("Result:", result)
    else:
        print("Could not find pytest check function")
        
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
