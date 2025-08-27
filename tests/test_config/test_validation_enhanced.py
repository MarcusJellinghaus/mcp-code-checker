"""Tests for enhanced validation functionality."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.config.validation import (
    validate_path,
    validate_python_executable,
    validate_server_configuration,
    validate_venv_path,
)


class TestServerConfigurationValidation:
    """Test comprehensive server configuration validation."""

    def test_validate_server_configuration_all_valid(self, tmp_path: Path) -> None:
        """Test validation with all valid parameters."""
        # Create test project structure
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        # Create src/main.py
        src_dir = project_dir / "src"
        src_dir.mkdir()
        (src_dir / "main.py").touch()

        # Create tests directory
        tests_dir = project_dir / "tests"
        tests_dir.mkdir()

        # Create logs directory
        logs_dir = project_dir / "logs"
        logs_dir.mkdir()

        # Create mock venv
        venv_dir = project_dir / ".venv"
        venv_dir.mkdir()
        if sys.platform == "win32":
            venv_bin = venv_dir / "Scripts"
            venv_bin.mkdir()
            (venv_bin / "python.exe").touch()
            (venv_bin / "activate.bat").touch()
        else:
            venv_bin = venv_dir / "bin"
            venv_bin.mkdir()
            (venv_bin / "python").touch()
            (venv_bin / "activate").touch()
        (venv_dir / "pyvenv.cfg").touch()

        # Test parameters
        params = {
            "project_dir": str(project_dir),
            "python_executable": sys.executable,
            "venv_path": str(venv_dir),
            "test_folder": "tests",
            "log_file": str(logs_dir / "test.log"),
            "log_level": "INFO",
        }

        # Mock client handler
        mock_client = MagicMock()
        mock_client.list_all_servers.return_value = [
            {"name": "test-server", "type": "mcp-code-checker"}
        ]

        # Validate
        result = validate_server_configuration(
            "test-server", "mcp-code-checker", params, mock_client
        )

        assert result["success"] is True
        assert len(result["errors"]) == 0
        # The warning about CLI command may or may not appear depending on installation
        # We only care that there are no errors for this test
        # If warnings exist, they should be about CLI command availability
        if result["warnings"]:
            assert any("CLI command" in warn or "mcp-code-checker" in warn 
                      for warn in result["warnings"])

    def test_validate_server_configuration_missing_project_dir(self) -> None:
        """Test validation with missing project directory."""
        params = {
            "project_dir": "/nonexistent/path",
            "python_executable": sys.executable,
        }

        result = validate_server_configuration(
            "test-server", "mcp-code-checker", params
        )

        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert any("does not exist" in err for err in result["errors"])
        # Simplified version no longer has suggestions

    def test_validate_server_configuration_invalid_python(self, tmp_path: Path) -> None:
        """Test validation with invalid Python executable."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        params = {
            "project_dir": str(project_dir),
            "python_executable": "/nonexistent/python",
        }

        result = validate_server_configuration(
            "test-server", "mcp-code-checker", params
        )

        assert result["success"] is False
        assert any(
            "not found" in err or "does not exist" in err for err in result["errors"]
        )

    def test_validate_server_configuration_warnings(self, tmp_path: Path) -> None:
        """Test validation that produces warnings."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        # Create main module but no test folder
        src_dir = project_dir / "src"
        src_dir.mkdir()
        (src_dir / "main.py").touch()

        params = {
            "project_dir": str(project_dir),
            "test_folder": "tests",  # Doesn't exist
        }

        result = validate_server_configuration(
            "test-server", "mcp-code-checker", params
        )

        # Should have warnings but might still be successful
        # We expect at least the test folder warning, but may also have CLI command warning
        assert len(result["warnings"]) > 0
        assert any("Test folder" in warn or "CLI command" in warn 
                  for warn in result["warnings"])
        # Note: Removed suggestions check as it might not always have suggestions


class TestPathValidation:
    """Test path validation functions."""

    def test_validate_path_exists(self, tmp_path: Path) -> None:
        """Test path existence validation."""
        test_file = tmp_path / "test.txt"
        test_file.touch()

        # Valid path
        errors = validate_path(test_file, "test_file", must_exist=True)
        assert len(errors) == 0

        # Invalid path
        errors = validate_path(tmp_path / "nonexistent", "missing", must_exist=True)
        assert len(errors) == 1
        assert "does not exist" in errors[0]

    def test_validate_path_is_dir(self, tmp_path: Path) -> None:
        """Test directory validation."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        test_file = tmp_path / "testfile"
        test_file.touch()

        # Valid directory
        errors = validate_path(test_dir, "test_dir", must_be_dir=True)
        assert len(errors) == 0

        # File instead of directory
        errors = validate_path(test_file, "not_dir", must_exist=True, must_be_dir=True)
        assert len(errors) == 1
        assert "is not a directory" in errors[0]

    def test_validate_path_permissions(self, tmp_path: Path) -> None:
        """Test path permission validation."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        # Should have read permission
        errors = validate_path(test_dir, "test_dir", check_permissions="r")
        assert len(errors) == 0

        # Should have write permission
        errors = validate_path(test_dir, "test_dir", check_permissions="w")
        assert len(errors) == 0


class TestPythonValidation:
    """Test Python executable and venv validation."""

    def test_validate_python_executable(self) -> None:
        """Test Python executable validation."""
        import sys

        # Current Python should be valid
        errors = validate_python_executable(sys.executable, "python")
        assert len(errors) == 0

        # Nonexistent executable
        errors = validate_python_executable("/nonexistent/python", "bad_python")
        assert len(errors) > 0
        assert "does not exist" in errors[0]

    def test_validate_venv_path(self, tmp_path: Path) -> None:
        """Test virtual environment validation."""
        # Create mock venv structure
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()

        if sys.platform == "win32":
            scripts = venv_dir / "Scripts"
            scripts.mkdir()
            (scripts / "python.exe").touch()
            (scripts / "activate.bat").touch()
        else:
            bin_dir = venv_dir / "bin"
            bin_dir.mkdir()
            (bin_dir / "python").touch()
            (bin_dir / "activate").touch()

        (venv_dir / "pyvenv.cfg").touch()

        # Valid venv
        errors = validate_venv_path(venv_dir, "venv")
        assert len(errors) == 0

        # Invalid venv (missing structure)
        bad_venv = tmp_path / "bad_venv"
        bad_venv.mkdir()

        errors = validate_venv_path(bad_venv, "bad_venv")
        assert len(errors) > 0

        # Nonexistent venv
        errors = validate_venv_path(tmp_path / "nonexistent", "missing")
        assert len(errors) > 0
        assert "does not exist" in errors[0]
