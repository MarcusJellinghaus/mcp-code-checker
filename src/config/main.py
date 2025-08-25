"""Main CLI entry point for MCP Configuration Helper."""

import argparse
import sys
from pathlib import Path
from typing import Any

from src.config.clients import get_client_handler
from src.config.detection import detect_python_environment
from src.config.integration import remove_mcp_server, setup_mcp_server
from src.config.servers import registry
from src.config.utils import validate_required_parameters


def create_main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="mcp-config",
        description="MCP Configuration Helper - Automate MCP server setup for Claude Desktop and other clients",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp-config setup mcp-code-checker my-checker --project-dir .
  mcp-config setup mcp-code-checker debug --project-dir . --log-level DEBUG --keep-temp-files
  mcp-config remove my-checker
  mcp-config list --detailed
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.required = True

    # Add subcommand parsers
    add_setup_parser(subparsers)
    add_remove_parser(subparsers)
    add_list_parser(subparsers)

    return parser


def add_setup_parser(subparsers: Any) -> None:
    """Add the setup command parser with dynamic options."""
    setup_parser = subparsers.add_parser(
        "setup",
        help="Setup an MCP server configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Setup an MCP server in Claude Desktop configuration",
    )

    # Positional arguments
    setup_parser.add_argument(
        "server_type", help='Server type (currently only "mcp-code-checker" supported)'
    )
    setup_parser.add_argument("server_name", help="Name for this server instance")

    # Global options
    setup_parser.add_argument(
        "--client",
        default="claude-desktop",
        choices=["claude-desktop"],
        help="MCP client to configure (default: claude-desktop)",
    )
    setup_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying them"
    )
    setup_parser.add_argument(
        "--verbose", action="store_true", help="Show detailed output"
    )
    setup_parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create backup before making changes (default: true)",
    )
    setup_parser.add_argument(
        "--no-backup", action="store_false", dest="backup", help="Skip backup creation"
    )

    # Add server-specific options dynamically
    # This will be implemented to read from ServerConfig
    add_server_specific_options(setup_parser, "mcp-code-checker")


def add_server_specific_options(
    parser: argparse.ArgumentParser, server_type: str
) -> None:
    """Add server-specific CLI options based on ServerConfig."""
    server_config = registry.get(server_type)
    if not server_config:
        return

    for param in server_config.parameters:
        option_name = f"--{param.name}"

        kwargs: dict[str, Any] = {
            "help": param.help,
            "dest": param.name.replace("-", "_"),  # Convert to valid Python identifier
        }

        if param.required:
            kwargs["required"] = True

        if param.default is not None:
            kwargs["default"] = param.default

        if param.param_type == "boolean" and param.is_flag:
            kwargs["action"] = "store_true"
        elif param.param_type == "choice":
            kwargs["choices"] = param.choices
        elif param.param_type == "path":
            kwargs["type"] = Path

        parser.add_argument(option_name, **kwargs)


def add_remove_parser(subparsers: Any) -> None:
    """Add the remove command parser."""
    remove_parser = subparsers.add_parser(
        "remove",
        help="Remove an MCP server configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Remove an MCP server from Claude Desktop configuration",
    )

    remove_parser.add_argument("server_name", help="Name of the server to remove")
    remove_parser.add_argument(
        "--client",
        default="claude-desktop",
        choices=["claude-desktop"],
        help="MCP client to configure (default: claude-desktop)",
    )
    remove_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying them"
    )
    remove_parser.add_argument(
        "--verbose", action="store_true", help="Show detailed output"
    )
    remove_parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create backup before making changes (default: true)",
    )
    remove_parser.add_argument(
        "--no-backup", action="store_false", dest="backup", help="Skip backup creation"
    )


def add_list_parser(subparsers: Any) -> None:
    """Add the list command parser."""
    list_parser = subparsers.add_parser(
        "list",
        help="List MCP server configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="List all MCP servers in Claude Desktop configuration",
    )

    list_parser.add_argument(
        "--client",
        default="claude-desktop",
        choices=["claude-desktop"],
        help="MCP client to query (default: claude-desktop)",
    )
    list_parser.add_argument(
        "--detailed", action="store_true", help="Show detailed server information"
    )
    list_parser.add_argument(
        "--managed-only",
        action="store_true",
        help="Show only mcp-config managed servers",
    )


def extract_user_parameters(
    args: argparse.Namespace, server_config: Any
) -> dict[str, Any]:
    """Extract user-provided parameters from CLI args."""
    user_params = {}

    for param in server_config.parameters:
        # Convert parameter name to the arg name (replace - with _)
        arg_name = param.name.replace("-", "_")

        # Get value from args if it exists
        if hasattr(args, arg_name):
            value = getattr(args, arg_name)
            # Only include if value was actually provided (not None or default)
            if value is not None:
                user_params[arg_name] = value

    return user_params


def print_setup_summary(
    server_name: str, server_config: Any, user_params: dict[str, Any], client: str
) -> None:
    """Print a summary of what will be configured."""
    print("\nSetup Summary:")
    print(f"  Client: {client}")
    print(f"  Server Name: {server_name}")
    print(f"  Server Type: {server_config.name}")
    print("  Parameters:")

    for key, value in user_params.items():
        if value is not None:
            # Convert snake_case back to kebab-case for display
            display_key = key.replace("_", "-")
            if isinstance(value, Path):
                value = str(value)
            print(f"    {display_key}: {value}")

    if "python_executable" in user_params:
        print(f"  Python Executable: {user_params['python_executable']}")
    if "venv_path" in user_params:
        print(f"  Virtual Environment: {user_params['venv_path']}")


