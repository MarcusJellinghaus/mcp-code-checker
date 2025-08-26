# Step 3: Move Discovery Info to Validate

## Objective
Move the useful verbose discovery information from init to validate command.

## Tasks

1. **Add system validation to validate command** (`src/config/main.py`)
   - When `server_name` is None, show discovered servers
   - Use `--verbose` flag to show detailed discovery info
   - Reuse existing discovery functions

2. **Simplify the output**
   - Don't duplicate what `list-server-types` already does well
   - Focus on showing what's available and any discovery errors

## Code Changes

In `handle_validate_command()`:
```python
def handle_validate_command(args: argparse.Namespace) -> int:
    try:
        # If no server name provided, validate system
        if not args.server_name:
            print("System Validation - Available MCP Server Types:\n")
            
            # Re-scan if verbose (like init did)
            if args.verbose:
                print("Scanning for MCP server configurations...")
                total_count, errors = initialize_all_servers(verbose=True)
                
                if errors:
                    print("\nDiscovery errors:")
                    for error in errors:
                        print(f"  ⚠ {error}")
                print()
            
            # Show available types
            configs = registry.get_all_configs()
            if configs:
                for name, config in sorted(configs.items()):
                    print(f"  ✓ {name}: {config.display_name}")
                print(f"\nTotal: {len(configs)} server type(s) available.")
            else:
                print("  No server types available.")
            
            print("\nHint: Use 'mcp-config validate <server-name>' to validate a configured server.")
            return 0
        
        # Rest of existing server validation code...
```

## Expected Outcome
- `mcp-config validate` shows available server types
- `mcp-config validate --verbose` shows discovery details (replacing init)
- Simpler code - reusing existing functions

## Test
- `mcp-config validate` - clean list of server types
- `mcp-config validate --verbose` - detailed discovery info
