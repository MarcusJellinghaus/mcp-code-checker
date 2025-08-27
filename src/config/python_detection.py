"""Enhanced Python executable detection for cross-platform support.

This module provides comprehensive Python detection across Windows, macOS,
and Linux with support for various installation methods.
"""

import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.config.paths import PathConstants, normalize_path


@dataclass
class PythonInfo:
    """Information about a Python installation."""

    executable: Path
    version: str
    version_info: tuple[int, ...]
    is_venv: bool
    venv_path: Optional[Path]
    platform: str
    architecture: str
    implementation: str
    prefix: Path
    base_prefix: Path

    @property
    def version_tuple(self) -> tuple[int, int, int]:
        """Get version as a tuple of (major, minor, patch)."""
        if len(self.version_info) >= 3:
            return (self.version_info[0], self.version_info[1], self.version_info[2])
        return (0, 0, 0)

    def meets_requirement(self, requirement: str) -> bool:
        """Check if this Python meets a version requirement.

        Args:
            requirement: Version requirement (e.g., ">=3.11", "~=3.11.0")

        Returns:
            True if requirement is met
        """
        # Simple version comparison - can be enhanced with packaging.specifiers
        if requirement.startswith(">="):
            min_version = requirement[2:].strip()
            return self._compare_version(min_version) >= 0
        elif requirement.startswith(">"):
            min_version = requirement[1:].strip()
            return self._compare_version(min_version) > 0
        elif requirement.startswith("=="):
            exact_version = requirement[2:].strip()
            return self._compare_version(exact_version) == 0
        elif requirement.startswith("~="):
            # Compatible release
            base_version = requirement[2:].strip()
            return self._compatible_release(base_version)

        # Default to True if we can't parse the requirement
        return True

    def _compare_version(self, other_version: str) -> int:
        """Compare this version with another version string.

        Returns:
            -1 if this < other, 0 if equal, 1 if this > other
        """
        other_parts = [int(p) for p in other_version.split(".")]
        this_parts = list(self.version_tuple)

        # Pad with zeros to same length
        max_len = max(len(this_parts), len(other_parts))
        this_parts.extend([0] * (max_len - len(this_parts)))
        other_parts.extend([0] * (max_len - len(other_parts)))

        for this, other in zip(this_parts, other_parts):
            if this < other:
                return -1
            elif this > other:
                return 1
        return 0

    def _compatible_release(self, base_version: str) -> bool:
        """Check if version is compatible with base version."""
        base_parts = [int(p) for p in base_version.split(".")]
        this_parts = list(self.version_tuple)

        if len(base_parts) < 2:
            return False

        # Major and minor must match
        if len(this_parts) < 2:
            return False

        if this_parts[0] != base_parts[0]:
            return False

        if len(base_parts) == 2:
            # ~=3.11 means >=3.11, <4.0
            return this_parts[1] >= base_parts[1]
        else:
            # ~=3.11.0 means >=3.11.0, <3.12.0
            return this_parts[1] == base_parts[1] and this_parts[2] >= base_parts[2]


@dataclass
class VenvInfo:
    """Information about a virtual environment."""

    path: Path
    python_executable: Path
    is_valid: bool
    type: str  # 'venv', 'virtualenv', 'conda', 'pipenv', 'poetry'
    base_python: Optional[str] = None


def detect_python_executable(
    project_dir: Path, required_version: Optional[str] = None, prefer_venv: bool = True
) -> Optional[PythonInfo]:
    """Comprehensive Python executable detection.

    Priority order:
    1. Virtual environment in project (if prefer_venv=True)
    2. Python specified in pyproject.toml requires-python
    3. Current Python executable (sys.executable)
    4. System Python on PATH
    5. Platform-specific Python locations

    Args:
        project_dir: Project directory
        required_version: Required Python version (e.g., ">=3.11")
        prefer_venv: Whether to prefer virtual environments

    Returns:
        PythonInfo if found, None otherwise
    """
    candidates: list[Path] = []

    # 1. Check for virtual environments
    if prefer_venv:
        venv_info = detect_venv_cross_platform(project_dir)
        if venv_info and venv_info.is_valid:
            candidates.append(venv_info.python_executable)

    # 2. Check pyproject.toml for Python requirement
    pyproject_python = get_pyproject_python_requirement(project_dir)
    if pyproject_python and required_version is None:
        required_version = pyproject_python

    # 3. Current Python executable
    candidates.append(Path(sys.executable))

    # 4. System Python on PATH
    candidates.extend(find_python_in_path())

    # 5. Platform-specific locations
    candidates.extend(find_platform_specific_pythons())

    # Validate and check each candidate
    for candidate in candidates:
        if not candidate.exists():
            continue

        python_info = get_python_info(candidate)
        if python_info is None:
            continue

        # Check version requirement
        if required_version and not python_info.meets_requirement(required_version):
            continue

        return python_info

    return None


