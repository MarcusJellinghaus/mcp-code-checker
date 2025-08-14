@echo off
setlocal

:: Get the sleep duration from the first argument, default to 5 if not provided
set sleep_seconds=%1
if "%sleep_seconds%"=="" set sleep_seconds=5

:: Validate the input is a number (basic check)
echo %sleep_seconds%| findstr /r "^[0-9][0-9]*$" >nul
if errorlevel 1 (
    echo Error: Invalid sleep duration. Must be a positive integer.
    exit /b 1
)

:: Log start
echo Starting sleep for %sleep_seconds% seconds...

:: Sleep using timeout command
timeout /t %sleep_seconds% /nobreak >nul 2>&1

:: Log completion
echo Sleep completed successfully after %sleep_seconds% seconds.

exit /b 0
