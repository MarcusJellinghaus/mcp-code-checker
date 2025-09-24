"""
Functions for formatting and reporting pytest test results.
"""

import logging
from typing import Optional, Dict, Any

import structlog

from mcp_code_checker.code_checker_pytest.models import PytestReport
from mcp_code_checker.log_utils import log_function_call

logger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)


def should_show_details(test_results: Dict[str, Any], show_details: bool) -> bool:
    """
    Determine if detailed output should be shown based on test results and user preference.
    
    Args:
        test_results: Dictionary containing test summary information
        show_details: User preference for showing details
        
    Returns:
        True if conditions meet criteria for showing details, False otherwise
    """
    # If show_details is explicitly True, always show details (output truncation handles length)
    if show_details:
        return True
    
    # For default behavior (show_details=False), never show details
    return False


@log_function_call
def create_prompt_for_failed_tests(
    test_session_result: PytestReport,
    max_number_of_tests_reported: int = 1,
    include_print_output: bool = True,
    max_failures: int = 10,
    max_output_lines: int = 300
) -> Optional[str]:
    """
    Creates a prompt for an LLM based on the failed tests from a test session result.

    Args:
        test_session_result: The test session result to analyze
        max_number_of_tests_reported: Maximum number of tests to include in the prompt
        include_print_output: Whether to include stdout/stderr/longrepr output
        max_failures: Maximum number of failures to report (hardcoded limit)
        max_output_lines: Overall output line limit with truncation indicator

    Returns:
        A prompt string, or None if no tests failed
    """
    prompt_parts = []
    line_count = 0

    # Helper function to add content with line counting
    def add_content(content: str) -> bool:
        nonlocal line_count
        lines = content.count('\n')
        if line_count + lines > max_output_lines:
            remaining_lines = max_output_lines - line_count
            if remaining_lines > 0:
                content_lines = content.split('\n')
                prompt_parts.append('\n'.join(content_lines[:remaining_lines]))
                prompt_parts.append('\n\n[Output truncated at {} lines...]\n'.format(max_output_lines))
            return False  # Signal to stop processing
        prompt_parts.append(content)
        line_count += lines
        return True

    failed_collectors = []
    if test_session_result.collectors:
        failed_collectors = [
            collector
            for collector in test_session_result.collectors
            if collector.outcome in ["failed", "error"]
        ]
    if len(failed_collectors) > 0:
        if not add_content("The following collectors failed during the test session:\n"):
            return "\n".join(prompt_parts)
    for failed_collector in failed_collectors:
        if not add_content(f"Collector ID: {failed_collector.nodeid} - outcome {failed_collector.outcome}\n"):
            return "\n".join(prompt_parts)
        # Collection errors are always shown (critical setup issues)
        if failed_collector.longrepr:
            if not add_content(f"  Longrepr: {failed_collector.longrepr}\n"):
                return "\n".join(prompt_parts)
        if failed_collector.result:
            for result in failed_collector.result:
                if not add_content(f"  Result: {result}\n"):
                    return "\n".join(prompt_parts)
        if not add_content("\n"):
            return "\n".join(prompt_parts)

    failed_tests = []
    if test_session_result.tests:
        failed_tests = [
            test
            for test in test_session_result.tests
            if test.outcome in ["failed", "error"]
        ]

    # Limit the number of failures reported
    failed_tests = failed_tests[:max_failures]

    test_count = 0
    if len(failed_tests) > 0:
        if not add_content("The following tests failed during the test session:\n"):
            return "\n".join(prompt_parts)
    for test in failed_tests:
        if not add_content(f"Test ID: {test.nodeid} - outcome {test.outcome}\n"):
            return "\n".join(prompt_parts)
        if test.call and test.call.crash:
            if not add_content(f"  Error Message: {test.call.crash.message}\n"):
                return "\n".join(prompt_parts)
        if test.call and test.call.traceback:
            if not add_content("  Traceback:\n"):
                return "\n".join(prompt_parts)
            for entry in test.call.traceback:
                if not add_content(f"   - {entry.path}:{entry.lineno} - {entry.message}\n"):
                    return "\n".join(prompt_parts)
        
        # Include output sections only if include_print_output is True
        if include_print_output:
            if test.call and test.call.stdout:
                if not add_content(f"  Stdout:\n```\n{test.call.stdout}\n```\n"):
                    return "\n".join(prompt_parts)
            if test.call and test.call.stderr:
                if not add_content(f"  Stderr:\n```\n{test.call.stderr}\n```\n"):
                    return "\n".join(prompt_parts)
            if test.call and test.call.longrepr:
                if not add_content(f"  Longrepr:\n```\n{test.call.longrepr}\n```\n"):
                    return "\n".join(prompt_parts)

        if test.setup and test.setup.outcome == "failed":
            if not add_content(f"  Test Setup Outcome: {test.setup.outcome}\n"):
                return "\n".join(prompt_parts)
            if test.setup.crash:
                if not add_content(f"  Test Setup Crash Error Message: {test.setup.crash.message}\n"):
                    return "\n".join(prompt_parts)
                if not add_content(f"  Test Setup Crash Error Path: {test.setup.crash.path}\n"):
                    return "\n".join(prompt_parts)
                if not add_content(f"  Setup Crash Error Line: {test.setup.crash.lineno}\n"):
                    return "\n".join(prompt_parts)
            if test.setup.traceback:
                if not add_content("  Test Setup Traceback:\n"):
                    return "\n".join(prompt_parts)
                for entry in test.setup.traceback:
                    if not add_content(f"   - {entry.path}:{entry.lineno} - {entry.message}\n"):
                        return "\n".join(prompt_parts)
            
            # Include setup output sections only if include_print_output is True
            if include_print_output:
                if test.setup.stdout:
                    if not add_content(f"  Test Setup Stdout:\n```\n{test.setup.stdout}\n```\n"):
                        return "\n".join(prompt_parts)
                if test.setup.stderr:
                    if not add_content(f"  Test Setup Stderr:\n```\n{test.setup.stderr}\n```\n"):
                        return "\n".join(prompt_parts)
                if test.setup.longrepr:
                    if not add_content(f"  Test Setup Longrepr:\n```\n{test.setup.longrepr}\n```\n"):
                        return "\n".join(prompt_parts)

        if not add_content("\n"):
            return "\n".join(prompt_parts)

        test_count = test_count + 1
        if test_count >= max_number_of_tests_reported:
            break

        if not add_content("===============================================================================\n"):
            return "\n".join(prompt_parts)
        if not add_content("\n"):
            return "\n".join(prompt_parts)

    if len(prompt_parts) > 0:
        if not add_content("Can you provide an explanation for why these tests failed and suggest how they could be fixed?"):
            return "\n".join(prompt_parts)
        return "".join(prompt_parts)
    else:
        return None


