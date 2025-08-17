"""
Subprocess execution utilities with MCP STDIO isolation support.

This module provides functions for executing command-line tools with proper
timeout handling and STDIO isolation for Python commands in MCP server contexts.
"""

import logging
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import structlog

from src.log_utils import log_function_call

logger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)


@dataclass
class CommandResult:
    """Represents the result of a command execution."""

    return_code: int
    stdout: str
    stderr: str
    timed_out: bool
    execution_error: Optional[str] = None
    command: Optional[List[str]] = field(default=None)
    runner_type: Optional[str] = field(default=None)
    execution_time_ms: Optional[int] = field(default=None)


@dataclass
class CommandOptions:
    """Configuration options for command execution."""

    cwd: Optional[str] = None
    timeout_seconds: int = 120
    env: Optional[Dict[str, str]] = None
    capture_output: bool = True
    text: bool = True
    check: bool = False
    shell: bool = False
    input_data: Optional[str] = None


def get_isolated_environment() -> Dict[str, str]:
    """
    Creates an environment dictionary that isolates Python subprocess from MCP STDIO.

    Returns:
        Environment dictionary with STDIO isolation settings
    """
    env = os.environ.copy()

    # Critical: Prevent Python subprocess from inheriting MCP's STDIO pipes
    env.update(
        {
            # Force Python to use unbuffered output
            "PYTHONUNBUFFERED": "1",
            # Prevent Python from trying to detect terminal capabilities
            "PYTHONDONTWRITEBYTECODE": "1",
            # Ensure UTF-8 encoding consistency
            "PYTHONIOENCODING": "utf-8",
            # Disable Python startup optimizations that might interfere
            "PYTHONNOUSERSITE": "1",
            # Prevent interactive mode detection
            "PYTHONHASHSEED": "0",
            # Clear any existing Python path complications
            "PYTHONSTARTUP": "",
        }
    )

    # Remove MCP-specific environment variables that might confuse subprocess
    mcp_vars_to_remove = [
        "MCP_STDIO_TRANSPORT",
        "MCP_SERVER_NAME",
        "MCP_CLIENT_PARAMS",
    ]

    for var in mcp_vars_to_remove:
        env.pop(var, None)

    return env


def is_python_command(command: List[str]) -> bool:
    """
    Determine if a command is a Python execution command.

    Args:
        command: Command list to check

    Returns:
        True if this is a Python command that needs STDIO isolation
    """
    if not command:
        return False

    # Check if the first element is a Python executable
    python_executables = ["python", "python3", "python.exe", "python3.exe"]
    executable = Path(command[0]).name.lower()

    # Direct Python executable
    if executable in python_executables:
        return True

    # Check if it's sys.executable (absolute path)
    if command[0] == sys.executable:
        return True

    # Check for python -m module execution
    if (
        len(command) >= 3
        and executable in python_executables
        and command[1] == "-m"
    ):
        return True

    return False


def execute_with_stdio_isolation(
    command: List[str],
    cwd: Optional[str] = None,
    timeout: float = 30.0,
    env: Optional[Dict[str, str]] = None,
    capture_output: bool = True,
    text: bool = True,
    shell: bool = False,
    input_data: Optional[str] = None,
) -> subprocess.CompletedProcess[str]:
    """
    Execute a Python command with complete STDIO isolation.

    Args:
        command: Command to execute
        cwd: Working directory
        timeout: Execution timeout in seconds
        env: Environment variables (will be enhanced with isolation settings)
        capture_output: Whether to capture stdout/stderr
        text: Whether to return text output
        shell: Whether to use shell execution
        input_data: Input data to pass to subprocess

    Returns:
        CompletedProcess with captured output

    Raises:
        subprocess.TimeoutExpired: If execution exceeds timeout
        subprocess.CalledProcessError: If subprocess returns non-zero exit code
    """
    # Get isolated environment
    isolated_env = get_isolated_environment()

    # Merge with provided environment
    if env:
        isolated_env.update(env)

    structured_logger.debug(
        "Executing Python command with STDIO isolation",
        command=command[:3],  # Log first few elements for security
        cwd=cwd,
        timeout=timeout,
        python_env_vars=[
            "PYTHONUNBUFFERED",
            "PYTHONIOENCODING",
            "PYTHONNOUSERSITE",
        ],
    )

    # Method 1: File-based STDIO (most reliable for MCP context)
    if capture_output:
        with tempfile.TemporaryDirectory() as temp_dir:
            stdout_file = Path(temp_dir) / "stdout.txt"
            stderr_file = Path(temp_dir) / "stderr.txt"

            # Execute with files for STDIO
            with (
                open(stdout_file, "w", encoding="utf-8") as stdout_f,
                open(stderr_file, "w", encoding="utf-8") as stderr_f,
            ):

                stdin_input = (
                    subprocess.DEVNULL if input_data is None else subprocess.PIPE
                )

                process = subprocess.run(
                    command,
                    cwd=cwd,
                    stdout=stdout_f,
                    stderr=stderr_f,
                    stdin=stdin_input,  # Critical: Prevent STDIN inheritance
                    text=text,
                    timeout=timeout,
                    env=isolated_env,
                    shell=shell,
                    input=input_data,
                    # Prevent any STDIO inheritance
                    start_new_session=True,  # Creates new process group
                )

            # Read outputs while still within the temp directory context
            stdout_content = (
                stdout_file.read_text(encoding="utf-8")
                if stdout_file.exists()
                else ""
            )
            stderr_content = (
                stderr_file.read_text(encoding="utf-8")
                if stderr_file.exists()
                else ""
            )

        # Create CompletedProcess-like result
        return subprocess.CompletedProcess(
            args=command,
            returncode=process.returncode,
            stdout=stdout_content,
            stderr=stderr_content,
        )
    else:
        # Method 2: Direct execution without capture
        stdin_input = subprocess.DEVNULL if input_data is None else subprocess.PIPE

        return subprocess.run(
            command,
            cwd=cwd,
            stdout=None,
            stderr=None,
            stdin=stdin_input,
            text=text,
            timeout=timeout,
            env=isolated_env,
            shell=shell,
            input=input_data,
            start_new_session=True,
            # Additional isolation on Unix systems
            preexec_fn=os.setsid if hasattr(os, "setsid") else None,
        )


