"""Enhanced validation system for MCP server parameters.

This module provides comprehensive validation for all parameter types,
including path validation, choice validation, and auto-detection logic.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


def validate_path_exists(path: Path | str, param_name: str) -> list[str]:
    """Validate that a path exists.

    Args:
        path: Path to validate
        param_name: Parameter name for error messages

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []
    path_obj = Path(path) if isinstance(path, str) else path

    if not path_obj.exists():
        errors.append(f"Path for '{param_name}' does not exist: {path}")

    return errors


def validate_path_is_dir(path: Path | str, param_name: str) -> list[str]:
    """Validate that a path is a directory.

    Args:
        path: Path to validate
        param_name: Parameter name for error messages

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []
    path_obj = Path(path) if isinstance(path, str) else path

    if path_obj.exists() and not path_obj.is_dir():
        errors.append(f"Path for '{param_name}' is not a directory: {path}")

    return errors


def validate_path_is_file(path: Path | str, param_name: str) -> list[str]:
    """Validate that a path is a file.

    Args:
        path: Path to validate
        param_name: Parameter name for error messages

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []
    path_obj = Path(path) if isinstance(path, str) else path

    if path_obj.exists() and not path_obj.is_file():
        errors.append(f"Path for '{param_name}' is not a file: {path}")

    return errors


