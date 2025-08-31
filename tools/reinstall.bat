@echo off
REM Reinstall mcp-code-checker package in development mode
echo =============================================
echo MCP-Code-Checker Package Reinstallation
echo =============================================
echo.

echo [1/3] Uninstalling existing packages...
REM Note: mcp-config is uninstalled here but will be automatically reinstalled 
REM as a dependency when mcp-code-checker is installed (see pyproject.toml)
pip uninstall mcp-code-checker mcp-config -y
echo ✓ Packages uninstalled

echo.
echo [2/3] Installing mcp-code-checker in development mode...
pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo ✗ mcp-code-checker installation failed!
    pause
    exit /b 1
)
echo ✓ mcp-code-checker installed

echo.
echo [3/3] Verifying installation...
mcp-code-checker --help >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ✗ CLI verification failed!
    pause
    exit /b 1
)
echo ✓ Installation verified

echo.
echo =============================================
echo Reinstallation completed successfully!
echo =============================================
pause
