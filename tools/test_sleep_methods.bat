@echo off
REM Test runner for all second_sleep implementation methods
setlocal enabledelayedexpansion

echo ========================================
echo Testing second_sleep Implementation Methods
echo ========================================
echo.

set "script_dir=%~dp0"
set "total_tests=0"
set "passed_tests=0"
set "failed_tests=0"

REM Test durations
set "durations=1 5"

REM Test methods
set "methods=default python batch hybrid subprocess_test"

echo Starting comprehensive tests...
echo.

REM Loop through each method and duration
for %%m in (%methods%) do (
    echo ----------------------------------------
    echo Testing method: %%m
    echo ----------------------------------------
    
    for %%d in (%durations%) do (
        set /a total_tests+=1
        echo.
        echo Test !total_tests!: %%d seconds using %%m method
        echo Start time: !date! !time!
        
        REM Call the client
        call "%script_dir%sleep_client.bat" %%d %%m
        set "test_result=!errorlevel!"
        
        echo End time: !date! !time!
        
        if !test_result! equ 0 (
            echo Result: PASS
            set /a passed_tests+=1
        ) else (
            echo Result: FAIL ^(exit code !test_result!^)
            set /a failed_tests+=1
        )
        echo.
    )
)

echo ========================================
echo Test Summary
echo ========================================
echo Total tests: !total_tests!
echo Passed: !passed_tests!
echo Failed: !failed_tests!
echo.

if !failed_tests! equ 0 (
    echo All tests PASSED! 🎉
    exit /b 0
) else (
    echo Some tests FAILED! ❌
    exit /b 1
)
