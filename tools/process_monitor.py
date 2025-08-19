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


def print_header(cmdline_length: int = 50):
    """Print the table header"""
    if cmdline_length == -1:
        header = f"{'PID':<8} {'Name':<25} {'Status':<12} {'Type':<15} {'CPU%':<8} {'Memory%':<10} {'Memory':<12} {'Threads':<8} {'User':<15} {'Started':<19} {'Command Line'}"
    else:
        header = f"{'PID':<8} {'Name':<25} {'Status':<12} {'Type':<15} {'CPU%':<8} {'Memory%':<10} {'Memory':<12} {'Threads':<8} {'User':<15} {'Started':<19} {'Command Line':<{cmdline_length}}"
    print(header)
    print("-" * len(header))


def print_process_row(info: Dict[str, Any], indent_level: int = 0, cmdline_length: int = 50):
    """Print a single process row with tree indentation"""
    memory_mb = info['memory_info'].rss / (1024 * 1024)
    started_time = format_time(info['create_time'])

    # Handle command line truncation based on cmdline_length parameter
    if cmdline_length == -1:  # No truncation
        cmdline = info['cmdline']
    else:
        truncate_at = cmdline_length - 3  # Leave room for "..."
        cmdline = info['cmdline'][:truncate_at] + "..." if len(info['cmdline']) > cmdline_length else info['cmdline']

    # Create tree indentation
    tree_prefix = "  " * indent_level
    if indent_level > 0:
        tree_prefix += "└─ "

    # Adjust name field to account for tree indentation
    name_field_width = max(25 - len(tree_prefix), 10)
    process_name = tree_prefix + info['name'][:name_field_width]

    # Format the row - adjust command line field width
    if cmdline_length == -1:
        # No truncation - let command line extend naturally
        row = f"{info['pid']:<8} {process_name:<25} {info['status']:<12} {info['type']:<15} {info['cpu_percent']:<8.1f} {info['memory_percent']:<10.1f} {memory_mb:<12.1f} {info['num_threads']:<8} {info['username'][:12]:<15} {started_time:<19} {cmdline}"
    else:
        row = f"{info['pid']:<8} {process_name:<25} {info['status']:<12} {info['type']:<15} {info['cpu_percent']:<8.1f} {info['memory_percent']:<10.1f} {memory_mb:<12.1f} {info['num_threads']:<8} {info['username'][:12]:<15} {started_time:<19} {cmdline:<{cmdline_length}}"

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
                       visited: set = None,
                       cmdline_length: int = 50):
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
        print_process_row(child, indent_level, cmdline_length)

        # Recursively print children
        if child_pid in children_dict and children_dict[child_pid]:
            print_process_tree(children_dict, process_dict, child_pid,
                               indent_level + 1, visited.copy(), cmdline_length)


