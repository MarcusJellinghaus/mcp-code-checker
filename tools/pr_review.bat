@echo off
setlocal enabledelayedexpansion

REM Generate git diff and create review prompt
(
    echo Can you please do a review of the current changes in this PR?
    echo Do they all make sense? What should be changed / amended?
    echo.
    echo === GIT DIFF ===
    echo.
    git diff --unified=5 --no-prefix main...HEAD
) | clip

echo PR review prompt with git diff copied to clipboard!
echo Paste it in the LLM to get a code review.
exit /b 0
