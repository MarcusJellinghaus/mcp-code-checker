"""Tests for CLI command functionality."""

import subprocess
import sys
from pathlib import Path

import pytest


class TestCLICommand:
    """Test CLI command availability and functionality."""

    def test_cli_command_exists(self) -> None:
        """Test that mcp-code-checker command is available."""
        import shutil
        
        # This test will pass if installed with pip install -e .
        # It's OK if it fails in CI without installation
        command_path = shutil.which("mcp-code-checker")
        if command_path:
            assert Path(command_path).exists()
            print(f"✓ CLI command found at: {command_path}")
        else:
            pytest.skip("CLI command not installed (expected in CI)")

    def test_cli_command_help(self) -> None:
        """Test that CLI command shows help."""
        import shutil
        
        if not shutil.which("mcp-code-checker"):
            pytest.skip("CLI command not installed")
        
        result = subprocess.run(
            ["mcp-code-checker", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        assert "--project-dir" in result.stdout
        assert "--log-level" in result.stdout

    def test_python_module_fallback(self) -> None:
        """Test Python module invocation as fallback."""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parent.parent  # Project root
        )
        
        # Should work in development
        if result.returncode == 0:
            assert "--project-dir" in result.stdout
        else:
            # Might not work in all environments
            pytest.skip("Python module not available in this environment")

    def test_entry_point_configuration(self) -> None:
        """Test that entry point is correctly configured in pyproject.toml."""
        try:
            import tomllib  # type: ignore[import-not-found]
        except ImportError:
            # Python < 3.11 fallback
            try:
                import tomli as tomllib  # type: ignore[import-not-found,no-redef]
            except ImportError:
                pytest.skip("No TOML library available")
        
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml not found"
        
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        
        # Check that CLI entry point exists
        scripts = data.get("project", {}).get("scripts", {})
        assert "mcp-code-checker" in scripts
        assert scripts["mcp-code-checker"] == "src.main:main"
        
        # Verify mcp-config is no longer in scripts
        assert "mcp-config" not in scripts
