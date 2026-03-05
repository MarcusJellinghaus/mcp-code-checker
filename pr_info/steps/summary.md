# Summary: Simplify run_pylint_check — Remove Category Filter, Add extra_args, Defer to pyproject.toml

## Issue
GitHub Issue #85

## Problem Statement

`run_pylint_check` silently suppressed pylint output via two hardcoded mechanisms:

1. **`disable_codes` defaults** — a fixed list of codes passed as CLI flags, overriding any `pyproject.toml` settings before pylint even runs
2. **`categories` post-filter** — discards all messages except ERROR and FATAL after pylint runs

This meant that warnings a project explicitly configured in `pyproject.toml` were never surfaced. The MCP layer was overriding and undermining the project's own pylint configuration.

**Key insight:** Pylint already reads `pyproject.toml` automatically. The MCP tool should pass results through cleanly and let `pyproject.toml` be the single source of truth.

---

## Architectural / Design Changes

### Before

```
MCP tool run_pylint_check(categories, disable_codes, target_directories)
    └─► _parse_pylint_categories(categories) → Set[PylintMessageType]
    └─► get_pylint_prompt(categories, disable_codes, ...)
            └─► get_pylint_results(disable_codes, ...)   # adds --disable=C0114,C0116,...
            └─► filter_pylint_codes_by_category(codes, categories)  # drops W/C/R
            └─► generate prompt for first remaining code
```

Two independent suppression layers stacked on top of each other.

### After

```
MCP tool run_pylint_check(extra_args, target_directories)
    └─► get_pylint_prompt(extra_args, ...)
            └─► get_pylint_results(extra_args, ...)   # passes args straight to pylint CLI
            └─► generate prompt for first code reported by pylint
```

No post-filtering. No hardcoded defaults. Pylint's own output (governed by `pyproject.toml`) is used as-is.

### Design Principle Applied

**Single source of truth:** `pyproject.toml` controls what pylint reports.  
Users who want to replicate the old `{ERROR, FATAL}` default add this to their `pyproject.toml`:
```toml
[tool.pylint.messages_control]
disable = ["W", "C", "R"]
```

---

## Files Modified or Created

### Modified

| File | Change |
|------|--------|
| `src/mcp_code_checker/code_checker_pylint/runners.py` | Replace `disable_codes` with `extra_args` in `get_pylint_results`; delete `run_pylint_check` (unused wrapper) |
| `src/mcp_code_checker/code_checker_pylint/reporting.py` | Remove `categories` + `disable_codes`; add `extra_args`; remove `filter_pylint_codes_by_category` call |
| `src/mcp_code_checker/code_checker_pylint/models.py` | Remove `DEFAULT_CATEGORIES` constant |
| `src/mcp_code_checker/code_checker_pylint/utils.py` | Remove `filter_pylint_codes_by_category` function (dead code) |
| `src/mcp_code_checker/code_checker_pylint/__init__.py` | Remove `DEFAULT_CATEGORIES`, `filter_pylint_codes_by_category`, `run_pylint_check`, `PylintCategory` from exports |
| `src/mcp_code_checker/server.py` | Delete `_parse_pylint_categories`; update `run_pylint_check` and `run_all_checks` MCP tools |
| `pyproject.toml` | Add `[tool.pylint.messages_control]` section |
| `README.md` | Update Pylint Parameters table; add config section |
| `tests/test_code_checker_pylint_main.py` | Update API call sites; remove tests for deleted code |
| `tests/test_code_checker_pylint/test_models.py` | Remove `test_default_categories` |
| `tests/test_code_checker_pylint/test_utils.py` | Remove `TestFilterPylintCodesByCategory` |
| `tests/test_code_checker_pylint/test_reporting.py` | Update to new `get_pylint_prompt` signature |
| `tests/test_server_params.py` | Remove `categories` from `run_all_checks` call |

### Created

| File | Purpose |
|------|---------|
| `docs/pyproject-configuration.md` | Migration guide and configuration reference |

---

## What Is NOT Changed

- `PylintMessageType` enum — kept in `models.py`
- `normalize_path` in `utils.py` — still used by `reporting.py`
- `target_directories` and `python_executable` parameters — unchanged throughout
- All pytest and mypy tooling — unaffected

## What Is Also Removed (decided during plan review)

- `run_pylint_check()` in `runners.py` — unused wrapper, deleted in Step 1 (D2)
- `PylintCategory` alias in `models.py` — dead backward-compat alias, deleted in Step 4 (D1)

---

## Step Overview

| Step | Focus | TDD |
|------|-------|-----|
| Step 1 | `runners.py` — replace `disable_codes` with `extra_args` | Yes |
| Step 2 | `reporting.py` — remove category filter, add `extra_args` | Yes |
| Step 3 | `server.py` — update MCP tools, delete `_parse_pylint_categories` | Yes |
| Step 4 | Dead code removal — `models.py`, `utils.py`, `__init__.py` | Yes (remove tests first) |
| Step 5 | Config + docs — `pyproject.toml`, `docs/`, `README.md` | No (config/docs only) |
