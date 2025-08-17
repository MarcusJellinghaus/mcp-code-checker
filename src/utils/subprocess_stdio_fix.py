"""
Backward compatibility module for subprocess_stdio_fix.

This module maintains compatibility with existing code that imports from subprocess_stdio_fix.
All functionality has been moved to subprocess_runner.py.
"""

import subprocess
import warnings

# Import from the new location
from typing import Any, Dict, Optional

from .subprocess_runner import (
    execute_regular_subprocess,
    execute_with_stdio_isolation,
    get_isolated_environment,
    is_python_command,
)


class SubprocessSTDIOFix:
    """
    Backward compatibility class. All methods are now available as module-level functions
    in subprocess_runner.py.
    """

    def __init__(self) -> None:
        warnings.warn(
            "SubprocessSTDIOFix class is deprecated. "
            "Use module-level functions from subprocess_runner instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    @staticmethod
    def get_isolated_environment() -> dict[str, str]:
        """Backward compatibility wrapper."""
        return get_isolated_environment()

    @staticmethod
    def is_python_command(command: list[str]) -> bool:
        """Backward compatibility wrapper."""
        return is_python_command(command)

    @staticmethod
    def execute_with_stdio_isolation(
        command: list[str],
        cwd: Optional[str] = None,
        timeout: float = 30.0,
        env: Optional[dict[str, str]] = None,
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
        command: list[str],
        cwd: Optional[str] = None,
        timeout: float = 30.0,
        env: Optional[dict[str, str]] = None,
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


# Re-export for backward compatibility
__all__ = [
    "SubprocessSTDIOFix",
    "get_isolated_environment",
    "is_python_command",
    "execute_with_stdio_isolation",
    "execute_regular_subprocess",
]
