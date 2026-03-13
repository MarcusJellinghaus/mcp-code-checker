# Decisions Log — Issue #89

Decisions made during plan review discussion.

## Decision 1: Missing test in Step 1

**Context:** `tests/test_code_checker/test_runners.py` line 103 asserts `result.environment_context is not None`. This will break when `EnvironmentContext` and `collect_environment_info()` are removed.

**Decision:** Add `tests/test_code_checker/test_runners.py` to Step 1's file list. Delete the assertion line entirely (the field is being removed from `PytestReport`, so no assertion is needed).

## Decision 2: Mypy "No module named" check placement

**Context:** `run_mypy_check()` already surfaces stderr when `return_code == 2` (config errors). The new "No module named" detection needs to integrate without duplicating.

**Decision:** Add the "No module named mypy" check **early**, right after `execute_command()` returns, before any parsing or existing return_code checks. This gives tool-missing detection priority over other error handling.

## Decision 3: Shared helper for error formatting

**Context:** All three runners need the same "No module named" detection + stderr truncation logic (~5 lines each).

**Decision:** Extract a shared helper function in `subprocess_runner.py` (e.g., `check_tool_missing_error(stderr, tool_name, python_path)`) alongside `MAX_STDERR_IN_ERROR`. DRY, consistent error messages, single place to update.

## Decision 4: Venv resolution — also refactor runners

**Context:** The summary mentioned "centralizing" venv resolution but Step 3 only added it to `server.py`. Runners (especially `run_tests()`) still do their own venv→executable resolution.

**Decision:** Expand Step 3 to also refactor runners to use the centralized resolution. In practice, `run_tests()` has internal venv resolution logic that should move to the server layer. The server resolves the python executable once and passes it down — which is already the pattern for pylint and mypy runners.

## Decision 5: Log resolved Python path at startup

**Context:** The plan only logged warnings when tools are missing. Logging the resolved path when everything is fine aids debugging.

**Decision:** Log the resolved Python executable path and tool availability at **DEBUG** level (not INFO). Keeps logs clean in normal operation but available when troubleshooting.

## Decision 6: Add `execute_command` to Step 1 import cleanup

**Context:** Step 1 listed `json`, `platform`, `sys` as imports to remove from `utils.py`, but `execute_command` is also only used by `collect_environment_info()` and should be removed.

**Decision:** Add `execute_command` to the import cleanup list in Step 1.

## Decision 7: Simplify TestMaxStderrTruncation tests

**Context:** The plan had a dedicated test class for `truncate_stderr()`, but it's a pure function with trivial logic.

**Decision:** Replace the `TestMaxStderrTruncation` class with 1-2 standalone test functions. Less boilerplate for trivial logic.

## Decision 8: Add restart note to README troubleshooting

**Context:** Tool availability is cached at startup. Users who install missing tools need to restart the server.

**Decision:** Add a note to the README troubleshooting section: "After installing missing tools, restart the MCP server for changes to take effect."

## Decision 9: Error message consistency between Steps 2 and 3

**Context:** Runner-level errors (Step 2) and server short-circuit errors (Step 3) have slightly different messages. Server version includes "Restart the server after installing."

**Decision:** Keep them different. Runner errors are runtime fallbacks; the server short-circuit is the primary path and is the only one that needs the restart hint.
