"""
Code checker that runs pytest tests and analyzes the results.
This module provides functionality to run pytest tests on a given project
and processes the test results.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile

# Import dataclasses for the results module
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Results data classes
@dataclass
class Crash:
    path: str
    lineno: int
    message: str


@dataclass
class TracebackEntry:
    path: str
    lineno: int
    message: str


@dataclass
class LogRecord:
    name: str
    msg: str
    args: Optional[Any]
    levelname: str
    levelno: int
    pathname: str
    filename: str
    module: str
    exc_info: Optional[Any]
    exc_text: Optional[str]
    stack_info: Optional[str]
    lineno: int
    funcName: str
    created: float
    msecs: float
    relativeCreated: float
    thread: int
    threadName: str
    processName: str
    process: int
    taskName: str = ""
    asctime: str = ""


@dataclass
class Log:
    logs: List[LogRecord]


@dataclass
class TestStage:
    duration: float
    outcome: str
    crash: Optional[Crash] = None
    traceback: Optional[List[TracebackEntry]] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    log: Optional[Log] = None
    longrepr: Optional[str] = None


@dataclass
class Test:
    nodeid: str
    lineno: int
    keywords: List[str]
    outcome: str
    setup: Optional[TestStage] = None
    call: Optional[TestStage] = None
    teardown: Optional[TestStage] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CollectorResult:
    nodeid: str
    type: str
    lineno: Optional[int] = None
    deselected: Optional[bool] = None


@dataclass
class Collector:
    nodeid: str
    outcome: str
    result: List[CollectorResult]
    longrepr: Optional[str] = None


@dataclass
class Summary:
    collected: int
    total: int
    deselected: Optional[int] = None
    passed: Optional[int] = None
    failed: Optional[int] = None
    xfailed: Optional[int] = None
    xpassed: Optional[int] = None
    error: Optional[int] = None
    skipped: Optional[int] = None


@dataclass
class Warning:
    message: str
    code: Optional[str] = None
    path: Optional[str] = None
    nodeid: Optional[str] = None
    when: Optional[str] = None
    category: Optional[str] = None
    filename: Optional[str] = None
    lineno: Optional[str] = None


@dataclass
class PytestReport:
    created: float
    duration: float
    exitcode: int
    root: str
    environment: Dict[str, Any]
    summary: Summary
    collectors: Optional[List[Collector]] = None
    tests: Optional[List[Test]] = None
    warnings: Optional[List[Warning]] = None


def read_file(file_path: str) -> str:
    """
    Read the contents of a file.

    Args:
        file_path: Path to the file to read

    Returns:
        The contents of the file as a string

    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If access to the file is denied
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with a different encoding if UTF-8 fails
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()


def parse_test_stage(stage_data: Dict[str, Any]) -> TestStage:
    """Parse test stage data from the pytest JSON report."""
    crash = None
    if "crash" in stage_data and stage_data["crash"]:
        crash = Crash(**stage_data["crash"])

    traceback = None
    if "traceback" in stage_data and stage_data["traceback"]:
        traceback = [TracebackEntry(**entry) for entry in stage_data["traceback"]]

    log = None
    if "log" in stage_data and stage_data["log"]:
        log_records = [
            LogRecord(**log_record_data) for log_record_data in stage_data["log"]
        ]
        log = Log(logs=log_records)

    return TestStage(
        duration=stage_data["duration"],
        outcome=stage_data["outcome"],
        crash=crash,
        traceback=traceback,
        stdout=stage_data.get("stdout"),
        stderr=stage_data.get("stderr"),
        log=log,
        longrepr=stage_data.get("longrepr"),
    )


def parse_pytest_report(json_data: str) -> PytestReport:
    """
    Parse a JSON string into a PytestReport object.

    Args:
        json_data: JSON string from pytest json report

    Returns:
        PytestReport object with test results
    """
    import json

    data = json.loads(json_data)

    summary = Summary(**data["summary"])

    environment = data["environment"]

    collectors = None
    if "collectors" in data and data["collectors"]:
        collectors = []
        for collector_data in data["collectors"]:
            result_data_list = []
            for result_data in collector_data["result"]:
                result_data_list.append(CollectorResult(**result_data))
            collector = Collector(
                nodeid=collector_data["nodeid"],
                outcome=collector_data["outcome"],
                result=result_data_list,
                longrepr=collector_data.get("longrepr"),
            )
            collectors.append(collector)

    tests = None
    if "tests" in data and data["tests"]:
        tests = []
        for test_data in data["tests"]:
            setup_stage = None
            call_stage = None
            teardown_stage = None

            if "setup" in test_data:
                setup_stage = parse_test_stage(test_data["setup"])
            if "call" in test_data:
                call_stage = parse_test_stage(test_data["call"])
            if "teardown" in test_data:
                teardown_stage = parse_test_stage(test_data["teardown"])

            test = Test(
                nodeid=test_data["nodeid"],
                lineno=test_data["lineno"],
                keywords=test_data["keywords"],
                outcome=test_data["outcome"],
                setup=setup_stage,
                call=call_stage,
                teardown=teardown_stage,
                metadata=test_data.get("metadata"),
            )
            tests.append(test)

    warnings = None
    if "warnings" in data and data["warnings"]:
        warnings = [Warning(**warning_data) for warning_data in data["warnings"]]

    return PytestReport(
        created=data["created"],
        duration=data["duration"],
        exitcode=data["exitcode"],
        root=data["root"],
        environment=environment,
        summary=summary,
        collectors=collectors,
        tests=tests,
        warnings=warnings,
    )


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


