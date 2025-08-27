#!/usr/bin/env python3
"""
Automated test runner for VSCode support.
Run this to execute all VSCode-related tests.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ SUCCESS: {description}")
        if result.stdout:
            print("Output:", result.stdout[:200])
    else:
        print(f"❌ FAILED: {description}")
        if result.stderr:
            print("Error:", result.stderr[:500])
        if result.stdout:
            print("Output:", result.stdout[:500])

    return result.returncode == 0


def main():
    """Run all VSCode tests."""
    print("VSCode Support Test Runner")
    print("=" * 60)

    # Track results
    results = []

    # Test 1: Run VSCode handler tests
    results.append(
        run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_config/test_vscode_handler.py",
                "-v",
            ],
            "VSCode Handler Tests",
        )
    )

    # Test 2: Run VSCode CLI tests
    results.append(
        run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_config/test_vscode_cli.py",
                "-v",
            ],
            "VSCode CLI Tests",
        )
    )

    # Test 3: Run VSCode integration tests
    results.append(
        run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_config/test_vscode_integration.py",
                "-v",
            ],
            "VSCode Integration Tests",
        )
    )

    # Test 4: Run all config tests (to ensure no regression)
    results.append(
        run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_config/",
                "-k",
                "not slow",
                "--tb=short",
            ],
            "All Config Tests (Quick)",
        )
    )

    # Test 5: Check code style for new files
    vscode_files = [
        "tests/test_config/test_vscode_handler.py",
        "tests/test_config/test_vscode_cli.py",
    ]

    for file in vscode_files:
        if Path(file).exists():
            results.append(
                run_command(
                    [sys.executable, "-m", "pylint", file, "--errors-only"],
                    f"Pylint Check: {file}",
                )
            )

    # Test 6: Type checking
    for file in vscode_files:
        if Path(file).exists():
            results.append(
                run_command(
                    [sys.executable, "-m", "mypy", file, "--ignore-missing-imports"],
                    f"Type Check: {file}",
                )
            )

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if all(results):
        print("\n🎉 All tests passed! VSCode support is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
