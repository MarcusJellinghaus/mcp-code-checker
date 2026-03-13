# Step 4: Update Documentation (CLI Help + README)

## Context
See `pr_info/steps/summary.md` for full context. This is step 4 of 4.

## Goal
Update CLI `--help` strings and README to clarify that `--python-executable` / `--venv-path` should point to the tool's own venv (where pytest/pylint/mypy are installed), not the project's runtime venv.

## LLM Prompt
> Implement Step 4 of Issue #89 (see `pr_info/steps/summary.md` for context). Update the CLI help text in `main.py` for `--python-executable` and `--venv-path` to include guidance about pointing to the tool's venv. Add a Configuration/Troubleshooting section to `README.md` with correct vs. incorrect examples.

## WHERE

- `src/mcp_code_checker/main.py` — update argparse help strings
- `README.md` — add troubleshooting section

## WHAT

### In `main.py`:

**`--python-executable` help** — change from:
```python
"Path to Python interpreter to use for running tests. "
"If not specified, defaults to the current Python interpreter (sys.executable)"
```
To:
```python
"Path to Python interpreter for running pytest, pylint, and mypy. "
"Should point to the environment where these tools are installed "
"(the tool's own venv), not the project's runtime venv. "
"Defaults to the current Python interpreter (sys.executable)"
```

**`--venv-path` help** — change from:
```python
"Path to virtual environment to activate for running tests. "
"When specified, the Python executable from this venv will be used "
"instead of python-executable"
```
To:
```python
"Path to the virtual environment where pytest, pylint, and mypy are installed. "
"When specified, the Python executable from this venv will be used "
"instead of --python-executable. This should be the tool's own venv, "
"not the project's runtime venv"
```

### In `README.md`:

Add a new section **"## Environment Configuration"** after the "## Command Line Interface (CLI)" section. Content:

- Explanation that `--python-executable` and `--venv-path` must point to where pytest/pylint/mypy are installed
- Correct `.mcp.json` example (using `VIRTUAL_ENV`)
- Incorrect `.mcp.json` example (using project venv) with explanation of why it fails
- Troubleshooting: "If you see errors like 'No module named pytest', check that your configuration points to the correct environment"
- Restart note: "After installing missing tools, restart the MCP server for changes to take effect" (tool availability is cached at startup)

## HOW
Pure text changes — no code logic, no imports.

## ALGORITHM
N/A — documentation only.

## DATA
N/A — no data structures changed.

## Verification
- Run `mcp-code-checker --help` and verify updated descriptions
- Review README section for clarity and correctness
- Run full test suite to confirm no regressions from main.py changes
