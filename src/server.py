"""MCP server implementation for code checking functionality."""

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
    """MCP server for code checking functionality."""

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

        Args:
            project_dir: Path to the project directory to check
            python_executable: Optional path to Python interpreter to use
            venv_path: Optional path to a virtual environment to activate
            test_folder: Path to the test folder (relative to project_dir)
            keep_temp_files: Whether to keep temporary files after execution
        """
        self.project_dir = project_dir
        self.python_executable = python_executable
        self.venv_path = venv_path
        self.test_folder = test_folder
        self.keep_temp_files = keep_temp_files
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

            Args:
                disable_codes: Optional list of pylint error codes to disable during analysis

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
            verbosity: int = 2,
            extra_args: Optional[List[str]] = None,
            env_vars: Optional[Dict[str, str]] = None,
            continue_on_collection_errors: bool = True,
        ) -> str:
            """
            Run pytest on the project code and generate smart prompts for LLMs.

            Args:
                markers: Optional list of pytest markers to filter tests
                verbosity: Integer for pytest verbosity level (0-3), default 2
                extra_args: Optional list of additional pytest arguments
                env_vars: Optional dictionary of environment variables for the subprocess
                continue_on_collection_errors: Whether to continue on collection errors, default True

            Returns:
                A string containing either pytest results or a prompt for an LLM to interpret
            """
            try:
                logger.info(
                    f"Running pytest check on project directory: {self.project_dir}"
                )

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
                    verbosity=verbosity,
                    extra_args=extra_args,
                    env_vars=env_vars,
                    venv_path=self.venv_path,
                    keep_temp_files=self.keep_temp_files,
                    continue_on_collection_errors=continue_on_collection_errors,
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
            verbosity: int = 1,
            extra_args: Optional[List[str]] = None,
            env_vars: Optional[Dict[str, str]] = None,
            continue_on_collection_errors: bool = True,
            disable_codes: Optional[List[str]] = None,
            categories: Optional[Set[str]] = None,
        ) -> str:
            """
            Run all code checks (pylint and pytest) and generate combined results.

            Args:
                markers: Optional list of pytest markers to filter tests
                verbosity: Integer for pytest verbosity level (0-3), default 1
                extra_args: Optional list of additional pytest arguments
                env_vars: Optional dictionary of environment variables for the subprocess
                continue_on_collection_errors: Whether to continue on collection errors, default True
                disable_codes: Optional list of pylint error codes to disable during analysis
                categories: Optional set of pylint message categories to include (error, warning, etc.)

            Returns:
                A string containing results from all checks and/or LLM prompts
            """
            try:
                logger.info(
                    f"Running all code checks on project directory: {self.project_dir}"
                )

                # Run pylint check to generate prompt
                from src.code_checker_pylint import PylintMessageType, get_pylint_prompt

                # Use provided categories if available, otherwise use default (ERROR, FATAL)
                if categories is None:
                    pylint_categories = {
                        PylintMessageType.ERROR,
                        PylintMessageType.FATAL,
                    }
                else:
                    # Convert string categories to PylintMessageType enum values
                    pylint_categories = set()
                    for category in categories:
                        try:
                            pylint_categories.add(PylintMessageType(category.lower()))
                        except ValueError:
                            logger.warning(f"Unknown pylint category: {category}")

                pylint_prompt = get_pylint_prompt(
                    str(self.project_dir),
                    categories=pylint_categories,
                    disable_codes=disable_codes,
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
                    verbosity=verbosity,
                    extra_args=extra_args,
                    env_vars=env_vars,
                    venv_path=self.venv_path,
                    keep_temp_files=self.keep_temp_files,
                    continue_on_collection_errors=continue_on_collection_errors,
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
    Create a new CodeCheckerServer instance.

    Args:
        project_dir: Path to the project directory to check
        python_executable: Optional path to Python interpreter to use
        venv_path: Optional path to a virtual environment to activate
        test_folder: Path to the test folder (relative to project_dir)
        keep_temp_files: Whether to keep temporary files after execution

    Returns:
        A new CodeCheckerServer instance
    """
    return CodeCheckerServer(
        project_dir,
        python_executable=python_executable,
        venv_path=venv_path,
        test_folder=test_folder,
        keep_temp_files=keep_temp_files,
    )
