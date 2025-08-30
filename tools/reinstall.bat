@echo off
REM Reinstall mcp-code-checker and mcp-config packages in development mode
echo =============================================
echo MCP-Code-Checker Package Reinstallation
echo =============================================
echo.

echo [1/4] Uninstalling existing packages...
pip uninstall mcp-code-checker mcp-config -y
echo ✓ Packages uninstalled

echo.
echo [2/4] Installing mcp-config from Git...
pip install git+https://github.com/MarcusJellinghaus/mcp-config.git@first_setup
if %ERRORLEVEL% NEQ 0 (
    echo ✗ mcp-config installation failed!
    pause
    exit /b 1
)
echo ✓ mcp-config installed

echo.
echo [3/4] Installing mcp-code-checker in development mode...
pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo ✗ mcp-code-checker installation failed!
    pause
    exit /b 1
)
echo ✓ mcp-code-checker installed

echo.
echo [4/4] Verifying installation...
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
