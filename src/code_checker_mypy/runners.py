"""Runner for mypy type checking."""

import logging
import os
import sys
from pathlib import Path

import structlog

from log_utils import log_function_call
from utils.subprocess_runner import execute_command

from .models import MypyResult
from .parsers import parse_mypy_json_output

logger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)

# Default strict flags from tools/mypy.bat
STRICT_FLAGS = [
    "--strict",
    "--warn-redundant-casts",
    "--warn-unused-ignores",
    "--warn-unreachable",
    "--disallow-any-generics",
    "--disallow-untyped-defs",
    "--disallow-incomplete-defs",
    "--check-untyped-defs",
    "--disallow-untyped-decorators",
    "--no-implicit-optional",
    "--warn-return-any",
    "--no-implicit-reexport",
    "--strict-optional",
]


@log_function_call
def run_mypy_check(
    project_dir: str,
    strict: bool = True,
    disable_error_codes: list[str] | None = None,
    target_directories: list[str] | None = None,
    follow_imports: str = "normal",
    python_executable: str | None = None,
    cache_dir: str | None = None,
    config_file: str | None = None,
) -> MypyResult:
    """
    Run mypy type checking on project.

    Args:
        project_dir: Path to the project directory
        strict: Use strict mode settings (default: True)
        disable_error_codes: List of error codes to ignore (e.g., ['import', 'arg-type'])
        target_directories: Directories to check (default: ['src', 'tests'])
        follow_imports: How to handle imports ('normal', 'silent', 'skip', 'error')
        python_executable: Python interpreter to use (default: sys.executable)
        cache_dir: Custom cache directory for incremental checking
        config_file: Path to custom mypy config file

    Returns:
        MypyResult with execution results
    """
    if not os.path.isdir(project_dir):
        raise FileNotFoundError(f"Project directory not found: {project_dir}")

    # Convert to absolute path
    project_dir = os.path.abspath(project_dir)

    # Set default target directories
    if target_directories is None:
        target_directories = []
        for default_dir in ["src", "tests"]:
            dir_path = os.path.join(project_dir, default_dir)
            if os.path.exists(dir_path):
                target_directories.append(default_dir)

    # Validate target directories exist
    valid_directories = []
    for directory in target_directories:
        full_path = os.path.join(project_dir, directory)
        if os.path.exists(full_path):
            valid_directories.append(directory)
        else:
            structured_logger.warning("Target directory not found", directory=directory)

    if not valid_directories:
        return MypyResult(
            return_code=1, messages=[], error="No valid target directories found"
        )

    # Build command
    python_exe = python_executable or sys.executable
    command = [
        python_exe,
        "-m",
        "mypy",
        "--output",
        "json",
        "--no-color-output",
        "--show-column-numbers",
        "--show-error-codes",
    ]

    # Add strict flags if requested
    if strict:
        command.extend(STRICT_FLAGS)

    # Add config file if specified
    if config_file and os.path.exists(os.path.join(project_dir, config_file)):
        command.extend(["--config-file", config_file])

    # Add cache directory
    if cache_dir:
        command.extend(["--cache-dir", cache_dir])

    # Add follow imports setting
    command.extend(["--follow-imports", follow_imports])

    # Disable specific error codes
    if disable_error_codes:
        for code in disable_error_codes:
            command.extend(["--disable-error-code", code])

    # Add target directories
    command.extend(valid_directories)

    structured_logger.info(
        "Starting mypy check",
        project_dir=project_dir,
        strict=strict,
        targets=valid_directories,
        command=" ".join(command),
    )

    # Execute mypy
    result = execute_command(command=command, cwd=project_dir, timeout_seconds=120)

    # Handle execution errors
    if result.execution_error:
        return MypyResult(
            return_code=result.return_code, messages=[], error=result.execution_error
        )

    if result.timed_out:
        return MypyResult(
            return_code=1,
            messages=[],
            error="Mypy execution timed out after 120 seconds",
        )

    # Parse output
    messages, parse_error = parse_mypy_json_output(result.stdout)

    if parse_error:
        return MypyResult(
            return_code=result.return_code,
            messages=[],
            error=parse_error,
            raw_output=result.stdout,
        )

    # Count statistics
    errors_found = len([m for m in messages if m.severity == "error"])

    mypy_result = MypyResult(
        return_code=result.return_code,
        messages=messages,
        raw_output=result.stdout,
        errors_found=errors_found,
    )

    structured_logger.info(
        "Mypy check completed",
        return_code=result.return_code,
        total_messages=len(messages),
        errors=errors_found,
    )

    return mypy_result
