#!/usr/bin/env python3
"""
Python client for testing sleep implementations directly.
Simplified standalone version that works without complex dependencies.
"""

import sys
import subprocess
import os
from pathlib import Path


def main():
    """Main client function."""
    # Parse command line arguments
    sleep_seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
    method = sys.argv[2] if len(sys.argv) > 2 else "default"
    
    print(f"Python client calling second_sleep:")
    print(f"  Seconds: {sleep_seconds}")
    print(f"  Method: {method}")
    print()
    
    # Map default to python method
    if method == "default":
        method = "python"
    
    try:
        # Build command based on implementation method
        if method == "python":
            sleep_script = Path("tools") / "sleep_script.py"
            if not sleep_script.exists():
                print(f"ERROR: Sleep script not found: {sleep_script}")
                sys.exit(1)
                
            command = ["python", "-u", str(sleep_script), str(sleep_seconds)]
            
        elif method == "batch":
            batch_script = Path("tools") / "sleep_batch.bat"
            if not batch_script.exists():
                print(f"ERROR: Batch script not found: {batch_script}")
                sys.exit(1)
                
            command = [str(batch_script), str(sleep_seconds)]
            
        elif method == "hybrid":
            hybrid_script = Path("tools") / "sleep_hybrid.bat"
            if not hybrid_script.exists():
                print(f"ERROR: Hybrid script not found: {hybrid_script}")
                sys.exit(1)
                
            command = [str(hybrid_script), str(sleep_seconds)]
            
        elif method == "subprocess_test":
            subprocess_test_script = Path("tools") / "sleep_subprocess_test.py"
            if not subprocess_test_script.exists():
                print(f"ERROR: Subprocess test script not found: {subprocess_test_script}")
                sys.exit(1)
                
            command = ["python", str(subprocess_test_script), str(sleep_seconds)]
            
        else:
            print(f"ERROR: Unknown method: {method}")
            print("Valid methods: default, python, batch, hybrid, subprocess_test")
            sys.exit(1)

        # Execute command
        timeout_seconds = int(sleep_seconds) + 30
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        
        if result.returncode == 0:
            output = result.stdout.strip() or f"Successfully slept for {sleep_seconds} seconds using {method} method"
            print(f"Method: {method}")
            print(output)
        else:
            print(f"Sleep failed (method: {method}, code {result.returncode}): {result.stderr}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Client error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
