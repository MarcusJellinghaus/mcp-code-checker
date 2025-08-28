# Entry Point Fix Summary

## Issue
When running `mcp-code-checker` after installation, the following error occurred:
```
ModuleNotFoundError: No module named 'main'
```

## Root Cause
The entry point in `pyproject.toml` was incorrectly configured:
```toml
[project.scripts]
mcp-config = "config.main:main"
mcp-code-checker = "main:main"  # INCORRECT
```

Since the `main.py` file is located in the `src/` directory, and the project is configured with `package-dir = {"" = "src"}`, the entry point should reference the module correctly within the package structure.

## Solution
Fixed the entry point in `pyproject.toml`:
```toml
[project.scripts]
mcp-config = "config.main:main"
mcp-code-checker = "src.main:main"  # CORRECT
```

## Additional Fix
Updated the test in `tests/test_cli_command.py` that was checking for the old entry point configuration:
```python
# Changed from:
assert scripts["mcp-code-checker"] == "main:main"
# To:
assert scripts["mcp-code-checker"] == "src.main:main"
```

## Verification
- ✅ Pylint: No issues found
- ✅ Pytest: 448 tests passed, 4 skipped
- ✅ Mypy: No type errors

## Answers to Original Questions

1. **Is it a problem with the two entry points?**
   - No, having multiple entry points is perfectly valid and commonly used.

2. **Can you confirm whether two different entry points are possible?**
   - Yes, multiple entry points are fully supported. Your configuration with both `mcp-config` and `mcp-code-checker` is correct.

3. **Is there a need to move the mcp-code-checker code to a subfolder?**
   - No, the current folder structure is fine. The issue was just the incorrect entry point reference.

The fix ensures that when `mcp-code-checker` is installed via pip, the command will correctly locate and execute the main function from `src/main.py`.
