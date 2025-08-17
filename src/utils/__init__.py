"""
Utils package for shared utilities.

This package provides common utilities used across the codebase:
- subprocess_runner: Command execution with MCP STDIO isolation
- file_utils: File operation utilities
- command_runner: Backward compatibility (deprecated)
- subprocess_stdio_fix: Backward compatibility (deprecated)
"""

# Import deprecated modules for backward compatibility
from .command_runner import (
    CommandRunner,
    CommandRunnerFactory,
    CommandRunnerType,
    SubprocessCommandRunner,
)
from .file_utils import (
    read_file,
)

# Import from new modules
from .subprocess_runner import (
    CommandOptions,
    CommandResult,
    SubprocessResult,
    execute_command,
    execute_subprocess,
    execute_subprocess_with_timeout,
)
from .subprocess_stdio_fix import SubprocessSTDIOFix

__all__ = [
    # Core subprocess functionality
    "CommandOptions",
    "CommandResult",
    "SubprocessResult",
    "execute_command",
    "execute_subprocess_with_timeout",
    "execute_subprocess",
    # File utilities
    "read_file",
    # Deprecated classes (for backward compatibility)
    "CommandRunner",
    "SubprocessCommandRunner",
    "CommandRunnerFactory",
    "CommandRunnerType",
    "SubprocessSTDIOFix",
]
