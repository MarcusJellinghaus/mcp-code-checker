# Step 1: Remove Init Command

## Objective
Remove the `init` command entirely from the codebase to simplify the CLI.

## Tasks

1. **Remove `init` command from parser** (`src/config/cli_utils.py`)
   - Remove `add_init_parser()` function
   - Remove 'init' from command choices

2. **Remove `init` handler** (`src/config/main.py`)
   - Delete `handle_init_command()` function
   - Remove 'init' case from main() dispatcher

3. **Clean up imports**
   - Remove any imports only used by init command

## Expected Outcome
- The `init` command no longer exists
- Code is simpler with one less command
- All init functionality is removed (we'll add the useful parts to validate later)

## Test
After changes:
- `mcp-config init` should show "invalid choice: 'init'"
- All other commands should work normally
