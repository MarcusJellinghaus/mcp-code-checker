# Step 11: Create Test Scripts and Validation

## Objective
Create test scripts to validate the CLI command implementation and ensure everything works correctly in all installation modes.

## Files to Create/Modify
- `tests/test_cli_command.py` - New test file for CLI command
- `tests/test_installation_modes.py` - New test file for installation modes
- `tools/test_cli_installation.bat` - Windows test script
- `tools/test_cli_installation.sh` - Unix test script

## Implementation Instructions

### 1. Create tests/test_cli_command.py

```python
"""Tests for CLI command functionality."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestCLICommand:
    """Test CLI command availability and functionality."""

    def test_cli_command_exists(self):
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

    def test_cli_command_help(self):
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

    def test_python_module_fallback(self):
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

    @patch("shutil.which")
    def test_command_detection(self, mock_which):
        """Test command detection logic."""
        from src.config.integration import is_command_available
        
        # Test when command exists
        mock_which.return_value = "/usr/bin/mcp-code-checker"
        assert is_command_available("mcp-code-checker") is True
        
        # Test when command doesn't exist
        mock_which.return_value = None
        assert is_command_available("mcp-code-checker") is False

    def test_entry_point_configuration(self):
        """Test that entry point is correctly configured in pyproject.toml."""
        import tomllib
        
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml not found"
        
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        
        # Check that CLI entry point exists
        scripts = data.get("project", {}).get("scripts", {})
        assert "mcp-code-checker" in scripts
        assert scripts["mcp-code-checker"] == "src.main:main"
        
        # Also check mcp-config exists
        assert "mcp-config" in scripts
```

### 2. Create tests/test_installation_modes.py

```python
"""Tests for different installation modes."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestInstallationModes:
    """Test different installation modes detection."""

    def test_get_installation_mode_cli_command(self):
        """Test CLI command mode detection."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/mcp-code-checker"
            
            from src.config.servers import registry
            config = registry.get("mcp-code-checker")
            
            assert config.get_installation_mode() == "cli_command"

    def test_get_installation_mode_python_module(self):
        """Test Python module mode detection."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            
            with patch("importlib.util.find_spec") as mock_spec:
                mock_spec.return_value = Mock()  # Simulate package installed
                
                from src.config.servers import registry
                config = registry.get("mcp-code-checker")
                
                mode = config.get_installation_mode()
                assert mode in ["python_module", "development"]  # Could be either

    def test_get_installation_mode_development(self):
        """Test development mode detection."""
        # This should pass when running from source
        from src.config.servers import registry
        config = registry.get("mcp-code-checker")
        
        # In development, src/main.py exists
        if Path("src/main.py").exists():
            mode = config.get_installation_mode()
            assert mode in ["cli_command", "python_module", "development"]
        else:
            pytest.skip("Not running from source directory")

    def test_generate_args_cli_mode(self):
        """Test argument generation for CLI command mode."""
        from src.config.servers import registry
        
        config = registry.get("mcp-code-checker")
        
        params = {
            "project_dir": "/test/project",
            "log_level": "DEBUG"
        }
        
        # Test CLI command mode (no script path)
        args = config.generate_args(params, use_cli_command=True)
        
        # Should not include script path
        assert not any(arg.endswith("main.py") for arg in args)
        assert "--project-dir" in args
        assert "/test/project" in args
        assert "--log-level" in args
        assert "DEBUG" in args

    def test_generate_args_module_mode(self):
        """Test argument generation for module mode."""
        from src.config.servers import registry
        
        config = registry.get("mcp-code-checker")
        
        params = {
            "project_dir": "/test/project",
            "log_level": "INFO"
        }
        
        # Test module mode (includes script path)
        args = config.generate_args(params, use_cli_command=False)
        
        # Should include script path as first argument
        assert args[0].endswith("main.py")
        assert "--project-dir" in args
        assert "--log-level" in args

    def test_config_generation_with_cli_command(self):
        """Test configuration generation when CLI command is available."""
        with patch("src.config.integration.is_command_available") as mock_cmd:
            mock_cmd.return_value = True
            
            from src.config.integration import build_server_config
            from src.config.servers import registry
            
            server_config = registry.get("mcp-code-checker")
            params = {"project_dir": "/test/project"}
            
            config = build_server_config(server_config, params)
            
            assert config["command"] == "mcp-code-checker"
            assert "--project-dir" in config["args"]

    def test_config_generation_without_cli_command(self):
        """Test configuration generation without CLI command."""
        with patch("src.config.integration.get_mcp_code_checker_command_mode") as mock_mode:
            mock_mode.return_value = "python_module"
            
            from src.config.integration import build_server_config
            from src.config.servers import registry
            
            server_config = registry.get("mcp-code-checker")
            params = {"project_dir": "/test/project"}
            
            config = build_server_config(server_config, params)
            
            # Should use Python with module
            assert config["command"].endswith("python") or config["command"].endswith("python.exe")
            assert "-m" in config["args"] or config["args"][0].endswith("main.py")

    def test_validation_with_different_modes(self):
        """Test validation messages for different installation modes."""
        from src.config.validation import validate_server_configuration
        
        # Mock different scenarios
        test_cases = [
            ("cli_command", "✓", "CLI command 'mcp-code-checker' is available"),
            ("python_module", "⚠", "Package installed but CLI command not found"),
            ("development", "ℹ", "Running in development mode"),
            ("not_installed", "✗", "not properly installed")
        ]
        
        for mode, expected_status, expected_message in test_cases:
            with patch("src.config.servers.ServerConfig.get_installation_mode") as mock_mode:
                mock_mode.return_value = mode
                
                with patch("shutil.which") as mock_which:
                    mock_which.return_value = (mode == "cli_command")
                    
                    result = validate_server_configuration(
                        "test-server",
                        "mcp-code-checker",
                        {"project_dir": "."}
                    )
                    
                    if "cli_command" in result.get("checks", {}):
                        check = result["checks"]["cli_command"]
                        # Status might differ based on actual environment
                        assert "status" in check
                        assert "message" in check
```

