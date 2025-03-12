@echo off
setlocal enabledelayedexpansion

REM Run pylint with specified parameters
pylint -E ./src ./tests > checks_output.txt 2>&1
set PYLINT_EXIT_CODE=%errorlevel%

REM Check if Pylint found any issues
if %PYLINT_EXIT_CODE% neq 0 (
    (
        echo INSTRUCTIONS FOR LLM: PYLINT ANALYSIS
        echo Pylint has detected potential critical errors in the source code:
        echo - Review serious code quality issues
        echo - Focus on:
        echo   1. Critical syntax errors
        echo   2. Import errors
        echo   3. Undefined variables
        echo.
        type checks_output.txt
    ) > checks_clipboard.txt

    type checks_clipboard.txt | clip
    echo Pylint found critical code errors. Output copied to clipboard.
    del checks_output.txt
    del checks_clipboard.txt
    exit /b 1
)

REM Run pytest if Pylint passed
pytest tests > checks_output.txt 2>&1
set PYTEST_EXIT_CODE=%errorlevel%

REM Check pytest results
if %PYTEST_EXIT_CODE% neq 0 (
    (
        echo INSTRUCTIONS FOR LLM: PYTEST RESULTS
        echo Pytest has found issues in the test suite:
        echo - Carefully review test failures and errors
        echo - Investigate potential causes:
        echo   1. Broken test assertions
        echo   2. Unexpected test behaviors
        echo   3. Potential code implementation issues
        echo - Provide specific recommendations for fixing test failures
        echo.
        type checks_output.txt
    ) > checks_clipboard.txt

    type checks_clipboard.txt | clip
    echo Pytest detected test failures. Output copied to clipboard.
    del checks_output.txt
    del checks_clipboard.txt
    exit /b 1
)

REM If all checks pass
echo All checks passed successfully. No issues detected.
del checks_output.txt 2>nul
exit /b 0
