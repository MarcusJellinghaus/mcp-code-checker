@echo off
REM Subprocess test that mimics MCP server execution
setlocal enabledelayedexpansion

set "sleep_seconds=%1"
if "%sleep_seconds%"=="" set "sleep_seconds=1"

REM Validate input
for /f "tokens=1 delims=." %%i in ("%sleep_seconds%") do set "int_seconds=%%i"
if not defined int_seconds set "int_seconds=0"
if %int_seconds% lss 0 (
    echo Error: Sleep duration must be positive
    exit /b 1
)
if %int_seconds% gtr 300 (
    echo Error: Sleep duration must be 300 seconds or less
    exit /b 1
)

REM Get script directory and call Python subprocess test
set "script_dir=%~dp0"
echo Subprocess test: mimicking MCP server's exact subprocess.run() call
python "%script_dir%sleep_subprocess_test.py" %sleep_seconds%
set "exit_code=%errorlevel%"

exit /b %exit_code%