def execute_regular_subprocess(
    command: List[str],
    cwd: Optional[str] = None,
    timeout: float = 30.0,
    env: Optional[Dict[str, str]] = None,
    capture_output: bool = True,
    text: bool = True,
    shell: bool = False,
    input_data: Optional[str] = None,
) -> subprocess.CompletedProcess[str]:
    """
    Execute a non-Python command using regular subprocess.run().

    This is used for commands that don't need STDIO isolation.
    """
    structured_logger.debug(
        "Executing regular command",
        command=command[:3],  # Log first few elements for security
        cwd=cwd,
        timeout=timeout,
    )

    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
        env=env,
        shell=shell,
        input=input_data,
    )


@log_function_call
def execute_subprocess(
    command: List[str],
    options: Optional[CommandOptions] = None
) -> CommandResult:
    """
    Execute a command with automatic STDIO isolation for Python commands.

    Args:
        command: Command and arguments as a list
        options: Execution options

    Returns:
        CommandResult with execution details
    """
    # Validate command parameter
    if command is None:
        raise TypeError("Command cannot be None")

    if options is None:
        options = CommandOptions()

    structured_logger.debug(
        "Starting subprocess execution",
        command=command,
        cwd=options.cwd,
        timeout_seconds=options.timeout_seconds,
        env_keys=list(options.env.keys()) if options.env else None,
        is_python_command=is_python_command(command),
    )

    start_time = time.time()

    try:
        # Use STDIO isolation for Python commands to prevent MCP conflicts
        if is_python_command(command):
            structured_logger.debug(
                "Detected Python command, using STDIO isolation",
                command_executable=command[0] if command else None,
            )

            process = execute_with_stdio_isolation(
                command=command,
                cwd=options.cwd,
                timeout=options.timeout_seconds,
                env=options.env,
                capture_output=options.capture_output,
                text=options.text,
                shell=options.shell,
                input_data=options.input_data,
            )
        else:
            # Use regular subprocess for non-Python commands
            structured_logger.debug(
                "Using regular subprocess execution for non-Python command",
                command_executable=command[0] if command else None,
            )

            process = execute_regular_subprocess(
                command=command,
                cwd=options.cwd,
                timeout=options.timeout_seconds,
                env=options.env,
                capture_output=options.capture_output,
                text=options.text,
                shell=options.shell,
                input_data=options.input_data,
            )

        # Handle check parameter (raise exception on non-zero exit)
        if options.check and process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, command, process.stdout, process.stderr
            )

        execution_time_ms = int((time.time() - start_time) * 1000)

        structured_logger.debug(
            "Subprocess execution completed",
            return_code=process.returncode,
            stdout_length=len(process.stdout) if process.stdout else 0,
            stderr_length=len(process.stderr) if process.stderr else 0,
            stdout_preview=process.stdout[:200] if process.stdout else None,
            stderr_preview=process.stderr[:200] if process.stderr else None,
            execution_time_ms=execution_time_ms,
            used_stdio_isolation=is_python_command(command),
        )

        return CommandResult(
            return_code=process.returncode,
            stdout=process.stdout or "",
            stderr=process.stderr or "",
            timed_out=False,
            command=command,
            runner_type="subprocess",
            execution_time_ms=execution_time_ms,
        )

    except subprocess.TimeoutExpired:
        execution_time_ms = int((time.time() - start_time) * 1000)
        structured_logger.error(
            "Subprocess execution timed out",
            timeout_seconds=options.timeout_seconds,
            command=command[:3],  # First few elements for security
            execution_time_ms=execution_time_ms,
            used_stdio_isolation=is_python_command(command),
        )
        return CommandResult(
            return_code=1,
            stdout="",
            stderr="",
            timed_out=True,
            execution_error=f"Process timed out after {options.timeout_seconds} seconds",
            command=command,
            runner_type="subprocess",
            execution_time_ms=execution_time_ms,
        )

    except FileNotFoundError as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        structured_logger.error(
            "Subprocess executable not found",
            command_executable=command[0] if command else None,
            error=str(e),
        )
        return CommandResult(
            return_code=1,
            stdout="",
            stderr="",
            timed_out=False,
            execution_error=f"Executable not found: {e}",
            command=command,
            runner_type="subprocess",
            execution_time_ms=execution_time_ms,
        )

    except PermissionError as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        structured_logger.error(
            "Subprocess permission error",
            command_executable=command[0] if command else None,
            error=str(e),
        )
        return CommandResult(
            return_code=1,
            stdout="",
            stderr="",
            timed_out=False,
            execution_error=f"Permission error: {e}",
            command=command,
            runner_type="subprocess",
            execution_time_ms=execution_time_ms,
        )

    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        structured_logger.error(
            "Subprocess execution failed with unexpected error",
            error=str(e),
            error_type=type(e).__name__,
            command_preview=command[:3] if command else None,
            used_stdio_isolation=is_python_command(command),
        )
        return CommandResult(
            return_code=1,
            stdout="",
            stderr="",
            timed_out=False,
            execution_error=f"Unexpected error: {e}",
            command=command,
            runner_type="subprocess",
            execution_time_ms=execution_time_ms,
        )