def create_prompt_for_failed_tests(
    test_session_result: PytestReport, max_number_of_tests_reported: int = 1
) -> Optional[str]:
    """
    Creates a prompt for an LLM based on the failed tests from a test session result.

    Args:
        test_session_result: The test session result to analyze
        max_number_of_tests_reported: Maximum number of tests to include in the prompt

    Returns:
        A prompt string, or None if no tests failed
    """
    prompt_parts = []

    failed_collectors = []
    if test_session_result.collectors:
        failed_collectors = [
            collector
            for collector in test_session_result.collectors
            if collector.outcome == "failed"
        ]
    if len(failed_collectors) > 0:
        prompt_parts.append(
            "The following collectors failed during the test session:\n"
        )
    for failed_collector in failed_collectors:
        prompt_parts.append(
            f"Collector ID: {failed_collector.nodeid} - outcome {failed_collector.outcome}\n"
        )
        if failed_collector.longrepr:
            prompt_parts.append(f"  Longrepr: {failed_collector.longrepr}\n")
        if failed_collector.result:
            for result in failed_collector.result:
                prompt_parts.append(f"  Result: {result}\n")
        prompt_parts.append("\n")

    failed_tests = []
    if test_session_result.tests:
        failed_tests = [
            test
            for test in test_session_result.tests
            if test.outcome in ["failed", "error"]
        ]

    test_count = 0
    if len(failed_tests) > 0:
        prompt_parts.append("The following tests failed during the test session:\n")
    for test in failed_tests:
        prompt_parts.append(f"Test ID: {test.nodeid} - outcome {test.outcome}\n")
        if test.call and test.call.crash:
            prompt_parts.append(f"  Error Message: {test.call.crash.message}\n")
        if test.call and test.call.traceback:
            prompt_parts.append("  Traceback:\n")
            for entry in test.call.traceback:
                prompt_parts.append(
                    f"   - {entry.path}:{entry.lineno} - {entry.message}\n"
                )
        if test.call and test.call.stdout:
            prompt_parts.append(f"  Stdout:\n```\n{test.call.stdout}\n```\n")
        if test.call and test.call.stderr:
            prompt_parts.append(f"  Stderr:\n```\n{test.call.stderr}\n```\n")
        if test.call and test.call.longrepr:
            prompt_parts.append(f"  Longrepr:\n```\n{test.call.longrepr}\n```\n")

        if test.setup and test.setup.outcome == "failed":
            prompt_parts.append(f"  Test Setup Outcome: {test.setup.outcome}\n")
            if test.setup.crash:
                prompt_parts.append(
                    f"  Test Setup Crash Error Message: {test.setup.crash.message}\n"
                )
                prompt_parts.append(
                    f"  Test Setup Crash Error Path: {test.setup.crash.path}\n"
                )
                prompt_parts.append(
                    f"  Setup Crash Error Line: {test.setup.crash.lineno}\n"
                )
            if test.setup.traceback:
                prompt_parts.append("  Test Setup Traceback:\n")
                for entry in test.setup.traceback:
                    prompt_parts.append(
                        f"   - {entry.path}:{entry.lineno} - {entry.message}\n"
                    )
            if test.setup.stdout:
                prompt_parts.append(
                    f"  Test Setup Stdout:\n```\n{test.setup.stdout}\n```\n"
                )
            if test.setup.stderr:
                prompt_parts.append(
                    f"  Test Setup Stderr:\n```\n{test.setup.stderr}\n```\n"
                )
            if test.setup.longrepr:
                prompt_parts.append(
                    f"  Test Setup Longrepr:\n```\n{test.setup.longrepr}\n```\n"
                )
            if test.setup.traceback and len(test.setup.traceback) > 0:
                prompt_parts.append("  Test Setup Traceback:\n")
                for entry in test.setup.traceback:
                    prompt_parts.append(
                        f"   - {entry.path}:{entry.lineno} - {entry.message}\n"
                    )

        prompt_parts.append("\n")

        test_count = test_count + 1
        if test_count >= max_number_of_tests_reported:
            break

        prompt_parts.append(
            "===============================================================================\n"
        )
        prompt_parts.append("\n")

    if len(prompt_parts) > 0:
        prompt_parts.append(
            "Can you provide an explanation for why these tests failed and suggest how they could be fixed?"
        )
        return "".join(prompt_parts)
    else:
        return None


def get_test_summary(test_session_result: PytestReport) -> str:
    """
    Generate a human-readable summary of the test results.

    Args:
        test_session_result: The test session result to summarize

    Returns:
        A string with the test summary
    """
    summary = test_session_result.summary

    parts = []
    parts.append(
        f"Collected {summary.collected} tests in {test_session_result.duration:.2f} seconds"
    )

    if summary.passed:
        parts.append(f"✅ Passed: {summary.passed}")
    if summary.failed:
        parts.append(f"❌ Failed: {summary.failed}")
    if summary.error:
        parts.append(f"⚠️ Error: {summary.error}")
    if summary.skipped:
        parts.append(f"⏭️ Skipped: {summary.skipped}")
    if summary.xfailed:
        parts.append(f"🔶 Expected failures: {summary.xfailed}")
    if summary.xpassed:
        parts.append(f"🔶 Unexpected passes: {summary.xpassed}")

    return " | ".join(parts)


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
