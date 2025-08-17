#!/usr/bin/env python3
"""
Python client for testing sleep implementation directly.
Simplified standalone version that works without complex dependencies.
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Main client function."""
    # Parse command line arguments
    sleep_seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
    
    print(f"Python client calling second_sleep:")
    print(f"  Seconds: {sleep_seconds}")
    print()
    
    try:
        # Build command to execute Python sleep script
        sleep_script = Path("tools") / "sleep_script.py"
        if not sleep_script.exists():
            print(f"ERROR: Sleep script not found: {sleep_script}")
            sys.exit(1)
            
        command = ["python", "-u", str(sleep_script), str(sleep_seconds)]

        # Execute command
        timeout_seconds = int(sleep_seconds) + 30
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        
        if result.returncode == 0:
            print(result.stdout.strip() or f"Successfully slept for {sleep_seconds} seconds")
        else:
            print(f"Sleep failed (code {result.returncode}): {result.stderr}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Client error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
