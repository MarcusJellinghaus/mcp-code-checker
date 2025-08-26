# Step 2: Make validate server_name Optional

## Objective
Allow `validate` command to run without a server name argument.

## Tasks

1. **Update validate parser** (`src/config/cli_utils.py`)
   - Change `server_name` to optional argument using `nargs='?'`
   - Update help text to indicate it's optional

2. **Update validate handler** (`src/config/main.py`)
   - Modify `handle_validate_command()` to handle case when `args.server_name` is None
   - For now, just print a simple message about available server types

## Code Changes

In `cli_utils.py`, find `add_validate_parser()` and change:
```python
# FROM:
validate_parser.add_argument('server_name', help='...')

# TO:
validate_parser.add_argument('server_name', nargs='?', help='Server name to validate (optional)')
```

In `main.py`, modify `handle_validate_command()`:
```python
def handle_validate_command(args: argparse.Namespace) -> int:
    try:
        # If no server name provided, show available types
        if not args.server_name:
            configs = registry.get_all_configs()
            print(f"Available server types: {len(configs)}")
            for name in sorted(configs.keys()):
                print(f"  • {name}")
            return 0
        
        # Rest of existing validation code...
```

## Expected Outcome
- `mcp-config validate` works without error
- Shows simple list of available server types
- `mcp-config validate <server-name>` still works as before

## Test
- `mcp-config validate` - should list server types
- `mcp-config validate "my-server"` - should validate specific server
