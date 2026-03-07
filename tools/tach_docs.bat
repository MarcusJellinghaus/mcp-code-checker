@echo off
REM Generate architecture documentation (dependency graph)
REM
REM Usage: tools\tach_docs.bat
REM
REM Creates:
REM   - docs/architecture/dependencies/dependency_graph.html

python "%~dp0tach_docs.py" %*
exit /b %ERRORLEVEL%
