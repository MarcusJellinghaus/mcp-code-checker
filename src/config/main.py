"""Main CLI entry point for MCP Configuration Helper."""

import argparse
import sys
from pathlib import Path
from typing import Any

from src.config import initialize_all_servers
from src.config.cli_utils import create_full_parser, validate_setup_args
from src.config.clients import get_client_handler
from src.config.detection import detect_python_environment
from src.config.integration import (
    build_server_config,
    remove_mcp_server,
    setup_mcp_server,
)
from src.config.output import OutputFormatter
from src.config.servers import registry
from src.config.utils import validate_required_parameters
from src.config.validation import (
    validate_parameter_combination,
    validate_server_configuration,
)


def create_main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    # Use the enhanced parser from cli_utils
    return create_full_parser()


# The add_setup_parser, add_server_specific_options, add_remove_parser, and add_list_parser
# functions are now handled by cli_utils.py for better organization and reusability


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
        # Re-initialize to catch any newly installed servers
        if args.verbose:
            print("Checking for server configurations...")
            initialize_all_servers(verbose=False)

        # Validate server type
        server_config = registry.get(args.server_type)
        if not server_config:
            OutputFormatter.print_error(f"Unknown server type '{args.server_type}'")
            print(f"Available types: {', '.join(registry.list_servers())}")
            return 1

        # Get client handler
        client_handler = get_client_handler(args.client)

        # Extract user parameters from args
        user_params = extract_user_parameters(args, server_config)

        # Auto-detect Python environment if not provided
        auto_detected = {}
        if (
            "python_executable" not in user_params
            or not user_params["python_executable"]
        ):
            project_dir = Path(user_params.get("project_dir", "."))
            python_exe, venv_path = detect_python_environment(project_dir)
            if python_exe:
                user_params["python_executable"] = str(python_exe)
                auto_detected["python_executable"] = str(python_exe)
            if venv_path and "venv_path" not in user_params:
                user_params["venv_path"] = str(venv_path)
                auto_detected["venv_path"] = str(venv_path)

        # Validate required parameters
        validation_errors = validate_required_parameters(server_config, user_params)
        if validation_errors:
            OutputFormatter.print_validation_errors(validation_errors)
            return 1

        # Validate parameter combinations
        combination_errors = validate_parameter_combination(user_params)
        if combination_errors:
            OutputFormatter.print_validation_errors(combination_errors)
            return 1

        # Run additional validation from cli_utils
        cli_errors = validate_setup_args(args)
        if cli_errors:
            OutputFormatter.print_validation_errors(cli_errors)
            return 1

        # Show what will be done
        if args.dry_run:
            OutputFormatter.print_dry_run_header()

            # Show auto-detected parameters
            if auto_detected:
                OutputFormatter.print_auto_detected_params(auto_detected)
                print()

            # Build the server config that would be saved
            server_cfg = build_server_config(
                server_config,
                user_params,
                user_params.get("python_executable", sys.executable),
            )

            # Generate backup path
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = (
                client_handler.get_config_path().parent
                / f"claude_desktop_config.backup_{timestamp}.json"
            )

            OutputFormatter.print_dry_run_config_preview(
                server_cfg,
                client_handler.get_config_path(),
                backup_path if args.backup else None,
            )
            return 0
        elif args.verbose:
            OutputFormatter.print_configuration_details(
                args.server_name, server_config.name, user_params
            )

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
                OutputFormatter.print_error(
                    f"Server '{args.server_name}' exists but is not managed by mcp-config"
                )
                print("Only servers created by mcp-config can be removed")
                return 1
            else:
                OutputFormatter.print_error(f"Server '{args.server_name}' not found")
                if managed_names:
                    print(f"Managed servers: {', '.join(managed_names)}")
                return 1

        # Get server info
        server_info = next(s for s in managed_servers if s["name"] == args.server_name)

        # Show what will be removed
        if args.dry_run:
            OutputFormatter.print_dry_run_header()

            # Get other servers that will be preserved
            all_servers = client_handler.list_all_servers()
            other_servers = [s for s in all_servers if s["name"] != args.server_name]

            # Generate backup path
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = (
                client_handler.get_config_path().parent
                / f"claude_desktop_config.backup_{timestamp}.json"
            )

            OutputFormatter.print_dry_run_remove_preview(
                args.server_name,
                server_info,
                other_servers,
                client_handler.get_config_path(),
                backup_path if args.backup else None,
            )
            return 0
        elif args.verbose:
            print(f"Will remove server '{args.server_name}':")
            print(f"  Type: {server_info['type']}")
            print(f"  Command: {server_info['command']}")

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
            config_path = client_handler.get_config_path()

            if args.managed_only:
                servers = client_handler.list_managed_servers()
            else:
                servers = client_handler.list_all_servers()

            # Use enhanced output formatter
            OutputFormatter.print_enhanced_server_list(
                servers, client_name, config_path, args.detailed
            )

        return 0

    except Exception as e:
        print(f"List failed: {e}")
        if hasattr(args, "verbose") and args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_help_command(args: argparse.Namespace) -> int:
    """Handle the help command to show detailed documentation.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        from src.config.help_system import (
            print_parameter_help,
            print_quick_reference,
            print_command_help
        )
        
        # Handle --all flag
        if args.all:
            return print_command_help("all", verbose=True)
        
        # Determine what kind of help to show
        topic = args.topic
        
        # List of known commands
        commands = [
            "setup", "remove", "list", "validate", 
            "help", "all"
        ]
        
        # List of known server types
        server_types = registry.list_servers()
        
        # If no topic specified, show overview
        if not topic:
            if args.quick:
                # Show quick reference for all servers
                return print_quick_reference(None)
            else:
                # Show tool overview
                return print_command_help(None, args.verbose)
        
        # Determine topic type
        is_command = topic in commands or args.command
        is_server = topic in server_types or args.server
        
        # Handle conflicts
        if args.command and args.server:
            print("Error: Cannot use both --command and --server flags")
            return 1
        
        # If topic could be both, prefer command unless --server is specified
        if not is_command and not is_server:
            print(f"Unknown topic: {topic}")
            print(f"Available commands: {', '.join(commands)}")
            print(f"Available servers: {', '.join(server_types)}")
            return 1
        
        # Show command help
        if is_command and not args.server:
            if args.parameter:
                print("Error: --parameter flag is only for server help")
                return 1
            if args.quick:
                print("Error: --quick flag is only for server help")
                return 1
            return print_command_help(topic, args.verbose)
        
        # Show server help
        if is_server and not args.command:
            if args.quick:
                return print_quick_reference(topic)
            elif args.parameter:
                return print_parameter_help(topic, args.parameter, verbose=True)
            else:
                return print_parameter_help(topic, None, args.verbose)
        
        # Shouldn't reach here
        print(f"Could not determine help type for: {topic}")
        return 1

    except Exception as e:
        print(f"Failed to show help: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_validate_command(args: argparse.Namespace) -> int:
    """Handle the validate command with comprehensive checks."""
    try:
        # Get client handler
        client_handler = get_client_handler(args.client)

        # If no server name provided, show available types
        if not args.server_name:
            configs = registry.get_all_configs()
            if not configs:
                print("No server types available")
                return 1

            # Group by built-in vs external
            builtin_servers = []
            external_servers = []

            for name, config in sorted(configs.items()):
                if name == "mcp-code-checker":  # Known built-in
                    builtin_servers.append((name, config))
                else:
                    external_servers.append((name, config))

            print("Available server types:")

            # Display built-in servers
            if builtin_servers:
                print("\n  Built-in servers:")
                for name, config in builtin_servers:
                    print(f"    • {name}: {config.display_name}")
                    if args.verbose:
                        print(f"      Module: {config.main_module}")
                        print(f"      Parameters: {len(config.parameters)}")
                        required = config.get_required_params()
                        if required:
                            print(f"      Required: {', '.join(required)}")

                        # Show all parameters
                        print("      All parameters:")
                        for param in config.parameters:
                            req_mark = "*" if param.required else " "
                            auto_mark = "(auto)" if param.auto_detect else ""
                            print(
                                f"        {req_mark} {param.name}: {param.param_type} {auto_mark}"
                            )
                            if param.help and args.verbose:
                                # Wrap help text for readability
                                help_lines = param.help.split(". ")
                                for line in help_lines:
                                    if line:
                                        print(f"            {line}")
                        print()  # Empty line between server types

            # Display external servers
            if external_servers:
                print("\n  External servers:")
                for name, config in external_servers:
                    print(f"    • {name}: {config.display_name}")
                    if args.verbose:
                        print(f"      Module: {config.main_module}")
                        print(f"      Parameters: {len(config.parameters)}")
                        required = config.get_required_params()
                        if required:
                            print(f"      Required: {', '.join(required)}")

                        # Show all parameters
                        print("      All parameters:")
                        for param in config.parameters:
                            req_mark = "*" if param.required else " "
                            auto_mark = "(auto)" if param.auto_detect else ""
                            print(
                                f"        {req_mark} {param.name}: {param.param_type} {auto_mark}"
                            )
                            if param.help and args.verbose:
                                # Wrap help text for readability
                                help_lines = param.help.split(". ")
                                for line in help_lines:
                                    if line:
                                        print(f"            {line}")
                        print()  # Empty line between server types

            if args.verbose:
                print(f"\nTotal: {len(configs)} server type(s) available.")
                print("\nUse 'mcp-config help <server-type>' for detailed parameter documentation.")
            else:
                print("\nUse 'mcp-config validate --verbose' for detailed information.")
                print("Use 'mcp-config help <server-type>' for parameter documentation.")
            
            return 0

        # Get server configuration from client
        servers = client_handler.list_all_servers()
        server_info = None
        for server in servers:
            if server["name"] == args.server_name:
                server_info = server
                break

        if not server_info:
            OutputFormatter.print_error(
                f"Server '{args.server_name}' not found in {args.client} configuration"
            )
            managed_servers = client_handler.list_managed_servers()
            if managed_servers:
                print("\nAvailable managed servers:")
                for server in managed_servers:
                    print(f"  • {server['name']} ({server['type']})")
            return 1

        # Extract parameters from server configuration
        # This is a simplified extraction - in production, we'd parse the args
        params = {}
        if server_info.get("args"):
            args_list = server_info["args"]
            # Simple parsing of common parameters
            for i, arg in enumerate(args_list):
                if arg == "--project-dir" and i + 1 < len(args_list):
                    params["project_dir"] = args_list[i + 1]
                elif arg == "--python-executable" and i + 1 < len(args_list):
                    params["python_executable"] = args_list[i + 1]
                elif arg == "--venv-path" and i + 1 < len(args_list):
                    params["venv_path"] = args_list[i + 1]
                elif arg == "--test-folder" and i + 1 < len(args_list):
                    params["test_folder"] = args_list[i + 1]
                elif arg == "--log-file" and i + 1 < len(args_list):
                    params["log_file"] = args_list[i + 1]
                elif arg == "--log-level" and i + 1 < len(args_list):
                    params["log_level"] = args_list[i + 1]

        # Get the Python executable from command if not in args
        if "python_executable" not in params and server_info.get("command"):
            params["python_executable"] = server_info["command"]

        print(f"Validating server '{args.server_name}' configuration...")
        print()

        # Run comprehensive validation
        validation_result = validate_server_configuration(
            args.server_name, server_info.get("type", "unknown"), params, client_handler
        )

        # Print validation results
        OutputFormatter.print_validation_results(validation_result)

        # Show configuration details if valid
        if validation_result["success"]:
            OutputFormatter.print_configuration_details(
                args.server_name, server_info.get("type", "unknown"), params
            )

        return 0 if validation_result["success"] else 1

    except Exception as e:
        print(f"Validation failed: {e}")
        if args.verbose:
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
        elif args.command == "validate":
            return handle_validate_command(args)
        elif args.command == "help":
            return handle_help_command(args)
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