# Convenience functions for backward compatibility
@log_function_call
def execute_command(
    command: List[str],
    cwd: Optional[str] = None,
    timeout_seconds: int = 120,
    env: Optional[Dict[str, str]] = None,
    runner_type: Optional[str] = None,  # Kept for backward compatibility but ignored
) -> CommandResult:
    """
    Execute a command with automatic STDIO isolation for Python commands.

    Args:
        command: Complete command as list (e.g., ["python", "-m", "pylint", "src"])
        cwd: Working directory for subprocess
        timeout_seconds: Timeout in seconds
        env: Optional environment variables (inherits from current process if None)
        runner_type: Ignored, kept for backward compatibility

    Returns:
        CommandResult with execution details and output
    """
    options = CommandOptions(
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        env=env,
    )

    return execute_subprocess(command, options)


@log_function_call
def execute_subprocess_with_timeout(
    command: List[str],
    cwd: Optional[str] = None,
    timeout_seconds: int = 120,
    env: Optional[Dict[str, str]] = None,
) -> CommandResult:
    """
    Execute a subprocess with proper timeout and error handling.

    This function maintains backward compatibility with the original implementation
    while providing automatic STDIO isolation for Python commands in MCP contexts.

    Args:
        command: Complete command as list (e.g., ["python", "-m", "pylint", "src"])
        cwd: Working directory for subprocess
        timeout_seconds: Timeout in seconds
        env: Optional environment variables (inherits from current process if None)

    Returns:
        CommandResult with execution details and output
    """
    return execute_command(
        command=command,
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        env=env,
    )


# Type alias for backward compatibility
SubprocessResult = CommandResult


# Classes kept for backward compatibility but simplified
class SubprocessSTDIOFix:
    """
    Backward compatibility class. Methods are now module-level functions.
    """

    @staticmethod
    def get_isolated_environment() -> Dict[str, str]:
        """Backward compatibility wrapper."""
        return get_isolated_environment()

    @staticmethod
    def is_python_command(command: List[str]) -> bool:
        """Backward compatibility wrapper."""
        return is_python_command(command)

    @staticmethod
    def execute_with_stdio_isolation(
        command: List[str],
        cwd: Optional[str] = None,
        timeout: float = 30.0,
        env: Optional[Dict[str, str]] = None,
        capture_output: bool = True,
        text: bool = True,
        shell: bool = False,
        input_data: Optional[str] = None,
    ) -> subprocess.CompletedProcess[str]:
        """Backward compatibility wrapper."""
        return execute_with_stdio_isolation(
            command=command,
            cwd=cwd,
            timeout=timeout,
            env=env,
            capture_output=capture_output,
            text=text,
            shell=shell,
            input_data=input_data,
        )

    @staticmethod
    def execute_regular_subprocess(
        command: List[str],
        cwd: Optional[str] = None,
        timeout: float = 30.0,
        env: Optional[Dict[str, str]] = None,
        capture_output: bool = True,
        text: bool = True,
        shell: bool = False,
        input_data: Optional[str] = None,
    ) -> subprocess.CompletedProcess[str]:
        """Backward compatibility wrapper."""
        return execute_regular_subprocess(
            command=command,
            cwd=cwd,
            timeout=timeout,
            env=env,
            capture_output=capture_output,
            text=text,
            shell=shell,
            input_data=input_data,
        )
