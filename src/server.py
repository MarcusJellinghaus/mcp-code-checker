"""MCP server implementation for code checking functionality.

This module provides the server implementation for the Code Checker service. The server
manages several code checking tools and handles the parameter flow between the command-line
interface, server configuration, and tool execution.

Parameter Flow Overview:
-----------------------

1. COMMAND-LINE ARGUMENTS (main.py)
   - Defined in main.py:parse_args()
   - Processed in main.py:main()
   - Used to initialize server and set default values for tools
   - Examples: --project-dir, --python-executable, --preset

2. SERVER INITIALIZATION PARAMETERS (server.py:CodeCheckerServer.__init__)
   - Basic parameters received directly from command-line arguments
   - Used to configure the server instance during creation
   - Examples: project_dir, python_executable, test_folder

3. SERVER INSTANCE ATTRIBUTES (set after initialization)
   - Additional configuration applied after server creation
   - Usually from preset configurations in main.py:get_preset_config()
   - Examples: server.verbosity, server.pylint_categories

4. TOOL DYNAMIC PARAMETERS
   - Parameters passed directly when calling tools
   - Override corresponding server attributes when provided
   - Examples: markers, verbosity, categories

Parameter Precedence:
-------------------
Dynamic Tool Parameters > Server Instance Attributes > Server Initialization Parameters > Command-line Defaults

This means that values provided directly to tools take precedence over server attributes,
which in turn take precedence over initialization parameters, which default to command-line defaults.

Example Parameter Flow:
---------------------
1. User runs: python -m src.main --preset=debug
2. main.py sets server.verbosity = 3 (from debug preset)
3. Later, the user calls run_pytest_check(verbosity=1)
4. The tool uses verbosity=1 (dynamic parameter) instead of server.verbosity=3

But if the user calls run_pytest_check() without a verbosity parameter,
the tool uses server.verbosity=3 as the default value.
"""

import logging
from pathlib import Path

# Type stub for mcp.server.fastmcp
from typing import Callable, Dict, List, Optional, Protocol, Set, TypeVar

T = TypeVar("T")


class ToolDecorator(Protocol):
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]: ...


