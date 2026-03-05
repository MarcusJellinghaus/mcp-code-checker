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

### Step 1: Update `runners.py` — Replace `disable_codes` with `extra_args`
See [step_1.md](./steps/step_1.md) for full details.

- [ ] Update `tests/test_code_checker_pylint_main.py`: delete `test_run_pylint_check`, update `test_get_pylint_results_no_issues` to use `extra_args=[\"--disable=C0114,C0116\"]`, remove `run_pylint_check` import
- [ ] Update `src/mcp_code_checker/code_checker_pylint/runners.py`: rename `disable_codes` → `extra_args` in `get_pylint_results()`, replace `--disable=...` join logic with `pylint_command.extend(extra_args)`, delete `run_pylint_check()` entirely
- [ ] Update `src/mcp_code_checker/code_checker_pylint/__init__.py`: remove `run_pylint_check` from imports and `__all__`
- [ ] Run pylint, pytest, mypy — fix all issues found
- [ ] Prepare git commit message for Step 1

---

### Step 2: Update `reporting.py` — Remove Category Filter, Add `extra_args`
See [step_2.md](./steps/step_2.md) for full details.

- [ ] Update `tests/test_code_checker_pylint/test_reporting.py`: remove `categories=` and `disable_codes=` args from all `get_pylint_prompt` calls, add test verifying warning-level codes are included
- [ ] Update `src/mcp_code_checker/code_checker_pylint/reporting.py`: replace `categories`/`disable_codes` params with `extra_args`, remove `DEFAULT_CATEGORIES` fallback block, remove `disable_codes` defaults block, remove `filter_pylint_codes_by_category` call, remove unused imports (`DEFAULT_CATEGORIES`, `PylintMessageType`, `filter_pylint_codes_by_category`)
- [ ] Run pylint, pytest, mypy — fix all issues found
- [ ] Prepare git commit message for Step 2

---

### Step 3: Update `server.py` — Update MCP Tools, Delete `_parse_pylint_categories`
See [step_3.md](./steps/step_3.md) for full details.

- [ ] Update `tests/test_server_params.py`: remove `categories=[\"error\"]` from `run_all_checks` call, remove assertions checking pylint was called with categories, add test verifying `run_pylint_check` signature has `extra_args` and no `categories`/`disable_codes`
- [ ] Update `src/mcp_code_checker/server.py`: delete `_parse_pylint_categories()` method, update `run_pylint_check` MCP tool (remove `categories`/`disable_codes` params, add `extra_args`, update `get_pylint_prompt` call), update `run_all_checks` MCP tool (remove `categories` param, remove `_parse_pylint_categories` call, update `get_pylint_prompt` call), remove `PylintMessageType` from imports
- [ ] Run pylint, pytest, mypy — fix all issues found
- [ ] Prepare git commit message for Step 3

---

### Step 4: Dead Code Removal — `models.py`, `utils.py`, `__init__.py`
See [step_4.md](./steps/step_4.md) for full details.

- [ ] Remove dead tests first: delete `test_default_categories` from `tests/test_code_checker_pylint/test_models.py`, delete `TestFilterPylintCodesByCategory` from `tests/test_code_checker_pylint/test_utils.py`, delete `test_default_categories_from_init` and `TestFilterPylintCodesByCategory` from `tests/test_code_checker_pylint_main.py`, remove corresponding imports
- [ ] Verify tests still pass after test removal
- [ ] Remove `DEFAULT_CATEGORIES` constant from `src/mcp_code_checker/code_checker_pylint/models.py` (and `Set` from typing if unused)
- [ ] Remove `filter_pylint_codes_by_category` function from `src/mcp_code_checker/code_checker_pylint/utils.py` (and unused imports)
- [ ] Remove `PylintCategory` alias from `src/mcp_code_checker/code_checker_pylint/models.py`
- [ ] Update `src/mcp_code_checker/code_checker_pylint/__init__.py`: remove `DEFAULT_CATEGORIES`, `filter_pylint_codes_by_category`, `PylintCategory` from imports and `__all__`
- [ ] Run pylint, pytest, mypy — fix all issues found
- [ ] Prepare git commit message for Step 4

---

### Step 5: Config + Docs — `pyproject.toml`, `docs/`, `README.md`
See [step_5.md](./steps/step_5.md) for full details.

- [ ] Add `[tool.pylint.messages_control]` section to `pyproject.toml` (after `[tool.mypy]`): `disable = ["W", "C", "R"]`
- [ ] Create `docs/pyproject-configuration.md`: cover how pylint reads pyproject.toml, recommended config to replicate old ERROR/FATAL default, finer-grained code config, `extra_args` one-off override usage, link to pylint messages reference
- [ ] Update `README.md`: remove `categories` and `disable_codes` rows from Pylint Parameters table, add `extra_args` row, add `### Pylint Configuration` subsection linking to the new docs file
- [ ] Run pylint to verify project still runs cleanly with the new config
- [ ] Prepare git commit message for Step 5

---

## Pull Request

- [ ] Review all changes across Steps 1–5 for correctness and consistency
- [ ] Verify all tests pass and no regressions introduced
- [ ] Write PR summary describing the problem solved, architectural changes, and migration guidance for users
