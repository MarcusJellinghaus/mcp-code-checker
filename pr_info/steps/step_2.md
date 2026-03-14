# Step 2: Refactor `get_pylint_prompt()` with `max_issues`, location cap, summary + tests

> **Context**: See `pr_info/steps/summary.md` for the full issue and architectural overview.  
> **Depends on**: Step 1 (`_group_and_sort_issues` helper).

## Goal

Refactor `get_pylint_prompt()` to accept `max_issues`, produce detailed output for the top N issue types (capped at 50 locations each), and append a summary of remaining issues. Handle `max_issues=0` (stats only) and zero-issues cases.

## WHERE

- **Test**: `tests/test_code_checker_pylint/test_reporting.py`
- **Implementation**: `src/mcp_code_checker/code_checker_pylint/reporting.py`

## WHAT — Updated Signature

```python
MAX_LOCATIONS_PER_ISSUE = 50

@log_function_call
def get_pylint_prompt(
    project_dir: str,
    extra_args: Optional[list[str]] = None,
    python_executable: Optional[str] = None,
    target_directories: Optional[list[str]] = None,
    max_issues: int = 1,  # NEW
) -> Optional[str]:
```

## HOW — Integration Points

- Uses `_group_and_sort_issues()` from Step 1
- Calls existing `get_prompt_for_known_pylint_code()` and `get_prompt_for_unknown_pylint_code()` for detailed sections (unchanged)
- The location cap (50) applies by slicing the messages list before passing to the existing prompt functions — use a **wrapper** that truncates + appends overflow note, rather than modifying the existing functions
- `_format_pylint_result` in server.py currently returns "No issues found" when prompt is None — the zero-issues case now returns a string instead of None, so adjust `_format_pylint_result` accordingly (or just return the string directly — handled in Step 3)

## ALGORITHM (pseudocode)

```
1. Run pylint, handle errors (unchanged)
2. groups = _group_and_sort_issues(pylint_results.messages)
3. If no groups: return None (caller handles zero-issues messaging)
4. If max_issues == 0: return stats-only format (total + per-type counts)
5. For each group in groups[:max_issues]:
     - Cap messages at MAX_LOCATIONS_PER_ISSUE
     - Generate detail via get_prompt_for_known/unknown (existing)
     - If capped, append "... and X more occurrences"
6. For remaining groups[max_issues:]:
     - Append summary line: "- {code} {symbol}: {count} occurrences"
7. Add contextual hint if remaining > 0: "Use max_issues=N to see more details"
8. Return joined output
```

## DATA — Output Format

### `max_issues=1` (default), multiple issue types:
```
pylint found some issues related to code E0602.
{instruction / fix details}
Please consider especially the following locations in the source code:
{up to 50 locations as JSON}
... and 5 more occurrences

--- 3 additional issue types found (14 occurrences) ---
- W0613 unused-argument: 4 occurrences
- C0411 wrong-import-order: 3 occurrences
- C0301 line-too-long: 7 occurrences

Use max_issues=4 to see details for all issue types.
```

### `max_issues=0` (stats only):
```
pylint found 4 issue types (18 total occurrences):
- E0602 undefined-variable: 3 occurrences
- W0613 unused-argument: 4 occurrences
- C0411 wrong-import-order: 4 occurrences
- C0301 line-too-long: 7 occurrences

Use max_issues=4 to see details for all issue types.
```

### Zero issues:
Returns `None` (unchanged behavior — `_format_pylint_result` handles messaging).

## Tests to Write FIRST

Add/modify in `test_reporting.py`. All tests mock `get_pylint_results` (same pattern as existing `TestGetPylintPrompt`).

### New test class `TestGetPylintPromptMaxIssues`:

1. **`test_zero_issues_returns_none`** — no messages → returns None (unchanged behavior)
2. **`test_max_issues_default_one_detail_plus_summary`** — 3 issue types, default max_issues=1 → first type detailed, other 2 in summary with correct format (`- {code} {symbol}: {count} occurrences`), includes "Use max_issues=" hint
3. **`test_max_issues_zero_stats_only`** — max_issues=0 → no details, just counts per type
4. **`test_max_issues_greater_than_types`** — max_issues=5 but only 2 types → both detailed, no summary section, no hint
5. **`test_location_cap_at_50`** — one issue type with 60 occurrences → only 50 shown in detail, "... and 10 more occurrences" appended
6. **`test_error_passthrough_unchanged`** — pylint error → still returns error string (unchanged behavior)

### Update existing `TestGetPylintPrompt`:

- Update `test_get_pylint_prompt_includes_warning_codes` to account for the new output format (the assertion `"W0613" in prompt` should still pass since detailed output includes the code)

## LLM Prompt

```
Implement Step 2 of Issue #32 (see pr_info/steps/summary.md and pr_info/steps/step_2.md).

Step 1 is already complete (_group_and_sort_issues helper exists in reporting.py).

TDD approach:
1. Add test class `TestGetPylintPromptMaxIssues` with all 9 test cases to
   `tests/test_code_checker_pylint/test_reporting.py`
2. Run tests to confirm they fail
3. Refactor `get_pylint_prompt()` in `reporting.py`:
   - Add MAX_LOCATIONS_PER_ISSUE = 50
   - Add max_issues parameter
   - Replace the current "pick first code" logic with the new loop
   - Keep existing get_prompt_for_known/unknown functions unchanged
4. Run tests to confirm they pass
5. Run pylint/mypy checks on the changed files

Important: Do NOT modify get_prompt_for_known_pylint_code or 
get_prompt_for_unknown_pylint_code. Handle the 50-location cap by 
creating a truncated PylintResult (with sliced messages list) before 
calling those functions.

See pr_info/steps/Decisions.md for all design decisions.
```
