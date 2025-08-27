# Manual CLI Command Testing Checklist

## Pre-Installation Tests
- [ ] Verify `mcp-code-checker` command doesn't exist
- [ ] Verify `python -m mcp_code_checker` fails

## Installation Tests
- [ ] Run `pip install -e .` in project directory
- [ ] Verify `mcp-code-checker --help` works
- [ ] Verify `mcp-config --help` works

## Command Tests
- [ ] Test: `mcp-code-checker --project-dir . --dry-run`
- [ ] Test: `mcp-code-checker --project-dir . --log-level DEBUG`
- [ ] Test: `mcp-code-checker --version` (if implemented)

## Configuration Tests
- [ ] Test: `mcp-config validate`
- [ ] Test: `mcp-config setup mcp-code-checker "test" --project-dir . --dry-run`
- [ ] Verify generated config uses `"command": "mcp-code-checker"`

## Virtual Environment Tests
- [ ] Create new venv: `python -m venv test_venv`
- [ ] Activate venv
- [ ] Install: `pip install -e .`
- [ ] Verify command works in venv
- [ ] Deactivate and verify command not available

## Uninstall Tests
- [ ] Run `pip uninstall mcp-code-checker`
- [ ] Verify command no longer exists
- [ ] Verify module mode fails

## Platform-Specific Tests

### Windows
- [ ] Test in Command Prompt (cmd.exe)
- [ ] Test in PowerShell
- [ ] Test in Git Bash

### macOS/Linux
- [ ] Test in bash
- [ ] Test in zsh
- [ ] Test with different Python versions
