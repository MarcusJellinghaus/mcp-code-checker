"""Tests for Python environment detection utilities."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, List
from unittest.mock import MagicMock, call, patch

import pytest

from src.config.detection import (
    detect_python_environment,
    find_project_python_executable,
    find_virtual_environments,
    get_project_dependencies,
    get_python_info,
    get_venv_python,
    is_valid_conda_env,
    is_valid_venv,
    validate_python_executable,
)


class TestVirtualEnvironmentDetection:
    """Test virtual environment detection functions."""

    @pytest.fixture
    def mock_venv(self, tmp_path: Path) -> Path:
        """Create a mock virtual environment structure."""
        venv_path = tmp_path / "venv"
        venv_path.mkdir()

        if sys.platform == "win32":
            scripts = venv_path / "Scripts"
            scripts.mkdir()
            (scripts / "python.exe").touch()
            (scripts / "activate.bat").touch()
        else:
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            (bin_dir / "python").touch()
            (bin_dir / "activate").touch()

        # Add pyvenv.cfg for modern venvs
        (venv_path / "pyvenv.cfg").write_text("home = /usr/bin")

        return venv_path

    @pytest.fixture
    def mock_conda_env(self, tmp_path: Path) -> Path:
        """Create a mock conda environment structure."""
        conda_path = tmp_path / "conda-env"
        conda_path.mkdir()

        # Conda-specific structure
        conda_meta = conda_path / "conda-meta"
        conda_meta.mkdir()
        (conda_meta / "history").touch()

        if sys.platform == "win32":
            (conda_path / "python.exe").touch()
        else:
            bin_dir = conda_path / "bin"
            bin_dir.mkdir()
            (bin_dir / "python").touch()

        return conda_path

    def test_is_valid_venv_true(self, mock_venv: Path) -> None:
        """Test detecting a valid virtual environment."""
        assert is_valid_venv(mock_venv) is True

    def test_is_valid_venv_false_missing_python(self, tmp_path: Path) -> None:
        """Test venv detection fails without Python executable."""
        venv_path = tmp_path / "venv"
        venv_path.mkdir()

        if sys.platform == "win32":
            scripts = venv_path / "Scripts"
            scripts.mkdir()
            (scripts / "activate.bat").touch()
        else:
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            (bin_dir / "activate").touch()

        assert is_valid_venv(venv_path) is False

    def test_is_valid_venv_false_not_directory(self, tmp_path: Path) -> None:
        """Test venv detection fails for non-directory."""
        file_path = tmp_path / "not_a_venv"
        file_path.touch()
        assert is_valid_venv(file_path) is False

    def test_is_valid_venv_false_nonexistent(self, tmp_path: Path) -> None:
        """Test venv detection fails for nonexistent path."""
        assert is_valid_venv(tmp_path / "nonexistent") is False

    def test_is_valid_conda_env_true(self, mock_conda_env: Path) -> None:
        """Test detecting a valid conda environment."""
        assert is_valid_conda_env(mock_conda_env) is True

    def test_is_valid_conda_env_false_no_meta(self, tmp_path: Path) -> None:
        """Test conda detection fails without conda-meta."""
        conda_path = tmp_path / "conda-env"
        conda_path.mkdir()

        if sys.platform == "win32":
            (conda_path / "python.exe").touch()
        else:
            bin_dir = conda_path / "bin"
            bin_dir.mkdir()
            (bin_dir / "python").touch()

        assert is_valid_conda_env(conda_path) is False

    def test_get_venv_python(self, mock_venv: Path) -> None:
        """Test getting Python executable from venv."""
        python_exe = get_venv_python(mock_venv)
        assert python_exe is not None
        assert python_exe.exists()
        assert python_exe.name in ("python", "python.exe")

    def test_get_venv_python_none(self, tmp_path: Path) -> None:
        """Test getting Python from invalid venv returns None."""
        assert get_venv_python(tmp_path / "nonexistent") is None

    def test_find_virtual_environments(self, tmp_path: Path) -> None:
        """Test finding virtual environments in project."""
        # Create multiple venvs
        venv1 = tmp_path / "venv"
        venv2 = tmp_path / ".venv"
        venv1.mkdir()
        venv2.mkdir()

        # Create proper structure for one
        if sys.platform == "win32":
            scripts = venv1 / "Scripts"
            scripts.mkdir()
            (scripts / "python.exe").touch()
            (scripts / "activate.bat").touch()
        else:
            bin_dir = venv1 / "bin"
            bin_dir.mkdir()
            (bin_dir / "python").touch()
            (bin_dir / "activate").touch()

        venvs = find_virtual_environments(tmp_path)
        assert len(venvs) >= 1
        assert venv1 in venvs

    def test_find_virtual_environments_with_pipenv(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Test finding pipenv virtual environments."""
        # Create a Pipfile
        pipfile = tmp_path / "Pipfile"
        pipfile.write_text('[packages]\nrequests = "*"')

        # Mock pipenv --venv command
        mock_venv_path = (
            tmp_path / ".local" / "share" / "virtualenvs" / "project-abc123"
        )
        mock_venv_path.mkdir(parents=True)

        # Create venv structure
        if sys.platform == "win32":
            scripts = mock_venv_path / "Scripts"
            scripts.mkdir()
            (scripts / "python.exe").touch()
        else:
            bin_dir = mock_venv_path / "bin"
            bin_dir.mkdir()
            (bin_dir / "python").touch()
        (mock_venv_path / "pyvenv.cfg").touch()

        def mock_run(*args: Any, **kwargs: Any) -> MagicMock:
            if "pipenv" in args[0] and "--venv" in args[0]:
                return MagicMock(returncode=0, stdout=str(mock_venv_path))
            raise subprocess.SubprocessError()

        with patch("subprocess.run", side_effect=mock_run):
            venvs = find_virtual_environments(tmp_path)
            assert mock_venv_path in venvs


