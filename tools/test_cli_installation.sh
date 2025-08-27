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
