@echo off
REM Batch client for calling MCP server second_sleep function
setlocal enabledelayedexpansion

set "sleep_seconds=%1"
set "method=%2"

REM Default values
if "%sleep_seconds%"=="" set "sleep_seconds=5"
if "%method%"=="" set "method=default"

REM Validate input
if %sleep_seconds% lss 0 (
    echo Error: Sleep duration must be positive
    exit /b 1
)
if %sleep_seconds% gtr 300 (
    echo Error: Sleep duration must be 300 seconds or less
    exit /b 1
)

echo Batch client calling second_sleep function...
echo   Seconds: %sleep_seconds%
echo   Method: %method%
echo.

REM Get script directory and call Python client
set "script_dir=%~dp0"
python "%script_dir%sleep_client.py" %sleep_seconds% %method%
set "exit_code=%errorlevel%"

echo.
if %exit_code% equ 0 (
echo Batch client execution completed successfully
) else (
    echo Batch client execution failed with exit code %exit_code%
exit /b %exit_code%
)
