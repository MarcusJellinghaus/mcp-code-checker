"""Cross-platform path handling utilities for MCP Configuration Helper.

This module provides robust path normalization, validation, and handling
for Windows, macOS, and Linux platforms.
"""

import os
import platform
import sys
import unicodedata
from pathlib import Path
from typing import Optional


class PathConstants:
    """Platform-specific path constants and limits."""

    # Windows path limits
    WIN_MAX_PATH_CLASSIC = 260
    WIN_MAX_PATH_EXTENDED = 32767

    # Reserved Windows filenames
    WIN_RESERVED_NAMES = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    # Common virtual environment directory names
    VENV_NAMES = [
        "venv",
        ".venv",
        "env",
        ".env",
        "virtualenv",
        ".virtualenv",
        "ENV",
        ".ENV",
        "VENV",
        ".VENV",
    ]

    # Platform-specific Python executable names
    PYTHON_EXECUTABLES = {
        "win32": ["python.exe", "python3.exe", "py.exe"],
        "darwin": ["python3", "python", "python3.11", "python3.12", "python3.13"],
        "linux": ["python3", "python", "python3.11", "python3.12", "python3.13"],
    }


def get_platform_info() -> dict[str, str | bool]:
    """Get detailed platform information.

    Returns:
        Dictionary with platform details
    """
    return {
        "system": platform.system(),
        "platform": sys.platform,
        "version": platform.version(),
        "architecture": platform.machine(),
        "is_windows": sys.platform == "win32",
        "is_macos": sys.platform == "darwin",
        "is_linux": sys.platform.startswith("linux"),
        "is_wsl": (
            "microsoft" in platform.uname().release.lower()
            if hasattr(platform.uname(), "release")
            else False
        ),
    }


def normalize_path(
    path: str | Path,
    base_dir: Optional[Path] = None,
    expand_user: bool = True,
    resolve_symlinks: bool = True,
) -> Path:
    """Normalize paths for cross-platform compatibility.

    Args:
        path: Path to normalize
        base_dir: Base directory for relative paths
        expand_user: Whether to expand ~ to user home
        resolve_symlinks: Whether to resolve symbolic links

    Returns:
        Normalized absolute path
    """
    # Convert to Path object
    if isinstance(path, str):
        path = Path(path)

    # Expand user home directory
    if expand_user:
        path = path.expanduser()

    # Handle relative paths
    if not path.is_absolute():
        if base_dir:
            path = base_dir / path
        else:
            path = Path.cwd() / path

    # Resolve symlinks and normalize
    if resolve_symlinks:
        try:
            path = path.resolve()
        except (OSError, RuntimeError):
            # If resolve fails, at least make it absolute
            path = path.absolute()
    else:
        path = path.absolute()

    # Handle Windows-specific normalization
    if sys.platform == "win32":
        path = normalize_windows_path(path)

    # Handle macOS Unicode normalization
    elif sys.platform == "darwin":
        path = normalize_macos_path(path)

    return path


def normalize_windows_path(path: Path) -> Path:
    """Windows-specific path normalization.

    Args:
        path: Path to normalize

    Returns:
        Normalized Windows path
    """
    path_str = str(path)

    # Handle UNC paths
    if path_str.startswith("\\\\"):
        # Keep UNC format
        return Path(path_str)

    # Handle extended path prefix for long paths
    if len(path_str) > PathConstants.WIN_MAX_PATH_CLASSIC:
        if not path_str.startswith("\\\\?\\"):
            path_str = "\\\\?\\" + path_str

    # Ensure drive letter is uppercase
    if len(path_str) >= 2 and path_str[1] == ":":
        path_str = path_str[0].upper() + path_str[1:]

    return Path(path_str)


def normalize_macos_path(path: Path) -> Path:
    """macOS-specific path normalization.

    Handles Unicode normalization (NFD vs NFC) issues on macOS.

    Args:
        path: Path to normalize

    Returns:
        Normalized macOS path
    """
    # Normalize Unicode to NFC (Composed) form
    # macOS filesystem uses NFD but Python typically expects NFC
    path_str = unicodedata.normalize("NFC", str(path))
    return Path(path_str)


def validate_path(
    path: Path,
    path_type: str = "any",
    must_exist: bool = False,
    check_permissions: bool = False,
) -> tuple[bool, Optional[str]]:
    """Validate a path for platform-specific issues.

    Args:
        path: Path to validate
        path_type: Expected type ('file', 'directory', 'any')
        must_exist: Whether the path must exist
        check_permissions: Whether to check permissions

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check existence if required
    if must_exist and not path.exists():
        return False, f"Path does not exist: {path}"

    # Check path type
    if path.exists():
        if path_type == "file" and not path.is_file():
            return False, f"Path is not a file: {path}"
        elif path_type == "directory" and not path.is_dir():
            return False, f"Path is not a directory: {path}"

    # Platform-specific validation
    if sys.platform == "win32":
        is_valid, error = validate_windows_path(path)
        if not is_valid:
            return False, error

    # Check permissions if requested
    if check_permissions and path.exists():
        is_valid, error = check_path_permissions(path)
        if not is_valid:
            return False, error

    return True, None


def validate_windows_path(path: Path) -> tuple[bool, Optional[str]]:
    """Validate Windows-specific path constraints.

    Args:
        path: Path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    path_str = str(path)

    # Check path length
    if (
        not path_str.startswith("\\\\?\\")
        and len(path_str) > PathConstants.WIN_MAX_PATH_CLASSIC
    ):
        return (
            False,
            f"Path exceeds Windows MAX_PATH limit ({PathConstants.WIN_MAX_PATH_CLASSIC} chars)",
        )

    # Check for reserved names
    name = path.name.upper()
    base_name = name.split(".")[0] if "." in name else name
    if base_name in PathConstants.WIN_RESERVED_NAMES:
        return False, f"Path contains Windows reserved name: {name}"

    # Check for invalid characters
    invalid_chars = '<>:"|?*'
    if path.drive:
        # Remove drive from check
        check_str = str(path).replace(path.drive, "", 1)
    else:
        check_str = path_str

    for char in invalid_chars:
        if char in check_str and not (char == ":" and check_str.index(char) == 1):
            return False, f"Path contains invalid Windows character: {char}"

    return True, None


