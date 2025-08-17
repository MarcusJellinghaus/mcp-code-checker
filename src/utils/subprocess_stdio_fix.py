"""
Subprocess STDIO fix for MCP servers.

This module provides STDIO isolation techniques to prevent Python subprocess
STDIO inheritance conflicts in MCP server contexts.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


class SubprocessSTDIOFix:
    """
    Handles subprocess execution with STDIO isolation for MCP servers.

    Prevents STDIO inheritance conflicts between MCP server and spawned Python processes.
    """

    @staticmethod
    def get_isolated_environment() -> dict[str, str]:
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

    @staticmethod
    def is_python_command(command: list[str]) -> bool:
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

    @staticmethod
    def execute_with_stdio_isolation(
        command: list[str],
        cwd: str | Path | None = None,
        timeout: float = 30.0,
        env: dict[str, str] | None = None,
        capture_output: bool = True,
        text: bool = True,
        shell: bool = False,
        input_data: str | None = None,
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
        isolated_env = SubprocessSTDIOFix.get_isolated_environment()

        # Merge with provided environment
        if env:
            isolated_env.update(env)

        logger.debug(
            "Executing Python command with STDIO isolation",
            command=command[:3],  # Log first few elements for security
            cwd=str(cwd) if cwd else None,
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
                        cwd=str(cwd) if cwd else None,
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

                # CRITICAL FIX: Read outputs while still within the temp directory context
                # Files must be read BEFORE the temp directory gets deleted
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

            # Create CompletedProcess-like result (outside temp dir context)
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
                cwd=str(cwd) if cwd else None,
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

    @staticmethod
    def execute_regular_subprocess(
        command: list[str],
        cwd: str | Path | None = None,
        timeout: float = 30.0,
        env: dict[str, str] | None = None,
        capture_output: bool = True,
        text: bool = True,
        shell: bool = False,
        input_data: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """
        Execute a non-Python command using regular subprocess.run().

        This is used for commands that don't need STDIO isolation.
        """
        logger.debug(
            "Executing regular command",
            command=command[:3],  # Log first few elements for security
            cwd=str(cwd) if cwd else None,
            timeout=timeout,
        )

        return subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
            env=env,
            shell=shell,
            input=input_data,
        )
