"""
Backward compatibility module for command_runner.

This module maintains compatibility with existing code that imports from command_runner.
All functionality has been moved to subprocess_runner.py.
"""

import warnings
from typing import TYPE_CHECKING, Optional, Dict, Any

# Import everything from the new location
from .subprocess_runner import (
    CommandOptions,
    CommandResult,
    SubprocessResult,
    execute_command,
    execute_subprocess_with_timeout,
    is_python_command,
    get_isolated_environment,
    execute_with_stdio_isolation,
    execute_regular_subprocess,
    execute_subprocess,
)

from enum import Enum


# Deprecated classes and enums for backward compatibility
class CommandRunnerType(Enum):
    """Deprecated: Command runner types are no longer used."""
    SUBPROCESS = "subprocess"
    PLUMBUM = "plumbum"
    SH = "sh"
    INVOKE = "invoke"


class CommandRunner:
    """Deprecated: Abstract base class no longer used."""
    
    def __init__(self, name: str) -> None:
        warnings.warn(
            "CommandRunner base class is deprecated. Use execute_subprocess() directly.",
            DeprecationWarning,
            stacklevel=2
        )
        self.name = name

    def execute(self, command: list[str], options: Optional[CommandOptions] = None) -> CommandResult:
        """Execute command using subprocess."""
        return execute_subprocess(command, options)

    def is_available(self) -> bool:
        """Always returns True for subprocess."""
        return True


class SubprocessCommandRunner(CommandRunner):
    """Deprecated: Use execute_subprocess() directly."""
    
    def __init__(self) -> None:
        warnings.warn(
            "SubprocessCommandRunner is deprecated. Use execute_subprocess() directly.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__("subprocess")


class CommandRunnerFactory:
    """Deprecated: Factory pattern no longer used."""
    
    _runners: Dict[CommandRunnerType, CommandRunner] = {}
    _default_runner_type = CommandRunnerType.SUBPROCESS

    @classmethod
    def register_runner(cls, runner_type: CommandRunnerType, runner: CommandRunner) -> None:
        """Deprecated: No longer used."""
        warnings.warn(
            "CommandRunnerFactory is deprecated. Use execute_subprocess() directly.",
            DeprecationWarning,
            stacklevel=2
        )
        # Store the runner for backward compatibility
        cls._runners[runner_type] = runner

    @classmethod
    def get_runner(cls, runner_type: Optional[CommandRunnerType] = None) -> CommandRunner:
        """Deprecated: Returns a compatibility wrapper."""
        warnings.warn(
            "CommandRunnerFactory is deprecated. Use execute_subprocess() directly.",
            DeprecationWarning,
            stacklevel=2
        )
        if runner_type is None:
            runner_type = cls._default_runner_type
        
        # Check if we have a registered runner
        if runner_type in cls._runners:
            return cls._runners[runner_type]
        
        # Create and cache a subprocess runner
        if CommandRunnerType.SUBPROCESS not in cls._runners:
            cls._runners[CommandRunnerType.SUBPROCESS] = SubprocessCommandRunner()
        
        # Return the subprocess runner for any type (fallback)
        return cls._runners[CommandRunnerType.SUBPROCESS]

    @classmethod
    def set_default_runner(cls, runner_type: CommandRunnerType) -> None:
        """Deprecated: No longer used."""
        warnings.warn(
            "CommandRunnerFactory is deprecated.",
            DeprecationWarning,
            stacklevel=2
        )
        cls._default_runner_type = runner_type

    @classmethod
    def get_available_runners(cls) -> list[CommandRunnerType]:
        """Deprecated: Always returns subprocess."""
        warnings.warn(
            "CommandRunnerFactory is deprecated.",
            DeprecationWarning,
            stacklevel=2
        )
        return [CommandRunnerType.SUBPROCESS]

    @classmethod
    def reset(cls) -> None:
        """Deprecated: No longer needed."""
        cls._runners.clear()
        cls._default_runner_type = CommandRunnerType.SUBPROCESS


# Re-export everything for backward compatibility
__all__ = [
    # New simplified API
    "CommandOptions",
    "CommandResult",
    "SubprocessResult",
    "execute_command",
    "execute_subprocess_with_timeout",
    "execute_subprocess",
    # Deprecated classes
    "CommandRunner",
    "SubprocessCommandRunner",
    "CommandRunnerFactory",
    "CommandRunnerType",
    # STDIO isolation functions
    "is_python_command",
    "get_isolated_environment",
    "execute_with_stdio_isolation",
    "execute_regular_subprocess",
]
