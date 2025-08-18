#!/usr/bin/env python
"""Debug script to find where the NoneType > int error is occurring."""

import sys
import os
import traceback

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    try:
        # Import the server module
        from src.server import CodeCheckerServer
        from pathlib import Path
        
        # Create a server instance
        server = CodeCheckerServer(
            project_dir=Path(__file__).parent,
            test_folder="tests"
        )
        
        # Try to call run_pytest_check directly
        result = server._register_tools.run_pytest_check()
        
        print("Result:", result)
        
    except AttributeError:
        # The tools are registered differently, let's try another approach
        print("Direct method call failed, trying via MCP...")
        
        # Let's try to trace where the error happens
        from src.code_checker_pytest.runners import check_code_with_pytest
        
        try:
            result = check_code_with_pytest(
                project_dir=os.path.dirname(__file__),
                test_folder="tests",
                verbosity=2
            )
            print("Success:", result.get('success'))
            print("Summary:", result.get('summary'))
        except Exception as e:
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {e}")
            print("\nFull traceback:")
            traceback.print_exc()
            
            # Try to identify the exact line
            tb = sys.exc_info()[2]
            while tb.tb_next:
                frame = tb.tb_frame
                print(f"\nFrame: {frame.f_code.co_filename}:{frame.f_lineno}")
                print(f"Function: {frame.f_code.co_name}")
                # Print local variables at the error point
                if "summary" in frame.f_locals:
                    summary = frame.f_locals["summary"]
                    print(f"Summary object: {summary}")
                    if hasattr(summary, '__dict__'):
                        print(f"Summary attributes: {summary.__dict__}")
                tb = tb.tb_next

if __name__ == "__main__":
    main()
