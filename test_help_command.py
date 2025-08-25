#!/usr/bin/env python3
"""Test script to demonstrate the new help command functionality."""

import subprocess
import sys


def run_command(cmd: list[str]) -> None:
    """Run a command and print the output."""
    print("\n" + "=" * 60)
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60 + "\n")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    print("\n")


def main():
    """Test various help command options."""
    
    # Test basic help for mcp-code-checker
    print("1. Basic help for mcp-code-checker:")
    run_command(["python", "-m", "src.config.main", "help", "mcp-code-checker"])
    
    # Test verbose help
    print("2. Verbose help with examples and auto-detection details:")
    run_command(["python", "-m", "src.config.main", "help", "mcp-code-checker", "--verbose"])
    
    # Test help for specific parameter
    print("3. Help for specific parameter (project-dir):")
    run_command(["python", "-m", "src.config.main", "help", "mcp-code-checker", "--parameter", "project-dir"])
    
    # Test quick reference
    print("4. Quick reference card:")
    run_command(["python", "-m", "src.config.main", "help", "mcp-code-checker", "--quick"])
    
    # Test help for all servers (if multiple exist)
    print("5. Help for all available servers:")
    run_command(["python", "-m", "src.config.main", "help", "--quick"])


if __name__ == "__main__":
    main()
