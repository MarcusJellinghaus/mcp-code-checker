# Step 4: Dead Code Removal — `models.py`, `utils.py`, `__init__.py`

## Context
See `pr_info/steps/summary.md` for full architectural context.  
Depends on Steps 1–3. At this point, `DEFAULT_CATEGORIES` and `filter_pylint_codes_by_category`
have no remaining callers in production code.

For TDD, tests for dead code are removed first, then the dead code itself.

---

## WHERE

| File | Action |
|------|--------|
| `tests/test_code_checker_pylint/test_models.py` | Remove `test_default_categories` |
| `tests/test_code_checker_pylint/test_utils.py` | Remove `TestFilterPylintCodesByCategory` |
| `tests/test_code_checker_pylint_main.py` | Remove `TestFilterPylintCodesByCategory` class + `test_default_categories_from_init` |
| `src/mcp_code_checker/code_checker_pylint/models.py` | Remove `DEFAULT_CATEGORIES` |
| `src/mcp_code_checker/code_checker_pylint/utils.py` | Remove `filter_pylint_codes_by_category` |
| `src/mcp_code_checker/code_checker_pylint/__init__.py` | Remove dead exports |

---

## WHAT

### Remove from `models.py`
```python
# DELETE this constant:
DEFAULT_CATEGORIES: Set[PylintMessageType] = {
    PylintMessageType.ERROR,
    PylintMessageType.FATAL,
}
```

Also remove `Set` from the `typing` import if it is no longer used elsewhere in the file.

### Remove from `utils.py`
```python
# DELETE this entire function:
def filter_pylint_codes_by_category(
    pylint_codes: Set[str],
    categories: Set[PylintMessageType],
) -> Set[str]:
    ...
```

If `PylintMessageType` and `Set` are only used by this function, remove those imports too.

### Remove from `__init__.py`
```python
# Remove these from the import block:
DEFAULT_CATEGORIES,        # from models
filter_pylint_codes_by_category,  # from utils

# Remove from __all__:
"DEFAULT_CATEGORIES",
"filter_pylint_codes_by_category",
```

Keep all other exports unchanged (`PylintMessageType`, `PylintMessage`,
`PylintResult`, `get_pylint_results`, `get_pylint_prompt`,
`get_direct_instruction_for_pylint_code`, `normalize_path`).

Note: `run_pylint_check` was already removed from `__init__.py` in Step 1.

**Also remove `PylintCategory`** — it is an unused backward-compatibility alias
(`PylintCategory = PylintMessageType` in `models.py`). No external users exist;
it should be deleted from `models.py`, removed from `__init__.py` imports and `__all__`.

---

## HOW

No integration points — this is pure deletion.  
The TDD approach here is: **remove tests first, confirm tests pass, then remove code.**

Rationale: Removing tests before code causes test failures that confirm the code is still present;
removing code after tests ensures nothing unexpected depended on it.

Correct order for this step:
1. Remove test classes/functions for dead code → run tests (should pass; dead tests are gone)
2. Remove `DEFAULT_CATEGORIES` from `models.py`
3. Remove `filter_pylint_codes_by_category` from `utils.py`
4. Remove exports from `__init__.py`
5. Run all tests → should pass

---

## ALGORITHM

```
No algorithmic logic — pure deletion step.

For each file:
  1. identify dead symbol (DEFAULT_CATEGORIES, filter_pylint_codes_by_category)
  2. remove its definition
  3. remove its imports in other files
  4. remove from __all__ in __init__.py
  5. run tests to confirm nothing broke
```

---

## DATA

No new data structures. The `PylintMessageType` enum is **kept** — it is not dead code
(it is part of the public API and documents the pylint message type vocabulary).

---

## Tests to Remove

### `tests/test_code_checker_pylint/test_models.py`
```python
# DELETE:
def test_default_categories() -> None:
    assert DEFAULT_CATEGORIES == {PylintMessageType.ERROR, PylintMessageType.FATAL}
```
Also remove `DEFAULT_CATEGORIES` from the import at the top of the file.

### `tests/test_code_checker_pylint/test_utils.py`
```python
# DELETE entire class:
class TestFilterPylintCodesByCategory:
    ...
```
Also remove `filter_pylint_codes_by_category` from the import.

### `tests/test_code_checker_pylint_main.py`
```python
# DELETE:
def test_default_categories_from_init() -> None: ...

# DELETE entire class:
class TestFilterPylintCodesByCategory: ...
```
Also remove `DEFAULT_CATEGORIES`, `PylintCategory`, `filter_pylint_codes_by_category`
from the import at the top (they are no longer used after the deletions).

---

## LLM Prompt

```
You are implementing Step 4 of a refactoring task for the mcp-code-checker project.
Read pr_info/steps/summary.md and pr_info/steps/step_4.md for full context.
Steps 1–3 are complete. `DEFAULT_CATEGORIES` and `filter_pylint_codes_by_category`
have no remaining production callers.

TASK:
Remove dead code from the pylint checker package. Follow the order below.

STEP ORDER (important for TDD):

1. Remove tests for dead code FIRST:
   - In `tests/test_code_checker_pylint/test_models.py`:
     remove `test_default_categories()` and `DEFAULT_CATEGORIES` from its import
   - In `tests/test_code_checker_pylint/test_utils.py`:
     remove `TestFilterPylintCodesByCategory` class and `filter_pylint_codes_by_category` import
   - In `tests/test_code_checker_pylint_main.py`:
     remove `test_default_categories_from_init()`, `TestFilterPylintCodesByCategory` class,
     and `DEFAULT_CATEGORIES`, `PylintCategory`, `filter_pylint_codes_by_category` imports
     (only if they are no longer used in the remaining tests)

2. Run tests — they should all pass.

3. Remove production dead code:
   - In `src/mcp_code_checker/code_checker_pylint/models.py`:
     remove `DEFAULT_CATEGORIES` constant; remove `Set` from typing import if unused
   - In `src/mcp_code_checker/code_checker_pylint/utils.py`:
     remove `filter_pylint_codes_by_category` function; remove unused imports
   - In `src/mcp_code_checker/code_checker_pylint/__init__.py`:
     remove `DEFAULT_CATEGORIES` and `filter_pylint_codes_by_category` from imports and `__all__`

4. Run all tests again — should all pass.

Do NOT remove `PylintMessageType`, `normalize_path`, or any other symbols.
`PylintCategory` IS removed (it is a dead backward-compatibility alias — see step_4.md).
Do not modify any files outside this scope.
```
