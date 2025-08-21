#!/usr/bin/env python3
"""
Test script to identify process leak issues in pytest subprocess spawning.
"""

import subprocess
import time
import psutil
import os
import sys

def find_hanging_processes():
    """Find any hanging pytest or python processes."""
    
    hanging = []
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'status']):
        try:
            info = proc.info
            cmdline = info.get('cmdline', [])
            
            # Check for pytest or python processes
            if cmdline and any('pytest' in str(arg) for arg in cmdline):
                # Calculate how long the process has been running
                runtime = time.time() - info['create_time']
                
                if runtime > 10:  # Process running for more than 10 seconds
                    hanging.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'status': info['status'],
                        'runtime_seconds': int(runtime),
                        'cmdline': ' '.join(cmdline[:3]) if cmdline else 'N/A'
                    })
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return hanging

def kill_hanging_processes():
    """Kill hanging pytest processes."""
    
    hanging = find_hanging_processes()
    
    if not hanging:
        print("No hanging processes found.")
        return
    
    print(f"Found {len(hanging)} hanging processes:")
    for proc in hanging:
        print(f"  PID {proc['pid']}: {proc['name']} (running for {proc['runtime_seconds']}s)")
        print(f"    Status: {proc['status']}")
        print(f"    Command: {proc['cmdline']}")
    
    response = input("\nKill these processes? (y/n): ")
    if response.lower() == 'y':
        for proc_info in hanging:
            try:
                proc = psutil.Process(proc_info['pid'])
                proc.terminate()
                print(f"Terminated PID {proc_info['pid']}")
                
                # Give it time to terminate gracefully
                time.sleep(0.5)
                
                # Force kill if still alive
                if proc.is_running():
                    proc.kill()
                    print(f"Force killed PID {proc_info['pid']}")
                    
            except psutil.NoSuchProcess:
                print(f"Process {proc_info['pid']} already gone")
            except Exception as e:
                print(f"Failed to kill {proc_info['pid']}: {e}")

def test_subprocess_cleanup():
    """Test if subprocess.run properly cleans up on timeout."""
    
    print("\nTesting subprocess cleanup on timeout...")
    
    # Create a test script that sleeps forever
    test_script = '''
import time
print("Child process started")
time.sleep(1000)  # Sleep for a long time
'''
    
    with open('test_sleep.py', 'w') as f:
        f.write(test_script)
    
    try:
        print("Starting subprocess with 2 second timeout...")
        before_pids = set(p.pid for p in psutil.process_iter())
        
        try:
            result = subprocess.run(
                [sys.executable, 'test_sleep.py'],
                timeout=2,
                capture_output=True,
                text=True
            )
        except subprocess.TimeoutExpired as e:
            print(f"Subprocess timed out as expected")
            
            # Check if the process was properly cleaned up
            time.sleep(1)
            after_pids = set(p.pid for p in psutil.process_iter())
            
            new_pids = after_pids - before_pids
            if new_pids:
                print(f"⚠️  WARNING: Found {len(new_pids)} new processes after timeout!")
                for pid in new_pids:
                    try:
                        proc = psutil.Process(pid)
                        print(f"  Leaked PID {pid}: {proc.name()}")
                    except:
                        pass
            else:
                print("✅ Process was properly cleaned up")
                
    finally:
        if os.path.exists('test_sleep.py'):
            os.remove('test_sleep.py')

if __name__ == "__main__":
    print("=" * 60)
    print("PROCESS LEAK DETECTOR")
    print("=" * 60)
    
    # First check for hanging processes
    hanging = find_hanging_processes()
    if hanging:
        print(f"\n⚠️  Found {len(hanging)} hanging processes!")
        kill_hanging_processes()
    else:
        print("\n✅ No hanging processes found")
    
    # Test subprocess cleanup
    test_subprocess_cleanup()
