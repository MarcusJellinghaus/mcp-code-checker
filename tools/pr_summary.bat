@echo off
setlocal enabledelayedexpansion

REM Generate git diff and create PR summary prompt
(
    echo Please read the information in folder `PR_Info` ^(if any^) and review the code changes ^(git output^)
    echo Can you please create a limited size summary for a pull request?
    echo Please do not refer to the files in `PR_Info` directly !
    echo Please save the pull request summary in markdown file ^(as `PR_Info\summary.md`^) so that I can easily copy/paste it.
    echo Last step, delete all files from folder `PR_Info`
    echo.
    echo === GIT DIFF ===
    echo.
    git diff --unified=5 --no-prefix main...HEAD
) | clip

echo PR summary prompt with git diff copied to clipboard!
echo Paste it in the LLM to generate a pull request summary.
exit /b 0
