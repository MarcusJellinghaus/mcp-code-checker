# Step 1: Add VSCode Handler to clients.py

## Objective
Add a new `VSCodeHandler` class to support VSCode's native MCP configuration format (VSCode 1.102+).

## Background
VSCode now has built-in MCP support and uses `.vscode/mcp.json` for workspace configs or `~/.config/Code/User/mcp.json` for user-level configs.

## Requirements

### 1. Create VSCodeHandler Class
Add a new handler class in `src/config/clients.py` that:
- Supports both workspace (`.vscode/mcp.json`) and user profile configurations
- Follows the same pattern as `ClaudeDesktopHandler`
- Uses the VSCode MCP format: `{"servers": {name: {"command": ..., "args": ..., "env": ...}}}`
- Handles cross-platform config paths (Windows/macOS/Linux)

### 2. Key Methods to Implement
- `get_config_path()` - Returns path based on workspace/user mode and OS
- `setup_server()` - Adds server config in VSCode format
- `remove_server()` - Removes only managed servers
- `list_managed_servers()` - Lists servers managed by this tool
- `list_all_servers()` - Lists all configured servers
- `backup_config()` - Creates backup before modifications

### 3. Configuration Format
VSCode uses this format in `mcp.json`:
```json
{
  "servers": {
    "server-name": {
      "command": "python",
      "args": ["-m", "mcp_code_checker", "--project-dir", "/path"],
      "env": {"PYTHONPATH": "/path"}
    }
  }
}
```

### 4. Metadata Tracking
Like ClaudeDesktopHandler, use a separate `.mcp-config-metadata.json` file to track which servers are managed by this tool.

## Implementation Code

