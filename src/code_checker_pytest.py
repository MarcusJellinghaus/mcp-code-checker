"""
Code checker that runs pytest tests and analyzes the results.
This module provides functionality to run pytest tests on a given project
and processes the test results.
"""

import logging
import os
import subprocess
import sys
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Import dataclasses for the results module
from dataclasses import dataclass, field


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
        log_records = [LogRecord(**log_record_data) for log_record_data in stage_data["log"]]
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


def run_tests(project_dir: str, test_folder: str) -> PytestReport:
    """
    Run pytest tests in the specified project directory and test folder and returns the results.
    
    Args:
        project_dir: The path to the project directory
        test_folder: The path to the folder containing the tests relative to the project directory
        
    Returns:
        PytestReport: An object containing the results of the test session
        
    Raises:
        Exception: If pytest is not installed or if an error occurs during test execution
    """
    try:
        import pytest
    except ImportError:
        try:
            # Check if pytest-json-report is installed
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pytest-json-report"],
                check=True,
                capture_output=True
            )
            # Retry importing pytest
            import pytest
        except (ImportError, subprocess.CalledProcessError):
            raise Exception(
                "pytest and/or pytest-json-report are not installed. "
                "Please install them using 'pip install pytest pytest-json-report'"
            )

    pytest_result_file = "pytest_result.json"
    python_executable = sys.executable

    # Remove any existing report file
    if os.path.isfile(os.path.join(project_dir, pytest_result_file)):
        os.remove(os.path.join(project_dir, pytest_result_file))

    # Construct the pytest command
    command = [
        python_executable,
        "-m",
        "pytest",
        "--verbose",
        "--rootdir",
        project_dir,
        "--json-report",
        f"--json-report-file={pytest_result_file}",
        os.path.join(project_dir, test_folder),
    ]
    logger.debug(f"Running command: {' '.join(command)}")

    try:
        process = subprocess.run(
            command, capture_output=True, text=True, check=False, cwd=project_dir
        )

        # Handle different return codes
        if process.returncode == 1:
            if not os.path.isfile(os.path.join(project_dir, pytest_result_file)):
                print(process.stdout)
                raise Exception("Test Collection Errors: Pytest failed to collect tests.")
        elif process.returncode == 2:
            if not os.path.isfile(os.path.join(project_dir, pytest_result_file)):
                print(process.stdout)
                raise Exception("Test Collection Errors: Pytest failed to collect tests.")
        elif process.returncode == 3:
            print(process.stdout)
            raise Exception("Internal Error: Pytest encountered an internal error.")
        elif process.returncode == 4:  # can also happen if test folder does not exist
            print(process.stdout)
            raise Exception("Usage Error: Pytest was used incorrectly.")
        elif process.returncode == 5:
            print(process.stdout)
            raise Exception("No Tests Found: Pytest did not find any tests to run.")
        elif process.returncode != 0:
            raise Exception(f"Unknown pytest return code: {process.returncode}")

        file_contents = read_file(os.path.join(project_dir, pytest_result_file))

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
        prompt_parts.append("The following collectors failed during the test session:\n")
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
            test for test in test_session_result.tests if test.outcome in ["failed", "error"]
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
                prompt_parts.append(f"   - {entry.path}:{entry.lineno} - {entry.message}\n")
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
                prompt_parts.append(f"  Test Setup Crash Error Path: {test.setup.crash.path}\n")
                prompt_parts.append(f"  Setup Crash Error Line: {test.setup.crash.lineno}\n")
            if test.setup.traceback:
                prompt_parts.append("  Test Setup Traceback:\n")
                for entry in test.setup.traceback:
                    prompt_parts.append(f"   - {entry.path}:{entry.lineno} - {entry.message}\n")
            if test.setup.stdout:
                prompt_parts.append(f"  Test Setup Stdout:\n```\n{test.setup.stdout}\n```\n")
            if test.setup.stderr:
                prompt_parts.append(f"  Test Setup Stderr:\n```\n{test.setup.stderr}\n```\n")
            if test.setup.longrepr:
                prompt_parts.append(f"  Test Setup Longrepr:\n```\n{test.setup.longrepr}\n```\n")
            if test.setup.traceback and len(test.setup.traceback) > 0:
                prompt_parts.append("  Test Setup Traceback:\n")
                for entry in test.setup.traceback:
                    prompt_parts.append(f"   - {entry.path}:{entry.lineno} - {entry.message}\n")

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
    parts.append(f"Collected {summary.collected} tests in {test_session_result.duration:.2f} seconds")
    
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


def check_code_with_pytest(project_dir: str, test_folder: str = "tests") -> Dict[str, Any]:
    """
    Run pytest on the specified project and return results.
    
    Args:
        project_dir: Path to the project directory
        test_folder: Path to the test folder (relative to project_dir)
        
    Returns:
        Dictionary with test results
    """
    try:
        test_results = run_tests(project_dir, test_folder)
        
        summary = get_test_summary(test_results)
        
        failed_tests_prompt = None
        if (test_results.summary.failed and test_results.summary.failed > 0) or \
           (test_results.summary.error and test_results.summary.error > 0):
            failed_tests_prompt = create_prompt_for_failed_tests(test_results)
            
        return {
            "success": True,
            "summary": summary,
            "failed_tests_prompt": failed_tests_prompt,
            "test_results": test_results
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
