"""Output formatting utilities for CLI commands."""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class OutputFormatter:
    """Handle formatted output for CLI commands."""
    
    # Status symbols
    SUCCESS = "✓"
    ERROR = "✗" 
    WARNING = "⚠"
    INFO = "ℹ"
    SEARCH = "🔍"
    CHECK_PASS = "✅"
    CHECK_FAIL = "❌"
    
    # Tree symbols
    TREE_BRANCH = "├──"
    TREE_LAST = "└──"
    TREE_PIPE = "│   "
    TREE_SPACE = "    "

    @staticmethod
    def print_success(message: str) -> None:
        """Print success message with checkmark."""
        print(f"{OutputFormatter.SUCCESS} {message}")

    @staticmethod
    def print_error(message: str) -> None:
        """Print error message with X mark."""
        print(f"{OutputFormatter.ERROR} {message}")

    @staticmethod
    def print_info(message: str) -> None:
        """Print informational message."""
        print(f"{OutputFormatter.INFO} {message}")

    @staticmethod
    def print_warning(message: str) -> None:
        """Print warning message."""
        print(f"{OutputFormatter.WARNING} {message}")

    @staticmethod
    def print_setup_summary(
        server_name: str, server_type: str, params: dict[str, Any]
    ) -> None:
        """Print formatted setup summary.

        Args:
            server_name: Name of the server instance
            server_type: Type of server being configured
            params: Parameters for the server configuration
        """
        print("\nSetup Summary:")
        print(f"  Server Name: {server_name}")
        print(f"  Server Type: {server_type}")
        print("  Parameters:")

        for key, value in params.items():
            if value is not None:
                display_key = key.replace("_", "-")
                if isinstance(value, Path):
                    value = str(value)
                print(f"    {display_key}: {value}")

    @staticmethod
    def print_server_list(
        servers: list[dict[str, Any]], detailed: bool = False
    ) -> None:
        """Print formatted server list.

        Args:
            servers: List of server configurations
            detailed: Whether to show detailed information
        """
        if not servers:
            print("  No servers found")
            return

        for server in servers:
            managed_icon = "●" if server.get("managed", False) else "○"
            print(
                f"  {managed_icon} {server['name']} ({server.get('type', 'unknown')})"
            )

            if detailed:
                command = server.get("command", "N/A")
                print(f"    Command: {command}")

                if server.get("args"):
                    args_str = " ".join(server["args"])
                    if len(args_str) > 80:
                        args_str = args_str[:77] + "..."
                    print(f"    Args: {args_str}")

                if not server.get("managed", False):
                    print("    Note: External server (not managed by mcp-config)")
                print()

    @staticmethod
    def format_table(
        headers: list[str], rows: list[list[str]], max_width: int = 80
    ) -> str:
        """Format data as a table.

        Args:
            headers: Column headers
            rows: Data rows
            max_width: Maximum width for the table

        Returns:
            Formatted table string
        """
        if not headers:
            return ""

        # If we have headers but no rows, still show headers
        if not rows:
            header_line = " | ".join(headers)
            separator = "-" * len(header_line)
            return f"{header_line}\n{separator}"

        # Calculate column widths
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))

        # Apply max_width constraint if total width exceeds it
        # Account for separators (" | " between columns)
        separator_width = (len(headers) - 1) * 3
        total_width = sum(widths) + separator_width

        if total_width > max_width and headers:
            # Distribute max_width among columns proportionally
            available_width = max_width - separator_width
            if available_width > 0:
                # Ensure each column gets at least 4 chars (for "..." plus one char)
                min_col_width = 4
                max_col_width = available_width // len(headers)

                for i in range(len(widths)):
                    if widths[i] > max_col_width:
                        widths[i] = max(max_col_width, min_col_width)

        # Build table
        lines = []

        # Header
        header_line = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # Rows
        for row in rows:
            cells = []
            for i, (cell, width) in enumerate(zip(row, widths)):
                cell_str = str(cell)
                if len(cell_str) > width:
                    cell_str = cell_str[: width - 3] + "..."
                cells.append(cell_str.ljust(width))
            lines.append(" | ".join(cells))

        return "\n".join(lines)
        
    @staticmethod
    def print_auto_detected_params(params: dict[str, Any]) -> None:
        """Print auto-detected parameters.
        
        Args:
            params: Dictionary of auto-detected parameters
        """
        if not params:
            return
            
        print("Auto-detected parameters:")
        for key, value in params.items():
            if value is not None:
                display_key = key.replace("_", "-").title().replace("-", " ")
                value_str = str(value)
                
                # Add contextual hints based on the parameter and value
                if key == "python_executable" and (".venv" in value_str or "venv" in value_str):
                    value_str += " (from venv)"
                elif key == "venv_path":
                    value_str += " (detected)" if value_str else ""
                elif key == "log_file" and "auto" in value_str.lower():
                    value_str += " (auto-generated)"
                elif key in ["test_folder", "log_level"] and value in ["tests", "INFO"]:
                    value_str += " (default)"
                        
                prefix = OutputFormatter.TREE_BRANCH if key != list(params.keys())[-1] else OutputFormatter.TREE_LAST
                print(f"{prefix} {display_key}: {value_str}")
                
    @staticmethod  
    def supports_color() -> bool:
        """Check if terminal supports color output.
        
        Returns:
            True if color is supported
        """
        # Check for dumb terminal
        if os.environ.get("TERM") == "dumb":
            return False
            
        # Check for Windows console
        if sys.platform == "win32":
            # Try to enable ANSI escape sequences on Windows
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except Exception:
                return False
        else:
            # For Unix-like systems, check if stdout is a TTY
            return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    @staticmethod
    def print_validation_errors(errors: list[str]) -> None:
        """Print validation errors in a formatted way.

        Args:
            errors: List of validation error messages
        """
        if not errors:
            return

        print(f"\n{OutputFormatter.CHECK_FAIL} Validation Errors:")
        for error in errors:
            print(f"  • {error}")
            
    @staticmethod
    def print_validation_results(validation_result: dict[str, Any]) -> None:
        """Print comprehensive validation results.
        
        Args:
            validation_result: Dictionary with validation results
        """
        print("\nValidation Results:")
        print()
        
        # Print each check
        for check in validation_result.get("checks", []):
            status = check.get("status", "unknown")
            name = check.get("name", "Unknown check")
            message = check.get("message", "")
            
            if status == "success":
                symbol = OutputFormatter.SUCCESS
            elif status == "error":
                symbol = OutputFormatter.ERROR
            elif status == "warning":
                symbol = OutputFormatter.WARNING
            elif status == "info":
                symbol = OutputFormatter.INFO
            else:
                symbol = "○"
                
            print(f"{symbol} {message}")
        
        # Print overall result
        print()
        if validation_result.get("success"):
            print(f"{OutputFormatter.CHECK_PASS} Configuration is valid and ready to use")
        else:
            print(f"{OutputFormatter.CHECK_FAIL} Configuration has errors")
            
        # Print warnings if any
        warnings = validation_result.get("warnings", [])
        if warnings:
            print(f"\n{OutputFormatter.WARNING} Warnings:")
            for warning in warnings:
                print(f"  • {warning}")
                
        # Print suggestions if any
        suggestions = validation_result.get("suggestions", [])
        if suggestions:
            print("\nSuggestions:")
            for suggestion in suggestions:
                print(f"  • {suggestion}")
                
    @staticmethod
    def print_configuration_details(
        server_name: str,
        server_type: str, 
        params: dict[str, Any],
        tree_format: bool = True
    ) -> None:
        """Print configuration details in tree format.
        
        Args:
            server_name: Name of the server
            server_type: Type of server
            params: Configuration parameters
            tree_format: Whether to use tree formatting
        """
        print("\nConfiguration Details:")
        
        if tree_format:
            print(f"{OutputFormatter.TREE_BRANCH} Server Type: {server_type}")
            print(f"{OutputFormatter.TREE_BRANCH} Server Name: {server_name}")
            
            # Convert params to display format
            param_items = []
            for key, value in params.items():
                if value is not None:
                    display_key = key.replace("_", "-").title().replace("-", " ")
                    if isinstance(value, Path):
                        value = str(value)
                    param_items.append((display_key, value))
                    
            # Print parameters
            for i, (key, value) in enumerate(param_items):
                is_last = (i == len(param_items) - 1)
                prefix = OutputFormatter.TREE_LAST if is_last else OutputFormatter.TREE_BRANCH
                print(f"{prefix} {key}: {value}")
        else:
            print(f"  Server Type: {server_type}")
            print(f"  Server Name: {server_name}")
            print("  Parameters:")
            for key, value in params.items():
                if value is not None:
                    display_key = key.replace("_", "-")
                    if isinstance(value, Path):
                        value = str(value)
                    print(f"    {display_key}: {value}")
                    
    @staticmethod
    def print_dry_run_header() -> None:
        """Print dry-run mode header."""
        print(f"\n{OutputFormatter.SEARCH} DRY RUN: No changes will be applied")
        print()
        
    @staticmethod
    def print_dry_run_config_preview(
        config: dict[str, Any],
        config_path: Path,
        backup_path: Path | None = None
    ) -> None:
        """Print configuration preview for dry-run mode.
        
        Args:
            config: Configuration dictionary to preview
            config_path: Path where config would be saved
            backup_path: Path where backup would be created
        """
        import json
        
        print("Would add/update server configuration:")
        print(json.dumps(config, indent=2))
        print()
        print(f"Configuration file: {config_path}")
        
        if backup_path:
            print(f"Backup would be created: {backup_path}")
            
        print()
        print(f"{OutputFormatter.CHECK_PASS} Configuration is valid. Run without --dry-run to apply changes.")
        
    @staticmethod
    def print_dry_run_remove_preview(
        server_name: str,
        server_info: dict[str, Any],
        other_servers: list[dict[str, Any]],
        config_path: Path,
        backup_path: Path | None = None  
    ) -> None:
        """Print removal preview for dry-run mode.
        
        Args:
            server_name: Name of server to remove
            server_info: Information about server being removed
            other_servers: List of servers that will be preserved
            config_path: Path to configuration file
            backup_path: Path where backup would be created
        """
        print(f"Would remove server '{server_name}' from configuration.")
        print()
        print("Current configuration:")
        print(f"{OutputFormatter.TREE_BRANCH} Server Type: {server_info.get('type', 'unknown')}")
        print(f"{OutputFormatter.TREE_BRANCH} Command: {server_info.get('command', 'N/A')}")
        print(f"{OutputFormatter.TREE_LAST} Managed by: mcp-config")
        print()
        
        if other_servers:
            print("Other servers will be preserved:")
            for server in other_servers:
                managed = " (managed)" if server.get("managed") else " (external)"
                print(f"{OutputFormatter.TREE_BRANCH} {server['name']}{managed}")
        print()
        
        print(f"Configuration file: {config_path}")
        if backup_path:
            print(f"Backup would be created: {backup_path}")
            
        print()
        print(f"{OutputFormatter.CHECK_PASS} Removal is safe. Run without --dry-run to apply changes.")
        
    @staticmethod
    def print_enhanced_server_list(
        servers: list[dict[str, Any]],
        client_name: str,
        config_path: Path,
        detailed: bool = False
    ) -> None:
        """Print enhanced server list with better formatting.
        
        Args:
            servers: List of server configurations
            client_name: Name of the client
            config_path: Path to configuration file
            detailed: Whether to show detailed information
        """
        print(f"\nMCP Servers Configuration ({client_name})")
        print()
        
        # Separate managed and external servers
        managed_servers = [s for s in servers if s.get("managed", False)]
        external_servers = [s for s in servers if not s.get("managed", False)]
        
        if managed_servers:
            print(f"Managed Servers ({len(managed_servers)}):")
            for i, server in enumerate(managed_servers):
                is_last = (i == len(managed_servers) - 1)
                prefix = OutputFormatter.TREE_LAST if is_last else OutputFormatter.TREE_BRANCH
                
                status_icon = OutputFormatter.CHECK_PASS
                print(f"{prefix} {server['name']} ({server.get('type', 'unknown')}) {status_icon}")
                
                if detailed:
                    indent = OutputFormatter.TREE_SPACE if is_last else OutputFormatter.TREE_PIPE
                    if "command" in server:
                        print(f"{indent} {OutputFormatter.TREE_BRANCH} Command: {server['command']}")
                    if server.get("args"):
                        args_str = " ".join(server["args"])
                        if len(args_str) > 60:
                            args_str = args_str[:57] + "..."
                        print(f"{indent} {OutputFormatter.TREE_BRANCH} Args: {args_str}")
                    # Add status information
                    print(f"{indent} {OutputFormatter.TREE_LAST} Status: Ready")
        else:
            print("Managed Servers (0): None")
            
        if external_servers:
            print(f"\nExternal Servers ({len(external_servers)}):")
            for i, server in enumerate(external_servers):
                is_last = (i == len(external_servers) - 1)
                prefix = OutputFormatter.TREE_LAST if is_last else OutputFormatter.TREE_BRANCH
                print(f"{prefix} {server['name']} (external) - not managed by mcp-config")
        else:
            print("\nExternal Servers (0): None")
            
        print()
        print(f"Configuration: {config_path}")
        
        # Show last modified time if file exists
        if config_path.exists():
            mtime = datetime.fromtimestamp(config_path.stat().st_mtime)
            print(f"Last Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            
        print()
        print("Use 'mcp-config validate <server-name>' to check specific configurations.")
