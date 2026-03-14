# Step 1: Add `_group_and_sort_issues()` helper + tests (TDD)

> **Context**: See `pr_info/steps/summary.md` for the full issue and architectural overview.

## Goal

Add a private helper function to `reporting.py` that groups pylint messages by issue type and sorts them by severity then frequency. Write tests first (TDD).

## WHERE

- **Test**: `tests/test_code_checker_pylint/test_reporting.py`
- **Implementation**: `src/mcp_code_checker/code_checker_pylint/reporting.py`

## WHAT — Function Signature

```python
# In reporting.py

# Severity priority: lower = more severe
SEVERITY_PRIORITY: dict[str, int] = {
    "fatal": 0,
    "error": 1,
    "warning": 2,
    "refactor": 3,
    "convention": 4,
}

class IssueGroup(NamedTuple):
    """A group of pylint messages sharing the same message_id."""
    message_id: str
    symbol: str
    type: str
    messages: list[PylintMessage]

def _group_and_sort_issues(messages: list[PylintMessage]) -> list[IssueGroup]:
    """Group messages by message_id, sort by severity then frequency (descending)."""
```

## HOW — Integration Points

- Import: Uses `PylintMessage` from `models.py` (already imported)
- No decorator needed — private helper
- No new exports in `__init__.py` — underscore-prefixed = private
- `IssueGroup` is a module-level type alias, not a class

## ALGORITHM (pseudocode)

```
1. Group messages into dict[message_id -> list[PylintMessage]]
2. For each group, extract (message_id, symbol, type) from first message
3. Sort groups by:
   a. SEVERITY_PRIORITY.get(type, 99) ascending (fatal first, unknown last)
   b. len(messages) descending (most frequent first)  
4. Return list of (message_id, symbol, type, messages) tuples
```

## DATA — Return Value

```python
# Input: list of PylintMessage objects (unsorted, mixed types)
# Output example:
[
    IssueGroup("E0602", "undefined-variable", "error", [msg1, msg2, msg3]),   # 3 errors
    IssueGroup("W0613", "unused-argument", "warning", [msg4, msg5]),           # 2 warnings
    IssueGroup("C0411", "wrong-import-order", "convention", [msg6]),           # 1 convention
]
```

## Tests to Write FIRST

Add a new test class `TestGroupAndSortIssues` in `test_reporting.py`:

```python
from mcp_code_checker.code_checker_pylint.reporting import _group_and_sort_issues
```

### Test cases:

1. **`test_empty_messages`** — empty list returns empty list
2. **`test_single_issue_type`** — one message_id, returns single group
3. **`test_severity_ordering`** — fatal before error before warning before convention
4. **`test_frequency_ordering_within_same_severity`** — more occurrences first among same severity level
5. **`test_severity_takes_precedence_over_frequency`** — 1 error sorts before 10 conventions
6. **`test_group_contains_all_messages`** — each group has all messages for that message_id

## LLM Prompt

```
Implement Step 1 of Issue #32 (see pr_info/steps/summary.md for context).

Read pr_info/steps/step_1.md for the detailed specification.

TDD approach:
1. First, add the test class `TestGroupAndSortIssues` to 
   `tests/test_code_checker_pylint/test_reporting.py` with all 6 test cases
2. Run tests to confirm they fail
3. Add `SEVERITY_PRIORITY`, `IssueGroup` type alias, and `_group_and_sort_issues()` 
   to `src/mcp_code_checker/code_checker_pylint/reporting.py`
4. Run tests to confirm they pass
5. Run pylint/mypy checks on the changed files
```
