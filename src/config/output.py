"""Output formatting utilities for CLI commands."""

from pathlib import Path
from typing import Any


class OutputFormatter:
    """Handle formatted output for CLI commands."""

    @staticmethod
    def print_success(message: str) -> None:
        """Print success message with checkmark."""
        print(f"✓ {message}")

    @staticmethod
    def print_error(message: str) -> None:
        """Print error message with X mark."""
        print(f"✗ {message}")

    @staticmethod
    def print_info(message: str) -> None:
        """Print informational message."""
        print(f"ℹ {message}")

    @staticmethod
    def print_warning(message: str) -> None:
        """Print warning message."""
        print(f"⚠ {message}")

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
    def print_validation_errors(errors: list[str]) -> None:
        """Print validation errors in a formatted way.

        Args:
            errors: List of validation error messages
        """
        if not errors:
            return

        print("\n❌ Validation Errors:")
        for error in errors:
            print(f"  • {error}")