```python
class VSCodeHandler(ClientHandler):
    """Handler for VSCode native MCP configuration (VSCode 1.102+)."""
    
    MANAGED_SERVER_MARKER = "mcp-config-managed"
    METADATA_FILE = ".mcp-config-metadata.json"
    
    def __init__(self, workspace: bool = True):
        """Initialize VSCode handler.
        
        Args:
            workspace: If True, use workspace config (.vscode/mcp.json).
                      If False, use user profile config.
        """
        self.workspace = workspace
    
    def get_config_path(self) -> Path:
        """Get VSCode MCP config file path."""
        if self.workspace:
            # Workspace configuration in current directory
            return Path.cwd() / ".vscode" / "mcp.json"
        else:
            # User profile configuration
            home_str = str(Path.home())
            if os.name == "nt":  # Windows
                return Path(home_str) / "AppData" / "Roaming" / "Code" / "User" / "mcp.json"
            elif platform.system() == "Darwin":  # macOS
                return Path(home_str) / "Library" / "Application Support" / "Code" / "User" / "mcp.json"
            else:  # Linux
                return Path(home_str) / ".config" / "Code" / "User" / "mcp.json"
    
    def get_metadata_path(self) -> Path:
        """Get path to the metadata file for tracking managed servers."""
        config_path = self.get_config_path()
        return config_path.parent / self.METADATA_FILE
    
    def load_metadata(self) -> dict[str, Any]:
        """Load metadata about managed servers."""
        metadata_path = self.get_metadata_path()
        
        if not metadata_path.exists():
            return {}
        
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, IOError):
            return {}
    
    def save_metadata(self, metadata: dict[str, Any]) -> None:
        """Save metadata about managed servers."""
        metadata_path = self.get_metadata_path()
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            f.write("\n")
    
    def load_config(self) -> dict[str, Any]:
        """Load existing VSCode MCP configuration."""
        config_path = self.get_config_path()
        default_config: dict[str, Any] = {"servers": {}}
        
        if not config_path.exists():
            return default_config
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config: dict[str, Any] = json.load(f)
            
            if "servers" not in config:
                config["servers"] = {}
            
            return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Error loading config from {config_path}: {e}")
            return default_config
    
    def save_config(self, config: dict[str, Any]) -> None:
        """Save VSCode MCP configuration."""
        config_path = self.get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file first (atomic write)
        temp_path = config_path.with_suffix(".tmp")
        
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                f.write("\n")
            
            temp_path.replace(config_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise
    
    def setup_server(self, server_name: str, server_config: dict[str, Any]) -> bool:
        """Add server to VSCode MCP config."""
        try:
            self.backup_config()
            config = self.load_config()
            
            # Extract metadata fields
            metadata_fields = {
                "_managed_by": self.MANAGED_SERVER_MARKER,
                "_server_type": server_config.get("_server_type", "mcp-code-checker")
            }
            
            # Clean config for VSCode format (no metadata in main config)
            clean_config = {
                "command": server_config["command"],
                "args": server_config["args"]
            }
            if "env" in server_config and server_config["env"]:
                clean_config["env"] = server_config["env"]
            
            # Update server configuration
            config["servers"][server_name] = clean_config
            
            # Save config and metadata
            self.save_config(config)
            
            metadata = self.load_metadata()
            metadata[server_name] = metadata_fields
            self.save_metadata(metadata)
            
            return True
            
        except Exception as e:
            print(f"Error setting up server '{server_name}': {e}")
            return False
    
    def remove_server(self, server_name: str) -> bool:
        """Remove server from VSCode config if managed by us."""
        try:
            config = self.load_config()
            metadata = self.load_metadata()
            
            if server_name not in config.get("servers", {}):
                print(f"Server '{server_name}' not found in configuration")
                return False
            
            if server_name not in metadata or metadata[server_name].get("_managed_by") != self.MANAGED_SERVER_MARKER:
                print(f"Server '{server_name}' is not managed by this tool. Cannot remove external servers.")
                return False
            
            self.backup_config()
            
            del config["servers"][server_name]
            self.save_config(config)
            
            del metadata[server_name]
            self.save_metadata(metadata)
            
            return True
            
        except Exception as e:
            print(f"Error removing server '{server_name}': {e}")
            return False
    
    def list_managed_servers(self) -> list[dict[str, Any]]:
        """List only servers managed by this tool."""
        config = self.load_config()
        metadata = self.load_metadata()
        servers = []
        
        for name, server_config in config.get("servers", {}).items():
            if name in metadata and metadata[name].get("_managed_by") == self.MANAGED_SERVER_MARKER:
                servers.append({
                    "name": name,
                    "type": metadata[name].get("_server_type", "unknown"),
                    "command": server_config.get("command", ""),
                    "args": server_config.get("args", []),
                    "env": server_config.get("env", {})
                })
        
        return servers
    
    def list_all_servers(self) -> list[dict[str, Any]]:
        """List all servers in configuration."""
        config = self.load_config()
        metadata = self.load_metadata()
        servers = []
        
        for name, server_config in config.get("servers", {}).items():
            is_managed = (
                name in metadata and 
                metadata[name].get("_managed_by") == self.MANAGED_SERVER_MARKER
            )
            
            server_type = "unknown"
            if is_managed and name in metadata:
                server_type = metadata[name].get("_server_type", "unknown")
            
            servers.append({
                "name": name,
                "managed": is_managed,
                "type": server_type,
                "command": server_config.get("command", ""),
                "args": server_config.get("args", []),
                "env": server_config.get("env", {})
            })
        
        return servers
    
    def backup_config(self) -> Path:
        """Create a backup of the current configuration."""
        config_path = self.get_config_path()
        
        if not config_path.exists():
            return config_path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"mcp_backup_{timestamp}.json"
        backup_path = config_path.parent / backup_name
        
        shutil.copy2(config_path, backup_path)
        return backup_path
    
    def validate_config(self) -> list[str]:
        """Validate current configuration."""
        errors = []
        
        try:
            config = self.load_config()
            
            if "servers" not in config:
                errors.append("Configuration missing 'servers' section")
            elif not isinstance(config["servers"], dict):
                errors.append("'servers' must be an object")
            else:
                for name, server_config in config["servers"].items():
                    if not isinstance(server_config, dict):
                        errors.append(f"Server '{name}' configuration must be an object")
                        continue
                    
                    if "command" not in server_config:
                        errors.append(f"Server '{name}' missing required 'command' field")
                    
                    if "args" in server_config and not isinstance(server_config["args"], list):
                        errors.append(f"Server '{name}' 'args' field must be an array")
                    
                    if "env" in server_config and not isinstance(server_config["env"], dict):
                        errors.append(f"Server '{name}' 'env' field must be an object")
        
        except Exception as e:
            errors.append(f"Error reading configuration: {e}")
        
        return errors
```

## Registration
Add to the CLIENT_HANDLERS dictionary in `clients.py`:

```python
# Client registry
CLIENT_HANDLERS = {
    "claude-desktop": ClaudeDesktopHandler,
    "vscode": lambda: VSCodeHandler(workspace=True),  # Default to workspace
    "vscode-workspace": lambda: VSCodeHandler(workspace=True),
    "vscode-user": lambda: VSCodeHandler(workspace=False),
}
```

## Testing Checklist
- [ ] Test workspace config creation in `.vscode/mcp.json`
- [ ] Test user profile config on Windows/macOS/Linux
- [ ] Test metadata tracking for managed servers
- [ ] Test preservation of external servers
- [ ] Test backup functionality
- [ ] Test removal of managed servers only
- [ ] Test config validation

## Success Criteria
- VSCodeHandler follows same patterns as ClaudeDesktopHandler
- Supports both workspace and user configurations
- Properly tracks managed vs external servers
- Creates valid VSCode MCP configuration format
- Cross-platform path handling works correctly