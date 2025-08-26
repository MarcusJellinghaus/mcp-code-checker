"""Help system for MCP Configuration Helper.

This module provides detailed help and documentation for both tool commands
and server parameters.
"""

from typing import Any, Optional
from .servers import ServerConfig, registry


class CommandHelpFormatter:
    """Formats help documentation for mcp-config commands."""
    
    @staticmethod
    def format_tool_overview() -> str:
        """Format overview of the mcp-config tool.
        
        Returns:
            Formatted help string
        """
        lines = [
            "MCP Configuration Helper",
            "="*24,
            "",
            "A tool to automate MCP server setup for Claude Desktop and other clients.",
            "",
            "USAGE:",
            "  mcp-config <command> [options]",
            "",
            "COMMANDS:",
            "  setup              Setup an MCP server configuration",
            "  remove             Remove an MCP server configuration",
            "  list               List configured MCP servers",
            "  validate           Validate server configuration or show available types",
            "  help               Show detailed help and documentation",
            "",
            "GLOBAL OPTIONS:",
            "  --version          Show version information",
            "  -h, --help         Show help for any command",
            "",
            "Run 'mcp-config help <command>' for detailed information about a command.",
            "Run 'mcp-config help --all' for comprehensive documentation.",
        ]
        return "\n".join(lines)
    
    @staticmethod
    def format_setup_command_help(verbose: bool = False) -> str:
        """Format help for the setup command.
        
        Args:
            verbose: Whether to include extended help
            
        Returns:
            Formatted help string
        """
        lines = [
            "SETUP COMMAND",
            "=============",
            "",
            "Setup an MCP server configuration in Claude Desktop.",
            "",
            "USAGE:",
            "  mcp-config setup <server-type> <server-name> [options]",
            "",
            "ARGUMENTS:",
            "  server-type        Type of server to configure (e.g., mcp-code-checker)",
            "  server-name        Name for this server instance (your choice)",
            "",
            "COMMAND OPTIONS:",
            "  --client CHOICE    MCP client to configure [default: claude-desktop]",
            "                     Choices: claude-desktop",
            "  --dry-run          Preview changes without applying them",
            "  --verbose          Show detailed output during setup",
            "  --backup           Create backup before changes [default: true]",
            "  --no-backup        Skip backup creation",
            "",
        ]
        
        if verbose:
            lines.extend([
                "DETAILED OPTION DESCRIPTIONS:",
                "",
                "  --client:",
                "    Specifies which MCP client to configure. Currently only supports",
                "    'claude-desktop', but designed for future extensibility.",
                "",
                "  --dry-run:",
                "    Shows exactly what would be configured without making any changes.",
                "    Useful for testing your parameters and understanding the setup.",
                "    Displays the JSON configuration that would be written.",
                "",
                "  --verbose:",
                "    Provides detailed output during the setup process, including:",
                "    - Auto-detected parameters",
                "    - Validation steps",
                "    - Configuration details",
                "    - File paths being modified",
                "",
                "  --backup/--no-backup:",
                "    By default, creates a timestamped backup of the configuration",
                "    before making changes. Use --no-backup to skip this (not recommended).",
                "    Backups are saved as: claude_desktop_config.backup_TIMESTAMP.json",
                "",
            ])
        
        lines.extend([
            "SERVER-SPECIFIC OPTIONS:",
            "  Each server type has its own parameters. Use one of these to see them:",
            "    mcp-config help mcp-code-checker  # For code checker parameters",
            "    mcp-config setup <server> -h      # Quick parameter list",
            "",
            "EXAMPLES:",
            "  # Basic setup with auto-detection",
            "  mcp-config setup mcp-code-checker my-checker --project-dir .",
            "",
            "  # Preview changes without applying",
            "  mcp-config setup mcp-code-checker test --project-dir . --dry-run",
            "",
            "  # Verbose setup with custom Python",
            "  mcp-config setup mcp-code-checker prod --project-dir . \\",
            "    --python-executable /usr/bin/python3.11 --verbose",
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def format_remove_command_help(verbose: bool = False) -> str:
        """Format help for the remove command.
        
        Args:
            verbose: Whether to include extended help
            
        Returns:
            Formatted help string
        """
        lines = [
            "REMOVE COMMAND",
            "=============",
            "",
            "Remove an MCP server configuration from Claude Desktop.",
            "",
            "USAGE:",
            "  mcp-config remove <server-name> [options]",
            "",
            "ARGUMENTS:",
            "  server-name        Name of the server to remove",
            "",
            "OPTIONS:",
            "  --client CHOICE    MCP client to configure [default: claude-desktop]",
            "  --dry-run          Preview removal without applying changes",
            "  --verbose          Show detailed output",
            "  --backup           Create backup before removal [default: true]",
            "  --no-backup        Skip backup creation",
            "",
        ]
        
        if verbose:
            lines.extend([
                "IMPORTANT NOTES:",
                "  - Only servers created by mcp-config can be removed",
                "  - External servers (manually configured) cannot be removed",
                "  - A backup is created by default before removal",
                "  - Use 'mcp-config list' to see available servers",
                "",
            ])
        
        lines.extend([
            "EXAMPLES:",
            "  # Remove a server",
            "  mcp-config remove my-checker",
            "",
            "  # Preview removal",
            "  mcp-config remove my-checker --dry-run",
            "",
            "  # Remove without backup (not recommended)",
            "  mcp-config remove my-checker --no-backup",
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def format_list_command_help(verbose: bool = False) -> str:
        """Format help for the list command.
        
        Args:
            verbose: Whether to include extended help
            
        Returns:
            Formatted help string
        """
        lines = [
            "LIST COMMAND",
            "============",
            "",
            "List all MCP servers in Claude Desktop configuration.",
            "",
            "USAGE:",
            "  mcp-config list [options]",
            "",
            "OPTIONS:",
            "  --client CHOICE    MCP client to query [default: claude-desktop]",
            "  --detailed         Show detailed server information",
            "  --managed-only     Show only mcp-config managed servers",
            "",
        ]
        
        if verbose:
            lines.extend([
                "OUTPUT DETAILS:",
                "  ● = Managed by mcp-config (can be removed)",
                "  ○ = External server (manually configured)",
                "",
                "  The --detailed flag shows:",
                "    - Full command paths",
                "    - Command arguments",
                "    - Python executables",
                "    - Project directories",
                "",
            ])
        
        lines.extend([
            "EXAMPLES:",
            "  # List all servers",
            "  mcp-config list",
            "",
            "  # Show detailed information",
            "  mcp-config list --detailed",
            "",
            "  # Show only managed servers",
            "  mcp-config list --managed-only",
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def format_validate_command_help(verbose: bool = False) -> str:
        """Format help for the validate command.
        
        Args:
            verbose: Whether to include extended help
            
        Returns:
            Formatted help string
        """
        lines = [
            "VALIDATE COMMAND",
            "================",
            "",
            "Validate server configuration or show available server types.",
            "",
            "USAGE:",
            "  mcp-config validate [server-name] [options]",
            "",
            "ARGUMENTS:",
            "  server-name        Name of the server to validate (optional)",
            "",
            "OPTIONS:",
            "  --client CHOICE    MCP client to validate [default: claude-desktop]",
            "  --verbose          Show detailed validation information",
            "",
            "VALIDATION CHECKS:",
            "  ✓ Configuration file exists and is valid JSON",
            "  ✓ Server entry exists in configuration",
            "  ✓ Python executable exists and is valid",
            "  ✓ Project directory exists and is accessible",
            "  ✓ Virtual environment (if specified) exists",
            "  ✓ Main module file exists",
            "  ✓ Required dependencies are installed",
            "",
        ]
        
        if verbose:
            lines.extend([
                "TROUBLESHOOTING:",
                "  If validation fails, the command will indicate:",
                "    - Which checks passed/failed",
                "    - Specific error messages",
                "    - Suggestions for fixing issues",
                "",
            ])
        
        lines.extend([
            "EXAMPLES:",
            "  # Show available server types",
            "  mcp-config validate",
            "",
            "  # Show detailed server type information",
            "  mcp-config validate --verbose",
            "",
            "  # Validate a specific server",
            "  mcp-config validate my-checker",
            "",
            "  # Verbose validation",
            "  mcp-config validate my-checker --verbose",
        ])
        
        return "\n".join(lines)
    

    @staticmethod
    def format_all_commands_help() -> str:
        """Format comprehensive help for all commands.
        
        Returns:
            Formatted help string with all commands
        """
        sections = [
            CommandHelpFormatter.format_tool_overview(),
            "\n" + "="*60 + "\n",
            CommandHelpFormatter.format_setup_command_help(verbose=True),
            "\n" + "="*60 + "\n",
            CommandHelpFormatter.format_remove_command_help(verbose=True),
            "\n" + "="*60 + "\n",
            CommandHelpFormatter.format_list_command_help(verbose=True),
            "\n" + "="*60 + "\n",
            CommandHelpFormatter.format_validate_command_help(verbose=True),
        ]
        
        return "".join(sections)


class HelpFormatter:
    """Formats help documentation for server configurations."""
    
    @staticmethod
    def format_parameter_help(param: Any, verbose: bool = False) -> str:
        """Format help for a single parameter.
        
        Args:
            param: ParameterDef object
            verbose: Whether to include extended help
            
        Returns:
            Formatted help string
        """
        lines = []
        
        # Parameter header
        header = f"  --{param.name}"
        if param.param_type == "choice":
            header += f" {{{','.join(param.choices or [])}}}"
        elif param.param_type == "path":
            header += " <PATH>"
        elif param.param_type == "string":
            header += " <STRING>"
        elif param.is_flag:
            header += " (flag)"
            
        if param.required:
            header += " [REQUIRED]"
        elif param.auto_detect:
            header += " [AUTO-DETECTED]"
        elif param.default is not None:
            header += f" [DEFAULT: {param.default}]"
            
        lines.append(header)
        
        # Basic help text
        if param.help:
            # Wrap help text for readability
            help_lines = param.help.split(". ")
            for line in help_lines:
                if line.strip():
                    lines.append(f"      {line.strip()}")
                    if not line.endswith("."):
                        lines[-1] += "."
        
        # Extended information in verbose mode
        if verbose:
            lines.append("")
            lines.append(f"      Type: {param.param_type}")
            
            if param.param_type == "choice" and param.choices:
                lines.append(f"      Valid values: {', '.join(param.choices)}")
            
            if param.auto_detect:
                lines.append("      Auto-detection: This parameter will be automatically")
                lines.append("                      detected from your project if not specified.")
                
                if param.name == "python-executable":
                    lines.append("        - Looks for: .venv/bin/python, venv/bin/python,")
                    lines.append("                     env/bin/python, or system python")
                elif param.name == "venv-path":
                    lines.append("        - Looks for: .venv/, venv/, env/ directories")
                elif param.name == "log-file":
                    lines.append("        - Creates: project_dir/logs/mcp_TIMESTAMP.json")
            
            # Add examples for specific parameters
            if param.name == "project-dir":
                lines.append("")
                lines.append("      Examples:")
                lines.append("        --project-dir .")
                lines.append("        --project-dir /home/user/my-project")
                lines.append("        --project-dir ../another-project")
                
            elif param.name == "python-executable":
                lines.append("")
                lines.append("      Examples:")
                lines.append("        --python-executable /usr/bin/python3.11")
                lines.append("        --python-executable .venv/bin/python")
                lines.append("        --python-executable python3")
                
            elif param.name == "log-level":
                lines.append("")
                lines.append("      Log levels (from most to least verbose):")
                lines.append("        DEBUG    - Detailed diagnostic information")
                lines.append("        INFO     - General informational messages")
                lines.append("        WARNING  - Warning messages for potential issues")
                lines.append("        ERROR    - Error messages for failures")
                lines.append("        CRITICAL - Critical failures that may abort execution")
        
        lines.append("")
        return "\n".join(lines)
    
    @staticmethod
    def format_server_help(server_config: ServerConfig, verbose: bool = False) -> str:
        """Format complete help for a server configuration.
        
        Args:
            server_config: ServerConfig object
            verbose: Whether to include extended help
            
        Returns:
            Formatted help string
        """
        lines = []
        
        # Server header
        lines.append(f"{server_config.display_name} ({server_config.name})")
        lines.append("=" * len(lines[0]))
        lines.append("")
        
        # Server description
        if server_config.name == "mcp-code-checker":
            lines.append("A comprehensive code checking server that runs pylint, pytest,")
            lines.append("and mypy on your Python projects. Provides intelligent prompts")
            lines.append("for LLMs to help fix issues found during code analysis.")
            lines.append("")
        
        # Module information
        lines.append(f"Main module: {server_config.main_module}")
        lines.append("")
        
        # Group parameters by category
        required_params = []
        optional_params = []
        auto_detect_params = []
        
        for param in server_config.parameters:
            if param.required:
                required_params.append(param)
            elif param.auto_detect:
                auto_detect_params.append(param)
            else:
                optional_params.append(param)
        
        # Required parameters
        if required_params:
            lines.append("REQUIRED PARAMETERS:")
            lines.append("-" * 20)
            for param in required_params:
                lines.append(HelpFormatter.format_parameter_help(param, verbose))
        
        # Auto-detected parameters
        if auto_detect_params:
            lines.append("AUTO-DETECTED PARAMETERS (optional):")
            lines.append("-" * 37)
            lines.append("These parameters will be automatically detected from your project")
            lines.append("if not explicitly specified.")
            lines.append("")
            for param in auto_detect_params:
                lines.append(HelpFormatter.format_parameter_help(param, verbose))
        
        # Optional parameters
        if optional_params:
            lines.append("OPTIONAL PARAMETERS:")
            lines.append("-" * 20)
            for param in optional_params:
                lines.append(HelpFormatter.format_parameter_help(param, verbose))
        
        # Usage examples
        lines.append("USAGE EXAMPLES:")
        lines.append("-" * 15)
        lines.append("")
        
        lines.append("  # Basic setup with auto-detection:")
        lines.append(f"  mcp-config setup {server_config.name} my-checker --project-dir .")
        lines.append("")
        
        lines.append("  # Specify Python executable:")
        lines.append(f"  mcp-config setup {server_config.name} my-checker \\")
        lines.append("    --project-dir . \\")
        lines.append("    --python-executable /usr/bin/python3.11")
        lines.append("")
        
        lines.append("  # Debug configuration with custom logging:")
        lines.append(f"  mcp-config setup {server_config.name} debug-checker \\")
        lines.append("    --project-dir . \\")
        lines.append("    --log-level DEBUG \\")
        lines.append("    --log-file debug.log \\")
        lines.append("    --keep-temp-files")
        lines.append("")
        
        lines.append("  # Use with virtual environment:")
        lines.append(f"  mcp-config setup {server_config.name} venv-checker \\")
        lines.append("    --project-dir /path/to/project \\")
        lines.append("    --venv-path /path/to/project/.venv")
        lines.append("")
        
        lines.append("  # Console-only logging (no file output):")
        lines.append(f"  mcp-config setup {server_config.name} console-checker \\")
        lines.append("    --project-dir . \\")
        lines.append("    --console-only")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_quick_reference(server_config: ServerConfig) -> str:
        """Format a quick reference card for a server.
        
        Args:
            server_config: ServerConfig object
            
        Returns:
            Formatted quick reference string
        """
        lines = []
        lines.append(f"QUICK REFERENCE: {server_config.display_name}")
        lines.append("=" * (16 + len(server_config.display_name)))
        lines.append("")
        
        # Required parameters
        required = server_config.get_required_params()
        if required:
            lines.append("Required: " + ", ".join(f"--{p}" for p in required))
            lines.append("")
        
        # Common usage patterns
        lines.append("Common Usage Patterns:")
        lines.append("----------------------")
        lines.append("")
        
        lines.append("1. Minimal (auto-detects Python environment):")
        lines.append(f"   mcp-config setup {server_config.name} my-server --project-dir .")
        lines.append("")
        
        lines.append("2. With virtual environment:")
        lines.append(f"   mcp-config setup {server_config.name} my-server \\")
        lines.append("     --project-dir . --venv-path .venv")
        lines.append("")
        
        lines.append("3. Debug mode:")
        lines.append(f"   mcp-config setup {server_config.name} my-server \\")
        lines.append("     --project-dir . --log-level DEBUG --keep-temp-files")
        lines.append("")
        
        lines.append("4. Custom Python:")
        lines.append(f"   mcp-config setup {server_config.name} my-server \\")
        lines.append("     --project-dir . --python-executable python3.11")
        lines.append("")
        
        # Parameter cheat sheet
        lines.append("Parameter Cheat Sheet:")
        lines.append("---------------------")
        for param in server_config.parameters:
            marker = "*" if param.required else "°" if param.auto_detect else " "
            param_line = f" {marker} --{param.name}"
            
            # Add short description
            if param.param_type == "choice" and param.choices:
                param_line += f" [{'/'.join(param.choices)}]"
            elif param.param_type == "path":
                param_line += " <path>"
            elif param.is_flag:
                param_line += " (flag)"
                
            # Truncate help to fit on one line
            if param.help:
                short_help = param.help.split(".")[0]
                if len(short_help) > 40:
                    short_help = short_help[:37] + "..."
                param_line += f" - {short_help}"
                
            lines.append(param_line)
        
        lines.append("")
        lines.append("Legend: * = required, ° = auto-detected")
        
        return "\n".join(lines)


def print_command_help(command: Optional[str] = None, verbose: bool = False) -> int:
    """Print help for mcp-config commands.
    
    Args:
        command: Optional command to show help for. If None, shows overview.
        verbose: Whether to show extended help
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    if command is None:
        print(CommandHelpFormatter.format_tool_overview())
    elif command == "all":
        print(CommandHelpFormatter.format_all_commands_help())
    elif command == "setup":
        print(CommandHelpFormatter.format_setup_command_help(verbose))
    elif command == "remove":
        print(CommandHelpFormatter.format_remove_command_help(verbose))
    elif command == "list":
        print(CommandHelpFormatter.format_list_command_help(verbose))
    elif command == "validate":
        print(CommandHelpFormatter.format_validate_command_help(verbose))
    elif command == "help":
        print("HELP COMMAND")
        print("============")
        print("")
        print("Show detailed help and documentation for mcp-config.")
        print("")
        print("USAGE:")
        print("  mcp-config help [topic] [options]")
        print("")
        print("TOPICS:")
        print("  <command>          Show help for a specific command")
        print("  <server-type>      Show parameters for a server type")
        print("  all                Show comprehensive documentation")
        print("")
        print("OPTIONS:")
        print("  --command          Treat topic as a command name")
        print("  --server           Treat topic as a server type")
        print("  --parameter PARAM  Show help for specific parameter")
        print("  --quick            Show quick reference")
        print("  --verbose          Show extended help")
        print("")
        print("EXAMPLES:")
        print("  mcp-config help                    # Show overview")
        print("  mcp-config help setup               # Help for setup command")
        print("  mcp-config help mcp-code-checker    # Help for server parameters")
        print("  mcp-config help all                 # Complete documentation")
    else:
        print(f"Unknown command: {command}")
        print("Available commands: setup, remove, list, validate, help")
        return 1
    
    return 0


def print_parameter_help(server_type: str, parameter_name: Optional[str] = None, 
                         verbose: bool = False) -> int:
    """Print help for server parameters.
    
    Args:
        server_type: Type of server to show help for
        parameter_name: Optional specific parameter to show help for
        verbose: Whether to show extended help
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    server_config = registry.get(server_type)
    if not server_config:
        print(f"Error: Unknown server type '{server_type}'")
        print(f"Available types: {', '.join(registry.list_servers())}")
        return 1
    
    if parameter_name:
        # Show help for specific parameter
        param = server_config.get_parameter_by_name(parameter_name)
        if not param:
            print(f"Error: Parameter '--{parameter_name}' not found for server '{server_type}'")
            print(f"Available parameters for {server_config.display_name}:")
            for p in server_config.parameters:
                print(f"  --{p.name}")
            return 1
        
        print(HelpFormatter.format_parameter_help(param, verbose=True))
    else:
        # Show help for all parameters
        print(HelpFormatter.format_server_help(server_config, verbose))
    
    return 0


def print_quick_reference(server_type: Optional[str] = None) -> int:
    """Print quick reference for server(s).
    
    Args:
        server_type: Optional server type to show reference for.
                    If None, shows reference for all servers.
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    if server_type:
        server_config = registry.get(server_type)
        if not server_config:
            print(f"Error: Unknown server type '{server_type}'")
            print(f"Available types: {', '.join(registry.list_servers())}")
            return 1
        
        print(HelpFormatter.format_quick_reference(server_config))
    else:
        # Show reference for all servers
        configs = registry.get_all_configs()
        for i, (name, config) in enumerate(sorted(configs.items())):
            if i > 0:
                print("\n" + "=" * 60 + "\n")
            print(HelpFormatter.format_quick_reference(config))
    
    return 0
