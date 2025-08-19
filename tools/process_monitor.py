#!/usr/bin/env python3
"""
Process Monitor - Task Manager Style
Shows detailed information about all running processes
"""

import psutil
import time
import os
from datetime import datetime
from typing import List, Dict, Any


def get_process_info(proc: psutil.Process) -> Dict[str, Any]:
    """
    Extract detailed information from a process object
    """
    try:
        # Get process info with oneshot() for better performance
        with proc.oneshot():
            info = {
                'pid': proc.pid,
                'name': proc.name(),
                'status': proc.status(),
                'username': proc.username() if hasattr(proc, 'username') else 'N/A',
                'cpu_percent': proc.cpu_percent(),
                'memory_percent': proc.memory_percent(),
                'memory_info': proc.memory_info(),
                'create_time': proc.create_time(),
                'num_threads': proc.num_threads(),
                'cmdline': ' '.join(proc.cmdline()) if proc.cmdline() else 'N/A'
            }

            # Get parent process info
            try:
                parent = proc.parent()
                info['parent_pid'] = parent.pid if parent else None
                info['parent_name'] = parent.name() if parent else 'N/A'
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                info['parent_pid'] = None
                info['parent_name'] = 'N/A'

            # Get process type (approximation)
            if info['name'].endswith('.exe'):
                info['type'] = 'Application'
            elif 'python' in info['name'].lower():
                info['type'] = 'Python Script'
            elif any(service in info['name'].lower() for service in ['service', 'svc', 'daemon']):
                info['type'] = 'Service'
            else:
                info['type'] = 'Process'

    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None

    return info


def format_memory(bytes_value: int) -> str:
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.1f} TB"


def format_time(timestamp: float) -> str:
    """Convert timestamp to readable format"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def print_header():
    """Print the table header"""
    header = f"{'PID':<8} {'Name':<25} {'Status':<12} {'Type':<15} {'CPU%':<8} {'Memory%':<10} {'Memory':<12} {'Threads':<8} {'User':<15} {'Started':<19} {'Command Line':<50}"
    print(header)
    print("-" * len(header))


def print_process_row(info: Dict[str, Any]):
    """Print a single process row"""
    memory_mb = info['memory_info'].rss / (1024 * 1024)
    started_time = format_time(info['create_time'])
    cmdline = info['cmdline'][:47] + "..." if len(info['cmdline']) > 50 else info['cmdline']

    row = f"{info['pid']:<8} {info['name'][:22]:<25} {info['status']:<12} {info['type']:<15} {info['cpu_percent']:<8.1f} {info['memory_percent']:<10.1f} {memory_mb:<12.1f} {info['num_threads']:<8} {info['username'][:12]:<15} {started_time:<19} {cmdline:<50}"
    print(row)


def get_system_info():
    """Get system-wide information"""
    cpu_count = psutil.cpu_count()
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    boot_time = psutil.boot_time()

    print("=" * 120)
    print(f"SYSTEM INFORMATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 120)
    print(f"CPU Cores: {cpu_count} | CPU Usage: {cpu_percent}%")
    print(f"Memory: {format_memory(memory.used)} / {format_memory(memory.total)} ({memory.percent}% used)")
    print(f"Disk Usage: {format_memory(disk.used)} / {format_memory(disk.total)} ({(disk.used / disk.total * 100):.1f}% used)")
    print(f"System Boot Time: {format_time(boot_time)}")
    print()


def main():
    """Main function to display process information"""
    try:
        # Display system information
        get_system_info()

        # Get all processes
        print("PROCESS LIST")
        print("=" * 120)

        processes = []
        for proc in psutil.process_iter():
            info = get_process_info(proc)
            if info:
                processes.append(info)

        # Sort by CPU usage (descending)
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

        # Print header
        print_header()

        # Print each process
        for info in processes:
            print_process_row(info)

        # Summary statistics
        total_processes = len(processes)
        total_threads = sum(p['num_threads'] for p in processes)
        avg_cpu = sum(p['cpu_percent'] for p in processes) / total_processes if processes else 0

        print("\n" + "=" * 120)
        print(f"SUMMARY: {total_processes} processes, {total_threads} threads, Average CPU: {avg_cpu:.1f}%")
        print("=" * 120)

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")


def monitor_mode():
    """Continuous monitoring mode (updates every 5 seconds)"""
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
            main()
            print("\nPress Ctrl+C to exit. Refreshing in 5 seconds...")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


if __name__ == "__main__":
    import sys

    print("Process Monitor - Task Manager Style")
    print("Requirements: pip install psutil")
    print()

    try:
        import psutil
    except ImportError:
        print("Error: psutil library not found.")
        print("Please install it using: pip install psutil")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == '--monitor':
        print("Starting continuous monitoring mode...")
        monitor_mode()
    else:
        main()
        print("\nTip: Use --monitor flag for continuous monitoring mode")