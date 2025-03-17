"""
Tests for the code_checker_pytest implementation.
"""

import os
import shutil

# Add source directory to path
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.code_checker_pytest import (
    PytestReport,
    check_code_with_pytest,
    create_prompt_for_failed_tests,
    parse_pytest_report,
    run_tests,
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Sample JSON report for testing
SAMPLE_JSON = """
{
    "created": 1518371686.7981803,
    "duration": 0.1235666275024414,
    "exitcode": 1,
    "root": "/path/to/tests",
    "environment": {
        "Python": "3.6.4",
        "Platform": "Linux-4.56.78-9-ARCH-x86_64-with-arch",
        "Packages": {
            "pytest": "3.4.0",
            "py": "1.5.2",
            "pluggy": "0.6.0"
        },
        "Plugins": {
            "json-report": "0.4.1",
            "xdist": "1.22.0",
            "metadata": "1.5.1",
            "forked": "0.2",
            "cov": "2.5.1"
        },
        "foo": "bar"
    },
    "summary": {
        "collected": 10,
        "passed": 2,
        "failed": 3,
        "xfailed": 1,
        "xpassed": 1,
        "error": 2,
        "skipped": 1,
        "total": 10
    },
    "collectors": [
        {
            "nodeid": "",
            "outcome": "passed",
            "result": [
                {
                    "nodeid": "test_foo.py",
                    "type": "Module"
                }
            ]
        },
        {
            "nodeid": "test_foo.py",
            "outcome": "passed",
            "result": [
                {
                    "nodeid": "test_foo.py::test_pass",
                    "type": "Function",
                    "lineno": 24,
                    "deselected": true
                },
                {
                    "nodeid": "test_foo.py::test_fail",
                    "type": "Function",
                    "lineno": 50
                }
            ]
        },
        {
            "nodeid": "test_bar.py",
            "outcome": "failed",
            "result": [],
            "longrepr": "/usr/lib/python3.6 ... invalid syntax"
        }
    ],
    "tests": [
        {
            "nodeid": "test_foo.py::test_fail",
            "lineno": 50,
            "keywords": [
                "test_fail",
                "test_foo.py",
                "test_foo0"
            ],
            "outcome": "failed",
            "setup": {
              "duration": 0.00018835067749023438,
              "outcome": "passed"
            },
            "call": {
                "duration": 0.00018835067749023438,
                "outcome": "failed",
                "crash": {
                    "path": "/path/to/tests/test_foo.py",
                    "lineno": 54,
                    "message": "TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'"
                },
                "traceback": [
                    {
                        "path": "test_foo.py",
                        "lineno": 65,
                        "message": ""
                    },
                    {
                        "path": "test_foo.py",
                        "lineno": 63,
                        "message": "in foo"
                    },
                    {
                        "path": "test_foo.py",
                        "lineno": 63,
                        "message": "in <listcomp>"
                    },
                    {
                        "path": "test_foo.py",
                        "lineno": 54,
                        "message": "TypeError"
                    }
                ],
                "stdout": "foo\\nbar\\n",
                "stderr": "baz\\n"
            },
             "teardown": {
              "duration": 0.00018835067749023438,
              "outcome": "passed"
            },
            "metadata": {
                "foo": "bar"
            }
        },
        {
            "nodeid": "test_bar.py::test_error",
             "lineno": 50,
            "keywords": [
                "test_fail",
                "test_bar.py",
                "test_bar0"
            ],
            "outcome": "error",
           "setup": {
              "duration": 0.00018835067749023438,
              "outcome": "error",
               "longrepr": "/usr/lib/python3.6 ... invalid syntax"
            }
        }
    ],
    "warnings": [
        {
            "code": "C1",
            "path": "/path/to/tests/test_foo.py",
            "nodeid": "test_foo.py::TestFoo",
            "message": "cannot collect test class 'TestFoo' because it has a __init__ constructor"
        }
    ]
}
"""


def _create_test_project(test_dir: Path) -> None:
    """Creates a sample test project with a passing and a failing test."""
    (test_dir / "src").mkdir(parents=True, exist_ok=True)
    (test_dir / "tests").mkdir(parents=True, exist_ok=True)

    with open(test_dir / "src" / "__init__.py", "w") as f:
        f.write("")
    with open(test_dir / "tests" / "__init__.py", "w") as f:
        f.write("")
    with open(test_dir / "tests" / "test_sample.py", "w") as f:
        f.write(
            """
import pytest

def test_passing():
    assert 1 == 1

def test_failing():
    assert 1 == 2
"""
        )


def _cleanup_test_project(test_dir: Path) -> None:
    """Removes the sample test project after the test."""
    shutil.rmtree(test_dir)


def test_parse_report() -> None:
    """Test that pytest JSON report is correctly parsed into a PytestReport object."""
    report = parse_pytest_report(SAMPLE_JSON)

    assert isinstance(report, PytestReport)
    assert report.duration == 0.1235666275024414
    assert report.exitcode == 1
    assert report.summary.total == 10
    assert report.summary.passed == 2
    assert report.summary.failed == 3

    assert report.collectors is not None
    assert len(report.collectors) == 3
    assert report.collectors[0].nodeid == ""
    assert report.collectors[1].nodeid == "test_foo.py"
    assert report.collectors[2].nodeid == "test_bar.py"

    assert report.tests is not None
    assert len(report.tests) == 2
    assert report.tests[0].nodeid == "test_foo.py::test_fail"
    assert report.tests[1].nodeid == "test_bar.py::test_error"

    assert report.tests[0].call is not None
    assert report.tests[0].call.duration > 0
    assert report.tests[0].call.outcome == "failed"

    assert report.tests[0].call.crash is not None
    assert (
        report.tests[0].call.crash.message
        == "TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'"
    )

    assert report.tests[0].call.traceback is not None
    assert len(report.tests[0].call.traceback) == 4
    assert report.tests[0].call.traceback[0].message == ""

    assert report.warnings is not None
    assert len(report.warnings) == 1
    assert report.warnings[0].nodeid == "test_foo.py::TestFoo"


def test_parse_report_no_collectors() -> None:
    """Test parsing a report without collectors."""
    json_no_collectors = """
    {
        "created": 1518371686.7981803,
        "duration": 0.1235666275024414,
        "exitcode": 1,
        "root": "/path/to/tests",
        "environment": {
        "Python": "3.6.4",
        "Platform": "Linux-4.56.78-9-ARCH-x86_64-with-arch",
        "Packages": {
            "pytest": "3.4.0",
            "py": "1.5.2",
            "pluggy": "0.6.0"
        },
        "Plugins": {
            "json-report": "0.4.1",
            "xdist": "1.22.0",
            "metadata": "1.5.1",
            "forked": "0.2",
            "cov": "2.5.1"
        },
        "foo": "bar"
    },
    "summary": {
        "collected": 10,
        "passed": 2,
        "failed": 3,
        "xfailed": 1,
        "xpassed": 1,
        "error": 2,
        "skipped": 1,
        "total": 10
    },
        "tests": [],
        "warnings": []
    }
    """
    report = parse_pytest_report(json_no_collectors)
    assert isinstance(report, PytestReport)
    assert report.collectors is None


def test_parse_report_no_tests() -> None:
    """Test parsing a report without tests."""
    json_no_tests = """
    {
        "created": 1518371686.7981803,
        "duration": 0.1235666275024414,
        "exitcode": 1,
        "root": "/path/to/tests",
        "environment": {
        "Python": "3.6.4",
        "Platform": "Linux-4.56.78-9-ARCH-x86_64-with-arch",
        "Packages": {
            "pytest": "3.4.0",
            "py": "1.5.2",
            "pluggy": "0.6.0"
        },
        "Plugins": {
            "json-report": "0.4.1",
            "xdist": "1.22.0",
            "metadata": "1.5.1",
            "forked": "0.2",
            "cov": "2.5.1"
        },
        "foo": "bar"
    },
    "summary": {
        "collected": 10,
        "passed": 2,
        "failed": 3,
        "xfailed": 1,
        "xpassed": 1,
        "error": 2,
        "skipped": 1,
        "total": 10
    },
       "collectors": [],
        "warnings": []
    }
    """
    report = parse_pytest_report(json_no_tests)
    assert isinstance(report, PytestReport)
    assert report.tests is None


def test_parse_report_with_log() -> None:
    """Test parsing a report with log entries."""
    json_with_log = """
    {
        "created": 1518371686.7981803,
        "duration": 0.1235666275024414,
        "exitcode": 1,
        "root": "/path/to/tests",
        "environment": {
        "Python": "3.6.4",
        "Platform": "Linux-4.56.78-9-ARCH-x86_64-with-arch",
        "Packages": {
            "pytest": "3.4.0",
            "py": "1.5.2",
            "pluggy": "0.6.0"
        },
        "Plugins": {
            "json-report": "0.4.1",
            "xdist": "1.22.0",
            "metadata": "1.5.1",
            "forked": "0.2",
            "cov": "2.5.1"
        },
        "foo": "bar"
    },
    "summary": {
        "collected": 10,
        "passed": 2,
        "failed": 3,
        "xfailed": 1,
        "xpassed": 1,
        "error": 2,
        "skipped": 1,
        "total": 10
    },
        "collectors": [],
        "tests": [{
            "nodeid": "test_foo.py::test_fail",
            "lineno": 50,
            "keywords": [
            "test_fail",
            "test_foo.py",
            "test_foo0"
            ],
            "outcome": "failed",
            "setup": {
            "duration": 0.00018835067749023438,
            "outcome": "passed"
            },
            "call": {
            "duration": 0.00018835067749023438,
            "outcome": "failed",
            "crash": {
                "path": "/path/to/tests/test_foo.py",
                "lineno": 54,
                "message": "TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'"
            },
            "traceback": [
                {
                "path": "test_foo.py",
                "lineno": 65,
                "message": ""
                },
                {
                "path": "test_foo.py",
                "lineno": 63,
                "message": "in foo"
                },
                {
                "path": "test_foo.py",
                "lineno": 63,
                "message": "in <listcomp>"
                },
                {
                "path": "test_foo.py",
                "lineno": 54,
                "message": "TypeError"
                }
            ],
            "stdout": "foo\\nbar\\n",
            "stderr": "baz\\n",
             "log": [{
                "name": "root",
                "msg": "This is a warning.",
                "args": null,
                "levelname": "WARNING",
                "levelno": 30,
                "pathname": "/path/to/tests/test_foo.py",
                "filename": "test_foo.py",
                "module": "test_foo",
                "exc_info": null,
                "exc_text": null,
                "stack_info": null,
                "lineno": 8,
                "funcName": "foo",
                "created": 1519772464.291738,
                "msecs": 291.73803329467773,
                "relativeCreated": 332.90839195251465,
                "thread": 140671803118912,
                "threadName": "MainThread",
                "processName": "MainProcess",
                "process": 31481
            }]
            },
            "teardown": {
            "duration": 0.00018835067749023438,
            "outcome": "passed"
            }
        }],
        "warnings": []
    }
    """
    report = parse_pytest_report(json_with_log)
    assert isinstance(report, PytestReport)
    assert report.tests is not None
    assert len(report.tests) == 1
    assert report.tests[0].call is not None
    assert report.tests[0].call.log is not None
    assert report.tests[0].call.log.logs is not None
    assert report.tests[0].call.log.logs[0].msg == "This is a warning."


def test_run_tests() -> None:
    """Integration test for run_tests function with a sample project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        _create_test_project(test_dir)

        try:
            # Run the tests and parse the report
            result = run_tests(str(test_dir), "tests")
            assert isinstance(result, PytestReport)

            # Check the summary
            assert result.summary.total == 2
            assert result.summary.passed == 1
            assert result.summary.failed == 1
            assert result.summary.collected == 2

            # Make sure tests are not None before accessing
            assert result.tests is not None

            # Find the passing and failing tests
            passing_test = next(
                (t for t in result.tests if t.nodeid.endswith("::test_passing")), None
            )
            failing_test = next(
                (t for t in result.tests if t.nodeid.endswith("::test_failing")), None
            )

            # Assert the passing test
            assert passing_test is not None
            assert passing_test.outcome == "passed"
            assert passing_test.call is not None
            assert passing_test.call.outcome == "passed"

            # Assert the failing test
            assert failing_test is not None
            assert failing_test.outcome == "failed"
            assert failing_test.call is not None
            assert failing_test.call.outcome == "failed"
            assert failing_test.call.crash is not None
            assert "assert 1 == 2" in failing_test.call.crash.message
        finally:
            _cleanup_test_project(test_dir)


def test_run_tests_no_tests_found() -> None:
    """Test the run_tests function when no tests are found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        (test_dir / "src").mkdir(parents=True, exist_ok=True)
        (test_dir / "tests").mkdir(parents=True, exist_ok=True)

        with open(test_dir / "src" / "__init__.py", "w") as f:
            f.write("")
        with open(test_dir / "tests" / "__init__.py", "w") as f:
            f.write("")

        try:
            with pytest.raises(
                Exception, match="No Tests Found: Pytest did not find any tests to run."
            ):
                run_tests(str(test_dir), "tests")
        finally:
            _cleanup_test_project(test_dir)


def test_create_prompt_no_failed_tests() -> None:
    """Test creating a prompt when there are no failed tests."""
    json_no_failed_tests = """
    {
        "created": 1518371686.7981803,
        "duration": 0.1235666275024414,
        "exitcode": 0,
        "root": "/path/to/tests",
        "environment": {
        "Python": "3.6.4",
        "Platform": "Linux-4.56.78-9-ARCH-x86_64-with-arch",
        "Packages": {
            "pytest": "3.4.0",
            "py": "1.5.2",
            "pluggy": "0.6.0"
        },
        "Plugins": {
            "json-report": "0.4.1",
            "xdist": "1.22.0",
            "metadata": "1.5.1",
            "forked": "0.2",
            "cov": "2.5.1"
        },
        "foo": "bar"
    },
    "summary": {
        "collected": 10,
        "passed": 10,
        "total": 10
    },
        "collectors": [],
        "tests": [],
        "warnings": []
    }
    """
    report = parse_pytest_report(json_no_failed_tests)
    prompt = create_prompt_for_failed_tests(report)
    assert prompt is None


def test_create_prompt_for_failed_tests() -> None:
    """Test creating a prompt for failed tests."""
    report = parse_pytest_report(SAMPLE_JSON)
    prompt = create_prompt_for_failed_tests(report)
    assert prompt is not None
    assert "The following tests failed during the test session:" in prompt
    assert "Test ID: test_foo.py::test_fail" in prompt

    # Safely check for attributes with None checks
    assert report.tests is not None
    assert report.tests[0].call is not None
    assert report.tests[0].call.crash is not None
    assert (
        "Error Message: TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'"
        in prompt
    )

    assert "Stdout:" in prompt
    assert "Stderr:" in prompt
    assert "Traceback:" in prompt
    assert "test_foo.py:65 - " in prompt
    assert (
        "Can you provide an explanation for why these tests failed and suggest how they could be fixed?"
        in prompt
    )


def test_create_prompt_for_failed_tests_longrepr() -> None:
    """Test creating a prompt for failed tests with longrepr."""
    json_with_longrepr_tests = """
  {
      "created": 1518371686.7981803,
      "duration": 0.1235666275024414,
      "exitcode": 1,
      "root": "/path/to/tests",
      "environment": {
          "Python": "3.6.4",
          "Platform": "Linux-4.56.78-9-ARCH-x86_64-with-arch",
          "Packages": {
              "pytest": "3.4.0",
              "py": "1.5.2",
              "pluggy": "0.6.0"
          },
          "Plugins": {
              "json-report": "0.4.1",
              "xdist": "1.22.0",
              "metadata": "1.5.1",
              "forked": "0.2",
              "cov": "2.5.1"
          },
          "foo": "bar"
      },
      "summary": {
          "collected": 10,
          "passed": 2,
          "failed": 1,
          "total": 10
      },
      "collectors": [],
      "tests": [
          {
              "nodeid": "test_foo.py::test_fail",
              "lineno": 50,
              "keywords": [
                  "test_fail",
                  "test_foo.py",
                  "test_foo0"
              ],
              "outcome": "failed",
              "setup": {
                  "duration": 0.00018835067749023438,
                  "outcome": "passed"
              },
              "call": {
                  "duration": 0.00018835067749023438,
                  "outcome": "failed",
                  "longrepr": "def test_fail_nested():\\n    a = 1\\n    b = None\\n    a - b",
                  "crash": {
                      "path": "/path/to/tests/test_foo.py",
                      "lineno": 54,
                      "message": "TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'"
                  },
                  "traceback": [
                      {
                          "path": "test_foo.py",
                          "lineno": 65,
                          "message": ""
                      }
                  ]
              },
              "teardown": {
                  "duration": 0.00018835067749023438,
                  "outcome": "passed"
              },
              "metadata": {
                  "foo": "bar"
              }
          }
      ],
      "warnings": []
  }
  """
    report = parse_pytest_report(json_with_longrepr_tests)
    prompt = create_prompt_for_failed_tests(report)
    assert prompt is not None
    assert "Longrepr:" in prompt
    assert "def test_fail_nested():" in prompt


@patch("src.code_checker_pytest.runners.run_tests")
def test_check_code_with_pytest(mock_run_tests: MagicMock) -> None:
    """Test the full check_code_with_pytest function."""
    # Create a mock Summary instance for our mock report
    mock_summary = MagicMock()
    mock_summary.collected = 2
    mock_summary.total = 2
    mock_summary.passed = 2
    mock_summary.failed = 0
    mock_summary.error = 0
    mock_summary.skipped = 0
    mock_summary.xfailed = 0
    mock_summary.xpassed = 0
    mock_summary.deselected = 0

    # Mock the run_tests function to return a test report
    mock_report = PytestReport(
        created=1678972345.123,
        duration=0.5,
        exitcode=0,
        root="/path/to/project",
        environment={"Python": "3.9.0"},
        summary=mock_summary,
    )
    mock_run_tests.return_value = mock_report

    # Call the function
    result = check_code_with_pytest("/test/project")

    # Verify the results
    assert result["success"] is True
    assert "summary" in result
    assert "Collected 2 tests" in result["summary"]
    assert "✅ Passed: 2" in result["summary"]
    assert result["failed_tests_prompt"] is None
    assert result["test_results"] == mock_report
