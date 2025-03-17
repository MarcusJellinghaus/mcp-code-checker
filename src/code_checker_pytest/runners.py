"""
Functions for running pytest tests and processing results.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional

from .models import PytestReport
from .parsers import parse_pytest_report
from .reporting import create_prompt_for_failed_tests, get_test_summary
from .utils import read_file

logger = logging.getLogger(__name__)


def run_tests(
    project_dir: str,
    test_folder: str,
    python_executable: Optional[str] = None,
    markers: Optional[List[str]] = None,
    verbosity: int = 1,
    extra_args: Optional[List[str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    venv_path: Optional[str] = None,
    keep_temp_files: bool = False,
) -> PytestReport:
    """
    Run pytest tests in the specified project directory and test folder and returns the results.

    Args:
        project_dir: The path to the project directory
        test_folder: The path to the folder containing the tests relative to the project directory
        python_executable: Optional path to Python interpreter to use. Defaults to sys.executable if not provided
        markers: Optional list of pytest markers to filter tests
        verbosity: Integer for pytest verbosity level (0-3). Default is 1
        extra_args: Optional list of additional pytest arguments
        env_vars: Optional dictionary of environment variables to set for the subprocess
        venv_path: Optional path to a virtual environment to activate
        keep_temp_files: Whether to keep temporary files after execution (for debugging)

    Returns:
        PytestReport: An object containing the results of the test session

    Raises:
        Exception: If pytest is not installed or if an error occurs during test execution
    """

    # Create a temporary directory for output files
    temp_dir = tempfile.mkdtemp(prefix="pytest_runner_")
    temp_report_file = os.path.join(temp_dir, "pytest_result.json")

    try:
        # Define pytest type to avoid import-not-found error
        class PytestModule:
            @staticmethod
            def main(*args: Any, **kwargs: Any) -> Any: ...

        try:
            import pytest as pytest_module  # Import pytest dynamically
        except ImportError:
            try:
                # Check if pytest-json-report is installed
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "pytest-json-report"],
                    check=True,
                    capture_output=True,
                )
                # Retry importing pytest
                import pytest as pytest_module  # Import pytest dynamically
            except (ImportError, subprocess.CalledProcessError):
                raise Exception(
                    "pytest and/or pytest-json-report are not installed. "
                    "Please install them using 'pip install pytest pytest-json-report'"
                )

        # Determine Python executable
        py_executable = python_executable

        # Handle virtual environment activation
        if venv_path:
            if not os.path.exists(venv_path):
                raise Exception(f"Virtual environment path does not exist: {venv_path}")

            # Locate the Python executable in the virtual environment
            if os.name == "nt":  # Windows
                venv_python = os.path.join(venv_path, "Scripts", "python.exe")
            else:  # Unix-like systems
                venv_python = os.path.join(venv_path, "bin", "python")

            if not os.path.exists(venv_python):
                raise Exception(
                    f"Python executable not found in virtual environment: {venv_python}"
                )

            py_executable = venv_python

        # If no executable is specified (either directly or via venv), use the current one
        if not py_executable:
            py_executable = sys.executable

        # Construct the pytest command
        command = [
            py_executable,
            "-m",
            "pytest",
        ]

        # Add verbosity flags based on level
        if verbosity > 0:
            verbosity_flag = "-" + "v" * min(verbosity, 3)  # -v, -vv, or -vvv
            command.append(verbosity_flag)

        # Add markers if provided
        if markers and len(markers) > 0:
            if len(markers) == 1:
                command.extend(["-m", markers[0]])
            else:
                # Combine multiple markers with "and"
                command.extend(["-m", " and ".join(markers)])

        # Add rootdir and json-report options
        command.extend(
            [
                "--rootdir",
                project_dir,
                "--json-report",
                f"--json-report-file={temp_report_file}",
            ]
        )

        # Add any extra arguments
        if extra_args:
            command.extend(extra_args)

        # Add the test folder path
        command.append(os.path.join(project_dir, test_folder))

        logger.debug(f"Running command: {' '.join(command)}")

        # Prepare environment variables
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # If using a virtual environment, adjust PATH to prioritize it
        if venv_path:
            if os.name == "nt":  # Windows
                venv_bin = os.path.join(venv_path, "Scripts")
            else:  # Unix-like systems
                venv_bin = os.path.join(venv_path, "bin")

            env["PATH"] = f"{venv_bin}{os.pathsep}{env.get('PATH', '')}"

        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                cwd=project_dir,
                env=env,
            )

            # Handle different return codes
            if process.returncode == 1:
                if not os.path.isfile(temp_report_file):
                    print(process.stdout)
                    raise Exception(
                        "Test Collection Errors: Pytest failed to collect tests."
                    )
            elif process.returncode == 2:
                if not os.path.isfile(temp_report_file):
                    print(process.stdout)
                    raise Exception(
                        "Test Collection Errors: Pytest failed to collect tests."
                    )
            elif process.returncode == 3:
                print(process.stdout)
                raise Exception("Internal Error: Pytest encountered an internal error.")
            elif (
                process.returncode == 4
            ):  # can also happen if test folder does not exist
                print(process.stdout)
                raise Exception("Usage Error: Pytest was used incorrectly.")
            elif process.returncode == 5:
                print(process.stdout)
                raise Exception("No Tests Found: Pytest did not find any tests to run.")
            elif process.returncode != 0:
                raise Exception(f"Unknown pytest return code: {process.returncode}")

            if not os.path.isfile(temp_report_file):
                print(process.stdout)
                raise Exception(
                    "Test execution completed but no report file was generated."
                )

            file_contents = read_file(temp_report_file)

            output = process.stdout
            logger.debug(output)

        except Exception as e:
            command_line = " ".join(command)
            print(
                f"""Error during pytest execution:
