"""
Utilities for finding data files in both development and installed environments.

This module provides functions to locate data files that are included with the package
but kept outside the main package structure (e.g., scripts, configuration files).
"""

import importlib.util
import logging
from pathlib import Path
from typing import List, Optional

import structlog

logger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)


def find_data_file(
    package_name: str,
    relative_path: str,
    development_base_dir: Optional[Path] = None,
) -> Path:
    """
    Find a data file in both development and installed environments.
    
    This function searches for data files using multiple strategies:
    1. Development environment: Look relative to development_base_dir
    2. Installed package: Look in the package installation directory
    3. Alternative package location: Using package __file__ attribute
    
    Args:
        package_name: Name of the Python package (e.g., "mcp_code_checker")
        relative_path: Path to the file relative to the package/development root
                      (e.g., "tools/sleep_script.py")
        development_base_dir: Base directory for development environment.
                             If None, development lookup is skipped.
    
    Returns:
        Path to the data file
        
    Raises:
        FileNotFoundError: If the file cannot be found in any expected location
        
    Example:
        >>> # Find sleep_script.py in development or installed environment
        >>> script_path = find_data_file(
        ...     "mcp_code_checker",
        ...     "tools/sleep_script.py",
        ...     development_base_dir=Path("/project/root")
        ... )
    """
    # Start with comprehensive logging of the search parameters
    structured_logger.info(
        "Starting data file search",
        package_name=package_name,
        relative_path=relative_path,
        development_base_dir=str(development_base_dir) if development_base_dir else None,
    )
    
    search_locations = []
    
    # Option 1: Development environment
    if development_base_dir is not None:
        structured_logger.info(
            "Searching development environment",
            method="development",
            base_dir=str(development_base_dir),
        )
        
        # Try new structure: src/{package_name}/{relative_path}
        dev_file = development_base_dir / "src" / package_name / relative_path
        search_locations.append(str(dev_file))
        
        structured_logger.info(
            "Development path constructed",
            method="development",
            path=str(dev_file),
            exists=dev_file.exists(),
        )
        
        if dev_file.exists():
            structured_logger.info(
                "Found data file in development environment (src structure)",
                method="development",
                path=str(dev_file),
                relative_path=relative_path,
            )
            return dev_file
        else:
            structured_logger.info(
                "Development path not found",
                method="development",
                path=str(dev_file),
            )
    else:
        structured_logger.info(
            "Skipping development search - no base directory provided",
            method="development",
        )
    
    # Option 2: Installed package - using importlib.util.find_spec
    structured_logger.info(
        "Searching installed package via importlib",
        method="importlib_spec",
    )
    try:
        structured_logger.debug(
            "Attempting to find spec for package",
            method="importlib_spec",
            package_name=package_name,
        )
        spec = importlib.util.find_spec(package_name)
        
        if spec:
            structured_logger.info(
                "Package spec found",
                method="importlib_spec",
                origin=spec.origin,
                name=spec.name,
            )
            if spec.origin:
                package_dir = Path(spec.origin).parent
                installed_file = package_dir / relative_path
                search_locations.append(str(installed_file))
                
                structured_logger.info(
                    "Installed package path constructed",
                    method="importlib_spec",
                    package_dir=str(package_dir),
                    path=str(installed_file),
                    exists=installed_file.exists(),
                )
                
                if installed_file.exists():
                    structured_logger.info(
                        "Found data file in installed package (via importlib)",
                        method="importlib_spec",
                        path=str(installed_file),
                        relative_path=relative_path,
                    )
                    return installed_file
                else:
                    structured_logger.info(
                        "Installed package path not found",
                        method="importlib_spec",
                        path=str(installed_file),
                    )
            else:
                structured_logger.info(
                    "Spec found but origin is None - cannot determine package location",
                    method="importlib_spec",
                )
        else:
            structured_logger.info(
                "No spec found for package",
                method="importlib_spec",
                package_name=package_name,
            )
    except Exception as e:
        structured_logger.debug(
            "Error finding data file via importlib.util.find_spec",
            method="importlib_spec",
            error=str(e),
            package_name=package_name,
        )
    
    # Option 3: Alternative installed location - using __file__ attribute
    structured_logger.info(
        "Searching alternative installed location via __file__",
        method="module_file",
    )
    try:
        structured_logger.debug(
            "Attempting to import module",
            method="module_file",
            package_name=package_name,
        )
        package_module = importlib.import_module(package_name)
        
        structured_logger.debug(
            "Module imported successfully",
            method="module_file",
            module=str(package_module),
            has_file=hasattr(package_module, "__file__"),
        )
        
        if hasattr(package_module, "__file__") and package_module.__file__:
            structured_logger.info(
                "Module __file__ found",
                method="module_file",
                module_file=package_module.__file__,
            )
            package_dir = Path(package_module.__file__).parent
            alt_file = package_dir / relative_path
            search_locations.append(str(alt_file))
            
            structured_logger.info(
                "Alternative package path constructed",
                method="module_file",
                package_dir=str(package_dir),
                path=str(alt_file),
                exists=alt_file.exists(),
            )
            
            if alt_file.exists():
                structured_logger.info(
                    "Found data file in installed package (via __file__)",
                    method="module_file",
                    path=str(alt_file),
                    relative_path=relative_path,
                )
                return alt_file
            else:
                structured_logger.info(
                    "Alternative package path not found",
                    method="module_file",
                    path=str(alt_file),
                )
        else:
            structured_logger.info(
                "Module does not have __file__ attribute or it's None",
                method="module_file",
            )
    except Exception as e:
        structured_logger.debug(
            "Error finding data file via __file__ attribute",
            method="module_file",
            error=str(e),
            package_name=package_name,
        )
    
    # If we get here, the file wasn't found anywhere
    structured_logger.error(
        "Data file not found in any location",
        package_name=package_name,
        relative_path=relative_path,
        search_locations=search_locations,
        development_base_dir=str(development_base_dir) if development_base_dir else None,
    )
    
    raise FileNotFoundError(
        f"Data file '{relative_path}' not found for package '{package_name}'. "
        f"Searched locations: {search_locations}. "
        f"Make sure the package is properly installed or you're running in development mode."
    )


