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
