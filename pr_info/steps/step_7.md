# Step 7: Refactor `_get_tool` Test Helper to Robust Approach

## Context
See `pr_info/steps/summary.md` for full context. This is step 7 of 7 (post-review fix).

Identified during code review (Decision 13): The `_get_tool()` helper in `test_tool_availability.py` extracts registered tool functions by inspecting `mock_tool.call_args_list`. This is fragile — it relies on internal mock recording behavior and breaks silently if tool registration changes.

## Goal
Replace the fragile `_get_tool` approach with a more robust pattern for testing tool handler short-circuit behavior. Instead of extracting decorated functions from mock internals, test through the server's public interface.

## LLM Prompt
> Implement Step 7 of Issue #89 (see `pr_info/steps/summary.md` for context, Decision 13 in `pr_info/steps/Decisions.md`). Refactor the `TestToolHandlerShortCircuit` tests in `test_tool_availability.py` to use a more robust approach instead of the fragile `_get_tool` helper that inspects mock internals. Run all quality checks after.

## WHERE

- `tests/test_tool_availability.py` — refactor `TestToolHandlerShortCircuit` class and remove `_get_tool` helper

## WHAT

### Approach: Test via server tool handler methods directly

Instead of extracting decorated functions from mock call args, create a helper that invokes tool handlers through the server's registered tool functions. The key insight: FastMCP's `@self.mcp.tool()` decorator wraps functions and registers them, but the inner function still exists as a closure. We can test the behavior by:

1. Creating the server (which registers tools)
2. Overriding `_tool_availability` after construction
3. Calling the tool handler functions via the FastMCP instance's internal registry

**Alternative (simpler)**: Since the short-circuit check is the first thing in each handler, and we control `_tool_availability`, we can test the logic by directly calling the server's formatting/handling methods. But the cleanest approach is to add thin wrapper methods on the server that delegate to the registered tools.

### Recommended approach: Add testable wrapper methods

Add three public methods to `CodeCheckerServer` that the tool handlers call internally:

```python
def _run_pylint_check_impl(self, extra_args=None, target_directories=None) -> str:
    """Implementation of run_pylint_check, testable without MCP."""
    if not self._tool_availability.get("pylint", False):
        return self._tool_unavailable_message("pylint")
    # ... existing logic ...
```

**Actually, even simpler**: The tool handlers are closures that capture `self`. We can just test the short-circuit behavior by checking the return value pattern. The current tests already do this correctly — the issue is only with HOW we extract the function reference.

### Simplest robust approach

Replace `_get_tool(mock_tool, "name")` with accessing the tool function through the mock's decorator return value. Since `mock_tool` is the return value of `mcp.tool()`, and each handler is passed to it, we can capture them differently:

```python
# Instead of extracting from call_args_list by __name__:
# Use a dict to capture tool functions as they're registered
registered_tools = {}
def capture_tool(func):
    registered_tools[func.__name__] = func
    return func

mock_fastmcp.return_value.tool.return_value = capture_tool
```

This is more robust because:
- Explicit capture, not inspection of mock internals
- Function name matching is intentional, not incidental
- Fails loudly if registration changes (KeyError instead of silent wrong function)

### Modified: `TestToolHandlerShortCircuit`

- Remove `_get_tool` module-level function
- Add `_capture_tools` helper or inline the capture pattern
- Update all test methods in the class

## HOW

- Replace mock side_effect pattern with explicit capture dict
- No changes to production code needed

## ALGORITHM

```
# Helper to capture registered tools:
registered_tools = {}
def capture_tool(func):
    registered_tools[func.__name__] = func
    return func
mock_fastmcp.return_value.tool.return_value = capture_tool

# Create server (tools get captured)
server = _create_server(...)

# Access tool by name:
run_pytest_check = registered_tools["run_pytest_check"]
result = run_pytest_check()
```

## DATA

- No new data structures
- `registered_tools: dict[str, Callable]` — local capture dict in test helper

## Tests

- All existing `TestToolHandlerShortCircuit` tests must pass with the new approach
- No new test cases needed — this is a pure refactoring of test infrastructure

## Verification
- `tests/test_tool_availability.py` — all tests pass
- `_get_tool` function no longer exists in the file
- Run pylint, pytest, mypy — all pass
