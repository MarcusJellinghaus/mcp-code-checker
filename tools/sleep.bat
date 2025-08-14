@echo off
set sleep_seconds=%1
if "%sleep_seconds%"=="" set sleep_seconds=5

echo Start: %date% %time%
powershell -Command "Start-Sleep -Seconds %sleep_seconds%"
echo End: %date% %time%
echo Slept for %sleep_seconds% seconds