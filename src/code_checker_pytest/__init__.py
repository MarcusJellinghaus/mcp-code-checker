"""
Code checker package that runs pytest tests and analyzes the results.

This package provides functionality to run pytest tests on a given project
and process the test results.
"""

# Re-export all public models
from .models import (
    Crash, TracebackEntry, LogRecord, Log, TestStage, Test,
    CollectorResult, Collector, Summary, Warning, PytestReport
)

# Re-export parsing functions
from .parsers import parse_pytest_report, parse_test_stage

# Re-export runner functionality
from .runners import run_tests, check_code_with_pytest

# Re-export reporting functions
from .reporting import create_prompt_for_failed_tests, get_test_summary

# Re-export utility functions
from .utils import read_file

# Version information
__version__ = "1.0.0"

# Export all public symbols
__all__ = [
    'Crash', 'TracebackEntry', 'LogRecord', 'Log', 'TestStage', 'Test',
    'CollectorResult', 'Collector', 'Summary', 'Warning', 'PytestReport',
    'parse_pytest_report', 'parse_test_stage', 'run_tests',
    'create_prompt_for_failed_tests', 'get_test_summary',
    'read_file', 'check_code_with_pytest'
]
