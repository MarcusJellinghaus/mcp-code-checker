# Step 2: Update CLI to Support VSCode Client

## Objective
Update the CLI in `src/config/main.py` to support the new VSCode client options, including workspace vs user profile configuration.

## Background
With the VSCodeHandler implemented, we need to:
1. Add VSCode as a valid client option
2. Support `--workspace` flag for VSCode configurations
3. Update help text and examples

## Requirements

### 1. Update setup Command
Modify the `setup` command to:
- Accept `vscode` as a valid client option
- Add `--workspace` flag (VSCode only) to choose between workspace and user config
- Default to workspace config for VSCode

### 2. Update Client Choices
Add VSCode options to all commands that accept `--client`:
- `vscode` (defaults to workspace)
- `vscode-workspace` (explicit workspace)
- `vscode-user` (explicit user profile)

### 3. Update Help Text
Include VSCode examples in help documentation.

## Implementation Changes

### In `src/config/main.py`:

```python
# Update the client choices in all commands
SUPPORTED_CLIENTS = ["claude-desktop", "vscode", "vscode-workspace", "vscode-user"]

def setup_command(
    server_type: str,
    server_name: str,
    project_dir: str,
    client: str = "claude-desktop",
    workspace: bool = True,  # New parameter
    dry_run: bool = False,
    backup: bool = True,
    verbose: bool = False,
    **server_params: Any
) -> None:
    """Setup an MCP server for a specific client.
    
    Args:
        server_type: Type of server to setup
        server_name: Name for this server instance
        project_dir: Project directory path
        client: Client to configure (claude-desktop, vscode, etc.)
        workspace: For VSCode, use workspace config (True) or user config (False)
        dry_run: Preview changes without applying
        backup: Create backup before changes
        verbose: Show detailed output
        **server_params: Additional server-specific parameters
    """
    # Handle VSCode client with workspace flag
    if client == "vscode":
        # Use workspace flag to determine which handler to use
        client_key = "vscode-workspace" if workspace else "vscode-user"
    else:
        client_key = client
    
    # Get the appropriate client handler
    from src.config.clients import get_client_handler
    handler = get_client_handler(client_key)
    
    # Rest of the implementation...
```

### Update CLI Argument Parser:

```python
@click.command(name="setup")
@click.argument("server_type", type=click.Choice(["mcp-code-checker"]))
@click.argument("server_name")
@click.option(
    "--client",
    type=click.Choice(SUPPORTED_CLIENTS),
    default="claude-desktop",
    help="MCP client to configure (claude-desktop, vscode, vscode-workspace, vscode-user)"
)
@click.option(
    "--workspace/--user",
    "use_workspace",
    default=True,
    help="For VSCode: use workspace config (.vscode) or user profile config (default: workspace)"
)
@click.option("--project-dir", required=True, help="Project directory path")
@click.option("--dry-run", is_flag=True, help="Preview changes without applying")
@click.option("--backup/--no-backup", default=True, help="Create backup before changes")
@click.option("--verbose", is_flag=True, help="Show detailed output")
# Add all server-specific options dynamically...
def setup_command(server_type, server_name, client, use_workspace, project_dir, 
                 dry_run, backup, verbose, **kwargs):
    """Setup an MCP server configuration."""
    
    # Special handling for VSCode client selection
    if client.startswith("vscode"):
        if client == "vscode":
            # Use the workspace flag to determine config location
            client = "vscode-workspace" if use_workspace else "vscode-user"
        # else: client is already vscode-workspace or vscode-user
    
    # Validate project directory
    project_path = Path(project_dir).resolve()
    if not project_path.exists():
        click.echo(f"Error: Project directory does not exist: {project_path}", err=True)
        return 1
    
    # Continue with setup...
```

### Update list Command:

```python
@click.command(name="list")
@click.option(
    "--client",
    type=click.Choice(SUPPORTED_CLIENTS),
    help="Filter by client (default: all clients)"
)
@click.option("--detailed", is_flag=True, help="Show detailed configuration")
@click.option("--managed-only", is_flag=True, help="Show only managed servers")
def list_command(client, detailed, managed_only):
    """List configured MCP servers."""
    
    clients_to_check = []
    
    if client:
        clients_to_check = [client]
    else:
        # Check all clients
        clients_to_check = ["claude-desktop", "vscode-workspace", "vscode-user"]
    
    for client_name in clients_to_check:
        handler = get_client_handler(client_name)
        
        # Display client name
        if client_name == "vscode-workspace":
            display_name = "VSCode (Workspace)"
        elif client_name == "vscode-user":
            display_name = "VSCode (User Profile)"
        else:
            display_name = "Claude Desktop"
        
        click.echo(f"\n{display_name}:")
        click.echo("-" * len(display_name))
        
        # List servers...
```

### Update Help System:

```python
def show_examples():
    """Show usage examples."""
    examples = """
## Usage Examples

### Claude Desktop Setup
```bash
# Basic setup
mcp-config setup mcp-code-checker "my-project" --project-dir . --client claude-desktop

# With custom parameters
mcp-config setup mcp-code-checker "debug" --project-dir . --log-level DEBUG
```

### VSCode Setup
```bash
# Workspace configuration (recommended for team sharing)
mcp-config setup mcp-code-checker "my-project" --project-dir . --client vscode

# User profile configuration (personal, all projects)
mcp-config setup mcp-code-checker "global" --project-dir ~/projects --client vscode --user

# Explicit workspace config
mcp-config setup mcp-code-checker "team-project" --project-dir . --client vscode-workspace
```

### List Servers
```bash
# List all servers across all clients
mcp-config list --detailed

# List only VSCode workspace servers
mcp-config list --client vscode-workspace

# List only managed servers
mcp-config list --managed-only
```

### Remove Servers
```bash
# Remove from Claude Desktop
mcp-config remove "my-project" --client claude-desktop

# Remove from VSCode workspace
mcp-config remove "my-project" --client vscode
```
"""
    click.echo(examples)
```

## Validation Updates

In `src/config/validation.py`, update to handle VSCode:

```python
def validate_client_installation(client: str) -> list[str]:
    """Check if the target client is installed.
    
    Args:
        client: Client name to check
    
    Returns:
        List of warnings (empty if client is detected)
    """
    warnings = []
    
    if client.startswith("vscode"):
        # Check if VSCode is installed
        vscode_commands = ["code", "code-insiders", "codium"]
        vscode_found = False
        
        for cmd in vscode_commands:
            if shutil.which(cmd):
                vscode_found = True
                break
        
        if not vscode_found:
            warnings.append(
                "VSCode not detected. Please ensure VSCode 1.102+ is installed "
                "for native MCP support."
            )
        
        # Check for workspace config location if using workspace mode
        if client in ["vscode", "vscode-workspace"]:
            if not Path(".vscode").exists():
                warnings.append(
                    "No .vscode directory found. It will be created for workspace configuration."
                )
    
    elif client == "claude-desktop":
        # Check for Claude Desktop (platform-specific checks)
        pass
    
    return warnings
```

## Testing Checklist
- [ ] Test `--client vscode` defaults to workspace config
- [ ] Test `--client vscode --user` uses user profile config
- [ ] Test `--client vscode-workspace` explicit workspace
- [ ] Test `--client vscode-user` explicit user profile
- [ ] Test list command shows VSCode servers correctly
- [ ] Test remove command works for VSCode servers
- [ ] Test validation warnings for VSCode installation

## Success Criteria
- CLI accepts VSCode as a client option
- Workspace vs user profile configuration works correctly
- Help text includes VSCode examples
- List command shows VSCode servers with proper labels
- Backward compatibility maintained for Claude Desktop