class TestPythonExecutableValidation:
    """Test Python executable validation and info retrieval."""

    def test_validate_python_executable_valid(self) -> None:
        """Test validating current Python executable."""
        assert validate_python_executable(sys.executable) is True

    def test_validate_python_executable_invalid_path(self) -> None:
        """Test validation fails for invalid path."""
        assert validate_python_executable("/nonexistent/python") is False

    def test_validate_python_executable_empty(self) -> None:
        """Test validation fails for empty string."""
        assert validate_python_executable("") is False

    def test_validate_python_executable_with_mock(self, tmp_path: Path) -> None:
        """Test validation with mocked subprocess."""
        fake_python = tmp_path / "python"
        fake_python.touch()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert validate_python_executable(str(fake_python)) is True
            mock_run.assert_called_once()

    def test_get_python_info_valid(self) -> None:
        """Test getting Python info for valid executable."""
        info = get_python_info(sys.executable)
        assert info["valid"] is True
        assert "version" in info
        assert "platform" in info
        assert "executable" in info
        assert info["executable"] == sys.executable

    def test_get_python_info_invalid(self) -> None:
        """Test getting Python info for invalid executable."""
        info = get_python_info("/nonexistent/python")
        assert info["valid"] is False
        assert info["executable"] == "/nonexistent/python"

    def test_get_python_info_with_venv(self, tmp_path: Path) -> None:
        """Test detecting virtual environment in Python info."""
        fake_python = tmp_path / "venv" / "bin" / "python"
        fake_python.parent.mkdir(parents=True)
        fake_python.touch()

        with patch(
            "src.config.detection.validate_python_executable", return_value=True
        ):
            with patch("subprocess.run") as mock_run:
                mock_output = json.dumps(
                    {
                        "version": "3.9.0",
                        "version_info": [3, 9, 0, "final", 0],
                        "platform": "linux",
                        "implementation": "CPython",
                        "architecture": "x86_64",
                        "prefix": str(tmp_path / "venv"),
                        "base_prefix": "/usr",
                        "executable": str(fake_python),
                        "is_venv": True,
                    }
                )
                mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)

                info = get_python_info(str(fake_python))
                assert info["valid"] is True
                assert info["is_venv"] is True