def check_path_permissions(path: Path) -> tuple[bool, Optional[str]]:
    """Check if we have necessary permissions for a path.

    Args:
        path: Path to check

    Returns:
        Tuple of (has_permissions, error_message)
    """
    try:
        if path.is_file():
            # Check read permission
            if not os.access(path, os.R_OK):
                return False, f"No read permission for file: {path}"

            # Check if we need write permission (for config files)
            parent = path.parent
            if not os.access(parent, os.W_OK):
                return False, f"No write permission for directory: {parent}"

        elif path.is_dir():
            # Check read and execute permissions for directories
            if not os.access(path, os.R_OK | os.X_OK):
                return False, f"No read/execute permission for directory: {path}"

            # Check write permission if needed
            if not os.access(path, os.W_OK):
                return False, f"No write permission for directory: {path}"

        return True, None

    except OSError as e:
        return False, f"Permission check failed: {e}"


def find_case_insensitive_path(path: Path) -> Optional[Path]:
    """Find a path with case-insensitive matching (for case-insensitive filesystems).

    Args:
        path: Path to find

    Returns:
        Actual path if found, None otherwise
    """
    if path.exists():
        return path

    # Only relevant for case-insensitive filesystems
    if sys.platform not in ("win32", "darwin"):
        return None

    # Try to find the path by walking up to an existing parent
    parts = path.parts
    existing_path = Path(parts[0]) if parts else Path(".")

    for part in parts[1:]:
        if not existing_path.exists():
            return None

        # Look for case-insensitive match
        found = False
        if existing_path.is_dir():
            for item in existing_path.iterdir():
                if item.name.lower() == part.lower():
                    existing_path = item
                    found = True
                    break

        if not found:
            return None

    return existing_path if existing_path != path and existing_path.exists() else None


def get_safe_path_for_platform(
    base_name: str, directory: Path, extension: str = ""
) -> Path:
    """Generate a safe filename for the current platform.

    Args:
        base_name: Base name for the file
        directory: Directory where file will be created
        extension: File extension (including dot)

    Returns:
        Safe path for the platform
    """
    # Remove/replace invalid characters
    if sys.platform == "win32":
        # Windows invalid characters
        invalid_chars = '<>:"|?*\\/:'
        for char in invalid_chars:
            base_name = base_name.replace(char, "_")

        # Check reserved names
        if base_name.upper() in PathConstants.WIN_RESERVED_NAMES:
            base_name = f"_{base_name}"
    else:
        # Unix-like systems - mainly avoid null and /
        base_name = base_name.replace("\0", "_").replace("/", "_")

    # Construct path
    full_path = directory / f"{base_name}{extension}"

    # Check length on Windows
    if (
        sys.platform == "win32"
        and len(str(full_path)) > PathConstants.WIN_MAX_PATH_CLASSIC
    ):
        # Truncate base name to fit
        max_base_len = (
            PathConstants.WIN_MAX_PATH_CLASSIC
            - len(str(directory))
            - len(extension)
            - 2
        )
        base_name = base_name[:max_base_len]
        full_path = directory / f"{base_name}{extension}"

    return full_path


def ensure_parent_directory(path: Path, mode: int = 0o755) -> None:
    """Ensure parent directory exists with proper permissions.

    Args:
        path: Path whose parent directory should exist
        mode: Directory permissions (Unix-style, ignored on Windows)

    Raises:
        OSError: If directory cannot be created
    """
    parent = path.parent

    if not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True, mode=mode)
        except OSError as e:
            # Try to provide more helpful error message
            if (
                sys.platform == "win32"
                and len(str(parent)) > PathConstants.WIN_MAX_PATH_CLASSIC
            ):
                raise OSError(
                    f"Cannot create directory - path too long ({len(str(parent))} chars). "
                    f"Windows MAX_PATH limit is {PathConstants.WIN_MAX_PATH_CLASSIC} chars. "
                    f"Consider using shorter paths or enabling long path support."
                ) from e
            else:
                raise


def get_relative_path_safe(path: Path, base: Path) -> Path:
    """Get relative path, with fallback to absolute if not possible.

    Args:
        path: Path to make relative
        base: Base path

    Returns:
        Relative path if possible, otherwise absolute path
    """
    try:
        return path.relative_to(base)
    except ValueError:
        # Paths don't share a common base
        return path.absolute()
