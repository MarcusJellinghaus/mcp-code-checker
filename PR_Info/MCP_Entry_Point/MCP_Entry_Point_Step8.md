# Step 8: Update User Guide Documentation

## Objective
Update the User Guide (docs/config/USER_GUIDE.md) to reflect the new CLI command usage for mcp-code-checker.

## File to Modify
- `docs/config/USER_GUIDE.md` - Update all examples to use the new CLI command

## Implementation Instructions

### 1. Update Quick Start Section

Find the "Quick Start" section and update all examples to use the installed command:

**Replace:**
```bash
# Set up for Claude Desktop (default)
mcp-config setup mcp-code-checker "my-project" --project-dir .
```

**With:**
```bash
# Install MCP Code Checker first
pip install mcp-code-checker  # Or: pip install -e . for development

# Verify installation
mcp-code-checker --help

# Set up for Claude Desktop (default)
mcp-config setup mcp-code-checker "my-project" --project-dir .
```

### 2. Update Setup Command Examples

In the "setup" command section, update all examples to show that the tool will detect and use the CLI command:

**Add a new note after the setup command description:**
```markdown
**Note:** The config tool automatically detects if `mcp-code-checker` is installed as a command and will use it in the generated configuration. If not installed, it falls back to Python module invocation.
```

### 3. Add Installation Mode Detection

Add a new section after "Auto-Detection":

```markdown
## Installation Mode Detection

The configuration helper automatically detects how MCP Code Checker is installed:

1. **CLI Command** (Preferred): If `mcp-code-checker` is available as a command
   - Generated config uses: `"command": "mcp-code-checker"`
   - Installation: `pip install mcp-code-checker` or `pip install -e .`

2. **Python Module**: If installed as a package but no CLI command
   - Generated config uses: `"command": "python", "args": ["-m", "mcp_code_checker", ...]`
   - This happens with older installations or incomplete setups

3. **Development Mode**: Running from source without installation
   - Generated config uses: `"command": "python", "args": ["src/main.py", ...]`
   - Used when running directly from the repository

To check which mode will be used:
```bash
# Run validation to see installation mode
mcp-config validate "your-server-name"

# Or check if command is available
which mcp-code-checker  # Unix/macOS
where mcp-code-checker  # Windows
```
```

### 4. Update Configuration Storage Examples

In the "Configuration Storage" section, update the Claude Desktop example:

**Replace the existing example with:**
```json
{
  "mcpServers": {
    "my-project": {
      "command": "mcp-code-checker",
      "args": [
        "--project-dir",
        "/path/to/project",
        "--log-level",
        "INFO"
      ]
    }
  }
}
```

**And for VSCode:**
```json
{
  "servers": {
    "my-project": {
      "command": "mcp-code-checker",
      "args": ["--project-dir", "."]
    }
  }
}
```

### 5. Update Common Workflows

Update all workflow examples to show the command installation step:

**Claude Desktop Setup:**
```bash
# Ensure MCP Code Checker is installed
pip install mcp-code-checker

# Navigate to your project
cd ~/projects/my-app

# Configure for Claude
mcp-config setup mcp-code-checker "my-app" --project-dir .

# Restart Claude Desktop
```

**VSCode Team Project:**
```bash
# Ensure MCP Code Checker is installed for all team members
echo "mcp-code-checker" >> requirements.txt

# Install dependencies
pip install -r requirements.txt

# Configure for VSCode workspace
cd ~/projects/team-project
mcp-config setup mcp-code-checker "team-project" --client vscode --project-dir .

# Commit configuration
git add .vscode/mcp.json requirements.txt
git commit -m "Add MCP configuration for team"
```

### 6. Update Troubleshooting Section Reference

Add a note about command availability:

```markdown
### Troubleshooting

If you encounter issues:

1. **Command not found**: Ensure `mcp-code-checker` is installed:
   ```bash
   pip install mcp-code-checker
   # Or for development: pip install -e .
   ```

2. **Validate configuration**: Check your setup:
   ```bash
   mcp-config validate "my-app"
   ```

3. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions
```

## Validation

After making changes:
1. All examples should show the `mcp-code-checker` command
2. Installation verification steps should be included
3. The three installation modes should be clearly explained
4. Team workflow should include dependency management

## Next Step
Proceed to Step 9 to update the Troubleshooting guide.
