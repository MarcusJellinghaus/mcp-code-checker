#!/usr/bin/env python3
"""
Safe test runner that avoids integration tests and monitors for hanging processes.
"""

import subprocess
import sys
import time
import os

def run_safe_tests():
    """Run pytest with safety measures to prevent hanging."""
    
    print("="*60)
    print("SAFE TEST RUNNER")
    print("Running unit tests only (skipping integration tests)")
    print("="*60 + "\n")
    
    # Build the command
    cmd = [
        sys.executable,
        '-m', 'pytest',
        'tests',
        '-m', 'not integration',  # Skip integration tests that spawn subprocesses
        '-v',  # Verbose
        '--tb=short',  # Short traceback
        '--maxfail=5',  # Stop after 5 failures
        '--timeout=30',  # 30 second timeout per test (if pytest-timeout is installed)
    ]
    
    print(f"Command: {' '.join(cmd)}\n")
    
    start_time = time.time()
    
    try:
        # Run the tests
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # Overall 2 minute timeout
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Print output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"Tests completed in {elapsed:.1f} seconds")
        print(f"Exit code: {result.returncode}")
        
        # Parse results
        lines = result.stdout.split('\n')
        for line in lines:
            if 'passed' in line and 'failed' in line:
                print(f"Summary: {line.strip()}")
                break
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("\n⚠️ ERROR: Tests timed out after 2 minutes!")
        print("This likely means there are hanging processes.")
        print("Run: python tools/cleanup_pytest.py --auto")
        return 1
        
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_safe_tests()
    
    # Check for hanging processes
    print("\nChecking for hanging pytest processes...")
    try:
        if os.name == 'nt':
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq pytest.exe'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if 'pytest.exe' in result.stdout:
                print("⚠️ WARNING: Found hanging pytest processes!")
                print("Run: python tools/cleanup_pytest.py --auto")
            else:
                print("✅ No hanging pytest processes found")
        else:
            # Unix/Linux
            result = subprocess.run(
                ['pgrep', '-f', 'pytest'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout.strip():
                print("⚠️ WARNING: Found hanging pytest processes!")
                print("Run: python tools/cleanup_pytest.py --auto")
            else:
                print("✅ No hanging pytest processes found")
    except:
        pass  # Process checking is optional
    
    sys.exit(exit_code)
