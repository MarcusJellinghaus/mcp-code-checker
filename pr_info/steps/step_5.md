# Step 5: Config + Docs — `pyproject.toml`, `docs/pyproject-configuration.md`, `README.md`

## Context
See `pr_info/steps/summary.md` for full architectural context.  
Depends on Steps 1–4. This step has no code changes — config, documentation, and README only.

No TDD applies here.

---

## WHERE

| File | Action |
|------|--------|
| `pyproject.toml` | Add `[tool.pylint.messages_control]` section |
| `docs/pyproject-configuration.md` | Create new documentation file |
| `README.md` | Update Pylint Parameters table + add config section |

---

## WHAT

### `pyproject.toml` addition

Add a new section that replicates the old default filtering behaviour for this project,
so existing behaviour is preserved after the hardcoded defaults are removed:

```toml
[tool.pylint.messages_control]
disable = ["W", "C", "R"]
```

Place this after the existing `[tool.mypy]` section.

### `docs/pyproject-configuration.md` (new file)

A focused reference covering:
1. How the MCP tool invokes pylint (via `python -m pylint`) and that pylint reads
   `pyproject.toml` automatically when run from the project directory
2. Recommended minimal config to replicate the old `{ERROR, FATAL}` default:
   ```toml
   [tool.pylint.messages_control]
   disable = ["W", "C", "R"]
   ```
3. Config for previously hardcoded codes (for projects that want finer control):
   ```toml
   [tool.pylint.messages_control]
   disable = ["C0114", "C0116", "C0301", "C0303", "C0305", "W0311", "W0611", "W1514"]
   ```
4. How to use `extra_args` for one-off overrides without changing `pyproject.toml`:
   ```
   run_pylint_check(extra_args=["--disable=W0611"])
   ```
5. Link to the [pylint messages reference](https://pylint.readthedocs.io/en/stable/messages/messages_overview.html)

### `README.md` changes

**Update Pylint Parameters table** (under `### Pylint Parameters`):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `extra_args` | list | None | Optional list of additional pylint CLI arguments (e.g. `["--disable=W0611"]`) |
| `target_directories` | list | ["src", "tests"] | List of directories to analyze relative to project_dir |

Remove the `categories` and `disable_codes` rows.

**Add a new subsection** after the table:

```markdown
### Pylint Configuration

Pylint reads your project's `pyproject.toml` automatically. Control which issues
are reported by configuring `[tool.pylint.messages_control]` in your `pyproject.toml`.
See [docs/pyproject-configuration.md](docs/pyproject-configuration.md) for examples
and migration guidance.
```

---

## ALGORITHM

```
No algorithmic logic — configuration and documentation only.

1. Add [tool.pylint.messages_control] to pyproject.toml
2. Create docs/pyproject-configuration.md with migration guide
3. Update README.md Pylint Parameters table
4. Add Pylint Configuration subsection to README.md
5. Verify pylint still runs cleanly on this project with the new pyproject.toml config
```

---

## DATA

No data structures. The `docs/` directory must be created if it does not exist.

---

## Verification

After this step, run pylint manually on this project to confirm the `pyproject.toml`
config correctly replicates the old behaviour (only E/F codes reported):

```bash
python -m pylint src tests --output-format=json
```

Expected: only ERROR and FATAL messages (same as the old hardcoded default).

---

## LLM Prompt

```
You are implementing Step 5 of a refactoring task for the mcp-code-checker project.
Read pr_info/steps/summary.md and pr_info/steps/step_5.md for full context.
Steps 1–4 are complete. This step is config and documentation only — no Python code changes.

TASK:
1. In `pyproject.toml`, add the following section after `[tool.mypy]`:
   [tool.pylint.messages_control]
   disable = ["W", "C", "R"]

2. Create `docs/pyproject-configuration.md` (create the docs/ directory if needed).
   The file must cover:
   a. How pylint reads pyproject.toml automatically when invoked by the MCP tool
   b. Recommended config to replicate the old {ERROR, FATAL} default:
      disable = ["W", "C", "R"]
   c. Config for previously hardcoded codes (C0114, C0116, C0301, C0303, C0305, W0311, W0611, W1514)
      for projects wanting finer-grained control
   d. How to use extra_args=["--disable=W0611"] for one-off overrides
   e. A link to https://pylint.readthedocs.io/en/stable/messages/messages_overview.html

3. In `README.md`, under `### Pylint Parameters`:
   a. Update the table: remove the `categories` and `disable_codes` rows;
      add an `extra_args` row: "Optional list of additional pylint CLI arguments"
   b. Add a new `### Pylint Configuration` subsection pointing to the new docs file

Do not modify any Python source or test files. Do not run tests.
```
