@echo off
REM Hybrid implementation: batch wrapper that calls Python script
setlocal enabledelayedexpansion

set "sleep_seconds=%1"
if "%sleep_seconds%"=="" set "sleep_seconds=5"

REM Validate input at batch level (convert to integer first for comparison)
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

REM Get script directory and call Python
set "script_dir=%~dp0"
echo Hybrid sleep: calling Python script via batch wrapper
python -u "%script_dir%sleep_script.py" %sleep_seconds%
set "exit_code=%errorlevel%"

if %exit_code% neq 0 (
    echo Hybrid sleep failed with exit code %exit_code%
    exit /b %exit_code%
)

echo Hybrid sleep completed successfully
