#!/usr/bin/env python3
"""Test script to demonstrate the enhanced help command functionality."""

import subprocess
import sys


def run_command(cmd: list[str], description: str) -> None:
    """Run a command and print the output."""
    print("\n" + "=" * 70)
    print(f"TEST: {description}")
    print(f"CMD:  {' '.join(cmd)}")
    print("=" * 70 + "\n")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # Show just first 30 lines for long outputs
    lines = result.stdout.split('\n')
    if len(lines) > 30:
        print("[... Output truncated for brevity ...]")
    print("\n")


def main():
    """Test various help command options."""
    
    print("ENHANCED HELP SYSTEM TEST")
    print("=" * 70)
    
    # Test 1: Tool overview
    run_command(
        ["python", "-m", "src.config.main", "help"],
        "Tool Overview (no arguments)"
    )
    
    # Test 2: Help for setup command
    run_command(
        ["python", "-m", "src.config.main", "help", "setup"],
        "Help for 'setup' command"
    )
    
    # Test 3: Verbose help for setup command
    run_command(
        ["python", "-m", "src.config.main", "help", "setup", "--verbose"],
        "Verbose help for 'setup' command"
    )
    
    # Test 4: Help for remove command
    run_command(
        ["python", "-m", "src.config.main", "help", "remove"],
        "Help for 'remove' command"
    )
    
    # Test 5: Help for list command
    run_command(
        ["python", "-m", "src.config.main", "help", "list"],
        "Help for 'list' command"
    )
    
    # Test 6: Help for validate command
    run_command(
        ["python", "-m", "src.config.main", "help", "validate"],
        "Help for 'validate' command"
    )
    
    # Test 7: Help for init command
    run_command(
        ["python", "-m", "src.config.main", "help", "init"],
        "Help for 'init' command"
    )
    
    # Test 8: Help for server parameters
    run_command(
        ["python", "-m", "src.config.main", "help", "mcp-code-checker"],
        "Help for mcp-code-checker server parameters"
    )
    
    # Test 9: Quick reference for server
    run_command(
        ["python", "-m", "src.config.main", "help", "mcp-code-checker", "--quick"],
        "Quick reference for mcp-code-checker"
    )
    
    # Test 10: Help for specific parameter
    run_command(
        ["python", "-m", "src.config.main", "help", "mcp-code-checker", "--parameter", "project-dir"],
        "Help for specific parameter (project-dir)"
    )
    
    # Test 11: Help for the help command itself
    run_command(
        ["python", "-m", "src.config.main", "help", "help"],
        "Help for the 'help' command"
    )
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("The help system now covers both:")
    print("  1. mcp-config tool commands (setup, remove, list, etc.)")
    print("  2. Server-specific parameters (project-dir, log-level, etc.)")
    print("=" * 70)


if __name__ == "__main__":
    main()
