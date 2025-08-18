import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.code_checker_pytest.runners import check_code_with_pytest
    
    # Try to run a simple test
    result = check_code_with_pytest(
        project_dir=os.path.dirname(__file__),
        extra_args=['-k', 'test_command_result_creation', '-v']
    )
    
    print("Success:", result.get('success'))
    print("Summary:", result.get('summary'))
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
