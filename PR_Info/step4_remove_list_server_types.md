# Step 4: Remove Redundant list-server-types Command

## Objective
Since `validate` now shows available server types, we can remove `list-server-types` to further simplify.

## Tasks

1. **Analyze overlap**
   - `list-server-types` shows available server types with details
   - `validate` (no args) now shows the same information
   - They're redundant - keep only one

2. **Remove list-server-types command**
   - Remove from parser (`src/config/cli_utils.py`)
   - Remove handler from `main.py`
   - Update validate to show the useful details that list-server-types showed

## Alternative Approach (if we want to keep it)
- Keep `list-server-types` as an alias to `validate --system`
- But this adds complexity, not reduces it

## Recommendation
**REMOVE `list-server-types` entirely** because:
- `validate` (no args) naturally shows what types are available
- One less command = simpler codebase
- Users can use `help <server-type>` to get details about specific types

## Code Changes

1. Remove `add_list_server_types_parser()` from `cli_utils.py`
2. Remove `handle_list_server_types_command()` from `main.py`  
3. Remove 'list-server-types' from command dispatcher in `main()`

## Expected Outcome
- `mcp-config list-server-types` no longer exists
- `mcp-config validate` provides the same information
- Simpler codebase with fewer commands

## Test
- `mcp-config list-server-types` - should show "invalid choice"
- `mcp-config validate` - shows available types
- `mcp-config validate --verbose` - shows detailed info
