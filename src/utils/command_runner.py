"""
Command execution utilities with support for multiple backends and MCP STDIO isolation.

This module provides a unified interface for executing command-line tools
with different underlying implementations (subprocess, plumbum, sh, etc.).
Currently only subprocess is implemented, but the architecture is ready
for extending to other third-party libraries.

Includes special STDIO isolation for Python commands to prevent MCP server conflicts.
"""

import logging
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import structlog

from src.log_utils import log_function_call
from src.utils.subprocess_stdio_fix import SubprocessSTDIOFix

logger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)


class CommandRunnerType(Enum):
    """Available command runner implementations."""

    SUBPROCESS = "subprocess"
    PLUMBUM = "plumbum"
    SH = "sh"
    INVOKE = "invoke"


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


class CommandRunner(ABC):
    """Abstract base class for command execution strategies."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._logger = structured_logger.bind(runner=name)

    @abstractmethod
    def execute(
        self, command: List[str], options: Optional[CommandOptions] = None
    ) -> CommandResult:
        """
        Execute a command with the given options.

        Args:
            command: Command and arguments as a list
            options: Execution options

        Returns:
            CommandResult with execution details
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this runner is available (dependencies installed, etc.)."""
        pass

    def _get_default_options(self) -> CommandOptions:
        """Get default command options."""
        return CommandOptions()


class SubprocessCommandRunner(CommandRunner):
    """Command runner using Python's built-in subprocess module with MCP STDIO isolation."""

    def __init__(self) -> None:
        super().__init__("subprocess")

    def is_available(self) -> bool:
        """Subprocess is always available."""
        return True

    @log_function_call
    def execute(
        self, command: List[str], options: Optional[CommandOptions] = None
    ) -> CommandResult:
        """Execute command using subprocess.run() with MCP STDIO isolation for Python commands."""
        # Validate command parameter
        if command is None:
            raise TypeError("Command cannot be None")

        if options is None:
            options = self._get_default_options()

        self._logger.debug(
            "Starting subprocess execution",
            command=command,
            cwd=options.cwd,
            timeout_seconds=options.timeout_seconds,
            env_keys=list(options.env.keys()) if options.env else None,
            is_python_command=SubprocessSTDIOFix.is_python_command(command),
        )

        start_time = time.time()

        try:
            # Use STDIO isolation for Python commands to prevent MCP conflicts
            if SubprocessSTDIOFix.is_python_command(command):
                self._logger.debug(
                    "Detected Python command, using STDIO isolation",
                    command_executable=command[0] if command else None,
                )

                process = SubprocessSTDIOFix.execute_with_stdio_isolation(
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
                self._logger.debug(
                    "Using regular subprocess execution for non-Python command",
                    command_executable=command[0] if command else None,
                )

                process = SubprocessSTDIOFix.execute_regular_subprocess(
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

            self._logger.debug(
                "Subprocess execution completed",
                return_code=process.returncode,
                stdout_length=len(process.stdout) if process.stdout else 0,
                stderr_length=len(process.stderr) if process.stderr else 0,
                stdout_preview=process.stdout[:200] if process.stdout else None,
                stderr_preview=process.stderr[:200] if process.stderr else None,
                execution_time_ms=execution_time_ms,
                used_stdio_isolation=SubprocessSTDIOFix.is_python_command(command),
            )

            return CommandResult(
                return_code=process.returncode,
                stdout=process.stdout or "",
                stderr=process.stderr or "",
                timed_out=False,
                command=command,
                runner_type=self.name,
                execution_time_ms=execution_time_ms,
            )

        except subprocess.TimeoutExpired:
            execution_time_ms = int((time.time() - start_time) * 1000)
            self._logger.error(
                "Subprocess execution timed out",
                timeout_seconds=options.timeout_seconds,
                command=command[:3],  # First few elements for security
                execution_time_ms=execution_time_ms,
                used_stdio_isolation=SubprocessSTDIOFix.is_python_command(command),
            )
            return CommandResult(
                return_code=1,
                stdout="",
                stderr="",
                timed_out=True,
                execution_error=f"Process timed out after {options.timeout_seconds} seconds",
                command=command,
                runner_type=self.name,
                execution_time_ms=execution_time_ms,
            )

        except FileNotFoundError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            self._logger.error(
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
                runner_type=self.name,
                execution_time_ms=execution_time_ms,
            )

        except PermissionError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            self._logger.error(
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
                runner_type=self.name,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            self._logger.error(
                "Subprocess execution failed with unexpected error",
                error=str(e),
                error_type=type(e).__name__,
                command_preview=command[:3] if command else None,
                used_stdio_isolation=SubprocessSTDIOFix.is_python_command(command),
            )
            return CommandResult(
                return_code=1,
                stdout="",
                stderr="",
                timed_out=False,
                execution_error=f"Unexpected error: {e}",
                command=command,
                runner_type=self.name,
                execution_time_ms=execution_time_ms,
            )


class CommandRunnerFactory:
    """Factory for creating command runners."""

    _runners: Dict[str, CommandRunner] = {}
    _default_runner_type = CommandRunnerType.SUBPROCESS

    @classmethod
    def register_runner(
        cls, runner_type: CommandRunnerType, runner: CommandRunner
    ) -> None:
        """Register a command runner."""
        cls._runners[runner_type.value] = runner

    @classmethod
    def get_runner(
        cls, runner_type: Optional[CommandRunnerType] = None
    ) -> CommandRunner:
        """Get a command runner instance."""
        if runner_type is None:
            runner_type = cls._default_runner_type

        runner_key = runner_type.value

        if runner_key not in cls._runners:
            # Lazy initialization
            if runner_type == CommandRunnerType.SUBPROCESS:
                cls._runners[runner_key] = SubprocessCommandRunner()
            else:
                # For future third-party runners, fall back to subprocess for now
                structured_logger.warning(
                    "Requested runner not yet implemented, falling back to subprocess",
                    requested_runner=runner_type.value,
                    fallback_runner="subprocess",
                )
                return cls.get_runner(CommandRunnerType.SUBPROCESS)

        runner = cls._runners[runner_key]

        # Check if runner is available
        if not runner.is_available():
            structured_logger.warning(
                "Requested runner not available, falling back to subprocess",
                requested_runner=runner_type.value,
                fallback_runner="subprocess",
            )
            return cls.get_runner(CommandRunnerType.SUBPROCESS)

        return runner

    @classmethod
    def set_default_runner(cls, runner_type: CommandRunnerType) -> None:
        """Set the default runner type."""
        cls._default_runner_type = runner_type

    @classmethod
    def get_available_runners(cls) -> List[CommandRunnerType]:
        """Get list of available runner types."""
        available = []
        for runner_type in CommandRunnerType:
            runner_key = runner_type.value

            # Check if runner is actually implemented (not just falling back)
            if runner_key in cls._runners:
                runner = cls._runners[runner_key]
                if runner.is_available():
                    available.append(runner_type)
            elif runner_type == CommandRunnerType.SUBPROCESS:
                # Subprocess is always available even if not yet instantiated
                available.append(runner_type)
            # Don't include other runner types that would just fall back to subprocess

        return available

    @classmethod
    def reset(cls) -> None:
        """Reset the factory (mainly for testing)."""
        cls._runners.clear()
        cls._default_runner_type = CommandRunnerType.SUBPROCESS


# Convenience functions for backward compatibility and ease of use
@log_function_call
def execute_command(
    command: List[str],
    cwd: Optional[str] = None,
    timeout_seconds: int = 120,
    env: Optional[Dict[str, str]] = None,
    runner_type: Optional[CommandRunnerType] = None,
) -> CommandResult:
    """
    Execute a command with the specified runner.

    This is a convenience function that maintains compatibility with the original
    execute_subprocess_with_timeout function while providing access to new runners.
    Now includes automatic STDIO isolation for Python commands in MCP contexts.

    Args:
        command: Complete command as list (e.g., ["python", "-m", "pylint", "--output-format=json", "src"])
        cwd: Working directory for subprocess
        timeout_seconds: Timeout in seconds
        env: Optional environment variables (inherits from current process if None)
        runner_type: Type of runner to use (defaults to subprocess)

    Returns:
        CommandResult with execution details and output
    """
    options = CommandOptions(
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        env=env,
    )

    runner = CommandRunnerFactory.get_runner(runner_type)
    return runner.execute(command, options)


# For backward compatibility - this matches the original function signature
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
    while using the new command runner infrastructure with MCP STDIO isolation.

    Args:
        command: Complete command as list (e.g., ["python", "-m", "pylint", "--output-format=json", "src"])
        cwd: Working directory for subprocess
        timeout_seconds: Timeout in seconds
        env: Optional environment variables (inherits from current process if None)

    Returns:
        CommandResult with execution details and output (compatible with SubprocessResult)
    """
    return execute_command(
        command=command,
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        env=env,
        runner_type=CommandRunnerType.SUBPROCESS,
    )


# Type alias for backward compatibility
SubprocessResult = CommandResult