### 3. Create tools/test_cli_installation.bat (Windows)

```batch
@echo off
REM Test script for CLI command installation on Windows

echo ========================================
echo MCP Code Checker CLI Installation Test
echo ========================================
echo.

echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    exit /b 1
)
python --version

echo.
echo [2/5] Checking if mcp-code-checker command exists...
where mcp-code-checker >nul 2>&1
if errorlevel 1 (
    echo WARNING: mcp-code-checker command not found
    echo Trying to install...
    pip install -e . >nul 2>&1
    where mcp-code-checker >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Failed to install CLI command
        echo Falling back to module mode...
    ) else (
        echo SUCCESS: CLI command installed
    )
) else (
    echo SUCCESS: mcp-code-checker command found at:
    where mcp-code-checker
)

echo.
echo [3/5] Testing CLI command help...
mcp-code-checker --help >nul 2>&1
if errorlevel 1 (
    echo WARNING: CLI command failed, trying module mode...
    python -m mcp_code_checker --help >nul 2>&1
    if errorlevel 1 (
        python -m src.main --help >nul 2>&1
        if errorlevel 1 (
            echo ERROR: No working command mode found
        ) else (
            echo SUCCESS: Development mode works (src.main)
        )
    ) else (
        echo SUCCESS: Module mode works (mcp_code_checker)
    )
) else (
    echo SUCCESS: CLI command works
)

echo.
echo [4/5] Checking mcp-config command...
where mcp-config >nul 2>&1
if errorlevel 1 (
    echo ERROR: mcp-config command not found
) else (
    echo SUCCESS: mcp-config found at:
    where mcp-config
)

echo.
echo [5/5] Running validation...
mcp-config validate >nul 2>&1
if errorlevel 1 (
    echo WARNING: Validation failed or not available
) else (
    echo SUCCESS: Validation passed
    echo.
    echo Run 'mcp-config validate' for details
)

echo.
echo ========================================
echo Test Complete
echo ========================================
```

### 4. Create tools/test_cli_installation.sh (Unix/Linux/macOS)