def get_detailed_test_summary(test_session_result: PytestReport, show_details: bool) -> str:
    """
    Enhanced summary that can include additional detail hints.
    
    Args:
        test_session_result: The test session result to summarize
        show_details: Whether to include hints about detail availability
        
    Returns:
        A string with the enhanced test summary
    """
    summary_base = get_test_summary(test_session_result)
    
    if show_details:
        test_results = {
            "summary": {
                "collected": test_session_result.summary.collected,
                "failed": test_session_result.summary.failed,
                "error": test_session_result.summary.error
            }
        }
        if should_show_details(test_results, show_details):
            summary_base += " [Details available with show_details=True]"
    
    return summary_base


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

    if summary.passed is not None and summary.passed > 0:
        parts.append(f"✅ Passed: {summary.passed}")
    if summary.failed is not None and summary.failed > 0:
        parts.append(f"❌ Failed: {summary.failed}")
    if summary.error is not None and summary.error > 0:
        parts.append(f"⚠️ Error: {summary.error}")
    if summary.skipped is not None and summary.skipped > 0:
        parts.append(f"⏭️ Skipped: {summary.skipped}")
    if summary.xfailed is not None and summary.xfailed > 0:
        parts.append(f"🔶 Expected failures: {summary.xfailed}")
    if summary.xpassed is not None and summary.xpassed > 0:
        parts.append(f"🔶 Unexpected passes: {summary.xpassed}")

    return " | ".join(parts)
