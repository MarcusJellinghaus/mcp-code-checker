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

### Step 1: Remove `collect_environment_info()` Dead Code — [step_1.md](./steps/step_1.md)
- [x] Remove `EnvironmentContext` dataclass and `environment_context` field from `models.py`, delete `collect_environment_info()` from `utils.py`, remove call and `environment_info` logic from `runners.py`, update test assertions
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues found
- [x] Prepare git commit message for Step 1

### Step 2: Add Stderr Surfacing and "No Module Named" Detection — [step_2.md](./steps/step_2.md)
- [ ] Add `MAX_STDERR_IN_ERROR` constant, `check_tool_missing_error()` and `truncate_stderr()` helpers to `subprocess_runner.py`; improve error messages in pytest, pylint, and mypy runners; create `tests/test_error_transparency.py` with TDD tests
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues found
- [ ] Prepare git commit message for Step 2

### Step 3: Add Startup Tool Validation in Server — [step_3.md](./steps/step_3.md)
- [ ] Add `_resolve_python_executable()`, `_check_tool_availability()` to `CodeCheckerServer`, add short-circuit checks in tool handlers, remove internal venv resolution from pytest `run_tests()`; create `tests/test_tool_availability.py` with TDD tests
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues found
- [ ] Prepare git commit message for Step 3

### Step 4: Update Documentation (CLI Help + README) — [step_4.md](./steps/step_4.md)
- [ ] Update `--python-executable` and `--venv-path` help strings in `main.py`; add Environment Configuration / Troubleshooting section to `README.md`
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues found
- [ ] Prepare git commit message for Step 4

## Pull Request
- [ ] Review all changes across steps for consistency and completeness
- [ ] Prepare PR title, summary, and description
