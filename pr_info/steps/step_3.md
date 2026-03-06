# Step 3: Delete Dead Files

## Context
See [summary.md](summary.md) for full context.

`server.py` no longer imports `data_files` or references `sleep_script.py`. This step deletes those files and their now-empty folder.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for context.

Delete the following files and folder:

1. Delete file:  `src/mcp_code_checker/resources/sleep_script.py`
2. Delete folder: `src/mcp_code_checker/resources/`  (empty after step 1)
3. Delete file:  `src/mcp_code_checker/utils/data_files.py`

Use mcp__filesystem__delete_this_file for files.
Use a Bash rm command for the now-empty resources/ directory:
  Bash("rmdir src/mcp_code_checker/resources")

After deleting, run all checks to confirm nothing is broken.
```

---

## WHERE

| Path | Action |
|------|--------|
| `src/mcp_code_checker/resources/sleep_script.py` | **Delete** |
| `src/mcp_code_checker/resources/` | **Delete** (directory, empty after above) |
| `src/mcp_code_checker/utils/data_files.py` | **Delete** |

---

## WHAT

Pure file system deletions. No code changes.

### Why each file is safe to delete

| File | Last reference removed in |
|------|--------------------------|
| `resources/sleep_script.py` | Step 2 (`second_sleep` tool removed) |
| `resources/` | — empty after above |
| `utils/data_files.py` | Step 2 (`find_data_file` import removed from `server.py`) |

`utils/data_files.py` exports are also re-exported from `utils/__init__.py` — that re-export is cleaned up in Step 4. Deleting `data_files.py` first causes an import error in `utils/__init__.py` until Step 4 is applied, so **Steps 3 and 4 should be run together** (or Step 4 first if preferred).

---

## HOW

- Use `mcp__filesystem__delete_this_file` for individual `.py` files.
- Use `Bash("rmdir src/mcp_code_checker/resources")` for the now-empty directory.
- No source code changes.

---

## ALGORITHM

N/A — file system operations only.

---

## DATA

After this step:
- `src/mcp_code_checker/resources/` does not exist.
- `src/mcp_code_checker/utils/data_files.py` does not exist.
- `utils/__init__.py` still references `data_files` (broken until Step 4).

---

## Verification

Run after completing **both Step 3 and Step 4**:
```
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto", "-m", "not integration"])
mcp__code-checker__run_mypy_check()
```
