#!/usr/bin/env python3
"""
Script to check for potential circular pytest execution.
This will help us understand if pytest is spawning itself recursively.
"""

import os
import sys
import psutil
import time

def check_pytest_processes():
    """Check how many pytest processes are running."""
    pytest_processes = []
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if this is a pytest process
            cmdline = proc.info.get('cmdline', [])
            if cmdline and any('pytest' in str(arg) for arg in cmdline):
                pytest_processes.append({
                    'pid': proc.info['pid'],
                    'parent': proc.ppid(),
                    'cmdline': ' '.join(cmdline[:3]) if cmdline else 'N/A'
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return pytest_processes

def visualize_process_tree():
    """Visualize the process tree when pytest runs."""
    print("=" * 60)
    print("PYTEST PROCESS TREE ANALYSIS")
    print("=" * 60)
    
    processes = check_pytest_processes()
    print(f"\nFound {len(processes)} pytest-related processes:")
    
    for proc in processes:
        print(f"  PID: {proc['pid']} (Parent: {proc['parent']})")
        print(f"    Command: {proc['cmdline']}")
    
    print("\nProcess relationships:")
    # Build a tree structure
    for proc in processes:
        try:
            parent_proc = psutil.Process(proc['parent'])
            print(f"  {proc['pid']} is child of {proc['parent']} ({parent_proc.name()})")
        except:
            print(f"  {proc['pid']} is child of {proc['parent']} (unknown)")

if __name__ == "__main__":
    print("Checking for pytest processes...")
    visualize_process_tree()
    
    # If we're being called by pytest, show a warning
    if 'pytest' in sys.modules:
        print("\n⚠️  WARNING: This script is being run FROM WITHIN pytest!")
        print("This could indicate a circular execution pattern.")
