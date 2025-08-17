@echo off
REM Pure batch implementation for second-level sleep
setlocal enabledelayedexpansion

set "sleep_seconds=%1"
if "%sleep_seconds%"=="" set "sleep_seconds=5"

REM Validate input (convert to integer first for comparison)
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

REM Record start time
echo Sleep operation starting:
echo   Requested: %sleep_seconds% seconds
echo   Start time: %date% %time%

REM Use timeout for precise sleep (available on Windows Vista+)
REM timeout command doesn't handle decimals, use int_seconds from validation
if "%int_seconds%"=="0" set "int_seconds=1"
timeout /t %int_seconds% /nobreak >nul

REM Record end time and report
echo   End time: %date% %time%
echo Sleep operation completed successfully
