"""MCP Configuration Helper - Main package initialization."""

import logging
from typing import List, Tuple

from .discovery import initialize_external_servers
from .servers import registry

# Set up logging
logger = logging.getLogger(__name__)


def initialize_all_servers(verbose: bool = False) -> Tuple[int, List[str]]:
    """Initialize built-in and external servers.

    Args:
        verbose: Whether to print detailed initialization information

    Returns:
        Tuple of (total_server_count, list_of_errors)
    """

    # Built-in servers are already registered in servers.py
    builtin_count = len(registry.get_all_configs())

    if verbose:
        print(f"Loaded {builtin_count} built-in server configuration(s).")

    # Initialize external servers
    external_count, errors = initialize_external_servers(verbose)

    total_count = builtin_count + external_count

    if verbose:
        print(f"Total: {total_count} server configuration(s) available.")

    return total_count, errors


# Auto-initialize on import (with error handling)
try:
    initialize_all_servers(verbose=False)
except Exception as e:
    logger.warning(f"Failed to initialize external servers: {e}")
    # Continue with built-in servers only