def find_root_processes(processes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find processes that are roots (no parent in our process list)"""
    process_pids = {p['pid'] for p in processes}
    roots = []

    for proc in processes:
        parent_pid = proc['parent_pid']
        if parent_pid is None or parent_pid not in process_pids:
            roots.append(proc)

    return roots


def main(tree_view: bool = False, cmdline_length: int = 50, command_line_filter: str = None):
    """Main function to display process information
    
    Args:
        tree_view: Whether to show processes in tree view
        cmdline_length: Maximum length for command line display (-1 for no truncation)
        command_line_filter: Filter string to only show processes with this text in their command line
    """
    try:
        # Display system information
        get_system_info()

        # Get all processes
        if tree_view:
            print("PROCESS TREE VIEW")
        else:
            print("PROCESS LIST")

        if command_line_filter:
            print(f"(Filtering by command line containing: '{command_line_filter}')")
        
        if cmdline_length == -1:
            print("(Command lines shown in full - no truncation)")
        elif cmdline_length != 50:
            print(f"(Command lines truncated at {cmdline_length} characters)")

        print("=" * 120)

        processes = []
        for proc in psutil.process_iter():
            info = get_process_info(proc)
            if info:
                # Apply command line filter if specified
                if command_line_filter:
                    if command_line_filter.lower() in info['cmdline'].lower():
                        processes.append(info)
                else:
                    processes.append(info)

        # Print header
        print_header(cmdline_length)

        if tree_view:
            # Build process tree
            process_dict = {p['pid']: p for p in processes}
            children_dict = build_process_tree(processes)

            # Find and display root processes first
            root_processes = find_root_processes(processes)
            root_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

            # Print tree starting from roots
            for root in root_processes:
                print_process_tree(children_dict, process_dict, root['pid'], 0, None, cmdline_length)

            # Print orphaned processes (those with parents not in our list)
            orphaned = children_dict.get(None, [])
            if orphaned:
                print("\n" + "-" * 120)
                print("ORPHANED PROCESSES (parent not in current process list)")
                print("-" * 120)
                for proc in sorted(orphaned, key=lambda x: x['cpu_percent'], reverse=True):
                    print_process_row(proc, 0, cmdline_length)
        else:
            # Sort by CPU usage (descending) for flat view
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

            # Print each process
            for info in processes:
                print_process_row(info, 0, cmdline_length)

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


def monitor_mode(tree_view: bool = False, cmdline_length: int = 50, command_line_filter: str = None):
    """Continuous monitoring mode (updates every 5 seconds)
    
    Args:
        tree_view: Whether to show processes in tree view
        cmdline_length: Maximum length for command line display (-1 for no truncation)
        command_line_filter: Filter string to only show processes with this text in their command line
    """
    try:
        while True:
            # Capture the new output first
            output_buffer = []
            
            # Redirect stdout to capture the output
            import io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            try:
                # Generate the new output
                main(tree_view, cmdline_length, command_line_filter)
                filter_info = f" | Filter: '{command_line_filter}'" if command_line_filter else ""
                print(f"\nPress Ctrl+C to exit. Refreshing in 5 seconds... (Mode: {'Tree' if tree_view else 'List'}{filter_info})")
                
                # Capture the complete output
                output = sys.stdout.getvalue()
            finally:
                # Restore stdout
                sys.stdout = old_stdout
            
            # Now clear the screen and display the new output
            os.system('cls' if os.name == 'nt' else 'clear')
            print(output, end='')  # Print without extra newline
            
            # Wait for the next refresh
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

    # Handle command line length options
    cmdline_length = 50  # default
    if '--full-cmd' in sys.argv:
        cmdline_length = -1  # no truncation
    elif '--long-cmd' in sys.argv:
        cmdline_length = 100  # double length
    elif '--cmd-length' in sys.argv:
        # Custom length: --cmd-length 150
        try:
            idx = sys.argv.index('--cmd-length')
            if idx + 1 < len(sys.argv):
                cmdline_length = int(sys.argv[idx + 1])
            else:
                print("Error: --cmd-length requires a number")
                sys.exit(1)
        except (ValueError, IndexError):
            print("Error: --cmd-length requires a valid number")
            sys.exit(1)
    
    # Handle command line filter option
    command_line_filter = None
    if '--filter' in sys.argv:
        try:
            idx = sys.argv.index('--filter')
            if idx + 1 < len(sys.argv):
                command_line_filter = sys.argv[idx + 1]
            else:
                print("Error: --filter requires a filter string")
                sys.exit(1)
        except IndexError:
            print("Error: --filter requires a filter string")
            sys.exit(1)

    if monitor:
        print(f"Starting continuous monitoring mode ({'Tree' if tree_view else 'List'} view)...")
        if command_line_filter:
            print(f"Filtering processes with command line containing: '{command_line_filter}'")
        if cmdline_length == -1:
            print("Command lines will be shown in full (no truncation)")
        elif cmdline_length != 50:
            print(f"Command lines will be truncated at {cmdline_length} characters")
        monitor_mode(tree_view, cmdline_length, command_line_filter)
    else:
        main(tree_view, cmdline_length, command_line_filter)
        print("\nAvailable options:")
        print("  --tree        : Show processes in tree view (grouped by parent-child)")
        print("  --monitor     : Continuous monitoring mode (refreshes every 5 seconds)")
        print("  --filter STR  : Only show processes with STR in their command line")
        print("  --full-cmd    : Show full command lines (no truncation)")
        print("  --long-cmd    : Show longer command lines (100 chars vs default 50)")
        print("  --cmd-length N: Custom command line length (e.g., --cmd-length 150)")
        print("\nExamples:")
        print("  python -m tools.process_monitor --filter python")
        print("  python -m tools.process_monitor --tree --filter java --full-cmd")
        print("  python -m tools.process_monitor --monitor --filter chrome")
        print("  python -m tools.process_monitor --tree --cmd-length 200")