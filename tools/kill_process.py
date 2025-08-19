#!/usr/bin/env python3
"""
Process Killer Tool
Kill processes by matching command line patterns.
Usage: python kill_process.py [options] <command_pattern>
"""

import psutil
import argparse
import sys
import re
from typing import List, Optional


def find_processes_by_cmdline(pattern: str, exact_match: bool = False, case_sensitive: bool = False) -> List[psutil.Process]:
    """
    Find processes that match the given command line pattern.

    Args:
        pattern: Command line pattern to search for
        exact_match: If True, require exact match. If False, substring match.
        case_sensitive: If True, case-sensitive matching

    Returns:
        List of matching processes
    """
    matching_processes = []

    # Prepare pattern for matching
    search_pattern = pattern if case_sensitive else pattern.lower()

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
        try:
            cmdline = proc.info['cmdline']
            if not cmdline:
                continue

            # Join command line arguments into a single string
            full_cmdline = ' '.join(cmdline)

            # Prepare cmdline for comparison
            compare_cmdline = full_cmdline if case_sensitive else full_cmdline.lower()

            # Check if pattern matches
            if exact_match:
                if compare_cmdline == search_pattern:
                    matching_processes.append(proc)
            else:
                if search_pattern in compare_cmdline:
                    matching_processes.append(proc)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Process might have disappeared or we don't have access
            continue

    return matching_processes


def kill_processes(processes: List[psutil.Process], force: bool = False, dry_run: bool = False) -> int:
    """
    Kill the given processes.

    Args:
        processes: List of processes to kill
        force: If True, use SIGKILL (force kill). If False, use SIGTERM (graceful)
        dry_run: If True, only show what would be killed without actually killing

    Returns:
        Number of processes successfully killed
    """
    killed_count = 0

    for proc in processes:
        try:
            print(f"{'[DRY RUN] Would kill' if dry_run else 'Killing'} process:")
            print(f"  PID: {proc.pid}")
            print(f"  Name: {proc.name()}")
            print(f"  Command: {' '.join(proc.cmdline())}")

            if not dry_run:
                if force:
                    proc.kill()  # SIGKILL
                    print(f"  Status: Force killed")
                else:
                    proc.terminate()  # SIGTERM
                    print(f"  Status: Terminated (graceful)")

                killed_count += 1
            print()

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"  Error: {e}")
            print()

    return killed_count


def main():
    parser = argparse.ArgumentParser(
        description="Kill processes by command line pattern",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python kill_process.py "python.exe -m pytest"
  python kill_process.py --exact "C:\\path\\to\\python.exe -m pytest --trace-config"
  python kill_process.py --dry-run "pytest"
  python kill_process.py --force "hanging_process"
        """
    )

    parser.add_argument('pattern',
                        help='Command line pattern to match')
    parser.add_argument('--exact', '-e',
                        action='store_true',
                        help='Require exact match instead of substring match')
    parser.add_argument('--case-sensitive', '-c',
                        action='store_true',
                        help='Case-sensitive matching')
    parser.add_argument('--force', '-f',
                        action='store_true',
                        help='Force kill (SIGKILL) instead of graceful termination (SIGTERM)')
    parser.add_argument('--dry-run', '-d',
                        action='store_true',
                        help='Show what would be killed without actually killing')
    parser.add_argument('--confirm', '-y',
                        action='store_true',
                        help='Skip confirmation prompt')

    args = parser.parse_args()

    # Find matching processes
    print(f"Searching for processes matching: '{args.pattern}'")
    print(f"Match type: {'Exact' if args.exact else 'Substring'}")
    print(f"Case sensitive: {args.case_sensitive}")
    print("-" * 60)

    matching_processes = find_processes_by_cmdline(
        args.pattern,
        exact_match=args.exact,
        case_sensitive=args.case_sensitive
    )

    if not matching_processes:
        print("No matching processes found.")
        return 0

    print(f"Found {len(matching_processes)} matching process(es):")
    print()

    # Show what will be killed
    for i, proc in enumerate(matching_processes, 1):
        try:
            print(f"{i}. PID: {proc.pid}, Name: {proc.name()}")
            print(f"   Command: {' '.join(proc.cmdline())}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print(f"{i}. PID: {proc.pid} (process info not accessible)")
        print()

    # Confirmation (unless dry-run or --confirm flag)
    if not args.dry_run and not args.confirm:
        response = input("Do you want to kill these processes? [y/N]: ").strip().lower()
        if response not in ['y', 'yes']:
            print("Operation cancelled.")
            return 0

    # Kill processes
    print("-" * 60)
    killed_count = kill_processes(matching_processes, force=args.force, dry_run=args.dry_run)

    if args.dry_run:
        print(f"Dry run completed. Would have killed {len(matching_processes)} process(es).")
    else:
        print(f"Successfully killed {killed_count} out of {len(matching_processes)} process(es).")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)