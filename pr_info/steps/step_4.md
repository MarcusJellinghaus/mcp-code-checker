# Step 4: Update Configuration and Supporting Files

## Context
See [summary.md](summary.md) for full context.

This step completes the cleanup by removing all remaining references to the deleted modules and tools from configuration files and `utils/__init__.py`. Run Steps 3 and 4 together, or apply this step immediately after Step 3.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md for context.

Make the following changes:

1. `src/mcp_code_checker/utils/__init__.py`:
   - Remove the line: `from .data_files import find_data_file, find_package_data_files, get_package_directory`
   - Remove `"find_data_file"`, `"find_package_data_files"`, `"get_package_directory"` from `__all__`
   - Remove the `- data_files: Finding data files in development and installed environments`
     line from the module docstring.

2. `pyproject.toml`:
   - Remove the line: `"mcp_code_checker.resources" = ["sleep_script.py"]`
   - Also remove the comment above it: `# Include sleep_script.py from the src/mcp_code_checker/resources/ folder`
   - Keep `"*" = ["py.typed"]` and the rest of the `[tool.setuptools.package-data]` section.

3. `vulture_whitelist.py`:
   - Remove the line: `_.run_all_checks       # FastMCP tool handler`
   - Remove the line: `_.second_sleep         # FastMCP tool handler - used by MCP`

After making changes, run all three checks: pylint, pytest, mypy.
```

---

## WHERE

| File | Action |
|------|--------|
| `src/mcp_code_checker/utils/__init__.py` | Remove import, `__all__` entries, docstring line |
| `pyproject.toml` | Remove resources package-data entry + comment |
| `vulture_whitelist.py` | Remove two whitelist entries |

---

## WHAT

### `utils/__init__.py` — before/after

**Before** (docstring):
```
This package provides common utilities used across the codebase:
- subprocess_runner: Command execution with MCP STDIO isolation
- file_utils: File operation utilities
- data_files: Finding data files in development and installed environments
```

**After** (docstring):
```
This package provides common utilities used across the codebase:
- subprocess_runner: Command execution with MCP STDIO isolation
- file_utils: File operation utilities
```

**Before** (imports):
```python
from .data_files import find_data_file, find_package_data_files, get_package_directory
from .file_utils import read_file
from .subprocess_runner import (...)
```

**After** (imports):
```python
from .file_utils import read_file
from .subprocess_runner import (...)
```

**Before** (`__all__`):
```python
__all__ = [
    # Data file utilities
    "find_data_file",
    "find_package_data_files",
    "get_package_directory",
    # Core subprocess functionality
    ...
]
```

**After** (`__all__`):
```python
__all__ = [
    # Core subprocess functionality
    ...
]
```

### `pyproject.toml` — remove two lines

```toml
# Include sleep_script.py from the src/mcp_code_checker/resources/ folder  ← remove
"mcp_code_checker.resources" = ["sleep_script.py"]                          ← remove
```

Keep:
```toml
[tool.setuptools.package-data]
"*" = ["py.typed"]
```

### `vulture_whitelist.py` — remove two lines

```python
_.run_all_checks       # FastMCP tool handler      ← remove
_.second_sleep         # FastMCP tool handler - used by MCP  ← remove
```

---

## HOW

Config-only changes. No functional logic. The `utils/__init__.py` module continues to export `subprocess_runner` and `file_utils` symbols unchanged.

---

## ALGORITHM

N/A — configuration and import cleanup only.

---

## DATA

After this step:
- `utils.__all__` contains: `CommandOptions`, `CommandResult`, `execute_command`, `execute_subprocess`, `get_python_isolation_env`, `is_python_command`, `read_file`.
- `pyproject.toml` `[tool.setuptools.package-data]` contains only `"*" = ["py.typed"]`.
- `vulture_whitelist.py` has no entries for `run_all_checks` or `second_sleep`.

---

## Verification

Run all three checks — all must pass cleanly:
```
mcp__code-checker__run_pylint_check()
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto", "-m", "not integration"])
mcp__code-checker__run_mypy_check()
```

These passing checks confirm:
- No import errors from `utils/__init__.py`
- No test failures from remaining tests
- No type errors in the cleaned-up codebase
