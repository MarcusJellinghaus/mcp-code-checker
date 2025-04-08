#!/usr/bin/env python
"""
Setup script for configuring MCP Code Checker for Cline integration.

This script automates the process of setting up the MCP Code Checker
to work with Cline by:
1. Detecting the current Python environment
2. Finding the appropriate Cline MCP settings location
3. Creating or updating the Cline MCP settings file with the Code Checker configuration
"""

import argparse
import json
import logging
import os
import platform
import sys
from pathlib import Path
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_PRESET = "standard"
CLINE_MCP_SETTINGS_FILENAME = "cline_mcp_settings.json"


def get_cline_settings_path() -> Path:
    """
    Get the path to the Cline MCP settings file based on the operating system.
    
    Returns:
        Path to the Cline MCP settings directory
    """
    system = platform.system()
    
    if system == "Windows":
        # Windows: %APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise ValueError("APPDATA environment variable not found")
        return Path(appdata) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings"
    
    elif system == "Darwin":  # macOS
        # macOS: ~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings
        return Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings"
    
    elif system == "Linux":
        # Linux: ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings
        return Path.home() / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings"
    
    else:
        raise ValueError(f"Unsupported operating system: {system}")


def get_python_executable() -> str:
    """
    Get the path to the current Python executable.
    
    Returns:
        Path to the Python executable as a string
    """
    return sys.executable


def get_mcp_code_checker_path() -> Path:
    """
    Get the path to the MCP Code Checker installation.
    
    Returns:
        Path to the MCP Code Checker directory
    """
    # Get the directory of the current script
    return Path(__file__).resolve().parent


def create_or_update_mcp_settings(
    settings_dir: Path,
    mcp_code_checker_path: Path,
    project_dir: Path,
    preset: str,
    server_name: str = "code_checker",
) -> Path:
    """
    Create or update the Cline MCP settings file with the Code Checker configuration.
    
    Args:
        settings_dir: Path to the Cline MCP settings directory
        mcp_code_checker_path: Path to the MCP Code Checker installation
        project_dir: Path to the project directory to check
        preset: Configuration preset to use
        server_name: Name to use for the MCP server in the configuration
        
    Returns:
        Path to the created or updated settings file
    """
    # Create settings directory if it doesn't exist
    settings_dir.mkdir(parents=True, exist_ok=True)
    
    # Path to the settings file
    settings_file = settings_dir / CLINE_MCP_SETTINGS_FILENAME
    
    # Load existing settings if the file exists
    if settings_file.exists():
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings: Dict[str, Dict[str, Dict[str, object]]] = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse existing settings file: {settings_file}")
            settings = {}
    else:
        settings = {}
    
    # Ensure mcpServers key exists
    if "mcpServers" not in settings:
        settings["mcpServers"] = {}
    
    # Get the Python executable path
    python_executable = get_python_executable()
    
    # Create the MCP server configuration
    settings["mcpServers"][server_name] = {
        "command": python_executable,
        "args": [
            str(mcp_code_checker_path / "src" / "main.py"),
            "--project-dir",
            str(project_dir),
            "--preset",
            preset
        ],
        "env": {
            "PYTHONPATH": str(mcp_code_checker_path)
        },
        "disabled": False,
        "autoApprove": []
    }
    
    # Write the updated settings to the file
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
    
    logger.info(f"Updated Cline MCP settings file: {settings_file}")
    return settings_file


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Setup MCP Code Checker for Cline integration"
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default=os.getcwd(),
        help="Path to the project directory to check (defaults to current working directory)",
    )
    parser.add_argument(
        "--preset",
        type=str,
        choices=["strict", "standard", "minimal", "debug"],
        default=DEFAULT_PRESET,
        help=f"Configuration preset to use (default: {DEFAULT_PRESET})",
    )
    parser.add_argument(
        "--server-name",
        type=str,
        default="code_checker",
        help="Name to use for the MCP server in the configuration (default: code_checker)",
    )
    return parser.parse_args()


def main() -> None:
    """
    Main entry point for the setup script.
    """
    args = parse_args()
    
    try:
        # Get the path to the Cline MCP settings directory
        settings_dir = get_cline_settings_path()
        
        # Get the path to the MCP Code Checker installation
        mcp_code_checker_path = get_mcp_code_checker_path()
        
        # Validate project directory
        project_dir = Path(args.project_dir)
        if not project_dir.exists() or not project_dir.is_dir():
            logger.error(
                f"Project directory does not exist or is not a directory: {project_dir}"
            )
            sys.exit(1)
        
        # Create or update the Cline MCP settings file
        settings_file = create_or_update_mcp_settings(
            settings_dir,
            mcp_code_checker_path,
            project_dir,
            args.preset,
            args.server_name,
        )
        
        logger.info("MCP Code Checker has been configured for Cline integration")
        logger.info(f"Project directory: {project_dir}")
        logger.info(f"Configuration preset: {args.preset}")
        logger.info(f"Server name: {args.server_name}")
        logger.info(f"Settings file: {settings_file}")
        logger.info("Please restart VS Code for the changes to take effect")
        
    except Exception as e:
        logger.error(f"Error setting up MCP Code Checker for Cline: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