class TestPythonEnvironmentDetection:
    """Test complete environment detection."""

    def test_detect_python_environment_with_venv(self, tmp_path: Path) -> None:
        """Test detection with virtual environment present."""
        # Create venv structure
        venv_path = tmp_path / "venv"
        venv_path.mkdir()

        if sys.platform == "win32":
            scripts = venv_path / "Scripts"
            scripts.mkdir()
            python_exe = scripts / "python.exe"
        else:
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            python_exe = bin_dir / "python"

        python_exe.touch()
        (venv_path / "pyvenv.cfg").touch()

        # Mock validation
        with patch(
            "src.config.detection.validate_python_executable", return_value=True
        ):
            exe, venv = detect_python_environment(tmp_path)
            assert exe == str(python_exe)
            assert venv == str(venv_path)

    def test_detect_python_environment_no_venv(self) -> None:
        """Test detection without virtual environment."""
        with patch("src.config.detection.find_virtual_environments", return_value=[]):
            exe, venv = detect_python_environment(Path.cwd())
            assert exe == sys.executable
            assert venv is None

    def test_detect_python_environment_fallback(self, tmp_path: Path) -> None:
        """Test fallback to system Python."""
        with patch("src.config.detection.find_virtual_environments", return_value=[]):
            with patch(
                "src.config.detection.validate_python_executable"
            ) as mock_validate:
                # First call (sys.executable) fails, second (from PATH) succeeds
                mock_validate.side_effect = [False, True]

                with patch("subprocess.run") as mock_run:
                    mock_run.side_effect = [
                        MagicMock(returncode=0),  # python --version
                        MagicMock(returncode=0, stdout="/usr/bin/python3"),  # Get path
                    ]

                    exe, venv = detect_python_environment(tmp_path)
                    assert exe == "/usr/bin/python3"
                    assert venv is None

    def test_find_project_python_executable(self, tmp_path: Path) -> None:
        """Test convenience function for finding Python."""
        with patch("src.config.detection.detect_python_environment") as mock_detect:
            mock_detect.return_value = ("/usr/bin/python3", None)
            exe = find_project_python_executable(tmp_path)
            assert exe == "/usr/bin/python3"
            mock_detect.assert_called_once_with(tmp_path)


class TestProjectDependencies:
    """Test project dependency detection."""

    def test_get_dependencies_from_requirements(self, tmp_path: Path) -> None:
        """Test reading dependencies from requirements.txt."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(
            """# Comment
requests>=2.28.0
numpy==1.24.0

# Another comment
pandas
"""
        )

        deps = get_project_dependencies(tmp_path)
        assert "requests>=2.28.0" in deps
        assert "numpy==1.24.0" in deps
        assert "pandas" in deps
        assert len(deps) == 3  # Comments and empty lines excluded

    def test_get_dependencies_from_multiple_requirements(self, tmp_path: Path) -> None:
        """Test reading from multiple requirements files."""
        (tmp_path / "requirements.txt").write_text("requests")
        (tmp_path / "requirements-dev.txt").write_text("pytest")
        (tmp_path / "dev-requirements.txt").write_text("black")

        deps = get_project_dependencies(tmp_path)
        assert "requests" in deps
        assert "pytest" in deps
        assert "black" in deps

    def test_get_dependencies_from_pyproject(self, tmp_path: Path) -> None:
        """Test reading dependencies from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """[project]
name = "test-project"
dependencies = [
    "requests>=2.28.0",
    "click>=8.0"
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "black"]
test = ["coverage"]
"""
        )

        # Mock tomllib import
        mock_toml_data = {
            "project": {
                "name": "test-project",
                "dependencies": ["requests>=2.28.0", "click>=8.0"],
                "optional-dependencies": {
                    "dev": ["pytest>=7.0", "black"],
                    "test": ["coverage"],
                },
            }
        }

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = b""
            try:
                import tomllib

                with patch("tomllib.load", return_value=mock_toml_data):
                    deps = get_project_dependencies(tmp_path)
            except ImportError:
                try:
                    import tomli  # type: ignore[import-not-found]

                    with patch("tomli.load", return_value=mock_toml_data):
                        deps = get_project_dependencies(tmp_path)
                except ImportError:
                    # Skip test if neither tomllib nor tomli available
                    pytest.skip("No TOML library available")

        assert "requests>=2.28.0" in deps
        assert "click>=8.0" in deps
        assert "pytest>=7.0" in deps
        assert "black" in deps
        assert "coverage" in deps

    def test_get_dependencies_no_duplicates(self, tmp_path: Path) -> None:
        """Test that duplicate dependencies are removed."""
        (tmp_path / "requirements.txt").write_text("requests\nclick\nrequests")
        (tmp_path / "requirements-dev.txt").write_text("click\npytest")

        deps = get_project_dependencies(tmp_path)
        assert deps.count("requests") == 1
        assert deps.count("click") == 1
        assert "pytest" in deps

    def test_get_dependencies_empty_project(self, tmp_path: Path) -> None:
        """Test project with no dependency files."""
        deps = get_project_dependencies(tmp_path)
        assert deps == []
