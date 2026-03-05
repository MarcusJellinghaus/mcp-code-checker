# Step 1: Update `runners.py` — Replace `disable_codes` with `extra_args`

## Context
See `pr_info/steps/summary.md` for full architectural context.

This step replaces the hardcoded `disable_codes` mechanism in the runner layer with a transparent `extra_args` pass-through. No defaults are applied — callers control pylint output via `pyproject.toml`.

---

## WHERE

| File | Action |
|------|--------|
| `tests/test_code_checker_pylint_main.py` | Update tests — write first |
| `src/mcp_code_checker/code_checker_pylint/runners.py` | Update implementation |

---

## WHAT

### `get_pylint_results()` — updated signature
```python
def get_pylint_results(
    project_dir: str,
    extra_args: Optional[List[str]] = None,
    python_executable: Optional[str] = None,
    target_directories: Optional[List[str]] = None,
) -> PylintResult:
```

### `run_pylint_check()` — updated signature
```python
def run_pylint_check(
    project_dir: str,
    extra_args: Optional[List[str]] = None,
    python_executable: Optional[str] = None,
    target_directories: Optional[List[str]] = None,
) -> PylintResult:
```

---

## HOW

### `get_pylint_results()` — command construction change

**Before:**
```python
if disable_codes and len(disable_codes) > 0:
    pylint_command.append(f"--disable={','.join(disable_codes)}")
```

**After:**
```python
if extra_args:
    pylint_command.extend(extra_args)
```

### `run_pylint_check()` — becomes a thin pass-through

**Before:** applied hardcoded `disable_codes` defaults + category filtering block  
**After:** calls `get_pylint_results()` with `extra_args`, returns result directly

Remove the `categories` parameter and the entire category-filtering block entirely. Remove the hardcoded `disable_codes` default list.

---

## ALGORITHM

```
get_pylint_results(project_dir, extra_args, python_executable, target_directories):
  validate project_dir exists
  resolve valid target_directories (skip missing ones)
  build command: [python, "-m", "pylint", "--output-format=json"]
  if extra_args: extend command with extra_args directly
  extend command with valid target_directories
  execute command via execute_command()
  parse JSON output → List[PylintMessage]
  return PylintResult(return_code, messages, error, raw_output)

run_pylint_check(project_dir, extra_args, python_executable, target_directories):
  return get_pylint_results(project_dir, extra_args, python_executable, target_directories)
```

---

## DATA

**Input `extra_args` examples:**
- `None` — no extra flags (pylint reads `pyproject.toml` alone)
- `["--disable=W0611"]` — suppress one specific warning ad-hoc
- `["--enable=W0613", "--disable=C"]` — complex flag combinations

**Return:** `PylintResult` (unchanged NamedTuple):
```python
PylintResult(
    return_code: int,
    messages: List[PylintMessage],
    error: Optional[str],
    raw_output: Optional[str],
)
```

---

## TDD: Tests to Update in `tests/test_code_checker_pylint_main.py`

### Remove / replace
- `test_get_pylint_results_no_issues` — replace `disable_codes=["C0114", "C0116"]` with `extra_args=["--disable=C0114,C0116"]`
- `test_run_pylint_check` — remove `categories=` and `disable_codes=` calls; test with `extra_args=None` and `extra_args=["--disable=C0114"]`

### Keep unchanged
- `test_get_pylint_results_with_issues`
- `test_get_pylint_results_invalid_project_dir`
- `test_get_pylint_results_pylint_error`
- `test_get_pylint_results_empty_file`

---

## LLM Prompt

```
You are implementing Step 1 of a refactoring task for the mcp-code-checker project.
Read pr_info/steps/summary.md for full context, then implement this step.

TASK:
Update `src/mcp_code_checker/code_checker_pylint/runners.py` to replace the
`disable_codes` parameter with `extra_args: Optional[List[str]]` in both
`get_pylint_results()` and `run_pylint_check()`.

CHANGES REQUIRED:

1. In `get_pylint_results()`:
   - Rename parameter `disable_codes` → `extra_args: Optional[List[str]] = None`
   - Replace the `--disable=...` join logic with: `if extra_args: pylint_command.extend(extra_args)`
   - Update the structlog call to log `extra_args` instead of `disable_codes`
   - Update the docstring

2. In `run_pylint_check()`:
   - Remove parameters: `categories`, `disable_codes`
   - Add parameter: `extra_args: Optional[List[str]] = None`
   - Remove the hardcoded `disable_codes` default list
   - Remove the entire category-filtering block (the `if categories is not None:` block)
   - Call `get_pylint_results(project_dir, extra_args=extra_args, ...)` and return the result
   - Update the docstring

3. In `tests/test_code_checker_pylint_main.py`:
   - Update `test_get_pylint_results_no_issues`: change `disable_codes=["C0114", "C0116"]`
     to `extra_args=["--disable=C0114,C0116"]`
   - Update `test_run_pylint_check`: remove `categories=` and `disable_codes=` arguments;
     add a test call with `extra_args=["--disable=C0114,C0116"]`

Write tests first, then implement. Do not modify any other files in this step.
Run the tests to confirm they pass before finishing.
```
