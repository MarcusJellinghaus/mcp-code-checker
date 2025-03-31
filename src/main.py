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
    parser.add_argument(
        "--python-executable",
        type=str,
        help="Path to Python interpreter to use for running tests. If not specified, defaults to the current Python interpreter (sys.executable)",
    )
    parser.add_argument(
        "--venv-path",
        type=str,
        help="Path to virtual environment to activate for running tests. When specified, the Python executable from this venv will be used instead of python-executable",
    )
    parser.add_argument(
        "--test-folder",
        type=str,
        default="tests",
        help="Path to the test folder (relative to project_dir). Defaults to 'tests'",
    )
    parser.add_argument(
        "--keep-temp-files",
        action="store_true",
        help="Keep temporary files after test execution. Useful for debugging when tests fail",
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
    server = create_server(
        project_dir,
        python_executable=args.python_executable,
        venv_path=args.venv_path,
        test_folder=args.test_folder,
        keep_temp_files=args.keep_temp_files,
    )
    server.run()


if __name__ == "__main__":
    main()