def handle_setup_command(args: argparse.Namespace) -> int:
    """Handle the setup command with full validation and auto-detection."""
    try:
        # Validate server type
        server_config = registry.get(args.server_type)
        if not server_config:
            print(f"Error: Unknown server type '{args.server_type}'")
            print(f"Available types: {', '.join(registry.list_servers())}")
            return 1

        # Get client handler
        client_handler = get_client_handler(args.client)

        # Extract user parameters from args
        user_params = extract_user_parameters(args, server_config)

        # Auto-detect Python environment if not provided
        if (
            "python_executable" not in user_params
            or not user_params["python_executable"]
        ):
            project_dir = Path(user_params.get("project_dir", "."))
            python_exe, venv_path = detect_python_environment(project_dir)
            user_params["python_executable"] = str(python_exe) if python_exe else None
            if venv_path and "venv_path" not in user_params:
                user_params["venv_path"] = str(venv_path)

        # Validate parameters
        validation_errors = validate_required_parameters(server_config, user_params)
        if validation_errors:
            print("Validation errors:")
            for error in validation_errors:
                print(f"  - {error}")
            return 1

        # Show what will be done
        if args.verbose or args.dry_run:
            print_setup_summary(
                args.server_name, server_config, user_params, args.client
            )

        if args.dry_run:
            print("\nDry run completed. No changes made.")
            return 0

        # Perform setup
        result = setup_mcp_server(
            client_handler=client_handler,
            server_config=server_config,
            server_name=args.server_name,
            user_params=user_params,
            python_executable=user_params.get("python_executable", sys.executable),
            dry_run=False,
        )

        if result["success"]:
            print(f"✓ Successfully configured server '{args.server_name}'")
            if "backup_path" in result:
                print(f"  Backup created: {result['backup_path']}")
            print(f"  Configuration saved to: {client_handler.get_config_path()}")
            return 0
        else:
            print(
                f"✗ Failed to configure server: {result.get('error', 'Unknown error')}"
            )
            return 1

    except Exception as e:
        print(f"Setup failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_remove_command(args: argparse.Namespace) -> int:
    """Handle the remove command with safety checks."""
    try:
        # Get client handler
        client_handler = get_client_handler(args.client)

        # Check if server exists and is managed by us
        managed_servers = client_handler.list_managed_servers()
        managed_names = [s["name"] for s in managed_servers]

        if args.server_name not in managed_names:
            all_servers = client_handler.list_all_servers()
            all_names = [s["name"] for s in all_servers]

            if args.server_name in all_names:
                print(
                    f"Error: Server '{args.server_name}' exists but is not managed by mcp-config"
                )
                print("Only servers created by mcp-config can be removed")
                return 1
            else:
                print(f"Error: Server '{args.server_name}' not found")
                if managed_names:
                    print(f"Managed servers: {', '.join(managed_names)}")
                return 1

        # Show what will be removed
        if args.verbose or args.dry_run:
            server_info = next(
                s for s in managed_servers if s["name"] == args.server_name
            )
            print(f"Will remove server '{args.server_name}':")
            print(f"  Type: {server_info['type']}")
            print(f"  Command: {server_info['command']}")

        if args.dry_run:
            print("\nDry run completed. No changes made.")
            return 0

        # Perform removal
        result = remove_mcp_server(
            client_handler=client_handler, server_name=args.server_name, dry_run=False
        )

        if result["success"]:
            print(f"✓ Successfully removed server '{args.server_name}'")
            if "backup_path" in result:
                print(f"  Backup created: {result['backup_path']}")
            return 0
        else:
            print(f"✗ Failed to remove server: {result.get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"Remove failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def print_server_info(server: dict[str, Any], detailed: bool = False) -> None:
    """Print formatted server information."""
    managed_mark = "●" if server["managed"] else "○"
    print(f"  {managed_mark} {server['name']} ({server['type']})")

    if detailed:
        print(f"    Command: {server['command']}")
        if server.get("args"):
            args_str = " ".join(server["args"])
            if len(args_str) > 80:
                args_str = args_str[:77] + "..."
            print(f"    Args: {args_str}")
        if not server["managed"]:
            print("    Note: External server (not managed by mcp-config)")
        print()


def handle_list_command(args: argparse.Namespace) -> int:
    """Handle the list command with detailed output."""
    try:
        # Get client handler(s)
        if args.client:
            clients = [args.client]
        else:
            clients = ["claude-desktop"]  # Default for now

        for client_name in clients:
            client_handler = get_client_handler(client_name)

            print(f"\n{client_name.replace('-', ' ').title()} Configuration:")
            print(f"Config file: {client_handler.get_config_path()}")

            if args.managed_only:
                servers = client_handler.list_managed_servers()
                title = "Managed Servers"
            else:
                servers = client_handler.list_all_servers()
                title = "All Servers"

            if not servers:
                print("  No servers found")
                continue

            print(f"\n{title}:")
            for server in servers:
                print_server_info(server, args.detailed)

        return 0

    except Exception as e:
        print(f"List failed: {e}")
        if hasattr(args, "verbose") and args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def main() -> int:
    """Main CLI entry point."""
    try:
        parser = create_main_parser()
        args = parser.parse_args()

        # Dispatch to appropriate handler
        if args.command == "setup":
            return handle_setup_command(args)
        elif args.command == "remove":
            return handle_remove_command(args)
        elif args.command == "list":
            return handle_list_command(args)
        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if "args" in locals() and hasattr(args, "verbose") and args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
