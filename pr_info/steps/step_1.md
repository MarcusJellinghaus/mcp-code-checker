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
| `src/mcp_code_checker/code_checker_pylint/__init__.py` | Remove `run_pylint_check` from exports |

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

### `run_pylint_check()` — DELETE entirely

This function is not called by any production code (server.py → reporting.py → `get_pylint_results` directly).
It is a redundant wrapper. Remove the function definition and remove `run_pylint_check` from
`__init__.py` imports and `__all__`.

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

### `run_pylint_check()` — DELETE entirely

Remove the entire function from `runners.py`. It is not called by any production code;
`reporting.py` calls `get_pylint_results` directly.

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
- `test_run_pylint_check` — **delete entirely** (the function it tests is being removed)

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

2. DELETE `run_pylint_check()` from `runners.py` entirely.
   It is not called by any production code. `reporting.py` calls `get_pylint_results` directly.

3. In `src/mcp_code_checker/code_checker_pylint/__init__.py`:
   - Remove `run_pylint_check` from the import block and from `__all__`

4. In `tests/test_code_checker_pylint_main.py`:
   - Update `test_get_pylint_results_no_issues`: change `disable_codes=["C0114", "C0116"]`
     to `extra_args=["--disable=C0114,C0116"]`
   - DELETE `test_run_pylint_check` entirely (the function it tests is being removed)
   - Remove `run_pylint_check` from the import at the top of the file

Write tests first (delete test_run_pylint_check, update test_get_pylint_results_no_issues),
then implement. Do not modify any other files in this step.
Run the tests to confirm they pass before finishing.
```