class FastMCPProtocol(Protocol):
    def tool(self) -> ToolDecorator: ...
    def run(self) -> None: ...


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CodeCheckerServer:
    """
    MCP server for code checking functionality.

    The server provides tools for code checking using pylint and pytest,
    handling both static initialization parameters and dynamic parameters passed
    during tool invocation. Parameters can come from three sources:

    1. Command-line arguments: Set at startup, passed to server constructor
    2. Server instance attributes: Set at initialization or after
    3. Dynamic call parameters: Passed directly to the tools when invoked

    Parameters from more specific sources (dynamic call params) override those from
    more general sources (server attributes, then command-line/initialization params).
    """

    def __init__(
        self,
        project_dir: Path,
        python_executable: Optional[str] = None,
        venv_path: Optional[str] = None,
        test_folder: str = "tests",
        keep_temp_files: bool = False,
    ) -> None:
        """
        Initialize the server with the project directory and Python configuration.

        These parameters are set at server initialization (usually from command-line args
            processed by main.py) and stored as instance attributes. They remain constant
            throughout the server's lifecycle unless explicitly modified after initialization.

            Args:
            project_dir: Path to the project directory to check.
        Source: Command-line arg (--project-dir) with default of current directory.

            python_executable: Path to Python interpreter for running tests.
        Source: Command-line arg (--python-executable) or auto-detected.
        Default: sys.executable if not specified or detected.

            venv_path: Path to a virtual environment to activate for running tests.
        Source: Command-line arg (--venv-path) or auto-detected.
        Note: When specified, the Python executable from this venv takes precedence.

            test_folder: Path to the test folder (relative to project_dir).
        Source: Command-line arg (--test-folder).
        Default: 'tests'

            keep_temp_files: Whether to keep temporary files after test execution.
        Source: Command-line arg (--keep-temp-files) or preset config.
        Default: False
        Note: Useful for debugging when tests fail.
            """
        self.project_dir = project_dir
        self.python_executable = python_executable
        self.venv_path = venv_path
        self.test_folder = test_folder
        self.keep_temp_files = keep_temp_files

        # Additional configuration attributes that can be set after initialization.
        # These attributes are not part of the constructor but can be modified after
        # server creation, typically from preset configurations in main.py.
        # They provide default values that can be overridden by dynamic call parameters.

        # Default verbosity level for pytest (0-3)
        # Source: Preset configuration from --preset arg or explicitly set after initialization
        # Default: 2 (medium verbosity)
        # Can be overridden by: verbosity parameter in run_pytest_check() and run_all_checks()
        self.verbosity: int = 2

        # Pylint message categories to include in analysis
        # Source: Preset configuration from --preset arg or explicitly set after initialization
        # Default: None (include all categories)
        # Can be overridden by: categories parameter in run_all_checks()
        # Available values: 'convention', 'refactor', 'warning', 'error', 'fatal'
        self.pylint_categories: Optional[List[str]] = None
        # We cannot import the actual FastMCP for type checking
        from mcp.server.fastmcp import FastMCP

        self.mcp: FastMCPProtocol = FastMCP("Code Checker Service")
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all tools with the MCP server."""

        # Using type annotations directly on the decorated functions
        # to address the "Untyped decorator makes function untyped" issue
        @self.mcp.tool()
        async def run_pylint_check(disable_codes: Optional[List[str]] = None) -> str:
            """
            Run pylint on the project code and generate smart prompts for LLMs.

            This tool uses the following parameters:
            
            From server instance (set during initialization):
            - project_dir: Path to analyze (--project-dir)
            - python_executable: Python interpreter to use (--python-executable)
            
            Dynamic parameters (passed during tool invocation):
            - disable_codes: Pylint error codes to disable

            Args:
                disable_codes: Optional list of pylint error codes to disable during analysis.
                    Default: None (no codes disabled)
                    Dynamic parameter passed at invocation time.
            
            Common codes to disable include:
            - C0114: Missing module docstring
            - C0116: Missing function docstring
            - C0301: Line too long
            - W0611: Unused import
            - W1514: Using open without explicitly specifying an encoding

            Returns:
                A string containing either pylint results or a prompt for an LLM to interpret
            """
            try:
                logger.info(
                    f"Running pylint check on project directory: {self.project_dir}"
                )

                # Import the code_checker_pylint module to run pylint checks
                from src.code_checker_pylint import get_pylint_prompt

                # Generate a prompt for pylint issues
                pylint_prompt = get_pylint_prompt(
                    str(self.project_dir),
                    disable_codes=disable_codes,
                    python_executable=self.python_executable,
                )

                # Format the results as a string
                if pylint_prompt is None:
                    result = "Pylint check completed. No issues found that require attention."
                else:
                    result = (
                        f"Pylint found issues that need attention:\n\n{pylint_prompt}"
                    )

                return result
            except Exception as e:
                logger.error(f"Error running pylint check: {str(e)}")
                raise

        @self.mcp.tool()
        async def run_pytest_check(
            markers: Optional[List[str]] = None,
            verbosity: Optional[int] = None,
            extra_args: Optional[List[str]] = None,
            env_vars: Optional[Dict[str, str]] = None,
        ) -> str:
            """
            Run pytest on the project code and generate smart prompts for LLMs.

            This tool uses the following parameters:

                From server instance (set during initialization):
                - project_dir: Path to analyze (--project-dir)
                - test_folder: Test directory to run (--test-folder)
                - python_executable: Python interpreter to use (--python-executable)
                - venv_path: Virtual environment to activate (--venv-path)
            - keep_temp_files: Whether to keep test artifacts (--keep-temp-files)
                - verbosity: Default verbosity level (set via --preset)

                Dynamic parameters (passed during tool invocation and override server parameters):
                - markers: Pytest markers to filter tests 
                - verbosity: Override the server's verbosity setting
                - extra_args: Additional pytest arguments
                - env_vars: Environment variables for the subprocess

                Args:
                    markers: Optional list of pytest markers to filter tests.
                        Default: None (run all tests)
                        Examples: ['slow', 'integration']
                        Dynamic parameter passed at invocation time.

                    verbosity: Integer for pytest verbosity level (0-3).
                        Default: Uses server.verbosity (default 2)
                        Higher values provide more detailed output.
                        Dynamic parameter that overrides server.verbosity if provided.

                    extra_args: Optional list of additional pytest arguments.
                        Default: None (no extra arguments)
                        Examples: ['-xvs', '--no-header']
                        Dynamic parameter passed at invocation time.

                    env_vars: Optional dictionary of environment variables for the subprocess.
                        Default: None (use current environment)
                        Example: {'DEBUG': '1', 'PYTHONPATH': '/custom/path'}
                        Dynamic parameter passed at invocation time.

                Returns:
                    A string containing either pytest results or a prompt for an LLM to interpret
                """
            try:
                logger.info(
                    f"Running pytest check on project directory: {self.project_dir}"
                )

                # Use preset verbosity if available and not overridden
                actual_verbosity = (
                    verbosity if verbosity is not None else self.verbosity
                )
                # Ensure verbosity is an int
                if actual_verbosity is None:
                    actual_verbosity = 2  # Default to 2 if somehow still None

                # Import the code_checker_pytest module to run pytest checks and generate prompts
                from src.code_checker_pytest.reporting import (
                    create_prompt_for_failed_tests,
                )
                from src.code_checker_pytest.runners import check_code_with_pytest

                # Run pytest on the project directory
                test_results = check_code_with_pytest(
                    project_dir=str(self.project_dir),
                    test_folder=self.test_folder,
                    python_executable=self.python_executable,
                    markers=markers,
                    verbosity=actual_verbosity,
                    extra_args=extra_args,
                    env_vars=env_vars,
                    venv_path=self.venv_path,
                    keep_temp_files=self.keep_temp_files,
                )

                if not test_results["success"]:
                    result = f"Error running pytest: {test_results.get('error', 'Unknown error')}"
                else:
                    summary = test_results["summary"]

                    if (
                        summary.get("failed", 0) > 0 or summary.get("error", 0) > 0
                    ) and test_results.get("test_results"):
                        # Use create_prompt_for_failed_tests to generate a prompt for the failed tests
                        failed_tests_prompt = create_prompt_for_failed_tests(
                            test_results["test_results"]
                        )
                        result = f"Pytest found issues that need attention:\n\n{failed_tests_prompt}"
                    else:
                        result = (
                            "Pytest check completed. All tests passed successfully."
                        )

                return result
            except Exception as e:
                logger.error(f"Error running pytest check: {str(e)}")
                raise

        @self.mcp.tool()
        async def run_all_checks(
            markers: Optional[List[str]] = None,
            verbosity: Optional[int] = None,
            extra_args: Optional[List[str]] = None,
            env_vars: Optional[Dict[str, str]] = None,
            categories: Optional[Set[str]] = None,
        ) -> str:
            """
            Run all code checks (pylint and pytest) and generate combined results.

            This tool runs both pylint and pytest checks with a single invocation.
                It combines the functionality of run_pylint_check and run_pytest_check.

                This tool uses the following parameters:

                From server instance (set during initialization):
                    - project_dir: Path to analyze (--project-dir)
                    - test_folder: Test directory to run (--test-folder)
                    - python_executable: Python interpreter to use (--python-executable)
            - venv_path: Virtual environment to activate (--venv-path)
                - keep_temp_files: Whether to keep test artifacts (--keep-temp-files)
            - verbosity: Default verbosity level (set via --preset)
            - pylint_categories: Default pylint categories to include (set via --preset)

            Dynamic parameters (passed during tool invocation and override server parameters):
            - markers: Pytest markers to filter tests
            - verbosity: Override the server's verbosity setting
            - extra_args: Additional pytest arguments
            - env_vars: Environment variables for the subprocess
            - categories: Override default pylint message categories

            Args:
                markers: Optional list of pytest markers to filter tests.
                    Default: None (run all tests)
                    Examples: ['slow', 'integration']
                    Dynamic parameter passed at invocation time.

                verbosity: Integer for pytest verbosity level (0-3).
                    Default: Uses server.verbosity (default 2)
                    Higher values provide more detailed output.
                    Dynamic parameter that overrides server.verbosity if provided.

                extra_args: Optional list of additional pytest arguments.
                    Default: None (no extra arguments)
                    Examples: ['-xvs', '--no-header']
                    Dynamic parameter passed at invocation time.

                env_vars: Optional dictionary of environment variables for the subprocess.
                    Default: None (use current environment)
                    Example: {'DEBUG': '1', 'PYTHONPATH': '/custom/path'}
                    Dynamic parameter passed at invocation time.

                categories: Optional set of pylint message categories to include.
                    Default: Uses server.pylint_categories if set, otherwise None (all categories)
                    Available values: 'convention', 'refactor', 'warning', 'error', 'fatal'
                    Dynamic parameter that overrides server.pylint_categories if provided.

            Returns:
                A string containing results from all checks and/or LLM prompts
            """
            try:
                logger.info(
                    f"Running all code checks on project directory: {self.project_dir}"
                )

                # Use preset verbosity if available and not overridden
                actual_verbosity = (
                    verbosity if verbosity is not None else self.verbosity
                )
                # Ensure verbosity is an int
                if actual_verbosity is None:
                    actual_verbosity = 2  # Default to 2 if somehow still None

                # Run pylint check to generate prompt
                from src.code_checker_pylint import PylintMessageType, get_pylint_prompt

                # Use preset pylint categories if available and not overridden
                actual_categories = categories
                if actual_categories is None and self.pylint_categories:
                    actual_categories = set(self.pylint_categories)

                # Convert string categories to PylintMessageType enum values if provided
                enum_categories = set()
                if actual_categories:
                    for category in actual_categories:
                        try:
                            enum_categories.add(
                                PylintMessageType(category.lower())
                            )
                        except ValueError:
                            logger.warning(f"Unknown pylint category: {category}")

                # Run pylint with categories
                pylint_prompt = get_pylint_prompt(
                    str(self.project_dir),
                    categories=(
                        enum_categories if enum_categories else None
                    ),
                    python_executable=self.python_executable,
                )

                # Run pytest check
                from src.code_checker_pytest.reporting import (
                    create_prompt_for_failed_tests,
                )
                from src.code_checker_pytest.runners import check_code_with_pytest

                test_results = check_code_with_pytest(
                    project_dir=str(self.project_dir),
                    test_folder=self.test_folder,
                    python_executable=self.python_executable,
                    markers=markers,
                    verbosity=actual_verbosity,
                    extra_args=extra_args,
                    env_vars=env_vars,
                    venv_path=self.venv_path,
                    keep_temp_files=self.keep_temp_files,
                )

                # Generate prompt for failed tests if any
                failed_tests_prompt = None
                if test_results.get("success") and test_results.get("test_results"):
                    if (
                        test_results["summary"].get("failed", 0) > 0
                        or test_results["summary"].get("error", 0) > 0
                    ):
                        failed_tests_prompt = create_prompt_for_failed_tests(
                            test_results["test_results"]
                        )

                # Combine results
                result = "All code checks completed:\n\n"

                # Add pylint results
                if pylint_prompt is None:
                    result += "1. Pylint: No issues found that require attention.\n"
                else:
                    result += "1. Pylint found issues that need attention.\n"
                    result += "   " + pylint_prompt.replace("\n", "\n   ") + "\n"

                # Add pytest results
                if not test_results.get("success"):
                    result += f"2. Pytest check error: {test_results.get('error', 'Unknown error')}\n"
                elif failed_tests_prompt is None:
                    passed = test_results["summary"].get("passed", 0)
                    result += f"2. Pytest: All {passed} tests passed successfully.\n"
                else:
                    result += "2. Pytest found issues that need attention.\n"
                    result += "   " + failed_tests_prompt.replace("\n", "\n   ")

                return result
            except Exception as e:
                logger.error(f"Error running all code checks: {str(e)}")
                raise

    def run(self) -> None:
        """Run the MCP server."""
        self.mcp.run()


def create_server(
    project_dir: Path,
    python_executable: Optional[str] = None,
    venv_path: Optional[str] = None,
    test_folder: str = "tests",
    keep_temp_files: bool = False,
) -> CodeCheckerServer:
    """
    Create a new CodeCheckerServer instance with the specified initialization parameters.

    This function creates a server instance that will handle code checking tools.
        The parameters provided here become server instance attributes and are available to
    all tools. Additional configuration can be applied after creation by setting
        server attributes directly (e.g., server.verbosity = 3).

    Parameter Flow:
    1. Command-line arguments in main.py → Processed and passed to this function
    2. This function creates a server with those parameters as attributes
        3. Additional configuration (like presets) applied after server creation
    4. Tools use server attributes as default values when executed
        5. Dynamic parameters passed directly to tools override server attributes

            Args:
        project_dir: Path to the project directory to check.
        Source: Command-line arg (--project-dir) with default of current directory.
            Used by: All tools (run_pylint_check, run_pytest_check, run_all_checks).

        python_executable: Path to Python interpreter for running tests.
        Source: Command-line arg (--python-executable) or auto-detected.
            Default: sys.executable if not specified or detected.
            Used by: All tools for subprocess execution.
            Note: Overridden by the Python interpreter in venv_path if specified.

            venv_path: Path to a virtual environment to activate for running tests.
            Source: Command-line arg (--venv-path) or auto-detected.
            Default: None (use python_executable directly).
            Used by: run_pytest_check and run_all_checks.
    Note: When specified, the Python executable from this venv takes precedence
        over python_executable.

        test_folder: Path to the test folder (relative to project_dir).
            Source: Command-line arg (--test-folder).
            Default: 'tests'
            Used by: run_pytest_check and run_all_checks.
            Note: This is a fixed attribute that cannot be overridden by dynamic parameters.

        keep_temp_files: Whether to keep temporary files after test execution.
            Source: Command-line arg (--keep-temp-files) or preset config.
            Default: False
            Used by: run_pytest_check and run_all_checks.
            Note: Useful for debugging when tests fail.
                  This is a fixed attribute that cannot be overridden by dynamic parameters.

    Returns:
        A new CodeCheckerServer instance configured with the specified parameters
    """
    return CodeCheckerServer(
        project_dir,
        python_executable=python_executable,
        venv_path=venv_path,
        test_folder=test_folder,
        keep_temp_files=keep_temp_files,
    )
