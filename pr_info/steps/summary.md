# Issue #32: pylint checker — add `max_issues` parameter

## Summary

Enhance `run_pylint_check` so it shows **full details for the top N issue types** (sorted by severity, then frequency) plus a **summary count of all remaining issue types**, instead of only reporting the first arbitrary issue type.

## Architectural / Design Changes

### Current Design
- `get_pylint_prompt()` picks the **first** issue type from a Python `set` (arbitrary order)
- Returns details for that single code only; all other issue types are silently ignored
- No summary, no statistics, no way to control output scope

### New Design
- `get_pylint_prompt()` accepts `max_issues: int = 1`
- A new private helper `_group_and_sort_issues()` in `reporting.py` groups messages by `message_id` and sorts by severity (fatal > error > warning > refactor > convention), then by frequency (descending)
- Top `max_issues` issue types get full detailed output (reusing existing known/unknown prompt functions), capped at **50 locations** per type
- Remaining issue types appear as a flat summary: `- {code} {symbol}: {count} occurrences`
- `max_issues=0` produces statistics-only output
- Zero issues returns `None` (unchanged — `_format_pylint_result` handles messaging)

### Key Design Decisions
- **No changes to `models.py`** — grouping/sorting is a presentation concern, lives in `reporting.py`
- **Minimal new abstractions** — one `IssueGroup` NamedTuple, one ~15-line helper function
- **Existing helper functions unchanged** — `get_prompt_for_known_pylint_code` and `get_prompt_for_unknown_pylint_code` stay as-is, called from a loop
- **Backward compatible** — default `max_issues=1` gives enhanced version of current behavior (but now deterministically sorted instead of arbitrary)
- **Slim docstring** in `server.py` to reduce token overhead on every MCP call

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_code_checker/code_checker_pylint/reporting.py` | Add `IssueGroup` NamedTuple, `_group_and_sort_issues()` helper; refactor `get_pylint_prompt()` to use it with `max_issues` + location cap + summary |
| `src/mcp_code_checker/server.py` | Add `max_issues` param to `run_pylint_check`, pass through, slim docstring |
| `tests/test_code_checker_pylint/test_reporting.py` | Tests for sorting, `max_issues=0/1/N`, location cap, zero-issues, summary format |
| `tests/test_server_params.py` | Server integration tests for `max_issues` passthrough |

## Files NOT Modified

| File | Reason |
|------|--------|
| `models.py` | No new data structures needed — KISS |
| `runners.py` | Execution logic unchanged |
| `parsers.py` | Parsing logic unchanged |
| `__init__.py` | No new public exports (helper is private) |

## Implementation Steps

1. **Step 1** — `_group_and_sort_issues()` helper + its unit tests (TDD)
2. **Step 2** — Refactor `get_pylint_prompt()` with `max_issues`, location cap, summary output + tests
3. **Step 3** — Wire `max_issues` into `server.py`, slim docstring + integration test