def find_package_data_files(
    package_name: str,
    relative_paths: List[str],
    development_base_dir: Optional[Path] = None,
) -> List[Path]:
    """
    Find multiple data files for a package.
    
    Args:
        package_name: Name of the Python package
        relative_paths: List of relative paths to find
        development_base_dir: Base directory for development environment
    
    Returns:
        List of Path objects for found files
        
    Raises:
        FileNotFoundError: If any file cannot be found
        
    Example:
        >>> paths = find_package_data_files(
        ...     "mcp_code_checker",
        ...     ["tools/sleep_script.py", "config/defaults.json"],
        ...     development_base_dir=Path("/project/root")
        ... )
    """
    found_files = []
    
    for relative_path in relative_paths:
        file_path = find_data_file(
            package_name=package_name,
            relative_path=relative_path,
            development_base_dir=development_base_dir,
        )
        found_files.append(file_path)
    
    return found_files


def get_package_directory(package_name: str) -> Path:
    """
    Get the directory where a package is installed.
    
    Args:
        package_name: Name of the Python package
        
    Returns:
        Path to the package directory
        
    Raises:
        ImportError: If the package cannot be found
        
    Example:
        >>> package_dir = get_package_directory("mcp_code_checker")
        >>> print(package_dir)  # /path/to/site-packages/mcp_code_checker
    """
    try:
        # First try using importlib.util.find_spec
        spec = importlib.util.find_spec(package_name)
        if spec and spec.origin:
            return Path(spec.origin).parent
    except Exception as e:
        structured_logger.debug(
            "Error finding package directory via importlib.util.find_spec",
            error=str(e),
            package_name=package_name,
        )
    
    try:
        # Fallback to importing the module and using __file__
        package_module = importlib.import_module(package_name)
        if hasattr(package_module, "__file__") and package_module.__file__:
            return Path(package_module.__file__).parent
    except Exception as e:
        structured_logger.debug(
            "Error finding package directory via __file__",
            error=str(e),
            package_name=package_name,
        )
    
    raise ImportError(f"Cannot find package directory for '{package_name}'")
