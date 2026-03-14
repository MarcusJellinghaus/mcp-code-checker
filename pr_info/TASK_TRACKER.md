# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Add `_group_and_sort_issues()` helper + tests (TDD) — [step_1.md](./steps/step_1.md)

- [x] Implement `_group_and_sort_issues()` helper, `IssueGroup` NamedTuple, and `SEVERITY_PRIORITY` in `reporting.py`; write tests first (TDD)
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message

### Step 2: Refactor `get_pylint_prompt()` with `max_issues` + location cap + summary — [step_2.md](./steps/step_2.md)

- [ ] Refactor `get_pylint_prompt()` to accept `max_issues`, produce detailed output for top N issue types (capped at 50 locations each), and append summary of remaining issues; write tests first (TDD)
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message

### Step 3: Wire `max_issues` into `server.py`, slim docstring + integration test — [step_3.md](./steps/step_3.md)

- [ ] Add `max_issues` parameter to `run_pylint_check` in `server.py`, pass through to `get_pylint_prompt()`, slim docstring, simplify `_format_pylint_result`; write tests in `test_server_params.py`
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message

## Pull Request

- [ ] Review all changes across steps for consistency and completeness
- [ ] Prepare PR summary and description
