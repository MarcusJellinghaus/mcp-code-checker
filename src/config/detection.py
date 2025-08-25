"""Auto-detection utilities for Python environments and executables.

This module provides functions to automatically detect Python executables,
virtual environments, and validate Python installations.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


def detect_python_environment(
    project_dir: Path,
) -> tuple[Optional[str], Optional[str]]:
    """Auto-detect Python executable and virtual environment.

    Args:
        project_dir: Project directory to search for virtual environments

    Returns:
        Tuple of (python_executable, venv_path)
    """
    # First, look for virtual environments in the project
    venvs = find_virtual_environments(project_dir)

    if venvs:
        # Use the first valid venv found
        venv_path = venvs[0]
        python_exe = get_venv_python(venv_path)
        if python_exe and validate_python_executable(str(python_exe)):
            return str(python_exe), str(venv_path)

    # If no venv found or venv Python is invalid, use current Python
    current_python = sys.executable
    if validate_python_executable(current_python):
        return current_python, None

    # As a last resort, try to find Python in PATH
    python_cmd = "python3" if sys.platform != "win32" else "python"
    try:
        result = subprocess.run(
            [python_cmd, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Get the full path to this Python
            result = subprocess.run(
                [python_cmd, "-c", "import sys; print(sys.executable)"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                python_path = result.stdout.strip()
                if validate_python_executable(python_path):
                    return python_path, None
    except (subprocess.SubprocessError, OSError):
        pass

    return None, None


def find_virtual_environments(project_dir: Path) -> list[Path]:
    """Find all potential virtual environments in project directory.

    Args:
        project_dir: Directory to search

    Returns:
        List of virtual environment paths found
    """
    venv_paths = []

    # Common virtual environment directory names
    common_names = [
        "venv",
        ".venv",
        "env",
        ".env",
        "virtualenv",
        ".virtualenv",
    ]

    # Check for common venv directories
    for name in common_names:
        venv_dir = project_dir / name
        if is_valid_venv(venv_dir):
            venv_paths.append(venv_dir)

    # Also check for conda environments (if conda is installed)
    conda_env = project_dir / "conda-env"
    if is_valid_conda_env(conda_env):
        venv_paths.append(conda_env)

    # Check for pipenv
    pipfile = project_dir / "Pipfile"
    if pipfile.exists():
        # Try to get pipenv venv path
        try:
            result = subprocess.run(
                ["pipenv", "--venv"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                pipenv_path = Path(result.stdout.strip())
                if is_valid_venv(pipenv_path):
                    venv_paths.append(pipenv_path)
        except (subprocess.SubprocessError, OSError):
            pass

    return venv_paths


def is_valid_venv(venv_path: Path) -> bool:
    """Check if a path is a valid virtual environment.

    Args:
        venv_path: Path to check

    Returns:
        True if it's a valid virtual environment
    """
    if not venv_path.exists() or not venv_path.is_dir():
        return False

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
    return python_exe.exists() and (activate.exists() or pyvenv_cfg.exists())


def is_valid_conda_env(conda_path: Path) -> bool:
    """Check if a path is a valid conda environment.

    Args:
        conda_path: Path to check

    Returns:
        True if it's a valid conda environment
    """
    if not conda_path.exists() or not conda_path.is_dir():
        return False

    # Check for conda-meta directory (conda-specific)
    conda_meta = conda_path / "conda-meta"
    if not conda_meta.exists():
        return False

    # Check for Python executable
    if sys.platform == "win32":
        python_exe = conda_path / "python.exe"
    else:
        python_exe = conda_path / "bin" / "python"

    return python_exe.exists()


def get_venv_python(venv_path: Path) -> Optional[Path]:
    """Get the Python executable path from a virtual environment.

    Args:
        venv_path: Path to the virtual environment

    Returns:
        Path to Python executable, or None if not found
    """
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"

    if python_exe.exists():
        return python_exe

    return None


def validate_python_executable(python_path: str) -> bool:
    """Validate that a Python executable path is valid and working.

    Args:
        python_path: Path to Python executable

    Returns:
        True if valid, False otherwise
    """
    if not python_path or not Path(python_path).exists():
        return False

    try:
        # Try to run Python and get version
        result = subprocess.run(
            [python_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def get_python_info(python_path: str) -> dict[str, Any]:
    """Get information about a Python executable.

    Args:
        python_path: Path to Python executable

    Returns:
        Dictionary with version, platform, etc.
    """
    info: dict[str, Any] = {
        "executable": python_path,
        "valid": False,
    }

    if not validate_python_executable(python_path):
        return info

    try:
        # Get detailed Python information
        code = """
import sys
import platform
import json

info = {
    'version': sys.version,
    'version_info': list(sys.version_info),
    'platform': platform.platform(),
    'implementation': platform.python_implementation(),
    'architecture': platform.machine(),
    'prefix': sys.prefix,
    'base_prefix': getattr(sys, 'base_prefix', sys.prefix),
    'executable': sys.executable,
    'is_venv': hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
}
print(json.dumps(info))
"""
        result = subprocess.run(
            [python_path, "-c", code],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            py_info = json.loads(result.stdout)
            info.update(py_info)
            info["valid"] = True

    except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
        pass

    return info


def find_project_python_executable(project_dir: Path) -> Optional[str]:
    """Find the best Python executable for a project.

    This is a convenience function that combines environment detection
    with validation.

    Args:
        project_dir: Project directory

    Returns:
        Path to Python executable, or None if not found
    """
    python_exe, _ = detect_python_environment(project_dir)
    return python_exe


def get_project_dependencies(project_dir: Path) -> list[str]:
    """Get list of project dependencies from various sources.

    Args:
        project_dir: Project directory

    Returns:
        List of dependency specifications
    """
    dependencies = []

    # Check for requirements.txt
    requirements_files = [
        "requirements.txt",
        "requirements-dev.txt",
        "requirements.in",
        "dev-requirements.txt",
    ]

    for req_file in requirements_files:
        req_path = project_dir / req_file
        if req_path.exists():
            try:
                with open(req_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            dependencies.append(line)
            except IOError:
                pass

    # Check for pyproject.toml
    pyproject_path = project_dir / "pyproject.toml"
    if pyproject_path.exists():
        tomllib: Any = None
        try:
            import tomllib  # type: ignore[assignment]  # Python 3.11+
        except ImportError:
            try:
                import tomli  # type: ignore[import-not-found]  # Fallback for older Python

                tomllib = tomli  # type: ignore[assignment]
            except ImportError:
                pass

        if tomllib:
            try:
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    # Get dependencies from various sections
                    if "project" in data:
                        if "dependencies" in data["project"]:
                            dependencies.extend(data["project"]["dependencies"])
                        if "optional-dependencies" in data["project"]:
                            for group in data["project"][
                                "optional-dependencies"
                            ].values():
                                dependencies.extend(group)
            except (IOError, KeyError, tomllib.TOMLDecodeError):
                pass

    # Check for setup.py (basic parsing)
    setup_py = project_dir / "setup.py"
    if setup_py.exists():
        try:
            with open(setup_py, "r", encoding="utf-8") as f:
                content = f.read()
                # Very basic extraction - not foolproof
                if "install_requires" in content:
                    # This is a simplified approach; proper parsing would need AST
                    pass
        except IOError:
            pass

    # Remove duplicates while preserving order
    seen = set()
    unique_deps = []
    for dep in dependencies:
        if dep not in seen:
            seen.add(dep)
            unique_deps.append(dep)

    return unique_deps
