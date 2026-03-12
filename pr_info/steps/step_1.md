# Step 1: Remove `collect_environment_info()` Dead Code

## Context
See `pr_info/steps/summary.md` for full context. This is step 1 of 4.

## Goal
Remove `collect_environment_info()` and all related dead code. This function makes 4+ subprocess calls per pytest run using `sys.executable` (wrong executable), and the collected data is never surfaced to the MCP client.

## LLM Prompt
> Implement Step 1 of Issue #89 (see `pr_info/steps/summary.md` for context). Remove the `collect_environment_info()` dead code from the pytest module. The function, the `EnvironmentContext` model, and all references must be removed. Run tests afterward to confirm nothing breaks.

## WHERE

- `src/mcp_code_checker/code_checker_pytest/utils.py` — delete `collect_environment_info()` function
- `src/mcp_code_checker/code_checker_pytest/models.py` — delete `EnvironmentContext` dataclass, remove `environment_context` field from `PytestReport`
- `src/mcp_code_checker/code_checker_pytest/runners.py` — remove call to `collect_environment_info()`, remove `environment_info` from result dict

## WHAT

### In `utils.py`:
- **Delete**: `collect_environment_info(command: List[str]) -> EnvironmentContext` (entire function, ~100 lines)
- **Delete**: Import of `EnvironmentContext` from models
- **Delete**: Imports only used by `collect_environment_info`: `json`, `platform`, `sys` (verify no other usage first)
- **Keep**: `read_file()`, `get_pytest_exit_code_info()`, `create_error_context()`

### In `models.py`:
- **Delete**: `EnvironmentContext` dataclass (lines defining python_version, pytest_version, platform_info, installed_packages, loaded_plugins, command_line, working_directory, cpu_info, memory_info)
- **Delete**: `environment_context: Optional[EnvironmentContext] = None` field from `PytestReport`

### In `runners.py`:
- **Delete**: `from mcp_code_checker.code_checker_pytest.utils import collect_environment_info` (keep `create_error_context` and `read_file` imports)
- **Delete**: The call `environment_context = collect_environment_info(command)` (~line 121 in `run_tests()`)
- **Delete**: `parsed_results.environment_context = environment_context` (~line 185)
- **Delete**: The `environment_info` block in `check_code_with_pytest()` (~lines 262-273) that reads from `test_results.environment_context`
- **Delete**: `"environment_info": environment_info` from the return dict

## HOW
No new code — pure deletion. Verify that no other code references `EnvironmentContext` or `environment_context` or `environment_info` before deleting.

## ALGORITHM (pseudocode)
```
1. Delete EnvironmentContext from models.py
2. Remove environment_context field from PytestReport  
3. Delete collect_environment_info() from utils.py
4. Remove unused imports from utils.py (json, platform, sys if unused)
5. Remove collect_environment_info call + environment_info logic from runners.py
6. Run tests to confirm nothing breaks
```

## DATA
No new data structures. The `PytestReport` dataclass loses its `environment_context` field. The return dict from `check_code_with_pytest()` loses the `"environment_info"` key.

## Verification
- Run `mcp__code-checker__run_pytest_check` — all existing tests should pass
- Grep codebase for `environment_context`, `EnvironmentContext`, `collect_environment_info`, `environment_info` to confirm no remaining references
