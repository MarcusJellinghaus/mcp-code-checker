@echo off
setlocal enabledelayedexpansion

REM Check if we're in a git repository
git rev-parse --git-dir >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Not in a git repository
    exit /b 1
)

REM Get current branch name
for /f %%c in ('git branch --show-current 2^>nul') do set CURRENT_BRANCH=%%c

REM Detect the actual base branch or use environment variable
if defined BASE_BRANCH (
    set BASE_BRANCH_TO_USE=%BASE_BRANCH%
    echo Using specified base branch: !BASE_BRANCH_TO_USE!
) else (
    echo Detecting immediate parent branch from revision graph...
    
    REM For now, let's use a simpler approach and manually set config_helper
    git rev-parse --verify origin/config_helper >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        REM Check if config_helper is an ancestor and we have commits beyond it
        git merge-base --is-ancestor origin/config_helper HEAD >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            for /f %%n in ('git rev-list --count origin/config_helper..HEAD 2^>nul') do (
                if %%n GTR 0 (
                    set BASE_BRANCH_TO_USE=config_helper
                    echo Detected immediate parent branch: config_helper
                )
            )
        )
    )
    
    REM Fallback if config_helper doesn't work
    if not defined BASE_BRANCH_TO_USE (
        echo Fallback: trying main/master...
        git rev-parse --verify origin/main >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set BASE_BRANCH_TO_USE=main
        ) else (
            git rev-parse --verify origin/master >nul 2>&1
            if !ERRORLEVEL! EQU 0 (
                set BASE_BRANCH_TO_USE=master
            ) else (
                echo Error: Could not detect base branch. Set BASE_BRANCH environment variable.
                exit /b 1
            )
        )
        echo Detected base branch: !BASE_BRANCH_TO_USE!
    )
)

REM Show comparison info
echo.
echo Comparison will be: !BASE_BRANCH_TO_USE! -^> !CURRENT_BRANCH!
for /f %%m in ('git merge-base origin/!BASE_BRANCH_TO_USE! HEAD 2^>nul') do (
    echo Merge-base commit: %%m
    for /f "tokens=*" %%s in ('git show -s --format="%%s" %%m 2^>nul') do (
        echo Merge-base message: %%s
    )
)
echo.

REM Create temporary files
set TEMP_FILE=%TEMP%\pr_summary_%RANDOM%_%TIME:~6,2%%TIME:~9,2%.txt
set COMMITS_FILE=%TEMP%\commits_%RANDOM%_%TIME:~6,2%%TIME:~9,2%.txt

REM Get commit list first
git rev-list origin/!BASE_BRANCH_TO_USE!..HEAD > "!COMMITS_FILE!"

REM Generate PR summary structured by commits
(
    echo Can you please review this PR summary and provide feedback?
    echo Focus on the overall changes, commit structure, and whether the changes make sense together.
    echo.
    echo === PR SUMMARY ===
    echo Base branch: !BASE_BRANCH_TO_USE!
    echo Current branch: !CURRENT_BRANCH!
    echo.
    echo **Overview:**
    echo.
    for /f %%n in ('git rev-list --count origin/!BASE_BRANCH_TO_USE!..HEAD 2^>nul') do (
        echo Total commits: %%n
    )
    for /f %%f in ('git diff --name-only origin/!BASE_BRANCH_TO_USE!...HEAD 2^>nul ^| find /c /v ""') do (
        echo Total files changed: %%f
    )
    echo.
    echo **Commit Details newest first:**
    echo.
    
    REM Process each commit individually using the commits file
    for /f %%h in (!COMMITS_FILE!) do (
        echo ========================================
        echo **Commit %%h**
        git log -1 --format="Author: %%an <%%ae>" %%h
        git log -1 --format="Date: %%ad" --date=short %%h
        git log -1 --format="Message: %%s" %%h
        echo.
        
        REM Show files changed in this specific commit
        echo Files changed in this commit:
        for /f "tokens=1,2*" %%x in ('git show --name-status --format= %%h') do (
            if "%%x"=="A" echo   + Added: %%y
            if "%%x"=="M" echo   ~ Modified: %%y
            if "%%x"=="D" echo   - Deleted: %%y
            if "%%x"=="R" echo   ^> Renamed: %%y
            if "%%x"=="C" echo   ^> Copied: %%y
            if "%%x"=="T" echo   ~ Type changed: %%y
        )
        echo.
        
        REM Show statistics for this commit
        echo Statistics for this commit:
        git show --stat --format= %%h
        echo.
    )
) > "!TEMP_FILE!" 2>&1

REM Copy to clipboard
type "!TEMP_FILE!" | clip

REM Clean up
del "!TEMP_FILE!" >nul 2>&1
del "!COMMITS_FILE!" >nul 2>&1

echo.
echo PR summary copied to clipboard!
echo This provides a commit-structured overview without detailed line changes.
echo Use pr_review.bat if you need detailed diff information.
exit /b 0
