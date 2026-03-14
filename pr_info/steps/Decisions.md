# Decisions for Issue #32

## Decision 1: `IssueGroup` type — NamedTuple
Use a `NamedTuple` instead of a plain tuple type alias for `IssueGroup`. This is consistent with the existing pattern in `models.py` (`PylintMessage`, `PylintResult`) and makes fields self-documenting.

## Decision 2: Unknown severity fallback — silent `.get()`
Use `SEVERITY_PRIORITY.get(type, 99)` so unknown severity types sort last silently. No warning log needed.

## Decision 3: Zero-issues return — keep `None`
`get_pylint_prompt` continues to return `None` when there are no issues. `_format_pylint_result` already handles `None` → "No issues found" messaging. This avoids any logging changes in `server.py`.

## Decision 4: Step 2 test count — merge to 6 tests
Merge overlapping tests: fold `test_summary_section_format` and `test_contextual_hint_when_remaining` into `test_max_issues_default_one_detail_plus_summary`, and fold `test_no_hint_when_all_detailed` into `test_max_issues_greater_than_types`. Result: 6 tests with same coverage, less maintenance.

## Decision 5: Server integration tests — `test_server_params.py`
Place the Step 3 server integration tests in the existing `tests/test_server_params.py` instead of `test_reporting.py`. Server tests belong with server tests.

## Decision 6: Remove `run_all_checks` bullet from Step 3
There is no `run_all_checks` tool in `server.py`. Remove the bullet to avoid confusion during implementation.

## Decision 7: Location cap — truncated `PylintResult`
Apply the 50-location cap by constructing a truncated `PylintResult` with sliced messages. Do not modify existing `get_prompt_for_known_pylint_code` or `get_prompt_for_unknown_pylint_code` functions.