def validate_path_permissions(
    path: Path | str, param_name: str, mode: str = "r"
) -> list[str]:
    """Validate that we have the required permissions for a path.

    Args:
        path: Path to validate
        param_name: Parameter name for error messages
        mode: Permission mode to check ('r', 'w', 'x')

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []
    path_obj = Path(path) if isinstance(path, str) else path

    if not path_obj.exists():
        return errors  # Can't check permissions on non-existent path

    try:
        if mode == "r":
            if path_obj.is_file():
                with open(path_obj, "r"):
                    pass
            elif path_obj.is_dir():
                list(path_obj.iterdir())
        elif mode == "w":
            # Check write permission by trying to create a temp file
            if path_obj.is_dir():
                temp_file = path_obj / f".mcp_test_{os.getpid()}"
                try:
                    temp_file.touch()
                    temp_file.unlink()
                except (OSError, PermissionError):
                    errors.append(f"No write permission for '{param_name}': {path}")
            else:
                # For files, check parent directory write permission
                parent = path_obj.parent
                temp_file = parent / f".mcp_test_{os.getpid()}"
                try:
                    temp_file.touch()
                    temp_file.unlink()
                except (OSError, PermissionError):
                    errors.append(
                        f"No write permission for '{param_name}' parent directory: {parent}"
                    )
        elif mode == "x":
            if not os.access(path_obj, os.X_OK):
                errors.append(f"No execute permission for '{param_name}': {path}")
    except (OSError, PermissionError) as e:
        errors.append(f"Permission error for '{param_name}': {e}")

    return errors


def validate_python_executable(path: Path | str, param_name: str) -> list[str]:
    """Validate that a path points to a valid Python executable.

    Args:
        path: Path to Python executable
        param_name: Parameter name for error messages

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []
    path_str = str(path)

    # Check that file exists
    path_obj = Path(path_str)
    if not path_obj.exists():
        errors.append(f"Python executable for '{param_name}' does not exist: {path}")
        return errors

    # Check that it's executable
    if not os.access(path_obj, os.X_OK):
        errors.append(f"Python executable for '{param_name}' is not executable: {path}")
        return errors

    # Try to run it and get version
    import subprocess

    try:
        result = subprocess.run(
            [path_str, "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            errors.append(f"Python executable for '{param_name}' failed to run: {path}")
    except (subprocess.SubprocessError, OSError) as e:
        errors.append(f"Failed to validate Python executable for '{param_name}': {e}")

    return errors


def validate_venv_path(path: Path | str, param_name: str) -> list[str]:
    """Validate that a path points to a valid virtual environment.

    Args:
        path: Path to virtual environment
        param_name: Parameter name for error messages

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []
    venv_path = Path(path) if isinstance(path, str) else path

    if not venv_path.exists():
        errors.append(f"Virtual environment for '{param_name}' does not exist: {path}")
        return errors

    if not venv_path.is_dir():
        errors.append(
            f"Virtual environment path for '{param_name}' is not a directory: {path}"
        )
        return errors

    # Check for venv structure
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        activate = venv_path / "Scripts" / "activate.bat"
    else:
        python_exe = venv_path / "bin" / "python"
        activate = venv_path / "bin" / "activate"

    # Check for pyvenv.cfg (created by venv module)
    pyvenv_cfg = venv_path / "pyvenv.cfg"

    # Valid if has Python executable and either activate script or pyvenv.cfg
    if not python_exe.exists():
        errors.append(
            f"Virtual environment for '{param_name}' missing Python executable: {python_exe}"
        )

    if not (activate.exists() or pyvenv_cfg.exists()):
        errors.append(
            f"Virtual environment for '{param_name}' missing activation script or pyvenv.cfg"
        )

    return errors


def validate_log_level(value: str, param_name: str) -> list[str]:
    """Validate log level value.

    Args:
        value: Log level value
        param_name: Parameter name for error messages

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    if value.upper() not in valid_levels:
        errors.append(
            f"Invalid log level for '{param_name}': '{value}'. "
            f"Must be one of: {', '.join(valid_levels)}"
        )

    return errors


def normalize_path(path: Path | str, base_dir: Path | None = None) -> Path:
    """Normalize a path to absolute form.

    Args:
        path: Path to normalize
        base_dir: Base directory for relative paths (defaults to current directory)

    Returns:
        Normalized absolute path
    """
    path_obj = Path(path) if isinstance(path, str) else path

    if path_obj.is_absolute():
        return path_obj.resolve()

    if base_dir is None:
        base_dir = Path.cwd()

    return (base_dir / path_obj).resolve()


def auto_detect_python_executable(project_dir: Path) -> Path | None:
    """Auto-detect Python executable for a project.

    Args:
        project_dir: Project directory

    Returns:
        Path to Python executable, or None if not found
    """
    from src.config.detection import detect_python_environment

    python_exe, _ = detect_python_environment(project_dir)
    return Path(python_exe) if python_exe else None


def auto_detect_venv_path(project_dir: Path) -> Path | None:
    """Auto-detect virtual environment path for a project.

    Args:
        project_dir: Project directory

    Returns:
        Path to virtual environment, or None if not found
    """
    from src.config.detection import find_virtual_environments

    venvs = find_virtual_environments(project_dir)
    return venvs[0] if venvs else None


def auto_generate_log_file_path(project_dir: Path) -> Path:
    """Auto-generate a log file path with timestamp.

    Args:
        project_dir: Project directory

    Returns:
        Generated log file path
    """
    logs_dir = project_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"mcp_code_checker_{timestamp}.log"

    return log_file


def create_parameter_validator(
    param_type: str,
    required: bool = False,
    validate_exists: bool = False,
    validate_executable: bool = False,
    validate_venv: bool = False,
) -> Callable[[Any, str], list[str]]:
    """Create a validator function for a parameter.

    Args:
        param_type: Type of parameter
        required: Whether parameter is required
        validate_exists: Whether to validate path exists
        validate_executable: Whether to validate as executable
        validate_venv: Whether to validate as virtual environment

    Returns:
        Validator function
    """

    def validator(value: Any, param_name: str) -> list[str]:
        errors: list[str] = []

        # Skip validation if value is None and not required
        if value is None:
            if required:
                errors.append(f"Parameter '{param_name}' is required")
            return errors

        # Type-specific validation
        if param_type == "path":
            if not isinstance(value, (str, Path)):
                errors.append(
                    f"Parameter '{param_name}' must be a path, got {type(value).__name__}"
                )
                return errors

            path_obj = Path(value) if isinstance(value, str) else value

            if validate_exists:
                errors.extend(validate_path_exists(path_obj, param_name))

            if validate_executable:
                errors.extend(validate_python_executable(path_obj, param_name))

            if validate_venv:
                errors.extend(validate_venv_path(path_obj, param_name))

        elif param_type == "choice":
            # Choice validation is handled elsewhere
            pass

        elif param_type == "boolean":
            if not isinstance(value, bool):
                errors.append(
                    f"Parameter '{param_name}' must be boolean, got {type(value).__name__}"
                )

        elif param_type == "string":
            if not isinstance(value, str):
                try:
                    str(value)
                except (TypeError, ValueError) as e:
                    errors.append(
                        f"Parameter '{param_name}' cannot be converted to string: {e}"
                    )

        return errors

    return validator


def validate_parameter_combination(params: dict[str, Any]) -> list[str]:
    """Validate parameter combinations and dependencies.

    Args:
        params: Dictionary of parameter values

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []

    # If venv-path is specified, it takes precedence over python-executable
    if params.get("venv_path") and params.get("python_executable"):
        # This is just a warning, not an error
        pass  # Could add a warning system later

    # If console-only is true, log-file should not be used
    if params.get("console_only") and params.get("log_file"):
        # This is also just a warning
        pass  # Could add a warning system later

    # Project dir must exist if specified
    if params.get("project_dir"):
        project_dir = Path(params["project_dir"])
        if not project_dir.exists():
            errors.append(f"Project directory does not exist: {project_dir}")
        elif not project_dir.is_dir():
            errors.append(f"Project directory is not a directory: {project_dir}")

    return errors
