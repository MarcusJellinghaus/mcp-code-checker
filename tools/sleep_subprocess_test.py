#!/usr/bin/env python3
"""
Subprocess test script that mimics the MCP server's exact subprocess execution.

This script replicates the exact subprocess.run() call that the MCP server makes,
helping diagnose whether timeout issues are MCP-specific or general subprocess problems.
"""

import subprocess
import sys
import time
import os
from pathlib import Path


def test_subprocess_execution(sleep_seconds: float = 1.0) -> dict:
    """
    Test subprocess execution using the exact same pattern as the MCP server.
    
    Args:
        sleep_seconds: Number of seconds to sleep
        
    Returns:
        Dictionary with test results
    """
    
    print(f"Testing subprocess execution with {sleep_seconds} seconds...")
    print(f"This mimics the exact subprocess.run() call from the MCP server")
    print()
    
    # Build the exact same command as the MCP server
    script_dir = Path(__file__).parent
    sleep_script = script_dir / "sleep_script.py"
    
    if not sleep_script.exists():
        return {
            "success": False,
            "error": f"Sleep script not found: {sleep_script}",
            "return_code": 1,
            "stdout": "",
            "stderr": "",
            "execution_time": 0,
            "timed_out": False
        }
    
    # Use same command structure as MCP server
    command = [sys.executable, "-u", str(sleep_script), str(sleep_seconds)]
    
    # Set same environment as MCP server
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    # Calculate timeout same as MCP server: sleep_seconds + 30
    timeout_seconds = int(sleep_seconds) + 30
    
    print(f"Command: {' '.join(command)}")
    print(f"Timeout: {timeout_seconds} seconds")
    print(f"Environment: PYTHONUNBUFFERED=1")
    print()
    print("Starting subprocess execution...")
    
    start_time = time.time()
    
    try:
        # This is the EXACT subprocess.run() call from the MCP server
        process = subprocess.run(
            command,
            cwd=str(script_dir.parent),  # Same as MCP server project_dir
            capture_output=True,
            text=True,
            check=False,  # Same as MCP server
            timeout=timeout_seconds,
            env=env,
            shell=False,  # Same as MCP server
            input=None   # Same as MCP server
        )
        
        execution_time = time.time() - start_time
        
        print(f"Subprocess completed!")
        print(f"Execution time: {execution_time:.3f} seconds")
        print(f"Return code: {process.returncode}")
        print(f"Stdout length: {len(process.stdout)} characters")
        print(f"Stderr length: {len(process.stderr)} characters")
        
        if process.stdout:
            print(f"\nStdout:\n{process.stdout}")
        
        if process.stderr:
            print(f"\nStderr:\n{process.stderr}")
        
        return {
            "success": process.returncode == 0,
            "error": None,
            "return_code": process.returncode,
            "stdout": process.stdout or "",
            "stderr": process.stderr or "",
            "execution_time": execution_time,
            "timed_out": False
        }
        
    except subprocess.TimeoutExpired as e:
        execution_time = time.time() - start_time
        
        print(f"TIMEOUT! Process timed out after {timeout_seconds} seconds")
        print(f"Actual execution time: {execution_time:.3f} seconds")
        
        return {
            "success": False,
            "error": f"Process timed out after {timeout_seconds} seconds",
            "return_code": 1,
            "stdout": "",
            "stderr": "",
            "execution_time": execution_time,
            "timed_out": True
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        print(f"ERROR! Subprocess failed: {e}")
        print(f"Error type: {type(e).__name__}")
        
        return {
            "success": False,
            "error": str(e),
            "return_code": 1,
            "stdout": "",
            "stderr": "",
            "execution_time": execution_time,
            "timed_out": False
        }


def main():
    """Main function."""
    sleep_seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    
    print("=" * 60)
    print("MCP Server Subprocess Execution Test")
    print("=" * 60)
    print()
    
    result = test_subprocess_execution(sleep_seconds)
    
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Return code: {result['return_code']}")
    print(f"Execution time: {result['execution_time']:.3f} seconds")
    print(f"Timed out: {result['timed_out']}")
    
    if result['error']:
        print(f"Error: {result['error']}")
    
    print()
    
    if result['success']:
        print("[PASS] Subprocess execution PASSED - same as direct script execution")
        print("   This suggests the issue is MCP communication-specific, not subprocess")
    else:
        print("[FAIL] Subprocess execution FAILED - same issue as MCP server")
        print("   This suggests the issue is in subprocess execution, not MCP-specific")
    
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