- folder {project_dir}
- {command_line}"""
            )
            raise e

        parsed_results = parse_pytest_report(file_contents)
        return parsed_results

    except Exception as e:
        raise e
    finally:
        # Clean up temporary files unless keep_temp_files is True
        if not keep_temp_files and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                logger.warning(
                    f"Failed to clean up temporary directory: {cleanup_error}"
                )


def check_code_with_pytest(
    project_dir: str,
    test_folder: str = "tests",
    python_executable: Optional[str] = None,
    markers: Optional[List[str]] = None,
    verbosity: int = 1,
    extra_args: Optional[List[str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    venv_path: Optional[str] = None,
    keep_temp_files: bool = False,
) -> Dict[str, Any]:
    """
    Run pytest on the specified project and return results.

    Args:
        project_dir: Path to the project directory
        test_folder: Path to the test folder (relative to project_dir)
        python_executable: Optional path to Python interpreter to use
        markers: Optional list of pytest markers to filter tests
        verbosity: Integer for pytest verbosity level (0-3)
        extra_args: Optional list of additional pytest arguments
        env_vars: Optional dictionary of environment variables to set for the subprocess
        venv_path: Optional path to a virtual environment to activate
        keep_temp_files: Whether to keep temporary files after execution (for debugging)

    Returns:
        Dictionary with test results
    """
    try:
        test_results = run_tests(
            project_dir,
            test_folder,
            python_executable,
            markers,
            verbosity,
            extra_args,
            env_vars,
            venv_path,
            keep_temp_files,
        )

        summary = get_test_summary(test_results)

        failed_tests_prompt = None
        if (test_results.summary.failed and test_results.summary.failed > 0) or (
            test_results.summary.error and test_results.summary.error > 0
        ):
            failed_tests_prompt = create_prompt_for_failed_tests(test_results)

        return {
            "success": True,
            "summary": summary,
            "failed_tests_prompt": failed_tests_prompt,
            "test_results": test_results,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
