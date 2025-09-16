@echo off
REM Reinstall mcp-code-checker package in development mode
echo =============================================
echo MCP-Code-Checker Package Reinstallation
echo =============================================
echo.

echo [0/4] Checking Python environment...
REM Check if we're in a virtual environment
if "%VIRTUAL_ENV%"=="" (
    echo ✗ Error: No Python virtual environment detected!
    echo.
    echo This script must be run from within an activated Python virtual environment.
    echo Please activate your virtual environment first:
    echo   - For venv: .venv\Scripts\activate
    echo   - For conda: conda activate your-env-name
    echo.
    pause
    exit /b 1
)

echo ✓ Python environment check passed (Virtual env: %VIRTUAL_ENV%)
echo.

echo [1/4] Uninstalling existing packages...
REM Note: mcp-config is uninstalled here but will be automatically reinstalled 
REM as a dependency when mcp-code-checker is installed (see pyproject.toml)
pip uninstall mcp-code-checker mcp-config mcp-server-filesystem -y
echo ✓ Packages uninstalled

echo.
echo [2/4] Installing mcp-code-checker in development mode...
pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo ✗ mcp-code-checker installation failed!
    pause
    exit /b 1
)
echo ✓ mcp-code-checker installed

echo.
echo [3/4] Installing developer dependencies...
pip install -e ".[dev]"
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Developer dependencies installation failed!
    pause
    exit /b 1
)
echo ✓ Developer dependencies installed

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
