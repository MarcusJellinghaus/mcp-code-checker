#!/usr/bin/env python3
"""
Cleanup script to kill hanging pytest processes.
Run this if you have zombie pytest processes after running tests.
"""

import psutil
import time
import sys
import os

def find_and_kill_hanging_pytest():
    """Find and kill hanging pytest processes."""
    
    print("=" * 60)
    print("PYTEST PROCESS CLEANUP UTILITY")
    print("=" * 60)
    
    current_pid = os.getpid()
    killed_count = 0
    
    # Find all pytest-related processes
    pytest_procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'status']):
        try:
            info = proc.info
            cmdline = info.get('cmdline', [])
            
            # Skip the current process
            if info['pid'] == current_pid:
                continue
            
            # Check if this is a pytest process
            if cmdline and any('pytest' in str(arg) for arg in cmdline):
                runtime = time.time() - info['create_time']
                pytest_procs.append({
                    'proc': proc,
                    'pid': info['pid'],
                    'name': info['name'],
                    'runtime': int(runtime),
                    'status': info['status'],
                    'cmdline': ' '.join(cmdline[:5]) if len(cmdline) > 5 else ' '.join(cmdline)
                })
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if not pytest_procs:
        print("\n✅ No pytest processes found running.")
        return 0
    
    print(f"\nFound {len(pytest_procs)} pytest process(es):")
    for p in pytest_procs:
        status_icon = "⚠️" if p['runtime'] > 60 else "ℹ️"
        print(f"{status_icon} PID {p['pid']}: {p['name']} (running for {p['runtime']}s)")
        print(f"   Status: {p['status']}")
        print(f"   Command: {p['cmdline'][:100]}...")
    
    # Ask for confirmation
    print("\n" + "=" * 60)
    if '--auto' in sys.argv or '-y' in sys.argv:
        response = 'y'
        print("Auto-kill mode enabled.")
    else:
        response = input("Kill ALL these processes? (y/n): ")
    
    if response.lower() != 'y':
        print("Aborted.")
        return 0
    
    # Kill the processes
    print("\nKilling processes...")
    for p in pytest_procs:
        try:
            proc = p['proc']
            pid = p['pid']
            
            # Try graceful termination first
            proc.terminate()
            print(f"  Sent SIGTERM to PID {pid}")
            
            # Wait a bit
            try:
                proc.wait(timeout=2)
                print(f"  ✅ PID {pid} terminated gracefully")
            except psutil.TimeoutExpired:
                # Force kill if still running
                proc.kill()
                print(f"  ⚠️  PID {pid} force killed")
                proc.wait(timeout=2)
            
            killed_count += 1
            
        except psutil.NoSuchProcess:
            print(f"  ℹ️  PID {pid} already gone")
        except psutil.AccessDenied:
            print(f"  ❌ Access denied for PID {pid} - try running as administrator")
        except Exception as e:
            print(f"  ❌ Failed to kill PID {pid}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Cleanup complete. Killed {killed_count} process(es).")
    
    # On Windows, also try to clean up using taskkill
    if os.name == 'nt' and killed_count < len(pytest_procs):
        print("\nRunning Windows taskkill as fallback...")
        os.system('taskkill /F /IM pytest.exe 2>nul')
        os.system('taskkill /F /IM python.exe /FI "WINDOWTITLE eq pytest*" 2>nul')
    
    return killed_count

def check_for_issues():
    """Check for common issues that cause hanging processes."""
    
    print("\nChecking for common issues...")
    
    # Check if running in CI/CD environment
    if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
        print("⚠️  Running in CI/CD environment - process cleanup may be limited")
    
    # Check Windows-specific issues
    if os.name == 'nt':
        print("ℹ️  Windows detected - subprocess handling can be problematic")
        print("   Consider using WSL or Linux for more reliable process management")
    
    # Check for pytest-xdist
    try:
        import pytest_xdist
        print("⚠️  pytest-xdist detected - parallel testing can leave orphaned processes")
    except ImportError:
        pass

if __name__ == "__main__":
    try:
        killed = find_and_kill_hanging_pytest()
        check_for_issues()
        
        if '--loop' in sys.argv:
            # Continuous monitoring mode
            print("\nEntering monitoring mode (Ctrl+C to exit)...")
            while True:
                time.sleep(10)
                hanging = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info.get('cmdline') and \
                           any('pytest' in str(arg) for arg in proc.info['cmdline']):
                            hanging.append(proc.info['pid'])
                    except:
                        pass
                
                if hanging:
                    print(f"⚠️  {len(hanging)} pytest process(es) still running: {hanging}")
                    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
