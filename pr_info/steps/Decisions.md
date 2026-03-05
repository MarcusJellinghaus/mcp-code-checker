# Decisions

Decisions made during plan review discussion for issue #85.

---

## D1: Remove `PylintCategory` alias (Step 4)

**Decision:** Remove `PylintCategory` from `models.py` and `__init__.py` along with the other dead code in Step 4.

**Rationale:** `PylintCategory = PylintMessageType` was a backward-compatibility alias with no known external users.
After the refactoring it has no callers anywhere (the tests that used it are deleted in Step 4).
It is dead code and should be removed.

**Impact:** Step 4 deletes `PylintCategory` from `models.py`, `__init__.py` imports, and `__all__`.

---

## D2: Remove `run_pylint_check` from `runners.py` (Step 1)

**Decision:** Delete `run_pylint_check()` from `runners.py` entirely rather than keeping it as a thin wrapper.

**Rationale:** The function is not called by any production code.
The call chain is `server.py → get_pylint_prompt() → get_pylint_results()` — `run_pylint_check` in
`runners.py` is never invoked. Keeping it would be misleading.

**Impact:** Step 1 deletes the function, removes it from `__init__.py` exports, and deletes `test_run_pylint_check`.

---

## D3: No `pylint_extra_args` on `run_all_checks` (Step 3)

**Decision:** `run_all_checks` will not gain a `pylint_extra_args` parameter.

**Rationale:** Users needing fine-grained pylint control should call `run_pylint_check` directly.
`run_all_checks` keeps its existing `extra_args` for pytest only. This keeps the combined tool simple.

**Impact:** No change to `run_all_checks` signature beyond removing `categories`.

---

## D4: Remove manual verification step from Step 5

**Decision:** Remove the manual pylint verification step from Step 5.

**Rationale:** No automated test was added as a replacement; the step was simply dropped as unnecessary overhead.

**Impact:** Step 5 no longer includes a manual `python -m pylint src tests` verification command.
