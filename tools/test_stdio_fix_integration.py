#!/usr/bin/env python3
"""
Integration test script to validate the MCP server STDIO fix.

This script tests the complete integration of the STDIO fix with the MCP server
to ensure Python subprocess calls work correctly without timing out.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.command_runner import execute_command


def test_python_subprocess_execution():
    """Test Python subprocess execution with STDIO isolation."""
    print("=" * 60)
    print("MCP Server STDIO Fix Integration Test")
    print("=" * 60)
    print()
    
    # Test 1: Simple Python script execution
    print("Test 1: Simple Python script execution")
    print("-" * 40)
    
    project_dir = Path(__file__).parent.parent
    sleep_script = project_dir / "tools" / "sleep_script.py"
    
    if not sleep_script.exists():
        print(f"❌ FAIL: Sleep script not found at {sleep_script}")
        return False
    
    command = [sys.executable, "-u", str(sleep_script), "1.0"]
    
    print(f"Command: {' '.join(command)}")
    print("Expected: Should complete in ~1 second (not timeout)")
    print()
    
    start_time = time.time()
    
    try:
        result = execute_command(
            command=command,
            cwd=str(project_dir),
            timeout_seconds=10
        )
        
        execution_time = time.time() - start_time
        
        print(f"✅ Execution completed in {execution_time:.2f} seconds")
        print(f"Return code: {result.return_code}")
        print(f"Timed out: {result.timed_out}")
        
        if result.stdout:
            print(f"Stdout: {result.stdout.strip()}")
        
        if result.stderr:
            print(f"Stderr: {result.stderr.strip()}")
        
        if result.return_code == 0 and not result.timed_out and execution_time < 5.0:
            print("✅ PASS: Python subprocess executed successfully")
        else:
            print("❌ FAIL: Python subprocess did not execute as expected")
            return False
            
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"❌ FAIL: Exception after {execution_time:.2f} seconds: {e}")
        return False
    
    print()
    
    # Test 2: Non-Python command execution
    print("Test 2: Non-Python command execution")
    print("-" * 40)
    
    if sys.platform == "win32":
        command = ["cmd", "/c", "echo", "Non-Python test"]
    else:
        command = ["echo", "Non-Python test"]
    
    print(f"Command: {' '.join(command)}")
    
    try:
        result = execute_command(
            command=command,
            timeout_seconds=5
        )
        
        print(f"Return code: {result.return_code}")
        print(f"Stdout: {result.stdout.strip()}")
        
        if result.return_code == 0 and "Non-Python test" in result.stdout:
            print("✅ PASS: Non-Python command executed successfully")
        else:
            print("❌ FAIL: Non-Python command did not execute as expected")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Exception in non-Python test: {e}")
        return False
    
    print()
    
    # Test 3: Multiple sequential Python commands
    print("Test 3: Multiple sequential Python commands")
    print("-" * 40)
    
    try:
        for i in range(3):
            command = [sys.executable, "-c", f"print('Test {i+1} output')"]
            result = execute_command(command=command, timeout_seconds=5)
            
            if result.return_code != 0:
                print(f"❌ FAIL: Command {i+1} failed with return code {result.return_code}")
                return False
            
            if f"Test {i+1} output" not in result.stdout:
                print(f"❌ FAIL: Command {i+1} output not as expected")
                return False
            
            print(f"  Command {i+1}: ✅ Success")
        
        print("✅ PASS: Multiple sequential Python commands executed successfully")
        
    except Exception as e:
        print(f"❌ FAIL: Exception in sequential test: {e}")
        return False
    
    print()
    print("=" * 60)
    print("All tests passed! ✅")
    print("The MCP server STDIO fix is working correctly.")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_python_subprocess_execution()
    sys.exit(0 if success else 1)
