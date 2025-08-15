#!/usr/bin/env python3
"""
Sleep script for testing MCP script execution with timeout fixes.

This script implements solutions to fix timeout issues when calling Python
subprocesses from MCP servers:

1. Force unbuffered output (-u flag) - handled by caller
2. Set appropriate timeouts (sleep_time + buffer) - handled by caller  
3. Use environment variables (PYTHONUNBUFFERED=1) - implemented here
4. Improved subprocess configuration - handled by caller
5. Immediate output flushing - implemented here
"""

import sys
import time
import os
from datetime import datetime


def main():
    """Main function to sleep for specified seconds with proper output handling."""
    
    # Solution 3: Set unbuffered environment if not already set
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    # Get sleep duration from command line argument
    if len(sys.argv) > 1:
        try:
            sleep_seconds = float(sys.argv[1])
        except ValueError:
            print(f"Error: Invalid sleep duration '{sys.argv[1]}'. Must be a number.", flush=True)
            sys.exit(1)
    else:
        sleep_seconds = 5.0
    
    # Validate input
    if sleep_seconds < 0:
        print("Error: Sleep duration cannot be negative.", flush=True)
        sys.exit(1)
    
    if sleep_seconds > 300:
        print("Error: Sleep duration cannot exceed 300 seconds for safety.", flush=True)
        sys.exit(1)
    
    # Solution 5: Immediate output with explicit flushing
    start_time = datetime.now()
    print(f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}", flush=True)
    print(f"Sleeping for {sleep_seconds} seconds...", flush=True)
    
    # Force stdout/stderr to flush immediately
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Record precise start time for measurement
    precise_start = time.time()
    
    # Sleep for the specified duration
    time.sleep(sleep_seconds)
    
    # Record precise end time
    precise_end = time.time()
    actual_sleep = precise_end - precise_start
    
    # Solution 5: Immediate output with explicit flushing
    end_time = datetime.now()
    print(f"End: {end_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}", flush=True)
    
    # Calculate precision
    precision_diff = abs(actual_sleep - sleep_seconds)
    
    # Output results with immediate flushing
    print("Sleep operation completed successfully:", flush=True)
    print(f"  Requested: {sleep_seconds} seconds", flush=True)
    print(f"  Actual: {actual_sleep:.3f} seconds", flush=True) 
    print(f"  Precision: {precision_diff:.3f} seconds difference", flush=True)
    
    # Final flush to ensure all output is sent
    sys.stdout.flush()
    sys.stderr.flush()


if __name__ == "__main__":
    main()
