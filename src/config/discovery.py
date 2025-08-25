"""External server discovery system for MCP Configuration Helper.

This module provides functionality to discover and integrate external MCP server
configurations via Python entry points.
"""

import logging
import sys
from typing import Any, Dict, List, Optional, Tuple

from .servers import ServerConfig, registry

logger = logging.getLogger(__name__)


class ServerDiscoveryError(Exception):
    """Raised when server discovery fails."""

    pass


class ExternalServerValidator:
    """Validates external server configurations."""

    @staticmethod
    def validate_server_config(config: Any, source_name: str) -> Tuple[bool, List[str]]:
        """Validate external server configuration.

        Args:
            config: The configuration object from external package
            source_name: Name of the source (for error reporting)

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check if it's a ServerConfig instance
        if not isinstance(config, ServerConfig):
            errors.append(
                f"Configuration from {source_name} is not a ServerConfig instance "
                f"(got {type(config).__name__})"
            )
            return False, errors

        # Validate required fields
        if not config.name:
            errors.append(
                f"Server config from {source_name} missing required 'name' field"
            )

        if not config.display_name:
            errors.append(
                f"Server config from {source_name} missing required 'display_name' field"
            )

        if not config.main_module:
            errors.append(
                f"Server config from {source_name} missing required 'main_module' field"
            )

        # Only validate name-specific rules if name exists
        if config.name:
            # Validate name format (should be valid for CLI)
            if not config.name.replace("-", "").replace("_", "").isalnum():
                errors.append(
                    f"Server config from {source_name} has invalid name '{config.name}' "
                    "(should contain only letters, numbers, hyphens, and underscores)"
                )

            # Check for name conflicts with built-in servers
            if config.name in ["mcp-code-checker"]:
                errors.append(
                    f"Server config from {source_name} conflicts with built-in server name "
                    f"'{config.name}'"
                )

        return len(errors) == 0, errors


def discover_external_servers() -> Dict[str, Tuple[ServerConfig, str]]:
    """Discover external MCP server configurations via entry points.

    Returns:
        Dict mapping server names to (ServerConfig, source_package) tuples
    """
    discovered: Dict[str, Tuple[ServerConfig, str]] = {}
    errors: List[str] = []

    try:
        # Try to import importlib.metadata (Python 3.8+)
        try:
            from importlib.metadata import PackageNotFoundError, entry_points
        except ImportError:
            # Fallback for older Python versions
            from importlib_metadata import (  # type: ignore
                PackageNotFoundError,
                entry_points,
            )

        # Use importlib.metadata for Python 3.8+ compatibility
        eps = entry_points()

        # Handle both old and new entry_points() API
        if hasattr(eps, "select"):
            # New API (Python 3.10+)
            mcp_entries = eps.select(group="mcp.server_configs")
        else:
            # Old API (Python 3.8-3.9)
            mcp_entries = eps.get("mcp.server_configs", [])  # type: ignore

        for entry_point in mcp_entries:
            try:
                logger.debug(
                    f"Loading server config from entry point: {entry_point.name}"
                )

                # Load the configuration
                config = entry_point.load()

                # Get source package name
                source_package = getattr(entry_point, "dist", None)
                source_name = (
                    source_package.name if source_package else entry_point.name
                )

                # Validate configuration
                validator = ExternalServerValidator()
                is_valid, validation_errors = validator.validate_server_config(
                    config, source_name
                )

                if is_valid:
                    # Check for duplicate names
                    if config.name in discovered:
                        existing_source = discovered[config.name][1]
                        logger.warning(
                            f"Duplicate server name '{config.name}' from {source_name} "
                            f"(already registered by {existing_source}). Skipping."
                        )
                        continue

                    discovered[config.name] = (config, source_name)
                    logger.info(
                        f"Discovered external server: {config.display_name} "
                        f"({config.name}) from {source_name}"
                    )
                else:
                    for error in validation_errors:
                        logger.warning(f"Invalid server config: {error}")
                        errors.extend(validation_errors)

            except Exception as e:
                error_msg = f"Failed to load server config from {entry_point.name}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

    except Exception as e:
        error_msg = f"Failed to discover external servers: {e}"
        logger.error(error_msg)
        errors.append(error_msg)

    return discovered


def register_external_servers(
    discovered_servers: Dict[str, Tuple[ServerConfig, str]],
) -> Tuple[int, List[str]]:
    """Register discovered external servers with the global registry.

    Args:
        discovered_servers: Dict from discover_external_servers()

    Returns:
        Tuple of (successfully_registered_count, list_of_errors)
    """
    registered_count = 0
    errors = []

    for server_name, (config, source_package) in discovered_servers.items():
        try:
            # Check if already registered (shouldn't happen, but be safe)
            if registry.is_registered(server_name):
                logger.warning(
                    f"Server '{server_name}' is already registered. "
                    f"Skipping external registration from {source_package}."
                )
                continue

            # Register with the global registry
            registry.register(config)
            registered_count += 1
            logger.debug(
                f"Registered external server: {config.display_name} from {source_package}"
            )

        except Exception as e:
            error_msg = (
                f"Failed to register server '{server_name}' from {source_package}: {e}"
            )
            logger.error(error_msg)
            errors.append(error_msg)

    return registered_count, errors


def initialize_external_servers(verbose: bool = False) -> Tuple[int, List[str]]:
    """Complete external server initialization process.

    Args:
        verbose: Whether to print detailed discovery information

    Returns:
        Tuple of (registered_count, list_of_errors)
    """
    if verbose:
        print("Discovering external MCP server configurations...")

    # Discover external servers
    discovered = discover_external_servers()

    if verbose and discovered:
        print(f"Found {len(discovered)} external server configuration(s):")
        for name, (config, source) in discovered.items():
            print(f"  • {config.display_name} ({name}) from {source}")
    elif verbose:
        print("No external server configurations found.")

    # Register discovered servers
    registered_count, errors = register_external_servers(discovered)

    if verbose and registered_count > 0:
        print(f"Successfully registered {registered_count} external server(s).")

    if verbose and errors:
        print("Errors during discovery:")
        for error in errors:
            print(f"  ⚠ {error}")

    return registered_count, errors
