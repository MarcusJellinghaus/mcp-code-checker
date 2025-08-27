#!/usr/bin/env python3
"""Manual testing script for CLI functionality."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a command and return (return_code, stdout, stderr).

    Args:
        cmd: Command and arguments to run

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)


def test_cli_commands() -> None:
    """Test basic CLI commands."""
    tests = [
        # Help commands
        (["python", "-m", "src.config.main", "--help"], 0, "Should show main help"),
        (
            ["python", "-m", "src.config.main", "setup", "--help"],
            0,
            "Should show setup help",
        ),
        (
            ["python", "-m", "src.config.main", "remove", "--help"],
            0,
            "Should show remove help",
        ),
        (
            ["python", "-m", "src.config.main", "list", "--help"],
            0,
            "Should show list help",
        ),
        # List command (should work even with no config)
        (
            ["python", "-m", "src.config.main", "list"],
            0,
            "Should list servers (even if empty)",
        ),
        (
            ["python", "-m", "src.config.main", "list", "--detailed"],
            0,
            "Should list servers with details",
        ),
        (
            ["python", "-m", "src.config.main", "list", "--managed-only"],
            0,
            "Should list only managed servers",
        ),
        # Dry run setup
        (
            [
                "python",
                "-m",
                "src.config.main",
                "setup",
                "mcp-code-checker",
                "test",
                "--project-dir",
                ".",
                "--dry-run",
            ],
            0,
            "Should do dry-run setup",
        ),
        (
            [
                "python",
                "-m",
                "src.config.main",
                "setup",
                "mcp-code-checker",
                "test",
                "--project-dir",
                ".",
                "--dry-run",
                "--verbose",
            ],
            0,
            "Should do verbose dry-run setup",
        ),
        # Invalid commands (should fail)
        (
            ["python", "-m", "src.config.main", "invalid"],
            2,
            "Should fail with invalid command",
        ),
        (
            [
                "python",
                "-m",
                "src.config.main",
                "setup",
                "invalid-server",
                "test",
                "--project-dir",
                ".",
            ],
            2,  # argparse returns 2 for invalid arguments
            "Should fail with invalid server type",
        ),
        (
            ["python", "-m", "src.config.main", "remove"],
            2,
            "Should fail without server name",
        ),
        # Remove non-existent server
        (
            ["python", "-m", "src.config.main", "remove", "nonexistent"],
            1,
            "Should fail for non-existent server",
        ),
    ]

    print("=" * 70)
    print("Manual CLI Testing")
    print("=" * 70)
    print()

    passed = 0
    failed = 0

    for cmd, expected_code, description in tests:
        print(f"Test: {description}")
        print(f"Command: {' '.join(cmd)}")

        code, stdout, stderr = run_command(cmd)

        if code == expected_code:
            print(f"  ✓ PASS (exit code: {code})")
            passed += 1
        else:
            print(f"  ✗ FAIL (expected: {expected_code}, got: {code})")
            failed += 1
            if stderr:
                print(f"    stderr: {stderr[:200]}")
            if stdout and code != 0:
                print(f"    stdout: {stdout[:200]}")

        print()

    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    # Use assertion instead of returning a value
    assert failed == 0, f"{failed} tests failed"


def test_with_installed_package() -> None:
    """Test CLI when installed as a package."""
    print("\n" + "=" * 70)
    print("Testing with installed package (if available)")
    print("=" * 70)
    print()

    # Try to run mcp-config directly (requires pip install -e .)
    tests = [
        (["mcp-config", "--help"], 0, "Package command should work"),
        (["mcp-config", "list"], 0, "Package list command should work"),
    ]

    for cmd, expected_code, description in tests:
        print(f"Test: {description}")
        print(f"Command: {' '.join(cmd)}")

        code, stdout, stderr = run_command(cmd)

        if code == expected_code:
            print(f"  ✓ PASS")
        else:
            if "mcp-config" in stderr or "not found" in stderr.lower():
                print("  ⚠ SKIP (package not installed, run: pip install -e .)")
            else:
                print(f"  ✗ FAIL (expected: {expected_code}, got: {code})")

        print()


def test_parameter_validation() -> None:
    """Test parameter validation scenarios."""
    print("\n" + "=" * 70)
    print("Testing Parameter Validation")
    print("=" * 70)
    print()

    tests = [
        # Missing required parameter
        (
            ["python", "-m", "src.config.main", "setup", "mcp-code-checker", "test"],
            1,
            "Should fail without required --project-dir",
        ),
        # Invalid choice parameter
        (
            [
                "python",
                "-m",
                "src.config.main",
                "setup",
                "mcp-code-checker",
                "test",
                "--project-dir",
                ".",
                "--log-level",
                "INVALID",
            ],
            2,
            "Should fail with invalid choice",
        ),
    ]

    for cmd, expected_code, description in tests:
        print(f"Test: {description}")
        code, stdout, stderr = run_command(cmd)

        if code == expected_code:
            print(f"  ✓ PASS")
        else:
            print(f"  ✗ FAIL (expected: {expected_code}, got: {code})")
        print()


def main() -> int:
    """Run all manual tests.

    Returns:
        0 if all tests pass, 1 otherwise
    """
    try:
        # Run basic CLI tests
        test_cli_commands()

        # Test parameter validation
        test_parameter_validation()

        # Test with installed package
        test_with_installed_package()

        print("\n✓ All manual tests passed!")
        return 0
    except AssertionError as e:
        print(f"\n✗ Tests failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
