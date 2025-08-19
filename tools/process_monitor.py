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


def print_process_row(info: Dict[str, Any], indent_level: int = 0):
    """Print a single process row with tree indentation"""
    memory_mb = info['memory_info'].rss / (1024 * 1024)
    started_time = format_time(info['create_time'])
    cmdline = info['cmdline'][:47] + "..." if len(info['cmdline']) > 50 else info['cmdline']

    # Create tree indentation
    tree_prefix = "  " * indent_level
    if indent_level > 0:
        tree_prefix += "└─ "

    # Adjust name field to account for tree indentation
    name_field_width = max(25 - len(tree_prefix), 10)
    process_name = tree_prefix + info['name'][:name_field_width]

    row = f"{info['pid']:<8} {process_name:<25} {info['status']:<12} {info['type']:<15} {info['cpu_percent']:<8.1f} {info['memory_percent']:<10.1f} {memory_mb:<12.1f} {info['num_threads']:<8} {info['username'][:12]:<15} {started_time:<19} {cmdline:<50}"
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


def build_process_tree(processes: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """Build a process tree structure"""
    # Create lookup dictionaries
    process_dict = {p['pid']: p for p in processes}
    children_dict = {}

    # Initialize children dict
    for proc in processes:
        children_dict[proc['pid']] = []

    # Build parent-child relationships
    for proc in processes:
        parent_pid = proc['parent_pid']
        if parent_pid and parent_pid in children_dict:
            children_dict[parent_pid].append(proc)
        elif parent_pid not in process_dict:
            # Parent not in our process list, treat as root
            if None not in children_dict:
                children_dict[None] = []
            children_dict[None].append(proc)

    return children_dict


def print_process_tree(children_dict: Dict[int, List[Dict[str, Any]]],
                       process_dict: Dict[int, Dict[str, Any]],
                       parent_pid: int = None,
                       indent_level: int = 0,
                       visited: set = None):
    """Recursively print the process tree"""
    if visited is None:
        visited = set()

    if parent_pid in visited:
        return  # Avoid infinite loops

    if parent_pid is not None:
        visited.add(parent_pid)

    # Get children of current parent
    children = children_dict.get(parent_pid, [])

    # Sort children by CPU usage (descending)
    children.sort(key=lambda x: x['cpu_percent'], reverse=True)

    for child in children:
        child_pid = child['pid']

        # Print the current process
        print_process_row(child, indent_level)

        # Recursively print children
        if child_pid in children_dict and children_dict[child_pid]:
            print_process_tree(children_dict, process_dict, child_pid,
                               indent_level + 1, visited.copy())


def find_root_processes(processes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find processes that are roots (no parent in our process list)"""
    process_pids = {p['pid'] for p in processes}
    roots = []

    for proc in processes:
        parent_pid = proc['parent_pid']
        if parent_pid is None or parent_pid not in process_pids:
            roots.append(proc)

    return roots


def main(tree_view: bool = False):
    """Main function to display process information"""
    try:
        # Display system information
        get_system_info()

        # Get all processes
        if tree_view:
            print("PROCESS TREE VIEW")
        else:
            print("PROCESS LIST")
        print("=" * 120)

        processes = []
        for proc in psutil.process_iter():
            info = get_process_info(proc)
            if info:
                processes.append(info)

        # Print header
        print_header()

        if tree_view:
            # Build process tree
            process_dict = {p['pid']: p for p in processes}
            children_dict = build_process_tree(processes)

            # Find and display root processes first
            root_processes = find_root_processes(processes)
            root_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

            # Print tree starting from roots
            for root in root_processes:
                print_process_tree(children_dict, process_dict, root['pid'], 0)

            # Print orphaned processes (those with parents not in our list)
            orphaned = children_dict.get(None, [])
            if orphaned:
                print("\n" + "-" * 120)
                print("ORPHANED PROCESSES (parent not in current process list)")
                print("-" * 120)
                for proc in sorted(orphaned, key=lambda x: x['cpu_percent'], reverse=True):
                    print_process_row(proc, 0)
        else:
            # Sort by CPU usage (descending) for flat view
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

            # Print each process
            for info in processes:
                print_process_row(info)

        # Summary statistics
        total_processes = len(processes)
        total_threads = sum(p['num_threads'] for p in processes)
        avg_cpu = sum(p['cpu_percent'] for p in processes) / total_processes if processes else 0

        print("\n" + "=" * 120)
        print(f"SUMMARY: {total_processes} processes, {total_threads} threads, Average CPU: {avg_cpu:.1f}%")
        if tree_view:
            root_count = len(find_root_processes(processes))
            print(f"Root processes: {root_count}")
        print("=" * 120)

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")


def monitor_mode(tree_view: bool = False):
    """Continuous monitoring mode (updates every 5 seconds)"""
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
            main(tree_view)
            print(f"\nPress Ctrl+C to exit. Refreshing in 5 seconds... (Mode: {'Tree' if tree_view else 'List'})")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
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

    # Parse command line arguments
    tree_view = '--tree' in sys.argv
    monitor = '--monitor' in sys.argv

    if monitor:
        print(f"Starting continuous monitoring mode ({'Tree' if tree_view else 'List'} view)...")
        monitor_mode(tree_view)
    else:
        main(tree_view)
        print("\nAvailable options:")
        print("  --tree     : Show processes in tree view (grouped by parent-child)")
        print("  --monitor  : Continuous monitoring mode (refreshes every 5 seconds)")
        print("  --tree --monitor : Tree view with continuous monitoring")