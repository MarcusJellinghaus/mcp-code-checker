"""
Utils package for shared utilities.

This package provides common utilities used across the codebase:
- subprocess_runner: Command execution with MCP STDIO isolation
- file_utils: File operation utilities
- data_files: Finding data files in development and installed environments
"""

# Import from data_files module
from .data_files import find_data_file, find_package_data_files, get_package_directory

# Import from file_utils module
from .file_utils import read_file

# Import from subprocess_runner module
from .subprocess_runner import (
    CommandOptions,
    CommandResult,
    execute_command,
    execute_subprocess,
    get_python_isolation_env,
    is_python_command,
)

__all__ = [
    # Data file utilities
    "find_data_file",
    "find_package_data_files",
    "get_package_directory",
    # Core subprocess functionality
    "CommandOptions",
    "CommandResult",
    "execute_command",
    "execute_subprocess",
    # Environment and utility functions
    "get_python_isolation_env",
    "is_python_command",
    # File utilities
    "read_file",
]
