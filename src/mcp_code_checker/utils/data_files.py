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

    IMPORTANT: For installed packages to work (methods 2 and 3), data files must be
    explicitly declared in pyproject.toml under [tool.setuptools.package-data]:

        [tool.setuptools.package-data]
        "*" = ["py.typed"]
        "your_package.resources" = ["script.py", "config.json", "templates/*"]

    Without this configuration, data files will only be found in development mode.

    Args:
        package_name: Name of the Python package (e.g., "mcp_code_checker.resources")
        relative_path: Path to the file relative to the package/development root
                      (e.g., "sleep_script.py")
        development_base_dir: Base directory for development environment.
                             If None, development lookup is skipped.

    Returns:
        Path to the data file

    Raises:
        FileNotFoundError: If the file cannot be found in any expected location.
                          For installed packages, this often means the file is not
                          declared in pyproject.toml package-data configuration.

    Example:
        >>> # Find sleep_script.py in development or installed environment
        >>> script_path = find_data_file(
        ...     "mcp_code_checker.resources",
        ...     "sleep_script.py",
        ...     development_base_dir=Path("/project/root")
        ... )

        # Requires this in pyproject.toml:
        # [tool.setuptools.package-data]
        # "mcp_code_checker.resources" = ["sleep_script.py"]
    """
    # Start with comprehensive logging of the search parameters
    structured_logger.info(
        "SEARCH STARTED: Looking for data file using 3 methods",
        package_name=package_name,
        relative_path=relative_path,
        development_base_dir=(
            str(development_base_dir) if development_base_dir else None
        ),
        methods="1=Development, 2=ImportLib, 3=Module __file__",
    )

    search_locations = []
    search_results = []  # Track results for each method

    # Option 1: Development environment
    method_1_result = "SKIPPED"
    method_1_path = None
    if development_base_dir is not None:
        structured_logger.info(
            "METHOD 1/3: Searching development environment",
            method="development",
            base_dir=str(development_base_dir),
        )

        # Try new structure: src/{package_name}/{relative_path}
        # Handle dotted package names (e.g., "mcp_code_checker.data")
        package_path = package_name.replace(".", "/")
        dev_file = development_base_dir / "src" / package_path / relative_path
        method_1_path = str(dev_file)
        search_locations.append(str(dev_file))

        structured_logger.info(
            "METHOD 1/3: Development path constructed",
            method="development",
            path=str(dev_file),
            exists=dev_file.exists(),
        )

        if dev_file.exists():
            method_1_result = "SUCCESS"
            structured_logger.info(
                "METHOD 1/3: SUCCESS - Found data file in development environment",
                method="development",
                path=str(dev_file),
                result=method_1_result,
            )
            search_results.append(
                {
                    "method": "1/3 Development",
                    "result": method_1_result,
                    "path": method_1_path,
                }
            )
            return dev_file
        else:
            method_1_result = "FAILED"
            structured_logger.info(
                "METHOD 1/3: FAILED - Development path not found",
                method="development",
                path=str(dev_file),
                result=method_1_result,
            )
    else:
        structured_logger.info(
            "METHOD 1/3: SKIPPED - No development base directory provided",
            method="development",
            result=method_1_result,
        )

    search_results.append(
        {"method": "1/3 Development", "result": method_1_result, "path": method_1_path}
    )

    # Option 2: Installed package - using importlib.util.find_spec
    method_2_result = "FAILED"
    method_2_path = None
    structured_logger.info(
        "METHOD 2/3: Searching installed package via importlib",
        method="importlib_spec",
    )
    try:
        structured_logger.info(
            "METHOD 2/3: Attempting to find spec for package",
            method="importlib_spec",
            package_name=package_name,
        )
        spec = importlib.util.find_spec(package_name)

        if spec:
            structured_logger.info(
                "METHOD 2/3: Package spec found",
                method="importlib_spec",
                origin=spec.origin,
                name=spec.name,
            )
            if spec.origin:
                package_dir = Path(spec.origin).parent
                installed_file = package_dir / relative_path
                method_2_path = str(installed_file)
                search_locations.append(str(installed_file))

                structured_logger.info(
                    "METHOD 2/3: Installed package path constructed",
                    method="importlib_spec",
                    package_dir=str(package_dir),
                    path=str(installed_file),
                    exists=installed_file.exists(),
                )

                if installed_file.exists():
                    method_2_result = "SUCCESS"
                    structured_logger.info(
                        "METHOD 2/3: SUCCESS - Found data file in installed package (via importlib)",
                        method="importlib_spec",
                        path=str(installed_file),
                        result=method_2_result,
                    )
                    search_results.append(
                        {
                            "method": "2/3 ImportLib",
                            "result": method_2_result,
                            "path": method_2_path,
                        }
                    )
                    return installed_file
                else:
                    method_2_result = "FAILED"
                    structured_logger.info(
                        "METHOD 2/3: FAILED - Installed package path not found",
                        method="importlib_spec",
                        path=str(installed_file),
                        result=method_2_result,
                    )
            else:
                method_2_result = "FAILED"
                structured_logger.info(
                    "METHOD 2/3: FAILED - Spec found but origin is None",
                    method="importlib_spec",
                    result=method_2_result,
                )
        else:
            method_2_result = "FAILED"
            structured_logger.info(
                "METHOD 2/3: FAILED - No spec found for package",
                method="importlib_spec",
                package_name=package_name,
                result=method_2_result,
            )
    except Exception as e:
        method_2_result = "ERROR"
        structured_logger.info(
            "METHOD 2/3: ERROR - Exception in importlib.util.find_spec",
            method="importlib_spec",
            error=str(e),
            package_name=package_name,
            result=method_2_result,
        )

    search_results.append(
        {"method": "2/3 ImportLib", "result": method_2_result, "path": method_2_path}
    )

    # Option 3: Alternative installed location - using __file__ attribute
    method_3_result = "FAILED"
    method_3_path = None
    structured_logger.info(
        "METHOD 3/3: Searching alternative installed location via __file__",
        method="module_file",
    )
    try:
        structured_logger.info(
            "METHOD 3/3: Attempting to import module",
            method="module_file",
            package_name=package_name,
        )
        package_module = importlib.import_module(package_name)

        structured_logger.info(
            "METHOD 3/3: Module imported successfully",
            method="module_file",
            module=str(package_module),
            has_file=hasattr(package_module, "__file__"),
        )

        if hasattr(package_module, "__file__") and package_module.__file__:
            structured_logger.info(
                "METHOD 3/3: Module __file__ found",
                method="module_file",
                module_file=package_module.__file__,
            )
            package_dir = Path(package_module.__file__).parent
            alt_file = package_dir / relative_path
            method_3_path = str(alt_file)
            search_locations.append(str(alt_file))

            structured_logger.info(
                "METHOD 3/3: Alternative package path constructed",
                method="module_file",
                package_dir=str(package_dir),
                path=str(alt_file),
                exists=alt_file.exists(),
            )

            if alt_file.exists():
                method_3_result = "SUCCESS"
                structured_logger.info(
                    "METHOD 3/3: SUCCESS - Found data file in installed package (via __file__)",
                    method="module_file",
                    path=str(alt_file),
                    result=method_3_result,
                )
                search_results.append(
                    {
                        "method": "3/3 Module __file__",
                        "result": method_3_result,
                        "path": method_3_path,
                    }
                )
                return alt_file
            else:
                method_3_result = "FAILED"
                structured_logger.info(
                    "METHOD 3/3: FAILED - Alternative package path not found",
                    method="module_file",
                    path=str(alt_file),
                    result=method_3_result,
                )
        else:
            method_3_result = "FAILED"
            structured_logger.info(
                "METHOD 3/3: FAILED - Module does not have __file__ attribute or it's None",
                method="module_file",
                result=method_3_result,
            )
    except Exception as e:
        method_3_result = "ERROR"
        structured_logger.info(
            "METHOD 3/3: ERROR - Exception in __file__ attribute method",
            method="module_file",
            error=str(e),
            package_name=package_name,
            result=method_3_result,
        )

    search_results.append(
        {
            "method": "3/3 Module __file__",
            "result": method_3_result,
            "path": method_3_path,
        }
    )

    # If we get here, the file wasn't found anywhere
    structured_logger.error(
        "SEARCH COMPLETE: Data file not found in any location",
        package_name=package_name,
        relative_path=relative_path,
        search_locations=search_locations,
        search_results=search_results,
        development_base_dir=(
            str(development_base_dir) if development_base_dir else None
        ),
    )

    # Log a clear summary of what was tried
    structured_logger.info(
        "SEARCH SUMMARY - All methods failed",
        search_results=search_results,
    )

    raise FileNotFoundError(
        f"Data file '{relative_path}' not found for package '{package_name}'. "
        f"Searched locations: {search_locations}. "
        f"Make sure the package is properly installed or you're running in development mode. "
        f"For installed packages, ensure the file is declared in pyproject.toml under "
        f"[tool.setuptools.package-data] with '{package_name}' = ['{relative_path}'] or ['{relative_path.split('/')[-1]}']."
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
