"""Tests for the validation module."""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config.validation import (
    auto_detect_python_executable,
    auto_detect_venv_path,
    auto_generate_log_file_path,
    normalize_path,
    validate_log_level,
    validate_parameter_combination,
    validate_path,
    validate_python_executable,
    validate_venv_path,
)


class TestPathValidation:
    """Test path validation functions."""

    def test_validate_path_exists(self, tmp_path: Path) -> None:
        """Test path existence validation."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Valid path
        errors = validate_path(test_file, "test_param", must_exist=True)
        assert errors == []

        # Invalid path
        errors = validate_path(tmp_path / "nonexistent", "test_param", must_exist=True)
        assert len(errors) == 1
        assert "does not exist" in errors[0]

    def test_validate_path_is_dir(self, tmp_path: Path) -> None:
        """Test directory validation."""
        # Valid directory
        errors = validate_path(tmp_path, "test_param", must_be_dir=True)
        assert errors == []

        # File instead of directory
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        errors = validate_path(
            test_file, "test_param", must_exist=True, must_be_dir=True
        )
        assert len(errors) == 1
        assert "is not a directory" in errors[0]

    def test_validate_path_is_file(self, tmp_path: Path) -> None:
        """Test file validation."""
        # Valid file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        errors = validate_path(test_file, "test_param", must_be_file=True)
        assert errors == []

        # Directory instead of file
        errors = validate_path(
            tmp_path, "test_param", must_exist=True, must_be_file=True
        )
        assert len(errors) == 1
        assert "is not a file" in errors[0]

    def test_validate_path_permissions(self, tmp_path: Path) -> None:
        """Test path permission validation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Read permission
        errors = validate_path(test_file, "test_param", check_permissions="r")
        assert errors == []

        # Write permission (directory)
        errors = validate_path(tmp_path, "test_param", check_permissions="w")
        assert errors == []

        # Non-existent path (should not error for permissions)
        errors = validate_path(
            tmp_path / "nonexistent", "test_param", check_permissions="r"
        )
        assert errors == []


class TestPythonValidation:
    """Test Python executable and venv validation."""

    def test_validate_python_executable(self) -> None:
        """Test Python executable validation."""
        # Current Python should be valid
        errors = validate_python_executable(sys.executable, "python")
        assert errors == []

        # Non-existent executable
        errors = validate_python_executable("/nonexistent/python", "python")
        assert len(errors) == 1
        assert "does not exist" in errors[0]

    def test_validate_venv_path(self, tmp_path: Path) -> None:
        """Test virtual environment validation."""
        # Create a mock venv structure
        venv_path = tmp_path / "test_venv"
        venv_path.mkdir()

        if sys.platform == "win32":
            scripts_dir = venv_path / "Scripts"
            scripts_dir.mkdir()
            (scripts_dir / "python.exe").touch()
            (scripts_dir / "activate.bat").touch()
        else:
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            (bin_dir / "python").touch()
            (bin_dir / "activate").touch()

        # Should be valid
        errors = validate_venv_path(venv_path, "venv")
        assert errors == []

        # Non-existent venv
        errors = validate_venv_path(tmp_path / "nonexistent_venv", "venv")
        assert len(errors) == 1
        assert "does not exist" in errors[0]

        # Directory without venv structure
        bad_venv = tmp_path / "bad_venv"
        bad_venv.mkdir()
        errors = validate_venv_path(bad_venv, "venv")
        assert len(errors) > 0


class TestValueValidation:
    """Test value validation functions."""

    def test_validate_log_level(self) -> None:
        """Test log level validation."""
        # Valid levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors = validate_log_level(level, "log_level")
            assert errors == []

        # Case insensitive
        errors = validate_log_level("debug", "log_level")
        assert errors == []

        # Invalid level
        errors = validate_log_level("INVALID", "log_level")
        assert len(errors) == 1
        assert "Invalid log level" in errors[0]


class TestPathNormalization:
    """Test path normalization."""

    def test_normalize_path_absolute(self, tmp_path: Path) -> None:
        """Test normalizing absolute paths."""
        abs_path = tmp_path / "test"
        normalized = normalize_path(abs_path)
        assert normalized.is_absolute()
        assert normalized == abs_path.resolve()

    def test_normalize_path_relative(self, tmp_path: Path) -> None:
        """Test normalizing relative paths."""
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            rel_path = Path("test/file.txt")
            normalized = normalize_path(rel_path)
            assert normalized.is_absolute()
            assert normalized == (tmp_path / "test/file.txt").resolve()

    def test_normalize_path_with_base(self, tmp_path: Path) -> None:
        """Test normalizing paths with custom base directory."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        rel_path = Path("test/file.txt")
        normalized = normalize_path(rel_path, base_dir)
        assert normalized.is_absolute()
        assert normalized == (base_dir / "test/file.txt").resolve()


class TestAutoDetection:
    """Test auto-detection functions."""

    @patch("src.config.detection.detect_python_environment")
    def test_auto_detect_python_executable(
        self, mock_detect: MagicMock, tmp_path: Path
    ) -> None:
        """Test Python executable auto-detection."""
        mock_detect.return_value = ("/usr/bin/python3", None)
        result = auto_detect_python_executable(tmp_path)
        assert result == Path("/usr/bin/python3")
        mock_detect.assert_called_once_with(tmp_path)

    @patch("src.config.detection.find_virtual_environments")
    def test_auto_detect_venv_path(self, mock_find: MagicMock, tmp_path: Path) -> None:
        """Test virtual environment auto-detection."""
        venv_path = tmp_path / ".venv"
        mock_find.return_value = [venv_path]
        result = auto_detect_venv_path(tmp_path)
        assert result == venv_path
        mock_find.assert_called_once_with(tmp_path)

    def test_auto_generate_log_file_path(self, tmp_path: Path) -> None:
        """Test log file path generation."""
        # Generate log path
        log_path = auto_generate_log_file_path(tmp_path)

        # Check structure
        assert log_path.parent == tmp_path / "logs"
        assert log_path.name.startswith("mcp_code_checker_")
        assert log_path.suffix == ".log"

        # Check that logs directory was created
        assert (tmp_path / "logs").exists()

        # Check timestamp format
        timestamp_part = log_path.stem.replace("mcp_code_checker_", "")
        # Should be able to parse as datetime
        datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")


class TestParameterCombination:
    """Test parameter combination validation."""

    def test_validate_parameter_combination(self, tmp_path: Path) -> None:
        """Test validating parameter combinations."""
        # Valid combination
        params = {
            "project_dir": str(tmp_path),
            "python_executable": sys.executable,
        }
        errors = validate_parameter_combination(params)
        assert errors == []

        # Non-existent project dir
        params = {
            "project_dir": str(tmp_path / "nonexistent"),
        }
        errors = validate_parameter_combination(params)
        assert len(errors) == 1
        assert "does not exist" in errors[0]

        # Project dir is a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        params = {
            "project_dir": str(test_file),
        }
        errors = validate_parameter_combination(params)
        assert len(errors) == 1
        assert "is not a directory" in errors[0]
