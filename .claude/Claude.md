# Claude System Instructions

## Core Workflow Rules

1. **After completing file edits:** Run `pytest`, `pylint`, and `mypy`

2. **Before committing:** Run formatter (`./tools/format_all.sh` or `tools\format_all.bat`)

3. **Tool preference:** Use MCP tools if available - strictly prefer them over alternatives
