"""Main entry point for the Code Checker MCP server."""

import argparse
import logging
import sys
from pathlib import Path

from src.server import create_server

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="MCP Code Checker Server")
    parser.add_argument(
        "--project-dir",
        type=str,
        required=True,
        help="Base directory for code checking operations (required)",
    )
    return parser.parse_args()


def main() -> None:
    """
    Main entry point for the MCP server.
    """
    args = parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Validate project directory
    project_dir = Path(args.project_dir)
    if not project_dir.exists() or not project_dir.is_dir():
        logger.error(
            f"Project directory does not exist or is not a directory: {project_dir}"
        )
        sys.exit(1)

    logger.info(
        f"Starting MCP Code Checker server with project directory: {project_dir}"
    )

    # Create and run the server
    server = create_server(project_dir)
    server.run()


if __name__ == "__main__":
    main()
