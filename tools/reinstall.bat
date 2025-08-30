@echo off
REM Reinstall mcp-code-checker package in development mode
REM This script uninstalls and reinstalls the package to ensure clean installation
echo =============================================
echo MCP-Code-Checker Package Reinstallation
echo =============================================
echo.
echo [1/3] Uninstalling existing mcp-code-checker package...
pip uninstall mcp-code-checker -y
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Uninstall failed or package not found
) else (
    echo ✓ Package uninstalled successfully
)
echo.
echo [2/3] Installing package in development mode...
pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Installation failed!
    echo Please check for errors above and try again.
    pause
    exit /b 1
)
echo ✓ Package installed successfully
echo.
echo [3/3] Verifying installation...
mcp-code-checker --help >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ✗ CLI command verification failed!
    echo The mcp-code-checker command is not working properly.
    pause
    exit /b 1
)
echo ✓ CLI command verified successfully
echo.
echo =============================================
echo Reinstallation completed successfully!
echo You can now use: mcp-code-checker --help
echo =============================================
pause
