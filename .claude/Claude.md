# Claude AI Assistant Guidelines

## Pre-Commit Checklist

Before creating any commit, you MUST run the code formatting tools to ensure code quality and consistency.

### Formatting Commands

**On Linux/Unix/macOS:**
```bash
./tools/format_all.sh
```

**On Windows:**
```batch
tools\format_all.bat
```

### What Gets Formatted

The formatting scripts will run:
- **black**: Code formatter for Python
- **isort**: Import statement organizer

Both tools are configured in `pyproject.toml` with:
- Line length: 88 characters
- Target Python version: 3.11
- isort profile: black (for compatibility)

### Workflow

1. Make your code changes
2. Run the formatting script: `./tools/format_all.sh` (or `.bat` on Windows)
3. Review the formatting changes
4. Stage all changes: `git add .`
5. Create your commit: `git commit -m "descriptive message"`
6. Push to remote: `git push -u origin <branch-name>`

### Important Notes

- Always run formatters before committing
- The formatters will modify files in place
- All code must pass black and isort formatting
- CI/CD pipeline expects properly formatted code

## Development Environment

- Python version: 3.11+
- Code style: Black
- Import sorting: isort with black profile
- Type checking: mypy (strict mode)
- Testing: pytest
- Linting: pylint

## Additional Quality Checks

While not automated in the format_all scripts, consider running these before commits:

```bash
# Type checking
mypy src tests

# Linting
pylint src tests

# Running tests
pytest
```
