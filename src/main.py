"""Main entry point for the Code Checker MCP server."""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, cast

# Check if the script is being run directly and if PYTHONPATH is set correctly
# This check must run before any 'src' imports
if __name__ == "__main__" and "src" in __file__:
    # Get the absolute path of the project root directory
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Check if the project root is in sys.path
    if str(project_root) not in sys.path:
        # Determine the OS-specific command to set PYTHONPATH
        if os.name == "nt":  # Windows
            set_cmd = f"set PYTHONPATH={project_root}"
            run_cmd = f"{set_cmd} && python src\\main.py"
        else:  # Unix-like systems
            set_cmd = f"export PYTHONPATH={project_root}"
            run_cmd = f"{set_cmd} && python src/main.py"

        print(
            f"""
ERROR: ModuleNotFoundError: No module named 'src'

This error occurs because the project root directory is not in your Python path.
To fix this, you have two options:

1. Set the PYTHONPATH environment variable:
   {set_cmd}
   python src/main.py

2. Run the script as a module from the project root:
   python -m src.main

For a permanent solution, add the PYTHONPATH to your environment variables.
"""
        )
        sys.exit(1)

# Now we can safely import from src
from src.server import create_server  # isort: skip

logger = logging.getLogger(__name__)


def detect_python_environment(project_dir: Path) -> Tuple[str, Optional[str]]:
    """
    Detect Python environment in the project directory.

    This function looks for virtual environments in the project directory
    and returns the path to the Python executable and virtual environment.

    Args:
        project_dir: Path to the project directory

    Returns:
        Tuple of (python_executable, venv_path)
    """
    python_executable = sys.executable
    venv_path = None

    # Common virtual environment directory names
    venv_dirs = [".venv", "venv", "env", ".env", "virtualenv"]

    # Check for virtual environments in the project directory
    for venv_dir in venv_dirs:
        venv_dir_path = project_dir / venv_dir
        if venv_dir_path.exists() and venv_dir_path.is_dir():
            # Determine the Python executable path based on the OS
            if os.name == "nt":  # Windows
                venv_python = venv_dir_path / "Scripts" / "python.exe"
            else:  # Unix-like systems
                venv_python = venv_dir_path / "bin" / "python"

            if venv_python.exists():
                logger.info(f"Found virtual environment at {venv_dir_path}")
                return str(venv_python), str(venv_dir_path)

    # If no virtual environment is found, return the current Python executable
    return python_executable, venv_path


def get_preset_config(preset: str) -> Dict[str, object]:
    """
    Get configuration values for a preset.

    Args:
        preset: The preset name ('strict', 'standard', 'minimal')

    Returns:
        Dictionary with configuration values for the preset
    """
    presets = {
        "strict": {
            "pylint_categories": [
                "convention",
                "refactor",
                "warning",
                "error",
                "fatal",
            ],
            "keep_temp_files": False,
            "verbosity": 2,
        },
        "standard": {
            "pylint_categories": ["warning", "error", "fatal"],
            "keep_temp_files": False,
            "verbosity": 2,
        },
        "minimal": {
            "pylint_categories": ["error", "fatal"],
            "keep_temp_files": False,
            "verbosity": 1,
        },
        "debug": {
            "pylint_categories": ["error", "fatal"],
            "keep_temp_files": True,
            "verbosity": 3,
        },
    }

    if preset not in presets:
        logger.warning(f"Unknown preset '{preset}', using 'standard' preset")
        preset = "standard"

    return presets[preset]


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
        default=os.getcwd(),
        help="Base directory for code checking operations (defaults to current working directory)",
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
    parser.add_argument(
        "--preset",
        type=str,
        choices=["strict", "standard", "minimal", "debug"],
        help="Use a predefined configuration preset. Available presets: strict (all checks), standard (warnings and errors), minimal (errors only), debug (errors with verbose output and temp files)",
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

    # Apply preset configuration if specified
    keep_temp_files = args.keep_temp_files
    verbosity = 2  # Default verbosity
    pylint_categories = None

    if args.preset:
        preset_config = get_preset_config(args.preset)
        logger.info(f"Using '{args.preset}' preset configuration")

        # Only override keep_temp_files if it wasn't explicitly set on the command line
        if not args.keep_temp_files:
            keep_temp_files = cast(bool, preset_config["keep_temp_files"])

        verbosity = cast(int, preset_config["verbosity"])
        pylint_categories = cast(List[str], preset_config["pylint_categories"])

    # Auto-detect Python environment if not specified
    python_executable = args.python_executable
    venv_path = args.venv_path

    if python_executable is None or venv_path is None:
        detected_executable, detected_venv = detect_python_environment(project_dir)

        if python_executable is None:
            python_executable = detected_executable
            logger.info(f"Using auto-detected Python executable: {python_executable}")

        if venv_path is None and detected_venv is not None:
            venv_path = detected_venv
            logger.info(f"Using auto-detected virtual environment: {venv_path}")

    # Create and run the server
    server = create_server(
        project_dir,
        python_executable=python_executable,
        venv_path=venv_path,
        test_folder=args.test_folder,
        keep_temp_files=keep_temp_files,
    )

    # Store preset configuration in server attributes for later use by tools
    if args.preset:
        # These attributes will be accessible to the tools when they're called
        server.verbosity = verbosity
        server.pylint_categories = pylint_categories
        logger.info(f"Applied '{args.preset}' preset configuration to server")

    server.run()


if __name__ == "__main__":
    main()
