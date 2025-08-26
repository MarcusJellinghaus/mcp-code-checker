"""Simplified validation system for MCP server parameters."""

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def validate_path(
    path: Path | str, 
    param_name: str, 
    must_exist: bool = False,
    must_be_dir: bool = False,
    must_be_file: bool = False,
    check_permissions: str | None = None
) -> list[str]:
    """Unified path validation function.

    Args:
        path: Path to validate
        param_name: Parameter name for error messages
        must_exist: Whether path must exist
        must_be_dir: Whether path must be a directory
        must_be_file: Whether path must be a file
        check_permissions: Permission mode to check ('r', 'w', 'x')

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []
    path_obj = Path(path) if isinstance(path, str) else path

    # Existence check
    if must_exist and not path_obj.exists():
        errors.append(f"Path for '{param_name}' does not exist: {path}")
        return errors  # No point checking other properties if doesn't exist
    
    # Type checks (only if path exists)
    if path_obj.exists():
        if must_be_dir and not path_obj.is_dir():
            errors.append(f"Path for '{param_name}' is not a directory: {path}")
        elif must_be_file and not path_obj.is_file():
            errors.append(f"Path for '{param_name}' is not a file: {path}")
        
        # Permission checks
        if check_permissions:
            try:
                if check_permissions == "r" and not os.access(path_obj, os.R_OK):
                    errors.append(f"No read permission for '{param_name}': {path}")
                elif check_permissions == "w" and not os.access(path_obj, os.W_OK):
                    errors.append(f"No write permission for '{param_name}': {path}")
                elif check_permissions == "x" and not os.access(path_obj, os.X_OK):
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
    path_obj = Path(path_str)

    # Check existence and executable permission
    path_errors = validate_path(
        path_obj, param_name, must_exist=True, must_be_file=True, check_permissions="x"
    )
    if path_errors:
        return path_errors

    # Try to run it and get version
    try:
        result = subprocess.run(
            [path_str, "--version"], capture_output=True, text=True, timeout=5, check=False
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

    # Check basic path requirements
    path_errors = validate_path(venv_path, param_name, must_exist=True, must_be_dir=True)
    if path_errors:
        return path_errors

    # Check for venv structure
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"

    if not python_exe.exists():
        errors.append(
            f"Virtual environment for '{param_name}' missing Python executable: {python_exe}"
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
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if value.upper() not in valid_levels:
        return [
            f"Invalid log level for '{param_name}': '{value}'. "
            f"Must be one of: {', '.join(valid_levels)}"
        ]
    return []


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
    return logs_dir / f"mcp_code_checker_{timestamp}.log"


def validate_server_configuration(
    server_name: str,
    server_type: str,
    params: dict[str, Any],
    client_handler: Any | None = None,
) -> dict[str, Any]:
    """Simplified validation of server configuration.

    Args:
        server_name: Name of the server
        server_type: Type of server (e.g., 'mcp-code-checker')
        params: Server parameters
        client_handler: Optional client handler for config validation

    Returns:
        Dictionary with validation results
    """
    checks = []
    errors = []
    warnings = []

    # Configuration existence check
    if client_handler:
        servers = client_handler.list_all_servers()
        server_names = [s["name"] for s in servers]
        if server_name in server_names:
            checks.append({
                "status": "success",
                "message": "Configuration found"
            })
        else:
            checks.append({
                "status": "error",
                "message": f"Server '{server_name}' not found in configuration"
            })
            errors.append(f"Server '{server_name}' not found")

    # Project directory validation
    if "project_dir" in params and params["project_dir"]:
        project_dir = Path(params["project_dir"])
        path_errors = validate_path(
            project_dir, "project_dir", must_exist=True, must_be_dir=True
        )
        
        if not path_errors:
            checks.append({
                "status": "success",
                "message": f"Project directory exists: {project_dir}"
            })
        else:
            checks.append({
                "status": "error",
                "message": path_errors[0]
            })
            errors.extend(path_errors)

    # Python executable validation
    if "python_executable" in params and params["python_executable"]:
        python_exe = Path(params["python_executable"])
        exe_errors = validate_python_executable(python_exe, "python_executable")
        
        if not exe_errors:
            checks.append({
                "status": "success",
                "message": f"Python executable found: {python_exe.name}"
            })
        else:
            checks.append({
                "status": "error",
                "message": exe_errors[0]
            })
            errors.extend(exe_errors)

    # Virtual environment validation (if specified)
    if "venv_path" in params and params["venv_path"]:
        venv_path = Path(params["venv_path"])
        venv_errors = validate_venv_path(venv_path, "venv_path")

        if not venv_errors:
            checks.append({
                "status": "success",
                "message": f"Virtual environment found: {venv_path.name}"
            })
        else:
            checks.append({
                "status": "warning",
                "message": f"Virtual environment issue: {venv_path.name}"
            })
            warnings.extend(venv_errors)

    # Test folder check for mcp-code-checker
    if server_type == "mcp-code-checker" and "project_dir" in params and params["project_dir"]:
        project_dir = Path(params["project_dir"])
        test_folder = params.get("test_folder", "tests")
        test_path = project_dir / test_folder
        
        if test_path.exists() and test_path.is_dir():
            checks.append({
                "status": "success",
                "message": f"Test folder exists: {test_folder}"
            })
        else:
            checks.append({
                "status": "warning",
                "message": f"Test folder missing: {test_folder}"
            })
            warnings.append(f"Test folder '{test_folder}' not found")

    return {
        "success": len(errors) == 0,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }


def validate_parameter_combination(params: dict[str, Any]) -> list[str]:
    """Validate parameter combinations and dependencies.

    Args:
        params: Dictionary of parameter values

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []

    # Project dir must exist if specified
    if params.get("project_dir"):
        project_dir = Path(params["project_dir"])
        if not project_dir.exists():
            errors.append(f"Project directory does not exist: {project_dir}")
        elif not project_dir.is_dir():
            errors.append(f"Project directory is not a directory: {project_dir}")

    return errors


def validate_client_installation(client: str) -> list[str]:
    """Check if the target client is installed.
    
    Args:
        client: Client name to check
    
    Returns:
        List of warnings (empty if client is detected)
    """
    warnings = []
    
    if client.startswith("vscode"):
        # Check if VSCode is installed
        vscode_commands = ["code", "code-insiders", "codium"]
        vscode_found = False
        
        for cmd in vscode_commands:
            if shutil.which(cmd):
                vscode_found = True
                break
        
        if not vscode_found:
            warnings.append(
                "VSCode not detected. Please ensure VSCode 1.102+ is installed "
                "for native MCP support."
            )
        
        # Check for workspace config location if using workspace mode
        if client in ["vscode", "vscode-workspace"]:
            if not Path(".vscode").exists():
                warnings.append(
                    "No .vscode directory found. It will be created for workspace configuration."
                )
    
    elif client == "claude-desktop":
        # Check for Claude Desktop (platform-specific checks could be added here)
        pass
    
    return warnings
