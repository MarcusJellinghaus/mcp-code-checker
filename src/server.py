"""MCP server implementation for code checking functionality."""

import logging
from pathlib import Path

# Type stub for mcp.server.fastmcp
from typing import Callable, Dict, List, Optional, Protocol, TypeVar

import structlog

from src.log_utils import log_function_call

T = TypeVar("T")


class ToolDecorator(Protocol):
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]: ...


class FastMCPProtocol(Protocol):
    def tool(self) -> ToolDecorator: ...
    def run(self) -> None: ...


# Initialize loggers
logger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)


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
            python_executable: Optional path to Python interpreter to use for running tests. If None, defaults to sys.executable.
            venv_path: Optional path to a virtual environment to activate for running tests. When specified, the Python executable from this venv will be used instead of python_executable.
            test_folder: Path to the test folder (relative to project_dir). Defaults to 'tests'.
            keep_temp_files: Whether to keep temporary files after test execution. Useful for debugging when tests fail.
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
        @log_function_call
        def run_pylint_check(
            categories: Optional[List[str]] = None,
            disable_codes: Optional[List[str]] = None,
            target_directories: Optional[List[str]] = None,
        ) -> str:
            """
            Run pylint on the project code and generate smart prompts for LLMs.

            Args:
                categories: Optional list of pylint message categories to include.
                    Available categories: 'convention', 'refactor', 'warning', 'error', 'fatal'
                    Defaults to ['error', 'fatal'] if not specified.
                    Examples:
                    - ['error', 'fatal'] - Only critical issues (default)
                    - ['error', 'fatal', 'warning'] - Include warnings
                    - ['convention', 'refactor'] - Only style and refactoring suggestions
                    - ['convention', 'refactor', 'warning', 'error', 'fatal'] - All categories
                disable_codes: Optional list of pylint error codes to disable during analysis.
                    Common codes to disable include:
                    - C0114: Missing module docstring
                    - C0116: Missing function docstring
                    - C0301: Line too long
                    - W0611: Unused import
                    - W1514: Using open without explicitly specifying an encoding
                target_directories: Optional list of directories to analyze relative to project_dir.
                    Defaults to ["src"] and conditionally "tests" if it exists.
                    Examples:
                    - ["src"] - Analyze only source code
                    - ["src", "tests"] - Analyze both source and tests (default)
                    - ["mypackage", "tests"] - Custom package structure
                    - ["."] - Analyze entire project (may be slow)

            Returns:
                A string containing either pylint results or a prompt for an LLM to interpret
            """
            try:
                logger.info(
                    f"Running pylint check on project directory: {self.project_dir}"
                )
                structured_logger.info(
                    "Starting pylint check",
                    project_dir=str(self.project_dir),
                    categories=categories,
                    disable_codes=disable_codes,
                    target_directories=target_directories,
                )

                # Import the code_checker_pylint module to run pylint checks
                from src.code_checker_pylint import PylintMessageType, get_pylint_prompt

                # Convert string categories to PylintMessageType enum values if provided
                pylint_categories = set()
                if categories:
                    for category in categories:
                        try:
                            pylint_categories.add(PylintMessageType(category.lower()))
                        except ValueError:
                            logger.warning(f"Unknown pylint category: {category}")

                # Generate a prompt for pylint issues
                pylint_prompt = get_pylint_prompt(
                    str(self.project_dir),
                    categories=pylint_categories if pylint_categories else None,
                    disable_codes=disable_codes,
                    python_executable=self.python_executable,
                    target_directories=target_directories,
                )

                # Format the results as a string
                if pylint_prompt is None:
                    result = "Pylint check completed. No issues found that require attention."
                    structured_logger.info(
                        "Pylint check completed",
                        issues_found=False,
                        result_length=len(result),
                    )
                else:
                    result = (
                        f"Pylint found issues that need attention:\n\n{pylint_prompt}"
                    )
                    structured_logger.info(
                        "Pylint check completed",
                        issues_found=True,
                        result_length=len(result),
                    )

                return result
            except Exception as e:
                logger.error(f"Error running pylint check: {str(e)}")
                structured_logger.error(
                    "Pylint check failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    project_dir=str(self.project_dir),
                    categories=categories,
                    disable_codes=disable_codes,
                    target_directories=target_directories,
                )
                raise

        @self.mcp.tool()
        @log_function_call
        def run_pytest_check(
            markers: Optional[List[str]] = None,
            verbosity: int = 2,
            extra_args: Optional[List[str]] = None,
            env_vars: Optional[Dict[str, str]] = None,
        ) -> str:
            """
            Run pytest on the project code and generate smart prompts for LLMs.

            Args:
                markers: Optional list of pytest markers to filter tests. Examples: ['slow', 'integration']
                verbosity: Integer for pytest verbosity level (0-3), default 2. Higher values provide more detailed output.
                extra_args: Optional list of additional pytest arguments. Examples: ['-xvs', '--no-header']
                env_vars: Optional dictionary of environment variables for the subprocess. Example: {'DEBUG': '1', 'PYTHONPATH': '/custom/path'}


            Returns:
                A string containing either pytest results or a prompt for an LLM to interpret
            """
            try:
                logger.info(
                    f"Running pytest check on project directory: {self.project_dir}"
                )
                structured_logger.info(
                    "Starting pytest check",
                    project_dir=str(self.project_dir),
                    test_folder=self.test_folder,
                    markers=markers,
                    verbosity=verbosity,
                    extra_args=extra_args,
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
                )

                if not test_results["success"]:
                    result = f"Error running pytest: {test_results.get('error', 'Unknown error')}"
                    structured_logger.error(
                        "Pytest execution failed",
                        error=test_results.get("error", "Unknown error"),
                    )
                else:
                    summary = test_results["summary"]
                    structured_logger.info(
                        "Pytest execution completed",
                        passed=summary.get("passed", 0),
                        failed=summary.get("failed", 0),
                        errors=summary.get("error", 0),
                        duration=test_results.get("duration", 0),
                    )

                    if (
                        summary.get("failed", 0) > 0 or summary.get("error", 0) > 0
                    ) and test_results.get("test_results"):
                        # Use create_prompt_for_failed_tests to generate a prompt for the failed tests
                        failed_tests_prompt = create_prompt_for_failed_tests(
                            test_results["test_results"]
                        )
                        result = f"Pytest found issues that need attention:\n\n{failed_tests_prompt}"
                        structured_logger.info(
                            "Pytest issues found",
                            failed_tests=summary.get("failed", 0),
                            error_tests=summary.get("error", 0),
                        )
                    else:
                        result = (
                            "Pytest check completed. All tests passed successfully."
                        )
                        structured_logger.info(
                            "All pytest tests passed",
                            total_tests=summary.get("passed", 0),
                        )

                return result
            except Exception as e:
                logger.error(f"Error running pytest check: {str(e)}")
                structured_logger.error(
                    "Pytest check failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    project_dir=str(self.project_dir),
                    test_folder=self.test_folder,
                    markers=markers,
                    verbosity=verbosity,
                )
                raise

        @self.mcp.tool()
        @log_function_call
        def run_all_checks(
            markers: Optional[List[str]] = None,
            verbosity: int = 2,
            extra_args: Optional[List[str]] = None,
            env_vars: Optional[Dict[str, str]] = None,
            categories: Optional[List[str]] = None,
            target_directories: Optional[List[str]] = None,
        ) -> str:
            """
            Run all code checks (pylint and pytest) and generate combined results.

            Args:
                markers: Optional list of pytest markers to filter tests. Examples: ['slow', 'integration']
                verbosity: Integer for pytest verbosity level (0-3), default 2. Higher values provide more detailed output.
                extra_args: Optional list of additional pytest arguments. Examples: ['-xvs', '--no-header']
                env_vars: Optional dictionary of environment variables for the subprocess. Example: {'DEBUG': '1', 'PYTHONPATH': '/custom/path'}
                categories: Optional list of pylint message categories to include.
                    Available categories: 'convention', 'refactor', 'warning', 'error', 'fatal'
                    Defaults to ['error', 'fatal'] if not specified.
                target_directories: Optional list of directories to analyze relative to project_dir.
                    Defaults to ["src"] and conditionally "tests" if it exists.
                    Examples:
                    - ["src"] - Analyze only source code
                    - ["src", "tests"] - Analyze both source and tests (default)
                    - ["mypackage", "tests"] - Custom package structure
                    - ["."] - Analyze entire project (may be slow)

            Returns:
                A string containing results from all checks and/or LLM prompts
            """
            try:
                logger.info(
                    f"Running all code checks on project directory: {self.project_dir}"
                )
                structured_logger.info(
                    "Starting all code checks",
                    project_dir=str(self.project_dir),
                    test_folder=self.test_folder,
                    markers=markers,
                    verbosity=verbosity,
                    categories=categories,
                    target_directories=target_directories,
                )

                # Run pylint check to generate prompt
                from src.code_checker_pylint import PylintMessageType, get_pylint_prompt

                # Convert string categories to PylintMessageType enum values if provided
                pylint_categories = set()
                if categories:
                    for category in categories:
                        try:
                            pylint_categories.add(PylintMessageType(category.lower()))
                        except ValueError:
                            logger.warning(f"Unknown pylint category: {category}")

                # Run pylint with categories and target directories
                pylint_prompt = get_pylint_prompt(
                    str(self.project_dir),
                    categories=pylint_categories if pylint_categories else None,
                    python_executable=self.python_executable,
                    target_directories=target_directories,
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

                structured_logger.info(
                    "All code checks completed",
                    pylint_issues_found=pylint_prompt is not None,
                    pytest_failed=(
                        test_results["summary"].get("failed", 0)
                        if test_results.get("success")
                        else None
                    ),
                    pytest_passed=(
                        test_results["summary"].get("passed", 0)
                        if test_results.get("success")
                        else None
                    ),
                    pytest_errors=(
                        test_results["summary"].get("error", 0)
                        if test_results.get("success")
                        else None
                    ),
                )

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
                structured_logger.error(
                    "All code checks failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    project_dir=str(self.project_dir),
                )
                raise

        @self.mcp.tool()
        @log_function_call
        def second_sleep(
            sleep_seconds: float = 5.0, implementation_method: str = "default"
        ) -> str:
            """
            Sleep for specified seconds using configurable implementation methods.

            Args:
                sleep_seconds: Number of seconds to sleep (default: 5.0, max: 300 for safety)
                implementation_method: Method to use ("default", "python", "batch", "hybrid")

            Returns:
                A string indicating the sleep operation result
            """
            # Input validation
            if not 0 <= sleep_seconds <= 300:
                raise ValueError("Sleep seconds must be between 0 and 300")

            valid_methods = ["default", "python", "batch", "hybrid", "subprocess_test"]
            if implementation_method not in valid_methods:
                raise ValueError(
                    f"Invalid method: {implementation_method}. Valid methods: {valid_methods}"
                )

            import os

            from src.utils.command_runner import execute_command

            # Map default to the most reliable method
            if implementation_method == "default":
                implementation_method = "python"

            # Build command based on implementation method
            if implementation_method == "python":
                sleep_script = self.project_dir / "tools" / "sleep_script.py"
                if not sleep_script.exists():
                    raise FileNotFoundError(f"Sleep script not found: {sleep_script}")
                python_exe = self.python_executable or "python"
                command = [python_exe, "-u", str(sleep_script), str(sleep_seconds)]

            elif implementation_method == "batch":
                batch_script = self.project_dir / "tools" / "sleep_batch.bat"
                if not batch_script.exists():
                    raise FileNotFoundError(
                        f"Batch sleep script not found: {batch_script}"
                    )
                command = [str(batch_script), str(sleep_seconds)]

            elif implementation_method == "hybrid":
                hybrid_script = self.project_dir / "tools" / "sleep_hybrid.bat"
                if not hybrid_script.exists():
                    raise FileNotFoundError(
                        f"Hybrid sleep script not found: {hybrid_script}"
                    )
                command = [str(hybrid_script), str(sleep_seconds)]
                
            elif implementation_method == "subprocess_test":
                subprocess_test_script = self.project_dir / "tools" / "sleep_subprocess_test.py"
                if not subprocess_test_script.exists():
                    raise FileNotFoundError(
                        f"Subprocess test script not found: {subprocess_test_script}"
                    )
                python_exe = self.python_executable or "python"
                command = [python_exe, str(subprocess_test_script), str(sleep_seconds)]
            else:
                # This should never happen due to validation above, but ensures command is always defined
                raise ValueError(
                    f"Unexpected implementation method after validation: {implementation_method}"
                )

            # Set environment for Python methods
            env = os.environ.copy()
            if implementation_method == "python":
                env["PYTHONUNBUFFERED"] = "1"

            # Execute with timeout buffer
            result = execute_command(
                command,
                cwd=str(self.project_dir),
                timeout_seconds=int(sleep_seconds) + 30,
                env=env,
            )

            if result.return_code == 0:
                output = (
                    result.stdout.strip()
                    or f"Successfully slept for {sleep_seconds} seconds using {implementation_method} method"
                )
                return f"Method: {implementation_method}\n{output}"
            else:
                return f"Sleep failed (method: {implementation_method}, code {result.return_code}): {result.stderr}"

        @self.mcp.tool()
        @log_function_call
        def subprocess_test(
            sleep_seconds: float = 1.0
        ) -> str:
            """
            Test subprocess execution using the exact same pattern as the MCP server.
            
            This method replicates the exact subprocess.run() call that the MCP server makes,
            helping diagnose whether timeout issues are MCP-specific or general subprocess problems.
            
            Args:
                sleep_seconds: Number of seconds to sleep (default: 1.0, max: 300 for safety)
            
            Returns:
                A string with detailed subprocess execution results
            """
            # Input validation
            if not 0 <= sleep_seconds <= 300:
                raise ValueError("Sleep seconds must be between 0 and 300")
            
            import os
            import subprocess
            import time
            
            # Build the exact same command as the MCP server
            sleep_script = self.project_dir / "tools" / "sleep_script.py"
            if not sleep_script.exists():
                return f"ERROR: Sleep script not found: {sleep_script}"
            
            python_exe = self.python_executable or "python"
            command = [python_exe, "-u", str(sleep_script), str(sleep_seconds)]
            
            # Set same environment as MCP server
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            
            # Calculate timeout same as MCP server: sleep_seconds + 30
            timeout_seconds = int(sleep_seconds) + 30
            
            result_lines = [
                "=" * 60,
                "MCP Server Subprocess Execution Test",
                "=" * 60,
                f"Command: {' '.join(command)}",
                f"Timeout: {timeout_seconds} seconds",
                f"Environment: PYTHONUNBUFFERED=1",
                f"Working directory: {self.project_dir}",
                "",
                "Starting subprocess execution..."
            ]
            
            start_time = time.time()
            
            try:
                # This is the EXACT subprocess.run() call from the MCP server
                process = subprocess.run(
                    command,
                    cwd=str(self.project_dir),
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=timeout_seconds,
                    env=env,
                    shell=False,
                    input=None
                )
                
                execution_time = time.time() - start_time
                
                result_lines.extend([
                    f"Subprocess completed!",
                    f"Execution time: {execution_time:.3f} seconds",
                    f"Return code: {process.returncode}",
                    f"Stdout length: {len(process.stdout)} characters",
                    f"Stderr length: {len(process.stderr)} characters"
                ])
                
                if process.stdout:
                    result_lines.extend([
                        "",
                        "Stdout:",
                        process.stdout.strip()
                    ])
                
                if process.stderr:
                    result_lines.extend([
                        "",
                        "Stderr:",
                        process.stderr.strip()
                    ])
                
                result_lines.extend([
                    "",
                    "=" * 60,
                    "Test Summary",
                    "=" * 60,
                    f"Success: {process.returncode == 0}",
                    f"Return code: {process.returncode}",
                    f"Execution time: {execution_time:.3f} seconds",
                    f"Timed out: False",
                    ""
                ])
                
                if process.returncode == 0:
                    result_lines.extend([
                        "[PASS] Subprocess execution PASSED - same as direct script execution",
                        "   This suggests the issue is MCP communication-specific, not subprocess"
                    ])
                else:
                    result_lines.extend([
                        "[FAIL] Subprocess execution FAILED - same issue as MCP server",
                        "   This suggests the issue is in subprocess execution, not MCP-specific"
                    ])
                
                return "\n".join(result_lines)
                
            except subprocess.TimeoutExpired:
                execution_time = time.time() - start_time
                
                result_lines.extend([
                    f"TIMEOUT! Process timed out after {timeout_seconds} seconds",
                    f"Actual execution time: {execution_time:.3f} seconds",
                    "",
                    "=" * 60,
                    "Test Summary",
                    "=" * 60,
                    f"Success: False",
                    f"Return code: 1",
                    f"Execution time: {execution_time:.3f} seconds",
                    f"Timed out: True",
                    "",
                    "[FAIL] Subprocess execution FAILED - same timeout issue as MCP server",
                    "   This confirms the issue is in subprocess execution, not MCP-specific"
                ])
                
                return "\n".join(result_lines)
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                result_lines.extend([
                    f"ERROR! Subprocess failed: {e}",
                    f"Error type: {type(e).__name__}",
                    "",
                    "=" * 60,
                    "Test Summary",
                    "=" * 60,
                    f"Success: False",
                    f"Return code: 1",
                    f"Execution time: {execution_time:.3f} seconds",
                    f"Timed out: False",
                    f"Error: {str(e)}",
                    "",
                    "[FAIL] Subprocess execution FAILED - unexpected error",
                    "   This suggests a different issue than the MCP timeout problem"
                ])
                
                return "\n".join(result_lines)

        @self.mcp.tool()
        @log_function_call
        def sleep_seconds(sleep_seconds: int = 5) -> str:
            """
            Legacy sleep function for backward compatibility.

            Args:
                sleep_seconds: Number of seconds to sleep (default: 5)

            Returns:
                A string indicating the sleep operation result
            """
            return second_sleep(float(sleep_seconds), "default")

    @log_function_call
    def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting MCP server")
        structured_logger.info("Starting MCP server")
        self.mcp.run()


@log_function_call
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
        python_executable: Optional path to Python interpreter to use for running tests. If None, defaults to sys.executable.
        venv_path: Optional path to a virtual environment to activate for running tests. When specified, the Python executable from this venv will be used instead of python_executable.
        test_folder: Path to the test folder (relative to project_dir). Defaults to 'tests'.
        keep_temp_files: Whether to keep temporary files after test execution. Useful for debugging when tests fail.

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