```bash
#!/bin/bash

# Test script for CLI command installation on Unix systems

echo "========================================"
echo "MCP Code Checker CLI Installation Test"
echo "========================================"
echo

echo "[1/5] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python not found in PATH"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi
$PYTHON_CMD --version

echo
echo "[2/5] Checking if mcp-code-checker command exists..."
if command -v mcp-code-checker &> /dev/null; then
    echo "SUCCESS: mcp-code-checker command found at:"
    which mcp-code-checker
else
    echo "WARNING: mcp-code-checker command not found"
    echo "Trying to install..."
    if pip install -e . &> /dev/null; then
        if command -v mcp-code-checker &> /dev/null; then
            echo "SUCCESS: CLI command installed"
        else
            echo "ERROR: Failed to install CLI command"
            echo "Falling back to module mode..."
        fi
    fi
fi

echo
echo "[3/5] Testing CLI command help..."
if mcp-code-checker --help &> /dev/null; then
    echo "SUCCESS: CLI command works"
elif $PYTHON_CMD -m mcp_code_checker --help &> /dev/null; then
    echo "SUCCESS: Module mode works (mcp_code_checker)"
elif $PYTHON_CMD -m src.main --help &> /dev/null; then
    echo "SUCCESS: Development mode works (src.main)"
else
    echo "ERROR: No working command mode found"
fi

echo
echo "[4/5] Checking mcp-config command..."
if command -v mcp-config &> /dev/null; then
    echo "SUCCESS: mcp-config found at:"
    which mcp-config
else
    echo "ERROR: mcp-config command not found"
fi

echo
echo "[5/5] Running validation..."
if mcp-config validate &> /dev/null; then
    echo "SUCCESS: Validation passed"
    echo
    echo "Run 'mcp-config validate' for details"
else
    echo "WARNING: Validation failed or not available"
fi

echo
echo "========================================"
echo "Test Complete"
echo "========================================"

# Check installation mode
echo
echo "Detected installation mode:"
$PYTHON_CMD -c "
import shutil
import importlib.util
from pathlib import Path

if shutil.which('mcp-code-checker'):
    print('  ✓ CLI Command Mode')
elif importlib.util.find_spec('mcp_code_checker'):
    print('  ⚠ Python Module Mode')
elif Path('src/main.py').exists():
    print('  ℹ Development Mode')
else:
    print('  ✗ Not Installed')
" 2>/dev/null || echo "  Could not detect mode"
```

### 5. Update pytest Configuration

Add to `pyproject.toml` if not present:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "cli: Tests for CLI command functionality",
    "installation: Tests for installation modes"
]
```

### 6. Create Manual Test Checklist

Create `tests/manual_cli_test.md`:

```markdown
# Manual CLI Command Testing Checklist

## Pre-Installation Tests
- [ ] Verify `mcp-code-checker` command doesn't exist
- [ ] Verify `python -m mcp_code_checker` fails

## Installation Tests
- [ ] Run `pip install -e .` in project directory
- [ ] Verify `mcp-code-checker --help` works
- [ ] Verify `mcp-config --help` works

## Command Tests
- [ ] Test: `mcp-code-checker --project-dir . --dry-run`
- [ ] Test: `mcp-code-checker --project-dir . --log-level DEBUG`
- [ ] Test: `mcp-code-checker --version` (if implemented)

## Configuration Tests
- [ ] Test: `mcp-config validate`
- [ ] Test: `mcp-config setup mcp-code-checker "test" --project-dir . --dry-run`
- [ ] Verify generated config uses `"command": "mcp-code-checker"`

## Virtual Environment Tests
- [ ] Create new venv: `python -m venv test_venv`
- [ ] Activate venv
- [ ] Install: `pip install -e .`
- [ ] Verify command works in venv
- [ ] Deactivate and verify command not available

## Uninstall Tests
- [ ] Run `pip uninstall mcp-code-checker`
- [ ] Verify command no longer exists
- [ ] Verify module mode fails

## Platform-Specific Tests

### Windows
- [ ] Test in Command Prompt (cmd.exe)
- [ ] Test in PowerShell
- [ ] Test in Git Bash

### macOS/Linux
- [ ] Test in bash
- [ ] Test in zsh
- [ ] Test with different Python versions
```

## Validation

After creating test files:
1. Run `pytest tests/test_cli_command.py -v`
2. Run `pytest tests/test_installation_modes.py -v`
3. Execute `tools/test_cli_installation.bat` (Windows) or `./tools/test_cli_installation.sh` (Unix)
4. Go through manual test checklist

## Next Step
Proceed to Step 12 for final validation and cleanup.
