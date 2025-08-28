# MCP Code Checker Packaging Fix

## Problem Description

When installing the package with:
```bash
pip install --force-reinstall git+https://github.com/MarcusJellinghaus/mcp-code-checker.git@config_helper
```

And then running `mcp-code-checker`, the following error occurred:
```
ModuleNotFoundError: No module named 'src'
```

## Root Cause Analysis

The issue was in the `pyproject.toml` packaging configuration. The problems were:

1. **Incorrect console script entry points**: The `[project.scripts]` section was using `src.main:main` and `src.config.main:main`, which assumes `src` is available as a top-level module
2. **Missing package directory configuration**: The setuptools configuration didn't properly map the `src` directory as the package root
3. **Incomplete package finding setup**: The `[tool.setuptools.packages.find]` section was incomplete

## Solution

### 1. Fixed setuptools configuration

Added the correct package directory mapping:
```toml
[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

This tells setuptools that the package root is in the `src` directory, so modules like `main.py` and `config/main.py` become importable as `main` and `config.main` respectively.

### 2. Corrected console script entry points

Changed from:
```toml
[project.scripts]
mcp-config = "src.config.main:main"
mcp-code-checker = "src.main:main"
```

To:
```toml
[project.scripts]
mcp-config = "config.main:main"
mcp-code-checker = "main:main"
```

With the `package-dir = {"" = "src"}` configuration, the modules are now accessible without the `src.` prefix.

## How the Fix Works

1. **Package Directory Mapping**: `package-dir = {"" = "src"}` tells setuptools that the root package (empty string "") is located in the `src` directory
2. **Module Resolution**: When Python looks for `main` module, it finds `src/main.py`
3. **Console Script Generation**: The entry points now correctly reference `main:main` instead of `src.main:main`
4. **Import Compatibility**: The relative imports in the source code (like `from .log_utils import setup_logging`) continue to work as expected

## Testing the Fix

After applying these changes, users should:

1. Reinstall the package:
   ```bash
   pip install --force-reinstall git+https://github.com/MarcusJellinghaus/mcp-code-checker.git@config_helper
   ```

2. Test the console commands:
   ```bash
   mcp-code-checker --help
   mcp-config --help
   ```

Both commands should now work without the `ModuleNotFoundError`.

## Alternative Solutions Considered

1. **Using src layout with __init__.py**: Would require making `src` a proper package, but this contradicts the src-layout pattern
2. **Flat layout**: Moving all modules to the project root, but this would break the established project structure
3. **Different entry point format**: Using module syntax like `-m src.main`, but this doesn't work well with console scripts

The chosen solution maintains the existing src-layout structure while fixing the packaging configuration to work correctly with pip install.
