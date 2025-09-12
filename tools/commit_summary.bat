@echo off
setlocal enabledelayedexpansion

REM Check if we're in a git repository
git rev-parse --git-dir >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Not in a git repository
    exit /b 1
)

REM Create temporary file for output with unique name
set TEMP_FILE=%TEMP%\commit_summary_%RANDOM%_%TIME:~6,2%%TIME:~9,2%.txt

REM Generate git diff including untracked files by adding them with --intent-to-add
echo Please review the code changes and provide a SHORT, CONCISE commit summary. > %TEMP_FILE%
echo. >> %TEMP_FILE%
echo REQUIREMENTS: >> %TEMP_FILE%
echo 1. Keep it BRIEF - aim for minimal text >> %TEMP_FILE%
echo 2. Format as inline markdown for easy copy/paste: >> %TEMP_FILE%
echo    - Commit heading: `type/scope: description` (max 50 chars) >> %TEMP_FILE%
echo    - Body (only if essential): Plain text, 1-2 sentences max >> %TEMP_FILE%
echo 3. Focus on WHAT changed, avoid implementation details >> %TEMP_FILE%
echo. >> %TEMP_FILE%
echo OUTPUT FORMAT: >> %TEMP_FILE%
echo Provide the commit in this markdown format: >> %TEMP_FILE%
echo `feat/auth: add user validation` >> %TEMP_FILE%
echo. >> %TEMP_FILE%
echo Optional body text here (if needed) >> %TEMP_FILE%
echo. >> %TEMP_FILE%
echo This makes it easy to copy the heading directly as inline code.
echo. >> %TEMP_FILE%
echo === GIT STATUS === >> %TEMP_FILE%
echo. >> %TEMP_FILE%
git status --short >> %TEMP_FILE%
echo. >> %TEMP_FILE%

REM Add untracked files with intent-to-add to make them visible in diff
echo Adding untracked files for preview...
git add --intent-to-add .
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to add files for preview
    del %TEMP_FILE%
    exit /b 1
)

echo === GIT DIFF (ALL CHANGES INCLUDING NEW FILES) === >> %TEMP_FILE%
echo. >> %TEMP_FILE%
git diff --unified=5 --no-prefix >> %TEMP_FILE%

echo === GIT DIFF (STAGED FILES) === >> %TEMP_FILE%
echo. >> %TEMP_FILE%
git diff --cached --unified=5 --no-prefix >> %TEMP_FILE%

REM Reset the intent-to-add so files remain untracked
echo Resetting file status...
git reset
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Failed to reset git status. You may need to run 'git reset' manually
)

REM Copy to clipboard
type %TEMP_FILE% | clip

REM Clean up
del %TEMP_FILE%

echo.
echo ===================================================
echo Commit summary copied to clipboard!
echo Includes: modified files + new untracked files
echo Paste it in your LLM to generate a commit message
echo ===================================================
exit /b 0