def detect_venv_cross_platform(project_dir: Path) -> Optional[VenvInfo]:
    """Detect virtual environments across platforms.

    Args:
        project_dir: Project directory to search

    Returns:
        VenvInfo if found, None otherwise
    """
    # Check common venv patterns
    for venv_name in PathConstants.VENV_NAMES:
        venv_path = project_dir / venv_name
        venv_info = validate_venv(venv_path)
        if venv_info and venv_info.is_valid:
            return venv_info

    # Check for Poetry environment
    poetry_venv = detect_poetry_venv(project_dir)
    if poetry_venv:
        return poetry_venv

    # Check for Pipenv environment
    pipenv_venv = detect_pipenv_venv(project_dir)
    if pipenv_venv:
        return pipenv_venv

    # Check for Conda environment
    conda_venv = detect_conda_venv(project_dir)
    if conda_venv:
        return conda_venv

    return None


def validate_venv(venv_path: Path) -> Optional[VenvInfo]:
    """Validate and get information about a virtual environment.

    Args:
        venv_path: Path to potential virtual environment

    Returns:
        VenvInfo if valid, None otherwise
    """
    if not venv_path.exists() or not venv_path.is_dir():
        return None

    # Determine Python executable location
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        activate = venv_path / "Scripts" / "activate.bat"
    else:
        python_exe = venv_path / "bin" / "python"
        activate = venv_path / "bin" / "activate"

    # Check for pyvenv.cfg (venv/virtualenv marker)
    pyvenv_cfg = venv_path / "pyvenv.cfg"

    # Check for conda-meta (conda marker)
    conda_meta = venv_path / "conda-meta"

    if not python_exe.exists():
        return None

    # Determine venv type
    venv_type = "unknown"
    base_python = None

    if pyvenv_cfg.exists():
        venv_type = "venv"
        # Try to read base Python from pyvenv.cfg
        try:
            with open(pyvenv_cfg, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("base-executable"):
                        base_python = line.split("=", 1)[1].strip()
                        break
        except IOError:
            pass
    elif conda_meta.exists():
        venv_type = "conda"
    elif activate.exists():
        venv_type = "virtualenv"

    # Validate Python executable
    if not validate_python_executable(python_exe):
        return VenvInfo(
            path=venv_path,
            python_executable=python_exe,
            is_valid=False,
            type=venv_type,
            base_python=base_python,
        )

    return VenvInfo(
        path=venv_path,
        python_executable=python_exe,
        is_valid=True,
        type=venv_type,
        base_python=base_python,
    )


def detect_poetry_venv(project_dir: Path) -> Optional[VenvInfo]:
    """Detect Poetry virtual environment.

    Args:
        project_dir: Project directory

    Returns:
        VenvInfo if found, None otherwise
    """
    pyproject = project_dir / "pyproject.toml"
    if not pyproject.exists():
        return None

    # Check if this is a Poetry project
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            return None

    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
            if "tool" not in data or "poetry" not in data["tool"]:
                return None
    except (IOError, tomllib.TOMLDecodeError):
        return None

    # Try to get Poetry env path
    try:
        result = subprocess.run(
            ["poetry", "env", "info", "--path"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            venv_path = Path(result.stdout.strip())
            venv_info = validate_venv(venv_path)
            if venv_info:
                venv_info.type = "poetry"
                return venv_info
    except (subprocess.SubprocessError, OSError):
        pass

    return None


def detect_pipenv_venv(project_dir: Path) -> Optional[VenvInfo]:
    """Detect Pipenv virtual environment.

    Args:
        project_dir: Project directory

    Returns:
        VenvInfo if found, None otherwise
    """
    pipfile = project_dir / "Pipfile"
    if not pipfile.exists():
        return None

    try:
        result = subprocess.run(
            ["pipenv", "--venv"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            venv_path = Path(result.stdout.strip())
            venv_info = validate_venv(venv_path)
            if venv_info:
                venv_info.type = "pipenv"
                return venv_info
    except (subprocess.SubprocessError, OSError):
        pass

    return None


def detect_conda_venv(project_dir: Path) -> Optional[VenvInfo]:
    """Detect Conda virtual environment.

    Args:
        project_dir: Project directory

    Returns:
        VenvInfo if found, None otherwise
    """
    # Check for environment.yml or environment.yaml
    for env_file in ["environment.yml", "environment.yaml"]:
        if (project_dir / env_file).exists():
            # Try to get conda env information
            try:
                result = subprocess.run(
                    ["conda", "env", "list", "--json"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if result.returncode == 0:
                    envs = json.loads(result.stdout)
                    # Check if there's an env matching the project
                    project_name = project_dir.name
                    for env_path in envs.get("envs", []):
                        env_path = Path(env_path)
                        if project_name in env_path.name:
                            venv_info = validate_venv(env_path)
                            if venv_info:
                                venv_info.type = "conda"
                                return venv_info
            except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
                pass

    # Check for conda-env subdirectory
    conda_env = project_dir / "conda-env"
    if conda_env.exists():
        venv_info = validate_venv(conda_env)
        if venv_info:
            venv_info.type = "conda"
            return venv_info

    return None


def find_python_in_path() -> list[Path]:
    """Find Python executables in system PATH.

    Returns:
        List of Python executable paths
    """
    pythons: list[Path] = []

    # Get executable names for current platform
    if sys.platform in PathConstants.PYTHON_EXECUTABLES:
        exe_names = PathConstants.PYTHON_EXECUTABLES[sys.platform]
    else:
        exe_names = ["python3", "python"]

    # Search in PATH
    path_env = os.environ.get("PATH", "").split(os.pathsep)

    for path_dir in path_env:
        if not path_dir:
            continue

        path_dir_path = Path(path_dir)
        if not path_dir_path.exists():
            continue

        for exe_name in exe_names:
            python_path = path_dir_path / exe_name
            if python_path.exists() and python_path.is_file():
                pythons.append(python_path)

    return pythons


def find_platform_specific_pythons() -> list[Path]:
    """Find Python installations in platform-specific locations.

    Returns:
        List of Python executable paths
    """
    pythons: list[Path] = []

    if sys.platform == "win32":
        pythons.extend(find_windows_pythons())
    elif sys.platform == "darwin":
        pythons.extend(find_macos_pythons())
    else:  # Linux and other Unix-like
        pythons.extend(find_linux_pythons())

    return pythons


def find_windows_pythons() -> list[Path]:
    """Find Python installations on Windows.

    Returns:
        List of Python executable paths
    """
    pythons: list[Path] = []

    # Check Python Launcher
    py_exe = Path("C:/Windows/py.exe")
    if py_exe.exists():
        pythons.append(py_exe)

    # Check common installation directories
    program_files = [
        Path(os.environ.get("ProgramFiles", "C:/Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")),
        Path(os.environ.get("LocalAppData", "")),
    ]

    for base_dir in program_files:
        if not base_dir or not base_dir.exists():
            continue

        # Check for Python installations
        for pattern in ["Python3*", "Python/*"]:
            for python_dir in base_dir.glob(pattern):
                python_exe = python_dir / "python.exe"
                if python_exe.exists():
                    pythons.append(python_exe)

    # Check Microsoft Store Python
    local_appdata = Path(os.environ.get("LocalAppData", ""))
    if local_appdata.exists():
        ms_python = local_appdata / "Microsoft/WindowsApps/python.exe"
        if ms_python.exists():
            pythons.append(ms_python)

    # Check Anaconda/Miniconda locations
    user_home = Path.home()
    conda_locations = [
        user_home / "Anaconda3/python.exe",
        user_home / "Miniconda3/python.exe",
        Path("C:/ProgramData/Anaconda3/python.exe"),
        Path("C:/ProgramData/Miniconda3/python.exe"),
    ]

    for conda_python in conda_locations:
        if conda_python.exists():
            pythons.append(conda_python)

    return pythons


def find_macos_pythons() -> list[Path]:
    """Find Python installations on macOS.

    Returns:
        List of Python executable paths
    """
    pythons: list[Path] = []

    # Homebrew locations (Intel and Apple Silicon)
    homebrew_locations = [
        Path("/usr/local/bin"),  # Intel Macs
        Path("/opt/homebrew/bin"),  # Apple Silicon
    ]

    for brew_bin in homebrew_locations:
        if brew_bin.exists():
            for python in brew_bin.glob("python3*"):
                if python.is_file():
                    pythons.append(python)

    # MacPorts
    macports = Path("/opt/local/bin")
    if macports.exists():
        for python in macports.glob("python3*"):
            if python.is_file():
                pythons.append(python)

    # System Python (be careful with this)
    system_python = Path("/usr/bin/python3")
    if system_python.exists():
        pythons.append(system_python)

    # Python.org installations
    pythonorg = Path("/Library/Frameworks/Python.framework/Versions")
    if pythonorg.exists():
        for version_dir in pythonorg.iterdir():
            if version_dir.is_dir():
                python_exe = version_dir / "bin/python3"
                if python_exe.exists():
                    pythons.append(python_exe)

    # Anaconda/Miniconda
    user_home = Path.home()
    conda_locations = [
        user_home / "anaconda3/bin/python",
        user_home / "miniconda3/bin/python",
        Path("/opt/anaconda3/bin/python"),
        Path("/opt/miniconda3/bin/python"),
    ]

    for conda_python in conda_locations:
        if conda_python.exists():
            pythons.append(conda_python)

    return pythons


def find_linux_pythons() -> list[Path]:
    """Find Python installations on Linux.

    Returns:
        List of Python executable paths
    """
    pythons: list[Path] = []

    # Standard locations
    standard_locations = [
        Path("/usr/bin"),
        Path("/usr/local/bin"),
        Path("/opt/bin"),
    ]

    for location in standard_locations:
        if location.exists():
            for python in location.glob("python3*"):
                if python.is_file() and not python.is_symlink():
                    pythons.append(python)

    # Snap packages
    snap_bin = Path("/snap/bin")
    if snap_bin.exists():
        for python in snap_bin.glob("python3*"):
            if python.is_file():
                pythons.append(python)

    # Flatpak (less common for Python)
    flatpak_exports = Path.home() / ".local/share/flatpak/exports/bin"
    if flatpak_exports.exists():
        for python in flatpak_exports.glob("*python3*"):
            if python.is_file():
                pythons.append(python)

    # pyenv installations
    pyenv_root = Path.home() / ".pyenv/versions"
    if pyenv_root.exists():
        for version_dir in pyenv_root.iterdir():
            if version_dir.is_dir():
                python_exe = version_dir / "bin/python"
                if python_exe.exists():
                    pythons.append(python_exe)

    # Anaconda/Miniconda
    user_home = Path.home()
    conda_locations = [
        user_home / "anaconda3/bin/python",
        user_home / "miniconda3/bin/python",
        Path("/opt/anaconda3/bin/python"),
        Path("/opt/miniconda3/bin/python"),
    ]

    for conda_python in conda_locations:
        if conda_python.exists():
            pythons.append(conda_python)

    return pythons


def validate_python_executable(python_path: Path | str) -> bool:
    """Validate that a Python executable path is valid and working.

    Args:
        python_path: Path to Python executable

    Returns:
        True if valid, False otherwise
    """
    if isinstance(python_path, str):
        python_path = Path(python_path)

    if not python_path.exists() or not python_path.is_file():
        return False

    try:
        result = subprocess.run(
            [str(python_path), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def get_python_info(python_path: Path | str) -> Optional[PythonInfo]:
    """Get detailed information about a Python executable.

    Args:
        python_path: Path to Python executable

    Returns:
        PythonInfo if successful, None otherwise
    """
    if isinstance(python_path, str):
        python_path = Path(python_path)

    if not validate_python_executable(python_path):
        return None

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

    try:
        result = subprocess.run(
            [str(python_path), "-c", code],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if result.returncode != 0:
            return None

        py_info = json.loads(result.stdout)

        # Determine venv path if in a venv
        venv_path = None
        if py_info["is_venv"]:
            venv_path = Path(py_info["prefix"])

        return PythonInfo(
            executable=python_path,
            version=py_info["version"],
            version_info=tuple(py_info["version_info"]),
            is_venv=py_info["is_venv"],
            venv_path=venv_path,
            platform=py_info["platform"],
            architecture=py_info["architecture"],
            implementation=py_info["implementation"],
            prefix=Path(py_info["prefix"]),
            base_prefix=Path(py_info["base_prefix"]),
        )

    except (subprocess.SubprocessError, OSError, json.JSONDecodeError, KeyError):
        return None


def get_pyproject_python_requirement(project_dir: Path) -> Optional[str]:
    """Get Python version requirement from pyproject.toml.

    Args:
        project_dir: Project directory

    Returns:
        Python requirement string (e.g., ">=3.11") or None
    """
    pyproject = project_dir / "pyproject.toml"
    if not pyproject.exists():
        return None

    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            return None

    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)

            # Check project.requires-python
            if "project" in data and "requires-python" in data["project"]:
                requires_python = data["project"]["requires-python"]
                return str(requires_python) if requires_python is not None else None

            # Check tool.poetry.dependencies.python
            if "tool" in data and "poetry" in data["tool"]:
                poetry = data["tool"]["poetry"]
                if "dependencies" in poetry and "python" in poetry["dependencies"]:
                    python_dep = poetry["dependencies"]["python"]
                    return str(python_dep) if python_dep is not None else None

    except (IOError, tomllib.TOMLDecodeError, KeyError):
        pass

    return None
